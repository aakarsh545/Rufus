#!/usr/bin/env python3
"""
Complete Voice AI Assistant - STT → GPT-4o-mini (Speech + Commands) → TTS
OpenAI generates TWO outputs:
1. Speech: What Rufus SAYS aloud
2. Commands: What Rufus DOES silently (servos, camera, etc.)

Uses ONLY OpenAI API (cheaper option - GPT-4o-mini is ~20x cheaper than Claude)
"""

import os
import json
import tempfile
import time
import serial
import threading
import soundfile as sf
import sounddevice as sd
from openai import OpenAI
from dotenv import load_dotenv
import pygame

# Load API key from .env file
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    print("❌ OPENAI_API_KEY not found in .env file!")
    print("   Run: python3 setup_voice.py")
    exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)

# Initialize pygame mixer for audio playback
pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)

# === ARDUINO SERIAL SETUP ===
ARDUINO_PORT = "/dev/ttyACM0"  # Pi default Arduino port
ARDUINO_BAUD = 9600
arduino = None

# Servo pin assignments
SERVO_PINS = {
    "head": 2,      # Pan servo
    "pan": 2,       # Alias for head
    "left_arm": 4,
    "right_arm": 5
}

# Servo rest positions
SERVO_REST = {
    "head": 90,
    "pan": 90,
    "left_arm": 90,
    "right_arm": 90
}

def init_arduino():
    """Initialize Arduino serial connection"""
    global arduino
    try:
        arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
        time.sleep(2)  # Wait for Arduino to reset

        # Wait for READY signal
        while True:
            if arduino.in_waiting > 0:
                response = arduino.readline().decode('utf-8').strip()
                if response == "READY":
                    print("✅ Arduino connected!")
                    return True

        print("✅ Arduino connected!")
        return True
    except Exception as e:
        print(f"⚠️  Arduino not connected: {e}")
        print("   Continuing without servo control...")
        return False

def send_servo_command(servo, angle):
    """Send servo command to Arduino"""
    global arduino

    if not arduino or not arduino.is_open:
        return False

    try:
        pin = SERVO_PINS.get(servo)
        if not pin:
            print(f"❌ Unknown servo: {servo}")
            return False

        command = f"{pin}:{angle}\n"
        arduino.write(command.encode('utf-8'))

        # Wait for acknowledgment
        time.sleep(0.05)
        if arduino.in_waiting > 0:
            response = arduino.readline().decode('utf-8').strip()
            return response.startswith("OK")

        return False
    except Exception as e:
        print(f"❌ Servo command failed: {e}")
        return False

def smooth_move(servo, target_angle, steps=10, delay=0.02):
    """Smooth servo movement"""
    global arduino

    if not arduino or not arduino.is_open:
        return

    try:
        current_pos = SERVO_REST.get(servo, 90)
        step_size = (target_angle - current_pos) / steps

        for i in range(steps):
            angle = int(current_pos + (step_size * (i + 1)))
            send_servo_command(servo, angle)
            time.sleep(delay)
    except Exception as e:
        print(f"❌ Smooth move failed: {e}")

# Audio settings
SAMPLE_RATE = 16000
DURATION_SEC = 5
RECORD_WAV = "input_5s.wav"

TTS_MODEL = "tts-1"
VOICE = "onyx"  # Deepest voice
WHISPER_MODEL = "whisper-1"
CHAT_MODEL = "gpt-4o-mini"  # Cheap and fast!
MAX_TURNS = 10

# === SYSTEM PROMPT ===
SYSTEM_PROMPT = """You are Rufus, a friendly, playful AI robot companion with a physical body.

IMPORTANT: You must respond with valid JSON in this exact format:
{
  "speech": "your full conversational response (detailed, friendly, 2-4 sentences)",
  "gesture": "yes|no|neutral"
}

GESTURE RULES:
- Analyze the USER'S INPUT and summarize it to: YES, NO, or NEUTRAL
- "yes" = User said something positive, agreeing, asking "yes" questions, greeting
- "no" = User said something negative, disagreeing, asking "no" questions
- "neutral" = Everything else (questions, statements, confusion, etc.)

Give FULL, detailed responses:
- Explain things thoroughly
- Be conversational and friendly
- Don't be too brief - expand on your answers
- Show enthusiasm and personality
- Use 2-4 sentences typically, more if needed

Examples:
User: "Hello!" → {"speech": "Well hello there! It's absolutely wonderful to see you! I'm Rufus, your friendly AI robot companion, and I'm really excited we get to chat today. How can I help you?", "gesture": "yes"}

User: "Are you a robot?" → {"speech": "I sure am! I'm Rufus, a friendly AI robot companion made with cardboard and servos. I love having conversations and helping out however I can. It's pretty cool being a robot!", "gesture": "neutral"}

User: "What's the weather?" → {"speech": "I don't actually have access to weather data or internet information, so I can't tell you what the weather's like right now. You could check a weather app or website for that! Is there anything else I can help you with instead?", "gesture": "neutral"}

User: "Tell me about space" → {"speech": "Space is absolutely fascinating! It's the vast expanse beyond Earth's atmosphere, filled with countless stars, planets, galaxies, and mysteries we're still discovering. Humans have been exploring space for decades, and there's still so much more to learn about our universe!", "gesture": "neutral"}

Be warm, friendly, and give thorough, detailed answers!"""

# Conversation memory (remembers last 10 turns)
conversation_history = []
MAX_TURNS = 10

def add_to_memory(role, content):
    """Add message to Claude's conversation memory"""
    conversation_history.append({"role": role, "content": content})
    # Keep only last MAX_TURNS exchanges
    if len(conversation_history) > MAX_TURNS * 2 + 1:
        conversation_history[:] = conversation_history[-(MAX_TURNS * 2 + 1):]

def record_audio(duration=DURATION_SEC):
    """Record audio from microphone"""
    print(f"\n🎤 Recording for {duration} seconds...")
    print("   (Speak now!)")

    try:
        audio = sd.rec(
            int(duration * SAMPLE_RATE),
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16"
        )
        sd.wait()
        sf.write(RECORD_WAV, audio, SAMPLE_RATE, subtype="PCM_16")
        print("✅ Recording saved")
        return True
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return False

def transcribe_audio():
    """Transcribe audio using Whisper"""
    print("\n📝 Transcribing with Whisper...")

    try:
        with open(RECORD_WAV, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=WHISPER_MODEL,
                file=audio_file
            )
        text = transcript.text.strip()
        print(f"✅ You said: '{text}'")
        return text
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return None

def speak_text(text):
    """Convert text to speech using OpenAI TTS and play with pygame"""
    print(f"\n🔊 Speaking: '{text}'")

    try:
        # Get speech from OpenAI
        response = client.audio.speech.create(
            model=TTS_MODEL,
            voice=VOICE,
            input=text,
            response_format="wav"
        )

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file = f.name
            f.write(response.content)

        # Play with pygame
        sound = pygame.mixer.Sound(temp_file)
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))

        # Clean up
        os.unlink(temp_file)
        print("✅ Playback complete")
        return True

    except Exception as e:
        print(f"❌ TTS failed: {e}")
        return False

def get_ai_response(user_message):
    """Get response from GPT-4o-mini with structured output (speech + actions)"""
    print("\n🧠 Rufus is thinking...")

    add_to_memory("user", user_message)

    # Build messages with system prompt
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    try:
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            max_tokens=500,
            temperature=0.8,
            response_format={"type": "json_object"}  # Force JSON output!
        )

        response_text = response.choices[0].message.content.strip()
        print(f"📤 GPT-4o-mini raw response:\n{response_text}\n")

        # Parse JSON response
        response_data = json.loads(response_text)

        speech = response_data.get("speech", "")
        gesture = response_data.get("gesture", "neutral")

        # Add AI's speech to memory (only the speech part, not JSON)
        add_to_memory("assistant", speech)

        return speech, gesture

    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse AI's JSON: {e}")
        return "I'm having trouble processing that right now.", "neutral"

    except Exception as e:
        print(f"❌ OpenAI API failed: {e}")
        return "Something went wrong. Can you try again?", "neutral"

def execute_gesture(gesture):
    """Execute simple gesture (yes, no, or neutral)"""
    if not gesture or gesture == "neutral":
        return

    print(f"\n⚙️  Gesture: {gesture}")

    if gesture == "yes":
        gesture_nod()
    elif gesture == "no":
        gesture_shake()

    print("✅ Gesture complete")

def perform_gesture(gesture_name):
    """Perform predefined gesture"""
    gestures = {
        "wave": lambda: gesture_wave(),
        "nod": lambda: gesture_nod(),
        "shake": lambda: gesture_shake(),
        "rest": lambda: gesture_rest()
    }

    gesture_func = gestures.get(gesture_name)
    if gesture_func:
        gesture_func()

def perform_mood_gesture(mood):
    """Perform gesture based on mood"""
    mood_gestures = {
        "happy": lambda: mood_happy(),
        "sad": lambda: mood_sad(),
        "excited": lambda: mood_excited(),
        "curious": lambda: mood_curious()
    }

    mood_func = mood_gestures.get(mood)
    if mood_func:
        mood_func()

# === GESTURE FUNCTIONS ===

def gesture_wave():
    """Wave hello/goodbye"""
    smooth_move("head", 90)
    time.sleep(0.2)
    for _ in range(3):
        smooth_move("right_arm", 70, steps=5)
        time.sleep(0.15)
        smooth_move("right_arm", 40, steps=5)
        time.sleep(0.15)
    gesture_rest()

def gesture_nod():
    """Nod yes"""
    for _ in range(2):
        smooth_move("head", 105, steps=5)
        time.sleep(0.15)
        smooth_move("head", 75, steps=5)
        time.sleep(0.15)
    smooth_move("head", 90)

def gesture_shake():
    """Shake no"""
    for _ in range(2):
        smooth_move("head", 65, steps=5)
        time.sleep(0.15)
        smooth_move("head", 115, steps=5)
        time.sleep(0.15)
    smooth_move("head", 90)

def gesture_rest():
    """Return to rest"""
    smooth_move("head", 90)
    smooth_move("left_arm", 90)
    smooth_move("right_arm", 90)

# === MOOD FUNCTIONS ===

def mood_happy():
    """Happy gesture"""
    smooth_move("left_arm", 170, steps=5)
    smooth_move("right_arm", 170, steps=5)
    time.sleep(0.3)
    for _ in range(3):
        smooth_move("head", 75, steps=3)
        time.sleep(0.1)
        smooth_move("head", 105, steps=3)
        time.sleep(0.1)
    gesture_rest()

def mood_sad():
    """Sad gesture"""
    smooth_move("head", 50, steps=10)
    time.sleep(0.3)
    smooth_move("left_arm", 60, steps=10)
    smooth_move("right_arm", 60, steps=10)
    time.sleep(1.5)
    gesture_rest()

def mood_excited():
    """Excited gesture"""
    smooth_move("left_arm", 170, steps=3)
    smooth_move("right_arm", 170, steps=3)
    time.sleep(0.2)
    for _ in range(2):
        smooth_move("head", 60, steps=4)
        smooth_move("head", 120, steps=4)
    gesture_rest()

def mood_curious():
    """Curious gesture"""
    smooth_move("head", 70, steps=10)
    time.sleep(0.2)
    smooth_move("left_arm", 110, steps=10)
    smooth_move("right_arm", 110, steps=10)
    time.sleep(1.0)
    gesture_rest()

def clear_memory():
    """Clear conversation memory"""
    global conversation_history
    conversation_history.clear()
    print("🧹 Memory cleared!")

def main():
    print("=" * 60)
    print("🤖 Voice AI Assistant - Rufus (OpenAI GPT-4o-mini)")
    print("=" * 60)
    print("Flow: STT → GPT-4o-mini (Speech + Commands) → TTS")
    print("=" * 60)

    # Initialize Arduino connection
    print("🔌 Connecting to Arduino...")
    init_arduino()

    print("=" * 60)
    print("Commands:")
    print("  1. Press ENTER to speak (5 seconds)")
    print("  2. Type your message directly")
    print("  3. Type 'clear' to reset memory")
    print("  4. Type 'exit' to quit")
    print("=" * 60)

    while True:
        user_input = input("\n>>> Your turn: ").strip()

        if user_input.lower() == "exit":
            print("👋 Goodbye! Rufus powering down...")
            break

        if user_input.lower() == "clear":
            clear_memory()
            continue

        # Get user message (voice or text)
        if user_input:
            # User typed text
            print(f"\n📝 You typed: '{user_input}'")
            user_message = user_input
        else:
            # User wants to speak
            if not record_audio():
                continue

            user_message = transcribe_audio()
            if not user_message:
                continue

        # Get AI response (speech + gesture)
        speech, gesture = get_ai_response(user_message)

        # Execute gesture silently (NOT spoken)
        execute_gesture(gesture)

        # Speak the response aloud
        if speech:
            speak_text(speech)

if __name__ == "__main__":
    main()
