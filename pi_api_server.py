#!/usr/bin/env python3
"""
Rufus Pi API Server
Receives commands from web interface (Vercel) via WiFi
Controls Arduino servos, gestures, and TTS
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import serial
import time
import os
from openai import OpenAI
from dotenv import load_dotenv
import pygame
import tempfile

app = Flask(__name__)
CORS(app)  # Allow requests from Vercel

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# Arduino serial setup
ARDUINO_PORT = "/dev/ttyACM0"
ARDUINO_BAUD = 9600
arduino = None

# Audio setup
pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=512)

# Servo pin assignments
SERVO_PINS = {
    "pan": 2,
    "left_arm": 4,
    "right_arm": 5
}

# Gesture sequences
GESTURES = {
    "wave": [
        ("pan", 90), ("right_arm", 70), ("right_arm", 40),
        ("right_arm", 70), ("right_arm", 40), ("right_arm", 70),
        ("right_arm", 40), ("left_arm", 90), ("right_arm", 90)
    ],
    "nod": [
        ("pan", 105), ("pan", 75), ("pan", 105), ("pan", 75), ("pan", 90)
    ],
    "shake": [
        ("pan", 65), ("pan", 115), ("pan", 65), ("pan", 115), ("pan", 90)
    ],
    "happy": [
        ("left_arm", 170), ("right_arm", 170), ("pan", 75),
        ("pan", 105), ("pan", 75), ("pan", 105),
        ("left_arm", 90), ("right_arm", 90), ("pan", 90)
    ],
    "sad": [
        ("pan", 50), ("left_arm", 60), ("right_arm", 60),
        ("pan", 50), ("left_arm", 90), ("right_arm", 90), ("pan", 90)
    ],
    "excited": [
        ("left_arm", 170), ("right_arm", 170), ("pan", 60),
        ("pan", 120), ("left_arm", 90), ("right_arm", 90), ("pan", 90)
    ],
    "curious": [
        ("pan", 70), ("left_arm", 110), ("right_arm", 110),
        ("pan", 70), ("left_arm", 90), ("right_arm", 90), ("pan", 90)
    ],
    "rest": [
        ("pan", 90), ("left_arm", 90), ("right_arm", 90)
    ]
}

def init_arduino():
    """Initialize Arduino connection"""
    global arduino
    try:
        arduino = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=1)
        time.sleep(2)
        while arduino.in_waiting > 0:
            response = arduino.readline().decode('utf-8').strip()
            if response == "READY":
                print("✅ Arduino connected!")
                return True
        return True
    except Exception as e:
        print(f"⚠️  Arduino not connected: {e}")
        return False

def send_servo_command(pin, angle):
    """Send servo command to Arduino"""
    global arduino
    if not arduino or not arduino.is_open:
        return False
    try:
        command = f"{pin}:{angle}\n"
        arduino.write(command.encode('utf-8'))
        time.sleep(0.05)
        return True
    except Exception as e:
        print(f"❌ Servo command failed: {e}")
        return False

def perform_gesture(gesture_name):
    """Execute a gesture sequence"""
    if gesture_name not in GESTURES:
        return False

    sequence = GESTURES[gesture_name]
    for servo, angle in sequence:
        pin = SERVO_PINS.get(servo)
        if pin:
            send_servo_command(pin, angle)
            time.sleep(0.15)
    return True

def speak_text(text):
    """Convert text to speech and play"""
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="onyx",
            input=text,
            response_format="wav"
        )

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            temp_file = f.name
            f.write(response.content)

        sound = pygame.mixer.Sound(temp_file)
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))

        os.unlink(temp_file)
        return True
    except Exception as e:
        print(f"❌ TTS failed: {e}")
        return False

# ==================== API ENDPOINTS ====================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'arduino_connected': arduino is not None})

@app.route('/api/servo', methods=['POST'])
def control_servo():
    """Control individual servo"""
    data = request.json
    servo = data.get('servo')
    angle = data.get('angle')

    pin = SERVO_PINS.get(servo)
    if not pin:
        return jsonify({'success': False, 'error': 'Unknown servo'})

    success = send_servo_command(pin, angle)
    return jsonify({'success': success})

@app.route('/api/gesture', methods=['POST'])
def trigger_gesture():
    """Trigger a gesture"""
    data = request.json
    gesture = data.get('gesture')

    success = perform_gesture(gesture)
    return jsonify({'success': success})

@app.route('/api/speak', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    data = request.json
    text = data.get('text')

    if not text:
        return jsonify({'success': False, 'error': 'No text provided'})

    success = speak_text(text)
    return jsonify({'success': success})

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI chat with gesture"""
    data = request.json
    user_message = data.get('message')

    if not user_message:
        return jsonify({'success': False, 'error': 'No message provided'})

    # Import the chat logic from voice_stt_tts_fixed.py
    # For now, return a simple response
    response = f"You said: {user_message}"
    gesture = "neutral"

    return jsonify({
        'success': True,
        'response': response,
        'gesture': gesture
    })

if __name__ == '__main__':
    print("🌐 Rufus Pi API Server")
    init_arduino()
    print("✅ Server running on http://0.0.0.0:5001")
    print("📡 Ready to receive commands from Vercel!")
    app.run(host='0.0.0.0', port=5001, debug=False)
