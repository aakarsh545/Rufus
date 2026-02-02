# 🤖 Rufus AI Robot Companion v3.0

A friendly AI robot with voice conversation, expressive gestures, and WiFi web control.

**Features:**
- 🗣️ Voice conversation (OpenAI Whisper STT + GPT-4o-mini + TTS)
- 🦾 Expressive gestures (Arduino-controlled servos)
- 🌐 WiFi web control (Vercel-hosted interface)
- 📡 Full remote control from any device on your network

---

## 🎯 Current Setup

### Hardware
- **Raspberry Pi** (any model with WiFi)
- **Arduino Uno** (servo control)
- **3x SG90 Servos:**
  - Pan servo (head side-to-side)
  - Left arm
  - Right arm
- **5V/4A+ power supply** (for servos)

### Software Architecture
```
Vercel (Web Interface) → WiFi → Pi API Server → Arduino (Servos + TTS)
```

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/YOUR-USERNAME/rufus.git
cd rufus
```

### 2. Setup Raspberry Pi

**Upload Arduino code (from Mac):**
1. Open Arduino IDE
2. Load: `ARDUINO UNO CODE/CODE/rufus_10gestures/rufus_10gestures.ino`
3. Upload to Arduino

**Deploy Pi code (from Mac):**
```bash
# Deploy voice assistant
scp voice_stt_tts_fixed.py pi@rufus-pi.local:/home/pi/rufus/

# Deploy Pi API server
scp pi_api_server.py pi@rufus-pi.local:/home/pi/rufus/

# Deploy requirements
scp requirements_pi_api.txt pi@rufus-pi.local:/home/pi/rufus/
```

**On Pi:**
```bash
cd /home/pi/rufus
source venv/bin/activate
pip install -r requirements_pi_api.txt

# Create .env file with your OpenAI API key
echo "OPENAI_API_KEY=sk-your-key-here" > .env
```

### 3. Run Rufus

**Option A: Voice Assistant (yes/no/neutral gestures)**
```bash
cd /home/pi/rufus
source venv/bin/activate
python3 voice_stt_tts_fixed.py
```

**Option B: WiFi Control (full gestures via web)**
```bash
cd /home/pi/rufus
source venv/bin/activate
python3 pi_api_server.py
```

### 4. Deploy Web Interface to Vercel

See `VERCEL_DEPLOYMENT.md` for complete instructions.

**Quick version:**
1. Go to [Vercel.com](https://vercel.com)
2. Drag the `vercel-deploy/` folder onto Vercel
3. Open your deployed URL
4. Enter your Pi's IP: `http://YOUR_PI_IP:5001`
5. Control Rufus from any device! 📱

---

## 📁 Project Structure

```
rufus/
├── ARDUINO UNO CODE/CODE/
│   └── rufus_10gestures/rufus_10gestures.ino  # Servo executor
├── PYTHON CODE/CODE/
│   ├── templates/                            # Flask templates
│   ├── voice_stt_tts_fixed.py                # Voice assistant (yes/no/neutral)
│   └── requirements_voice.txt                # Dependencies
├── pi_api_server.py                          # WiFi API server
├── rufus_web_controller.py                    # Web controller (old version)
├── vercel-deploy/
│   └── index.html                            # Web interface for Vercel
├── templates/                                 # Flask templates
├── requirements_pi_api.txt                   # Pi API server deps
└── README.md                                  # This file
```

---

## 🎮 Features

### Voice Assistant
- ✅ Speech-to-text (OpenAI Whisper)
- ✅ AI conversation (GPT-4o-mini - cheap & fast!)
- ✅ Text-to-speech (OpenAI TTS - onyx deep voice)
- ✅ Gesture detection (yes, no, neutral)

### WiFi Web Control
- ✅ Servo angle sliders (real-time control)
- ✅ Gesture buttons (wave, nod, shake, happy, sad, excited, curious, rest)
- ✅ Text-to-speech panel
- ✅ Works from phone, tablet, any device on WiFi

### Gestures
| Gesture | Description |
|---------|-------------|
| 👋 Wave | Greeting/friendly hello |
| ✅ Nod (Yes) | Affirmative/agreement |
| ❌ Shake (No) | Negative/disagreement |
| 😊 Happy | Excited/joyful |
| 😢 Sad | Disappointed |
| 🎉 Excited | Celebration |
| 🤨 Curious | Interested/attentive |
| 😴 Rest | Return to neutral position |

---

## 🔧 Configuration

### Servo Limits
| Servo | Pin | Min | Rest | Max |
|-------|-----|-----|------|-----|
| Pan (head) | 2 | 0° | 90° | 180° |
| Left Arm | 4 | 50° | 90° | 180° |
| Right Arm | 5 | 50° | 90° | 180° |

### Arduino Serial Commands
Format: `pin:angle`
- `2:90` → Pan to center
- `4:120` → Left arm to 120°
- `5:60` → Right arm to 60°

---

## 📝 Documentation Files

- `VERCEL_DEPLOYMENT.md` - Deploy web interface to Vercel
- `SERVO_WIRING_GUIDE.md` - Complete servo wiring guide
- `bluetooth_config.txt` - Bluetooth audio configuration

---

## 🛠️ Troubleshooting

### Servos not moving
- Check external power supply connection
- Verify Arduino is connected to Pi
- Check common ground between power supply and Arduino

### Can't connect to Pi from web interface
- Ensure Pi and device are on same WiFi network
- Verify Pi API server is running on port 5001
- Check Pi's firewall settings

### AI not responding
- Verify OPENAI_API_KEY in `.env` file
- Check internet connection on Pi
- Ensure API key has credits

---

## 🤝 Contributing

Contributions welcome! Feel free to:
- Add new gestures
- Improve the web interface
- Fix bugs
- Add documentation

---

## 📄 License

MIT License - Feel free to use this project for your own robots!

---

## 🎉 Credits

Built with ❤️ by [Your Name]

**Technologies used:**
- OpenAI (Whisper, GPT-4o-mini, TTS)
- Flask (web server)
- Arduino (servo control)
- Vercel (web hosting)
