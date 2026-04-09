# uart_comm.py — Serial communication with ESP32

import serial
import threading
import time
import config

class UARTComm:
    def __init__(self):
        self.ser = serial.Serial(
            config.UART_PORT,
            config.UART_BAUD,
            timeout=1
        )
        self.callbacks = {}
        self._running  = True
        self._thread   = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def send(self, command: str):
        """Send command to ESP32."""
        msg = command.strip() + "\n"
        self.ser.write(msg.encode())

    def on(self, prefix: str, callback):
        """Register a callback for messages starting with prefix."""
        self.callbacks[prefix] = callback

    def _read_loop(self):
        while self._running:
            try:
                line = self.ser.readline().decode("utf-8").strip()
                if not line:
                    continue
                print(f"[ESP32] {line}")
                for prefix, cb in self.callbacks.items():
                    if line.startswith(prefix):
                        cb(line)
                        break
            except Exception as e:
                print(f"UART error: {e}")
                time.sleep(0.1)

    def scan_rfid(self, timeout=15) -> str | None:
        """Block until RFID scanned or timeout."""
        result = {"uid": None}
        event  = threading.Event()

        def on_rfid(line):
            if line.startswith("RFID:"):
                result["uid"] = line.split(":")[1]
                event.set()
            elif line == "RFID_TIMEOUT":
                event.set()

        self.on("RFID", on_rfid)
        self.on("RFID_TIMEOUT", on_rfid)
        self.send("SCAN_RFID")
        event.wait(timeout)
        return result["uid"]

    def scan_fingerprint(self, timeout=15) -> int | None:
        """Block until fingerprint matched or timeout."""
        result = {"fp_id": None}
        event  = threading.Event()

        def on_fp(line):
            if line.startswith("FP_MATCH:"):
                result["fp_id"] = int(line.split(":")[1])
            event.set()

        self.on("FP_MATCH",   on_fp)
        self.on("FP_NO_MATCH", on_fp)
        self.on("FP_TIMEOUT",  on_fp)
        self.send("SCAN_FINGER")
        event.wait(timeout)
        return result["fp_id"]

    def dispense(self, weight_kg: float, on_weight=None, on_done=None):
        """Start dispensing. Callbacks get live weight and done event."""
        def on_msg(line):
            if line.startswith("WEIGHT:") and on_weight:
                w = float(line.split(":")[1])
                on_weight(w)
            elif line.startswith("DISPENSE_DONE:") and on_done:
                w = float(line.split(":")[1])
                on_done(w)

        self.on("WEIGHT",       on_msg)
        self.on("DISPENSE_DONE", on_msg)
        self.send(f"DISPENSE:{weight_kg:.2f}")

    def stop_dispense(self):
        self.send("STOP")

    def get_weight(self) -> float:
        """One-shot weight reading."""
        result = {"w": 0.0}
        event  = threading.Event()
        def on_w(line):
            result["w"] = float(line.split(":")[1])
            event.set()
        self.on("WEIGHT", on_w)
        self.send("WEIGHT?")
        event.wait(2)
        return result["w"]

    def close(self):
        self._running = False
        self.ser.close()