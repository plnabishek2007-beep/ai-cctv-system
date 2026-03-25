# ai-cctv-system
AI-powered CCTV system with real-time threat detection, intrusion alerts, and Telegram notifications using YOLOv8.
# 🔍 AI Powered CCTV Camera

## 🚀 Overview

An AI-powered surveillance system that detects intrusions, analyzes threats, and sends real-time alerts using Telegram.

## 🧠 Features

* Real-time person detection (YOLOv8)
* Intrusion & loitering detection
* Threat level classification (LOW / MEDIUM / HIGH / CRITICAL)
* Telegram alerts with image & video evidence
* REST API for monitoring

## 🛠️ Tech Stack

* Python
* OpenCV
* YOLOv8 (Ultralytics)
* Flask
* Telegram Bot API

## 🔐 Security

* No personal data stored
* API keys secured using environment variables
* Privacy-first design

## ⚙️ Setup

1. Clone repo:

```bash
git clone https://github.com/your-username/ai-cctv-system.git
cd ai-cctv-system
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create `.env` file:

```
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id
```

4. Run:

```bash
python app.py
```

## 📡 API Endpoints

* `/alert` → Current alert
* `/history` → Last 20 alerts

## 🎯 Future Improvements

* Face recognition
* Cloud deployment
* Mobile dashboard
* AI threat prediction

## 📽️ Demo

(Add your demo video link here)

---

Built for Hackathon 🚀
