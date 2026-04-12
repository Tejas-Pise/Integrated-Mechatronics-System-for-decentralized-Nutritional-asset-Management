# stock.py — Stock monitoring and alerts

import threading
import time
import requests
import config
from cloud import update_stock_level

class StockMonitor:
    def __init__(self, uart_comm, notify_callback=None):
        self.uart     = uart_comm
        self.notify   = notify_callback
        self.level_cm = 0.0
        self.alert_sent = False
        self._run     = True
        self._thread  = threading.Thread(target=self._monitor, daemon=True)

        # Register callback for stock messages from ESP32
        self.uart.on("STOCK:", self._on_stock)
        self.uart.on("STOCK_LOW:", self._on_stock_low)

    def start(self):
        self._thread.start()

    def _on_stock(self, line):
        try:
            self.level_cm = float(line.split(":")[1])
            update_stock_level(self.level_cm)
        except:
            pass

    def _on_stock_low(self, line):
        if not self.alert_sent:
            self.alert_sent = True
            print("STOCK LOW ALERT!")
            self._send_sms_alert(self.level_cm)
            if self.notify:
                self.notify(self.level_cm)

    def _monitor(self):
        """Periodically reset alert flag so next low reading alerts again after 1 hour."""
        while self._run:
            time.sleep(3600)
            self.alert_sent = False

    def get_percent(self) -> int:
        """Convert cm to percentage (0–100). Adjust max_cm to your hopper height."""
        max_cm = 50.0
        pct    = max(0, min(100, int(100 - (self.level_cm / max_cm) * 100)))
        return pct

    def _send_sms_alert(self, dist_cm: float):
        """Send SMS to admin via MSG91."""
        msg = f"ALERT: Ration kiosk stock low. Hopper distance: {dist_cm:.1f} cm. Refill needed."
        try:
            url = "https://api.msg91.com/api/sendhttp.php"
            params = {
                "authkey":  config.MSG91_API_KEY,
                "mobiles":  "91ADMIN_MOBILE_NUMBER",
                "message":  msg,
                "sender":   config.MSG91_SENDER,
                "route":    "4",
            }
            requests.get(url, params=params, timeout=5)
        except Exception as e:
            print(f"SMS error: {e}")