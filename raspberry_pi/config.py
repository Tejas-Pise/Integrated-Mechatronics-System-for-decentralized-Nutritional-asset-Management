# config.py — All configuration in one place

FIREBASE_CONFIG = {
    "apiKey": "YOUR_FIREBASE_API_KEY",
    "authDomain": "YOUR_PROJECT.firebaseapp.com",
    "databaseURL": "https://YOUR_PROJECT-default-rtdb.firebaseio.com",
    "projectId": "YOUR_PROJECT_ID",
    "storageBucket": "YOUR_PROJECT.appspot.com",
}

# UART port ESP32 is connected to
UART_PORT = "/dev/ttyS0"    # or /dev/serial0 on Pi
UART_BAUD = 115200

# TFT Display settings
TFT_WIDTH  = 480
TFT_HEIGHT = 320

# Dispense limits (kg)
MAX_GRAIN_KG = 10.0
MIN_GRAIN_KG = 0.5

# Stock alert threshold (cm from ultrasonic)
STOCK_LOW_CM = 20.0

# SMS/WhatsApp (Twilio or MSG91)
SMS_PROVIDER  = "msg91"  # or "twilio"
MSG91_API_KEY = "YOUR_MSG91_KEY"
MSG91_SENDER  = "KIOSK1"

# UPI Payment
UPI_ID        = "yourshop@upi"
UPI_NAME      = "PDS Ration Kiosk"
PAYMENT_TIMEOUT_SEC = 120

# Grain prices (₹ per kg) — update as needed
GRAIN_PRICES = {
    "wheat": 27,
    "rice":  32,
    "sugar": 40,
    "dal":   55,
}

# Government scheme: below poverty line gets free ration
FREE_SCHEME_TYPES = ["BPL", "AAY", "PMGKAY"]