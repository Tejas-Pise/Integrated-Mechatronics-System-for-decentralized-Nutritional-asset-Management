# voice.py — Voice guidance using gTTS (Hindi + English)

import subprocess
import os
import threading
from gtts import gTTS
import tempfile

MESSAGES = {
    "welcome":         "Welcome. Please scan your ration card.",
    "scan_rfid":       "Please scan your RFID card or enter ration card number.",
    "scan_finger":     "Please place your finger on the sensor.",
    "fp_ok":           "Fingerprint verified successfully.",
    "fp_fail":         "Fingerprint not recognised. Please try again.",
    "cloud_checking":  "Please wait. Checking your details.",
    "scheme_free":     "You are eligible for free ration under government scheme.",
    "scheme_paid":     "Please select grain and quantity. Then scan QR to pay.",
    "payment_qr":      "Please scan the QR code to make payment.",
    "payment_ok":      "Payment received. Starting grain dispensing.",
    "dispensing":      "Dispensing grain. Please wait.",
    "dispense_done":   "Dispensing complete. Please collect your ration.",
    "stock_low":       "Stock level is low. Please contact the operator.",
    "no_quota":        "Your monthly quota is exhausted.",
    "error":           "An error occurred. Please contact the operator.",
}

def speak(key: str, lang: str = "en", blocking: bool = False):
    """Play voice message for given key."""
    text = MESSAGES.get(key, key)
    t = threading.Thread(target=_speak_worker, args=(text, lang))
    t.daemon = True
    t.start()
    if blocking:
        t.join()

def _speak_worker(text: str, lang: str):
    try:
        tts = gTTS(text=text, lang=lang)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts.save(f.name)
            subprocess.run(["mpg123", "-q", f.name], timeout=30)
            os.unlink(f.name)
    except Exception as e:
        # Fallback: espeak
        try:
            subprocess.run(["espeak", text], timeout=10)
        except:
            print(f"Voice error: {e}")

def speak_custom(text: str, lang: str = "en"):
    """Speak any custom text."""
    t = threading.Thread(target=_speak_worker, args=(text, lang))
    t.daemon = True
    t.start()