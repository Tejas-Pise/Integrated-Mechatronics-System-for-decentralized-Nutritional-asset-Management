# Integrated Mechatronics System for Decentralized Nutritional Asset Management

An IoT-enabled smart ration kiosk platform that combines embedded control, biometric identity verification, stock sensing, and cloud coordination to deliver transparent and accountable nutritional asset distribution.

## Overview

This project is structured as a multi-node system:

- ESP32 firmware controls field hardware (RFID, fingerprint scanner, load cell, stock sensor, motor, and solenoid).
- Raspberry Pi runs orchestration, payment, UI, voice workflow, and cloud integration modules.
- Firebase is used as the intended cloud backend for user, transaction, and stock records.

The goal is to support decentralized, low-friction ration dispensing with better traceability and fraud resistance.

## Repository Structure

.
|- ESP32/
|  |- ration_kiosk_esp32/
|     |- ration_kiosk_esp32.ino
|- Firebase/
|  |- database_rules.json
|- raspberry_pi/
|  |- cloud.py
|  |- config.py
|  |- main.py
|  |- payment.py
|  |- requirements.txt
|  |- stock.py
|  |- uart_comm.py
|  |- ui.py
|  |- voice.py

## Current Status

- ESP32 firmware is implemented with UART protocol and sensor-actuator control loops.
- Raspberry Pi module files and Firebase rules file are present as scaffold files and are currently empty.

## System Architecture

1. User arrives at kiosk and requests ration.
2. Identity is verified through RFID and/or fingerprint.
3. Eligibility and quota are checked in backend records.
4. Payment step is executed (if required by policy).
5. Raspberry Pi sends dispense command and target weight to ESP32.
6. ESP32 actuates dispenser until load-cell target is reached.
7. Stock level and transaction logs are pushed to cloud.

## ESP32 Firmware Features

Implemented in ration_kiosk_esp32.ino:

- RFID read with timeout and UID reporting
- Fingerprint match with timeout and no-match handling
- HX711 load-cell tare and weight feedback
- Stepper-driven dispensing loop with target weight stop condition
- Solenoid gate control
- Ultrasonic stock monitoring with low-stock alert
- UART command/response protocol with Raspberry Pi

### UART Command Protocol (Pi -> ESP32)

- SCAN_RFID
- SCAN_FINGER
- DISPENSE:<target_weight>
- STOP
- TARE
- WEIGHT?

### UART Event/Response Examples (ESP32 -> Pi)

- ESP32_READY
- RFID_SCANNING
- RFID:<UID>
- RFID_TIMEOUT
- FP_SCANNING
- FP_MATCH:<id>
- FP_NO_MATCH
- FP_TIMEOUT
- DISPENSE_START
- WEIGHT:<value>
- DISPENSE_DONE:<final_weight>
- DISPENSE_STOP
- STOCK:<distance_cm>
- STOCK_LOW:<distance_cm>

## Hardware Bill of Materials

- ESP32 development board
- Raspberry Pi (3/4/5 recommended)
- MFRC522 RFID module
- Adafruit-compatible fingerprint sensor
- HX711 + load cell
- Ultrasonic distance sensor
- Stepper motor + driver
- Solenoid valve/gate actuator
- Power supply and relay/protection circuitry as required

## Software Stack

- Arduino IDE 2.x for ESP32 firmware
- Python 3.10+ on Raspberry Pi
- Firebase (Authentication + Realtime Database or Firestore)

## Setup Guide

### 1) ESP32 Setup

1. Open ESP32/ration_kiosk_esp32/ration_kiosk_esp32.ino in Arduino IDE.
2. Install required libraries:
   - MFRC522
   - Adafruit Fingerprint Sensor Library
   - HX711
3. Select board: ESP32 Dev Module.
4. Verify pin mappings in code match your wiring.
5. Upload firmware and open serial monitor at 115200 baud.

### 2) Raspberry Pi Setup

1. Install Python 3.10+.
2. Create and activate virtual environment.
3. Add dependencies in requirements.txt.
4. Install dependencies with pip.
5. Implement module logic in:
   - main.py
   - uart_comm.py
   - cloud.py
   - payment.py
   - stock.py
   - ui.py
   - voice.py

### 3) Firebase Setup

1. Create Firebase project.
2. Choose database mode (Realtime Database or Firestore).
3. Configure security rules in Firebase/database_rules.json.
4. Add credentials/config to Raspberry Pi configuration layer.

## Suggested Python Module Responsibilities

- main.py: application entry point and workflow orchestration
- uart_comm.py: serial transport and command/response parsing
- cloud.py: cloud sync, quota checks, transaction persistence
- payment.py: payment gateway integration and status handling
- stock.py: stock threshold policies and refill notifications
- ui.py: kiosk display and interaction flow
- voice.py: local language prompts and audio feedback
- config.py: environment variables, serial port, and limits

## Data Model (Suggested)

- users: id, uid, fingerprint_id, entitlement, status
- ration_transactions: user_id, item, quantity, timestamp, amount, status
- stock: item, current_level, threshold, last_refill
- kiosks: kiosk_id, firmware_version, health, last_seen

## Security and Reliability Notes

- Validate all UART messages and reject malformed payloads.
- Add retry and timeout handling around cloud and payment APIs.
- Use signed request tokens between kiosk and backend.
- Keep audit logs immutable for transaction traceability.
- Calibrate load-cell factor per physical assembly before deployment.

## Development Roadmap

1. Implement Raspberry Pi UART manager and finite-state workflow.
2. Integrate Firebase authentication and quota validation.
3. Implement payment flow and transaction finalization.
4. Add UI and multilingual voice prompts.
5. Build end-to-end tests with simulated UART responses.
6. Deploy pilot on one kiosk and tune calibration/thresholds.

## Future Enhancements

- Offline-first sync with queued transaction replay
- OTA updates for ESP32 firmware
- Edge anomaly detection for fraud patterns
- Multi-kiosk dashboard with predictive stock alerts

## License

Add a project license file (for example, MIT) before public distribution.

## Contributors

Project team: add member names, roles, and contact channels here.
