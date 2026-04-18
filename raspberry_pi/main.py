# main.py — Main kiosk controller
# Run with: python3 main.py

import time
import sys
import threading
import config
from uart_comm import UARTComm
from cloud     import (get_user_by_rfid, get_user_by_ration_card,
                       verify_fingerprint_id, get_monthly_quota,
                       record_transaction)
from payment   import generate_upi_qr, wait_for_payment, calculate_price
from voice     import speak
from stock     import StockMonitor
from ui        import KioskUI, pygame

class RationKiosk:
    def __init__(self):
        self.uart  = UARTComm()
        self.ui    = KioskUI()
        self.stock = StockMonitor(self.uart, self._on_stock_alert)
        self.stock.start()
        time.sleep(1)  # let ESP32 boot

    # ── Entry point ──────────────────────────────────────────
    def run(self):
        speak("welcome")
        while True:
            try:
                self._flow_authenticate()
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                self.ui.screen_error(str(e))
                speak("error")
                time.sleep(3)

    # ── Step 1 + 2: Auth + Biometric ────────────────────────
    def _flow_authenticate(self):
        while True:
            speak("scan_rfid")
            btn = self.ui.screen_welcome()
            start = time.time()

            # Wait for RFID or button touch (enter card manually)
            rfid_uid = self.uart.scan_rfid(timeout=15)

            if rfid_uid:
                user = get_user_by_rfid(rfid_uid)
            else:
                # Manual ration card entry (keyboard / numpad)
                card_no = self._get_manual_input("Enter Ration Card No:")
                user = get_user_by_ration_card(card_no) if card_no else None

            if not user:
                self.ui.screen_error("Card not found in database.")
                time.sleep(2)
                continue

            # ── Step 2: Fingerprint ──────────────────────────
            fp_verified = False
            for attempt in range(1, 4):
                self.ui.screen_fingerprint(attempt)
                speak("scan_finger")
                fp_id = self.uart.scan_fingerprint(timeout=10)
                if fp_id and verify_fingerprint_id(user["ration_card"], fp_id):
                    fp_verified = True
                    speak("fp_ok")
                    break
                speak("fp_fail")
                time.sleep(1)

            if not fp_verified:
                self.ui.screen_error("Fingerprint verification failed.")
                time.sleep(2)
                continue

            # ── Step 3: Cloud data ───────────────────────────
            speak("cloud_checking")
            quota = get_monthly_quota(user["ration_card"])

            if quota.get("remaining_kg", 0) <= 0:
                speak("no_quota")
                self.ui.screen_error("Monthly quota exhausted.")
                time.sleep(3)
                continue

            # ── Step 4: Show info + proceed to dispense ──────
            ok_btn, no_btn = self.ui.screen_user_info(user, quota)
            choice = self._wait_for_touch([ok_btn, no_btn])
            if choice == 1:  # Cancel
                continue

            self._flow_dispense(user, quota)
            return  # Loop back to welcome

    # ── Step 5–9: Dispense flow ──────────────────────────────
    def _flow_dispense(self, user: dict, quota: dict):
        scheme = quota.get("scheme_type", "PAID")
        is_free = scheme in config.FREE_SCHEME_TYPES
        grain  = "wheat"  # default; can add selection screen

        # Grain selection for paid users
        if not is_free:
            grain = self._select_grain()
            if not grain:
                return

        # Weight selection (simple fixed options)
        weight_kg = min(quota["remaining_kg"], 5.0)  # max 5kg per visit

        # Payment
        amount = 0.0
        txn_ref = "FREE"

        if not is_free:
            speak("scheme_paid")
            amount  = calculate_price(grain, weight_kg)
            qr_img, txn_ref = generate_upi_qr(
                amount, grain, user["ration_card"]
            )
            speak("payment_qr")
            confirm_btn, cancel_btn = self.ui.screen_payment(qr_img, amount, grain)
            choice = self._wait_for_touch([confirm_btn, cancel_btn], timeout=120)
            if choice == 1:  # Cancel
                return
            payment_ok = wait_for_payment(txn_ref, amount)
            if not payment_ok:
                self.ui.screen_error("Payment not confirmed.")
                time.sleep(3)
                return
            speak("payment_ok")
        else:
            speak("scheme_free")

        # ── Dispense ─────────────────────────────────────────
        speak("dispensing")
        done_event   = threading.Event()
        final_weight = {"w": 0.0}

        def on_weight(w):
            self.ui.screen_dispensing(grain, w, weight_kg)
            self.ui.flip()

        def on_done(w):
            final_weight["w"] = w
            done_event.set()

        self.uart.dispense(weight_kg, on_weight=on_weight, on_done=on_done)
        done_event.wait(timeout=120)

        actual_kg = final_weight["w"]
        speak("dispense_done")

        # ── Record transaction ────────────────────────────────
        mode = "FREE" if is_free else "PAID"
        record_transaction(
            user["ration_card"], grain, actual_kg,
            amount if not is_free else 0.0,
            mode, txn_ref
        )

        self.ui.screen_done(grain, actual_kg, amount, mode)
        time.sleep(4)

    # ── Helpers ──────────────────────────────────────────────
    def _select_grain(self) -> str | None:
        """Show grain selection, return chosen grain key."""
        btns = self.ui.screen_grain_select(config.GRAIN_PRICES)
        while True:
            pos = self.ui.get_touch()
            if not pos:
                time.sleep(0.05)
                continue
            for grain, rect in btns.items():
                if rect.collidepoint(pos):
                    return grain
            time.sleep(0.05)

    def _wait_for_touch(self, rects: list, timeout: int = 60) -> int:
        """Wait for touch on one of the rects. Returns 0-indexed match."""
        start = time.time()
        while time.time() - start < timeout:
            pos = self.ui.get_touch()
            if pos:
                for i, r in enumerate(rects):
                    if r.collidepoint(pos):
                        return i
            time.sleep(0.05)
        return -1  # timeout

    def _get_manual_input(self, prompt: str) -> str | None:
        """Simple on-screen keyboard placeholder — extend with pygame keyboard."""
        # For now: return None and rely on RFID only
        # TODO: implement pygame on-screen numpad
        return None

    def _on_stock_alert(self, dist_cm: float):
        """Called when stock is critically low."""
        self.ui.screen_error(f"Stock low! Hopper: {dist_cm:.1f}cm. Call operator.")
        speak("stock_low")


# ── Entry ─────────────────────────────────────────────────────
if __name__ == "__main__":
    kiosk = RationKiosk()
    kiosk.run()