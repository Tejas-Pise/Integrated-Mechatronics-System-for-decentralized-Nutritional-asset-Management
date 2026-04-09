# cloud.py — Firebase operations

import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import config

_initialized = False

def init_firebase():
    global _initialized
    if _initialized:
        return
    cred = credentials.Certificate("firebase_service_key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': config.FIREBASE_CONFIG['databaseURL']
    })
    _initialized = True


def get_user_by_rfid(rfid_uid: str) -> dict | None:
    """Fetch user record by RFID card UID."""
    init_firebase()
    ref = db.reference(f"users")
    users = ref.order_by_child("rfid_uid").equal_to(rfid_uid).get()
    if not users:
        return None
    return list(users.values())[0]


def get_user_by_ration_card(card_no: str) -> dict | None:
    """Fetch user by ration card number."""
    init_firebase()
    ref = db.reference(f"users/{card_no}")
    return ref.get()


def verify_fingerprint_id(ration_card_no: str, fp_id: int) -> bool:
    """Check stored fingerprint ID matches."""
    init_firebase()
    ref = db.reference(f"users/{ration_card_no}/fingerprint_id")
    stored = ref.get()
    return stored == fp_id


def get_monthly_quota(ration_card_no: str) -> dict:
    """Return monthly quota and remaining."""
    init_firebase()
    ref = db.reference(f"users/{ration_card_no}")
    user = ref.get()
    if not user:
        return {}
    month = datetime.now().strftime("%Y-%m")
    dispensed = user.get("dispensed", {}).get(month, 0)
    quota     = user.get("monthly_quota_kg", 5)
    return {
        "quota_kg":     quota,
        "dispensed_kg": dispensed,
        "remaining_kg": max(0, quota - dispensed),
        "scheme_type":  user.get("scheme_type", "PAID"),
        "family_size":  user.get("family_size", 1),
    }


def record_transaction(ration_card_no: str, grain: str, weight_kg: float,
                        amount_paid: float, mode: str, payment_ref: str = ""):
    """Write transaction to Firebase."""
    init_firebase()
    month = datetime.now().strftime("%Y-%m")
    ts    = datetime.now().isoformat()
    txn   = {
        "timestamp":   ts,
        "grain":       grain,
        "weight_kg":   weight_kg,
        "amount_paid": amount_paid,
        "mode":        mode,        # FREE or PAID
        "payment_ref": payment_ref,
    }
    # Push transaction log
    db.reference(f"transactions/{ration_card_no}").push(txn)

    # Update dispensed amount
    current = db.reference(
        f"users/{ration_card_no}/dispensed/{month}"
    ).get() or 0
    db.reference(
        f"users/{ration_card_no}/dispensed/{month}"
    ).set(current + weight_kg)


def update_stock_level(hopper_cm: float):
    """Update hopper level in Firebase."""
    init_firebase()
    db.reference("stock/hopper_distance_cm").set(hopper_cm)
    db.reference("stock/last_updated").set(datetime.now().isoformat())


def get_all_transactions(ration_card_no: str) -> list:
    """Get all past transactions for a user."""
    init_firebase()
    ref  = db.reference(f"transactions/{ration_card_no}")
    data = ref.get()
    if not data:
        return []
    return list(data.values())