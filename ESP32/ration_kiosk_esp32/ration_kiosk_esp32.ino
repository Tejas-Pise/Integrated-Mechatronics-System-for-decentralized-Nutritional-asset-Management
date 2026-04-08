// ============================================================
//  SMART RATION KIOSK — ESP32 FIRMWARE
//  File: ration_kiosk_esp32.ino
//  IDE: Arduino IDE 2.x
//  Board: ESP32 Dev Module
// ============================================================

#include <SPI.h>
#include <MFRC522.h>
#include <Adafruit_Fingerprint.h>
#include <HX711.h>

// ── Pin Definitions ─────────────────────────────────────────
#define RFID_SS_PIN   5
#define RFID_RST_PIN  22

#define FP_TX_PIN     16
#define FP_RX_PIN     17

#define HX711_DT_PIN  4
#define HX711_SCK_PIN 2

#define ULTRASONIC_TRIG 13
#define ULTRASONIC_ECHO 12

#define DFPLAYER_RX   26
#define DFPLAYER_TX   27

#define STEPPER_STEP  14
#define STEPPER_DIR   15
#define STEPPER_EN    33

#define SOLENOID_PIN  25

// ── UART with Pi (GPIO21=TX, GPIO32=RX) ─────────────────────
#define PI_UART_TX    21
#define PI_UART_RX    32
HardwareSerial PiSerial(1);

// ── Fingerprint UART ─────────────────────────────────────────
HardwareSerial fpSerial(2);
Adafruit_Fingerprint finger = Adafruit_Fingerprint(&fpSerial);

// ── RFID ────────────────────────────────────────────────────
MFRC522 rfid(RFID_SS_PIN, RFID_RST_PIN);

// ── Load Cell ───────────────────────────────────────────────
HX711 scale;

// ── State ───────────────────────────────────────────────────
float targetWeight   = 0.0;
bool  dispensing     = false;
bool  stepperRunning = false;
String currentUID    = "";

// ── Calibration factor (calibrate once) ─────────────────────
float CALIBRATION_FACTOR = 2280.0;

// ============================================================
void setup() {
  Serial.begin(115200);
  PiSerial.begin(115200, SERIAL_8N1, PI_UART_RX, PI_UART_TX);

  // RFID
  SPI.begin();
  rfid.PCD_Init();

  // Fingerprint
  fpSerial.begin(57600, SERIAL_8N1, FP_TX_PIN, FP_RX_PIN);
  finger.begin(57600);

  // Load Cell
  scale.begin(HX711_DT_PIN, HX711_SCK_PIN);
  scale.set_scale(CALIBRATION_FACTOR);
  scale.tare();

  // Ultrasonic
  pinMode(ULTRASONIC_TRIG, OUTPUT);
  pinMode(ULTRASONIC_ECHO, INPUT);

  // Stepper
  pinMode(STEPPER_STEP, OUTPUT);
  pinMode(STEPPER_DIR,  OUTPUT);
  pinMode(STEPPER_EN,   OUTPUT);
  digitalWrite(STEPPER_EN, HIGH); // disabled by default

  // Solenoid
  pinMode(SOLENOID_PIN, OUTPUT);
  digitalWrite(SOLENOID_PIN, LOW);

  Serial.println("ESP32 Ready");
  PiSerial.println("ESP32_READY");
}

// ============================================================
void loop() {
  handlePiCommands();
  if (dispensing) runDispenser();
  checkStock();
  delay(10);
}

// ── Pi Command Handler ───────────────────────────────────────
void handlePiCommands() {
  if (!PiSerial.available()) return;
  String cmd = PiSerial.readStringUntil('\n');
  cmd.trim();

  if (cmd == "SCAN_RFID") {
    scanRFID();
  } else if (cmd == "SCAN_FINGER") {
    scanFingerprint();
  } else if (cmd.startsWith("DISPENSE:")) {
    targetWeight = cmd.substring(9).toFloat();
    startDispensing();
  } else if (cmd == "STOP") {
    stopDispensing();
  } else if (cmd == "TARE") {
    scale.tare();
    PiSerial.println("TARE_DONE");
  } else if (cmd == "WEIGHT?") {
    float w = scale.get_units(3);
    PiSerial.println("WEIGHT:" + String(w, 2));
  }
}

// ── RFID ────────────────────────────────────────────────────
void scanRFID() {
  PiSerial.println("RFID_SCANNING");
  unsigned long start = millis();
  while (millis() - start < 10000) { // 10 second timeout
    if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
      delay(50);
      continue;
    }
    currentUID = "";
    for (byte i = 0; i < rfid.uid.size; i++) {
      if (rfid.uid.uidByte[i] < 0x10) currentUID += "0";
      currentUID += String(rfid.uid.uidByte[i], HEX);
    }
    currentUID.toUpperCase();
    rfid.PICC_HaltA();
    PiSerial.println("RFID:" + currentUID);
    return;
  }
  PiSerial.println("RFID_TIMEOUT");
}

// ── Fingerprint ──────────────────────────────────────────────
void scanFingerprint() {
  PiSerial.println("FP_SCANNING");
  int id = getFingerprintID();
  if (id > 0) {
    PiSerial.println("FP_MATCH:" + String(id));
  } else if (id == -2) {
    PiSerial.println("FP_NO_MATCH");
  } else {
    PiSerial.println("FP_TIMEOUT");
  }
}

int getFingerprintID() {
  unsigned long start = millis();
  while (millis() - start < 10000) {
    int p = finger.getImage();
    if (p == FINGERPRINT_OK) {
      p = finger.image2Tz();
      if (p == FINGERPRINT_OK) {
        p = finger.fingerFastSearch();
        if (p == FINGERPRINT_OK) return finger.fingerID;
        return -2; // no match
      }
    }
    delay(100);
  }
  return -1; // timeout
}

// ── Dispenser ────────────────────────────────────────────────
void startDispensing() {
  scale.tare();
  digitalWrite(SOLENOID_PIN, HIGH);
  digitalWrite(STEPPER_EN, LOW);
  digitalWrite(STEPPER_DIR, HIGH);
  dispensing = true;
  PiSerial.println("DISPENSE_START");
}

void stopDispensing() {
  dispensing = false;
  digitalWrite(SOLENOID_PIN, LOW);
  digitalWrite(STEPPER_EN, HIGH);
  PiSerial.println("DISPENSE_STOP");
}

void runDispenser() {
  float currentWeight = scale.get_units(5);
  PiSerial.println("WEIGHT:" + String(currentWeight, 2));

  if (currentWeight >= targetWeight) {
    stopDispensing();
    PiSerial.println("DISPENSE_DONE:" + String(currentWeight, 2));
    return;
  }

  // Step motor one pulse
  digitalWrite(STEPPER_STEP, HIGH);
  delayMicroseconds(800);
  digitalWrite(STEPPER_STEP, LOW);
  delayMicroseconds(800);
}

// ── Stock Monitor ────────────────────────────────────────────
void checkStock() {
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck < 5000) return;
  lastCheck = millis();

  float dist = getUltrasonicDistance();
  PiSerial.println("STOCK:" + String(dist, 1));

  if (dist > 25.0) { // hopper getting low (adjust per your hopper size)
    PiSerial.println("STOCK_LOW:" + String(dist, 1));
  }
}

float getUltrasonicDistance() {
  digitalWrite(ULTRASONIC_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(ULTRASONIC_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(ULTRASONIC_TRIG, LOW);
  long dur = pulseIn(ULTRASONIC_ECHO, HIGH, 30000);
  return (dur * 0.034) / 2.0;
}