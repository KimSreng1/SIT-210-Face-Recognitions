from picamera2 import Picamera2
import face_recognition
import numpy as np
import cv2
import os
import time
import threading
import requests
from datetime import datetime
from gpiozero import OutputDevice, LED, Buzzer
from mfrc522 import SimpleMFRC522
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- Telegram Config ---
BOT_TOKEN = "7779309577:AAGzezcekvVY0u_-7jf36w0m15gVJUy8bQc"
CHAT_ID = 632000439
TELEGRAM_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"

# --- GPIO Setup ---
relay = OutputDevice(23)
buzzer = Buzzer(24)
green_led = LED(25)
reader = SimpleMFRC522()

# --- Unlock Function ---
def unlock(source="Manual"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Access granted via {source}")
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
        "chat_id": CHAT_ID,
        "text": f"Access granted via {source} at {timestamp}"
    })
    relay.on()
    green_led.on()
    buzzer.on()
    time.sleep(0.5)
    buzzer.off()
    time.sleep(4.5)
    relay.off()
    green_led.off()
    print("Relay OFF (door locked)")

# --- Telegram Command Handler ---
async def unlock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == CHAT_ID:
        await update.message.reply_text("Unlocking door!")
        threading.Thread(target=unlock, args=("Telegram command",), daemon=True).start()
    else:
        await update.message.reply_text("You are not authorized.")

# --- Background System (Face + RFID + Camera) ---
def start_system():
    print("[SYSTEM] Starting camera + RFID system...")
    known_face_encodings = []
    known_face_names = []
    known_dir = "/home/kimsreng/face-recog/known"
    unknown_dir = "/home/kimsreng/face-recog/unknown_faces"

    for file in os.listdir(known_dir):
        if file.endswith(".jpg") or file.endswith(".png"):
            image = face_recognition.load_image_file(os.path.join(known_dir, file))
            encodings = face_recognition.face_encodings(image)
            if encodings:
                known_face_encodings.append(encodings[0])
                known_face_names.append(os.path.splitext(file)[0])
    print(f"Loaded {len(known_face_encodings)} known face(s).")

    rfid_detected = False
    rfid_id = None
    last_rfid_id = None
    last_rfid_time = 0
    known_rfid_ids = [605586077941, 868312045783]

    def rfid_loop():
        nonlocal rfid_detected, rfid_id
        while True:
            try:
                id, _ = reader.read_no_block()
                if id:
                    rfid_detected = True
                    rfid_id = id
                    time.sleep(0.2)
            except Exception as e:
                print(f"RFID error: {e}")
            time.sleep(0.1)

    threading.Thread(target=rfid_loop, daemon=True).start()

    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": "RGB888", "size": (640, 480)}))
    picam2.start()
    time.sleep(1)

    frame_count = 0
    last_recognized = None
    last_unlock_time = 0

    while True:
        if rfid_detected:
            if rfid_id != last_rfid_id or time.time() - last_rfid_time > 5:
                print(f"Scanned RFID ID: {rfid_id}")
                if rfid_id in known_rfid_ids:
                    threading.Thread(target=unlock, args=(f"RFID {rfid_id}",), daemon=True).start()
                    last_rfid_id = rfid_id
                    last_rfid_time = time.time()
                else:
                    print("Unknown RFID tag.")
            rfid_detected = False

        frame = picam2.capture_array()
        rgb_frame = frame[:, :, ::-1]
        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)

        if frame_count % 3 == 0:
            face_locations = face_recognition.face_locations(small_frame)
            face_encodings = face_recognition.face_encodings(small_frame, face_locations)
            face_names = []

            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                name = "Unknown"
                if True in matches:
                    index = matches.index(True)
                    name = known_face_names[index]
                face_names.append(name)

                if name != last_recognized or time.time() - last_unlock_time > 10:
                    if name == "Unknown":
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"unknown_{timestamp}.jpg"
                        path = os.path.join(unknown_dir, filename)
                        cv2.imwrite(path, frame)
                        caption = f"Unknown face detected at {timestamp}.\nTo unlock the door remotely, send /unlock."
                        with open(path, "rb") as photo:
                            requests.post(TELEGRAM_URL, data={"chat_id": CHAT_ID, "caption": caption}, files={"photo": photo})
                    else:
                        threading.Thread(target=unlock, args=(f"Face: {name}",), daemon=True).start()
                        last_recognized = name
                        last_unlock_time = time.time()

        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

        cv2.imshow("Face & RFID Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        frame_count += 1
        time.sleep(0.01)

# --- Main Entry Point ---
if __name__ == "__main__":
    threading.Thread(target=start_system, daemon=True).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("unlock", unlock_command))
    print("[TELEGRAM] Bot is listening...")
    app.run_polling()
