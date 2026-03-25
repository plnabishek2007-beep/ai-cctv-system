import cv2
import time
import os
import threading
import requests
from collections import deque
from ultralytics import YOLO
from flask import Flask, jsonify
from dotenv import load_dotenv

# ================== LOAD ENV ==================
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = str(os.getenv("TELEGRAM_CHAT_ID"))

# ================== CONFIG ==================
SAVE_FOLDER = "evidence"
os.makedirs(SAVE_FOLDER, exist_ok=True)

ZONE = (100, 100, 400, 400)
LOITERING_THRESHOLD = 10
PRE_EVENT_BUFFER = 100
POST_EVENT_FRAMES = 200
COOLDOWN_ALERT = 20

# ================== TELEGRAM ==================
last_telegram_time = 0

def send_telegram_alert(msg, image_path=None, video_path=None):
    global last_telegram_time
    now = time.time()

    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram not configured")
        return

    if now - last_telegram_time < COOLDOWN_ALERT:
        return

    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": msg}
        )

        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as img:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto",
                    files={"photo": img},
                    data={"chat_id": TELEGRAM_CHAT_ID}
                )

        if video_path and os.path.exists(video_path):
            with open(video_path, "rb") as vid:
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendVideo",
                    files={"video": vid},
                    data={"chat_id": TELEGRAM_CHAT_ID}
                )

        print("📲 Alert Sent")
        last_telegram_time = now

    except Exception as e:
        print("❌ Telegram Error:", e)

# ================== FLASK ==================
app = Flask(__name__)
latest_alert = {"status": "SAFE"}
alert_history = []
lock = threading.Lock()

@app.route("/alert")
def alert():
    with lock:
        return jsonify(latest_alert)

@app.route("/history")
def history():
    with lock:
        return jsonify(alert_history[-20:])

def run_server():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

threading.Thread(target=run_server, daemon=True).start()

# ================== MODEL ==================
model = YOLO("yolov8n.pt")

# ================== VIDEO ==================
cap = cv2.VideoCapture(0)

pre_buffer = deque(maxlen=PRE_EVENT_BUFFER)
is_recording = False
recording_out = None
frames_recorded = 0

last_saved_time = 0
last_alert_time = 0
loitering_start = None

current_video_file = None
current_image_file = None

# ================== MAIN LOOP ==================
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # 🔥 Performance boost
    frame = cv2.resize(frame, (640, 480))

    pre_buffer.append(frame)

    intruder_detected = False
    tamper_detected = False
    threat = "LOW"

    h, w = frame.shape[:2]

    # ================== TAMPER ==================
    if frame.mean() < 10:
        tamper_detected = True
        intruder_detected = True

    # ================== YOLO DETECTION ==================
    results = model(frame, verbose=False)
    person_count = 0

    for result in results:
        for box in result.boxes:
            if int(box.cls[0]) == 0:  # person
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
                cv2.putText(frame, "PERSON", (x1, y1-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)

                # Intrusion zone check
                if x2 > ZONE[0] and x1 < ZONE[2] and y2 > ZONE[1] and y1 < ZONE[3]:
                    intruder_detected = True
                    person_count += 1

    # ================== CROWD ==================
    if person_count > 5:
        threat = "HIGH"
        intruder_detected = True

    # ================== DRAW ZONE ==================
    cv2.rectangle(frame, (ZONE[0], ZONE[1]), (ZONE[2], ZONE[3]), (255,0,0), 2)

    # ================== LOITERING ==================
    if intruder_detected:
        if loitering_start is None:
            loitering_start = time.time()
    else:
        loitering_start = None

    if loitering_start:
        if time.time() - loitering_start > LOITERING_THRESHOLD:
            threat = "HIGH"

    # ================== THREAT LEVEL ==================
    if tamper_detected:
        threat = "CRITICAL"
    elif intruder_detected and threat != "HIGH":
        threat = "MEDIUM"

    current_time = time.time()

    # ================== SAVE IMAGE ==================
    if intruder_detected and (current_time - last_saved_time > 5):
        current_image_file = os.path.join(SAVE_FOLDER, f"intruder_{int(current_time)}.jpg")
        cv2.imwrite(current_image_file, frame)
        last_saved_time = current_time

    # ================== VIDEO RECORD ==================
    if intruder_detected and not is_recording:
        current_video_file = os.path.join(SAVE_FOLDER, f"event_{int(current_time)}.avi")

        recording_out = cv2.VideoWriter(
            current_video_file,
            cv2.VideoWriter_fourcc(*'XVID'),
            20,
            (w, h)
        )

        for f in pre_buffer:
            recording_out.write(f)

        is_recording = True
        frames_recorded = 0

    if is_recording:
        recording_out.write(frame)
        frames_recorded += 1

        if frames_recorded >= POST_EVENT_FRAMES:
            is_recording = False
            recording_out.release()

            msg = f"🚨 Intruder Alert!\nThreat: {threat}\nLocation: Secured Area"
            send_telegram_alert(msg, current_image_file, current_video_file)

    # ================== API UPDATE ==================
    if intruder_detected and (current_time - last_alert_time > COOLDOWN_ALERT):
        alert_data = {
            "status": "INTRUDER",
            "threat": threat,
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "location": "Secured Area"
        }

        with lock:
            latest_alert.clear()
            latest_alert.update(alert_data)
            alert_history.append(alert_data)

        last_alert_time = current_time

    # ================== DISPLAY ==================
    if intruder_detected:
        cv2.putText(frame, f"🚨 {threat}", (50,50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 3)

    cv2.imshow("AI CCTV SYSTEM", frame)

    if cv2.waitKey(1) == 27:
        break

# ================== CLEANUP ==================
cap.release()
cv2.destroyAllWindows()
