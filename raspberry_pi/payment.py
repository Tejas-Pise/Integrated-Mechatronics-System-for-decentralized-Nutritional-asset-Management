# payment.py — UPI QR code generation and verification

import qrcode
import io
import time
import hashlib
import requests
import config
from PIL import Image

def generate_upi_qr(amount: float, grain: str, ration_card: str) -> tuple[Image.Image, str]:
    """
    Returns (PIL Image of QR, transaction reference string).
    UPI deep-link format used by all Indian payment apps.
    """
    txn_ref = f"KIOSK{ration_card}{int(time.time())}"
    note    = f"Ration {grain} {ration_card}"
    upi_url = (
        f"upi://pay?"
        f"pa={config.UPI_ID}"
        f"&pn={config.UPI_NAME.replace(' ', '%20')}"
        f"&am={amount:.2f}"
        f"&cu=INR"
        f"&tn={note.replace(' ', '%20')}"
        f"&tr={txn_ref}"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=8,
        border=2,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    return img, txn_ref


def wait_for_payment(txn_ref: str, amount: float,
                     timeout: int = None) -> bool:
    """
    Poll for payment confirmation.
    In production: use Razorpay/PayU webhook instead of polling.
    This is a placeholder — replace with your payment gateway callback.
    """
    if timeout is None:
        timeout = config.PAYMENT_TIMEOUT_SEC

    print(f"Waiting for payment {txn_ref} ₹{amount:.2f}")
    # TODO: integrate Razorpay order status API here
    # For now: manual confirmation (shop operator presses button on UI)
    return True   # Replace with actual gateway check


def calculate_price(grain: str, weight_kg: float) -> float:
    """Return price in rupees."""
    rate = config.GRAIN_PRICES.get(grain, 30)
    return round(rate * weight_kg, 2)