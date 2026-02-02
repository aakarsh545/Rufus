# Deploy Rufus Web Interface to Vercel

## 📋 Files Created:
1. **pi_api_server.py** - Runs on Pi, receives WiFi commands
2. **vercel-deploy/index.html** - Web interface for Vercel

---

## 🚀 Step 1: Deploy Pi API Server

**On Mac:**
```bash
cd /Users/akarsh545/Workspaces/rufus
scp pi_api_server.py pi@rufus-pi.local:/home/pi/rufus/
scp requirements_pi_api.txt pi@rufus-pi.local:/home/pi/rufus/
```

**On Pi:**
```bash
cd /home/pi/rufus
source venv/bin/activate
pip install flask flask-cors
python3 pi_api_server.py
```

✅ Pi API server now runs on **http://0.0.0.0:5001**

---

## 🌐 Step 2: Deploy to Vercel

### Option A: Drag & Drop (Easiest)
1. Go to [Vercel.com](https://vercel.com)
2. Click "New Project"
3. Drag the **`vercel-deploy`** folder onto Vercel
4. Click "Deploy"

### Option B: Vercel CLI
```bash
npm install -g vercel
cd /Users/akarsh545/Workspaces/rufus/vercel-deploy
vercel
```

---

## ⚙️ Step 3: Configure Web Interface

1. **Open your deployed Vercel URL** (e.g., `https://rufus-controller.vercel.app`)
2. **Find your Pi's IP address:**
   ```bash
   # On Pi
   hostname -I
   ```
3. **Enter Pi URL in web interface:**
   - Format: `http://YOUR_PI_IP:5001`
   - Example: `http://192.168.1.100:5001`
4. **Click "Save & Connect"**

---

## 🎮 Step 4: Control Rufus!

Once connected, you can:
- ✅ Move servos with sliders
- ✅ Trigger gestures (wave, nod, shake, etc.)
- ✅ Make Rufus speak (text-to-speech)

**All from your phone/tablet/any device on WiFi!** 📱

---

## 🔄 Architecture:

```
Your Device (WiFi)
     ↓
Vercel (Web Interface)
     ↓
HTTP Request
     ↓
Pi API Server (port 5001)
     ↓
Arduino (Servos + TTS)
```

---

## 📌 Notes:

- Pi and device must be on **same WiFi network**
- Pi API server must be **running** to control Rufus
- Vercel URL works from **anywhere** (but only connects when on same WiFi as Pi)
- Make sure Pi's **port 5001** is open if using firewall

---

## 🧪 Testing:

1. Run Pi API server
2. Open Vercel URL in browser
3. Enter Pi IP: `http://192.168.1.XX:5001`
4. Click "Save & Connect"
5. Try moving a servo slider
6. Try a gesture button
7. Try text-to-speech

**Should work instantly!** 🚀
