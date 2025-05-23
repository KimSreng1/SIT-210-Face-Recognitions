# SIT-210-Face-Recognitions
A Raspberry Pi-based smart access control system using face recognition, RFID authentication, and Telegram bot commands for secure and remote unlocking.

# Smart Access Control System

This project is a secure, Raspberry Pi-based access control system that combines local authentication methods (face recognition and RFID tags) with remote control via a Telegram bot. It's designed for home, office, or lab environments where you want smart, real-time, and flexible access management.

## 🚀 Features

- **Face Recognition** using the PiCamera2 and `face_recognition` library
- **RFID Tag Scanning** using MFRC522 module
- **Remote Unlock via Telegram Bot** by sending `/unlock`
- **Alerts for Unknown Faces** — photo + notification sent instantly to Telegram
- **Relay, Buzzer, and LED** simulate a physical door lock with feedback

## 📦 Hardware Used

- Raspberry Pi (tested on Bookworm OS)
- PiCamera2
- MFRC522 RFID reader (via SPI)
- Relay module (for door lock simulation)
- Buzzer + LED (for feedback)

## 🛠 Software & Libraries

- `picamera2`
- `face_recognition`
- `opencv-python`
- `gpiozero`
- `mfrc522`
- `python-telegram-bot`
- `asyncio`, `threading`, `requests`

## 📷 System Demo

Watch the full project demo video here:  
👉 [Insert your YouTube or Google Drive video link here]

## 🔧 How to Run

1. Clone this repo to your Raspberry Pi:
   ```bash
   git clone https://github.com/yourusername/smart-access-control.git
   cd smart-access-control

