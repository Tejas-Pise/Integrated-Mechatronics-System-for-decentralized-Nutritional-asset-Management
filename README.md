# Integrated Mechatronics System for Decentralized Nutritional Asset Management

A cyber-physical public distribution platform for controlled, auditable, and low-friction ration dispensing. The system integrates embedded sensing and actuation (ESP32), edge orchestration (Raspberry Pi), and cloud-backed entitlement records (Firebase) to support accountable nutritional asset delivery at decentralized kiosks.

## Abstract

Conventional ration distribution pipelines in decentralized settings are vulnerable to leakage, weak traceability, and inconsistent beneficiary verification. This project proposes and implements a mechatronic kiosk architecture that combines multimodal identity checks, quota-aware dispensing logic, closed-loop gravimetric control, and transaction logging. The design objective is to reduce fraud opportunity, improve service throughput, and maintain verifiable audit trails while preserving practical deployability under constrained infrastructure.

## Research Motivation and Problem Statement

Public food distribution systems must satisfy three constraints simultaneously:

1. Identity assurance: only eligible beneficiaries should receive allocations.
2. Quantity fidelity: physical dispensed mass should match entitlement and payment policy.
3. Traceable accountability: each transaction should be reconstructable for post-hoc audit.

This repository operationalizes those constraints as a working prototype with a dual-node hardware-software stack and explicit machine-level protocol between nodes.

## Contributions

1. A modular edge architecture separating hard real-time control (ESP32) from business workflow orchestration (Raspberry Pi).
2. A serial command/event protocol for deterministic coordination of scan, verification, and dispense phases.
3. A closed-loop dispensing routine based on load-cell feedback and target-mass termination.
4. A cloud integration layer for entitlement lookup, monthly quota accounting, and transaction persistence.
5. An operator-facing kiosk interface with voice prompts, stock alerts, and payment flow scaffolding.

## High-Level System Architecture

The platform is organized into three cooperating layers:

1. Embedded control plane (ESP32): sensor IO, actuator control, weight feedback, and stock telemetry.
2. Edge orchestration plane (Raspberry Pi): user journey, identity flow, payment logic, UI/voice interaction, and cloud sync.
3. Cloud data plane (Firebase): user records, dispensed quota totals, and transaction logs.

### End-to-End Workflow

1. User initiates session at kiosk.
2. RFID scan and optional manual card entry identify candidate beneficiary.
3. Fingerprint match confirms identity linkage.
4. Cloud quota lookup determines remaining monthly entitlement and scheme type.
5. If paid scheme, UPI QR is generated and payment confirmation is awaited.
6. Raspberry Pi requests ESP32 dispensing to target mass.
7. ESP32 streams real-time weight and sends completion event.
8. Transaction is recorded and monthly dispensed counter is updated.
9. Hopper stock telemetry is periodically published and low-stock alerts are raised.

## Repository Layout

```text
.
|-- ESP32/
|   `-- ration_kiosk_esp32/
|       `-- ration_kiosk_esp32.ino
|-- Firebase/
|   `-- database_rules.json
|-- raspberry_pi/
|   |-- cloud.py
|   |-- config.py
|   |-- main.py
|   |-- payment.py
|   |-- requirements.txt
|   |-- stock.py
|   |-- uart_comm.py
|   |-- ui.py
|   `-- voice.py
`-- README.md
```

## Implementation Status (As of 2026-04-21)

Implemented:

1. ESP32 firmware with RFID, fingerprint scan routine, load-cell integration, dispensing control, and ultrasonic stock reporting.
2. Raspberry Pi orchestration flow in main controller with authentication, quota check, payment branch, dispensing callbacks, and transaction write.
3. Firebase access module for user lookup, quota calculation, transaction append, and stock updates.
4. Pygame-based kiosk UI screens and voice prompt layer.

Partially implemented or placeholder behavior:

1. Payment verification currently returns success via placeholder logic and must be replaced by gateway callback/webhook integration.
2. Manual ration-card entry UI is stubbed in controller.
3. Firebase security rules file exists but is currently empty and requires deployment-grade hardening.
4. Python dependency list is currently empty and should be pinned before production deployment.

## ESP32 Firmware Specification

Firmware file: ESP32/ration_kiosk_esp32/ration_kiosk_esp32.ino

### Sensors and Actuators

1. RFID: MFRC522 (SPI).
2. Fingerprint sensor: UART-based Adafruit-compatible module.
3. Mass measurement: HX711 + load cell.
4. Hopper level: ultrasonic distance sensor.
5. Dispense actuation: stepper motor + driver and solenoid gate.

### Control Semantics

1. Dispenser starts with tare reset, solenoid open, and stepper enable.
2. Weight samples are emitted during dispensing.
3. Dispensing halts when current weight exceeds or equals target mass.
4. Stock distance is reported periodically; threshold breach emits low-stock event.

## UART Protocol Contract

### Commands (Raspberry Pi -> ESP32)

1. SCAN_RFID
2. SCAN_FINGER
3. DISPENSE:<target_weight_kg>
4. STOP
5. TARE
6. WEIGHT?

### Events/Responses (ESP32 -> Raspberry Pi)

1. ESP32_READY
2. RFID_SCANNING
3. RFID:<UID_HEX>
4. RFID_TIMEOUT
5. FP_SCANNING
6. FP_MATCH:<finger_id>
7. FP_NO_MATCH
8. FP_TIMEOUT
9. DISPENSE_START
10. WEIGHT:<kg>
11. DISPENSE_DONE:<kg>
12. DISPENSE_STOP
13. STOCK:<distance_cm>
14. STOCK_LOW:<distance_cm>

## Raspberry Pi Software Architecture

### Module Responsibilities

1. raspberry_pi/main.py: session state flow, authentication pipeline, scheme-specific branching, and transaction finalization.
2. raspberry_pi/uart_comm.py: serial transport abstraction, callback dispatch, blocking scan primitives, and dispense streaming callbacks.
3. raspberry_pi/cloud.py: Firebase initialization and CRUD-style service methods.
4. raspberry_pi/payment.py: UPI QR generation, payment polling scaffold, and pricing computation.
5. raspberry_pi/stock.py: stock event handling, cloud stock update, and external alert trigger.
6. raspberry_pi/ui.py: touchscreen workflows implemented in pygame.
7. raspberry_pi/voice.py: non-blocking spoken prompts via gTTS with system fallback.
8. raspberry_pi/config.py: deployment constants for serial, pricing, UI dimensions, and policy thresholds.

### Logical State Machine

At a conceptual level, the controller behaves as a finite-state process:

1. S0 Idle/Welcome
2. S1 Identity Capture (RFID/manual card)
3. S2 Biometric Verification
4. S3 Cloud Quota Evaluation
5. S4 Scheme Branch (FREE or PAID)
6. S5 Payment (PAID branch only)
7. S6 Dispensing
8. S7 Transaction Commit
9. S8 Session Completion -> S0

Any validation failure routes to error display and restart from S0.

## Data Model (Firebase, Current Usage)

Observed key paths in current code:

1. users/<ration_card_no>
2. users/<ration_card_no>/dispensed/<YYYY-MM>
3. transactions/<ration_card_no>/<auto_key>
4. stock/hopper_distance_cm
5. stock/last_updated

Representative user fields:

1. name
2. ration_card
3. rfid_uid
4. fingerprint_id
5. monthly_quota_kg
6. scheme_type
7. family_size

## Experimental and Deployment Prerequisites

### Hardware

1. ESP32 dev board
2. Raspberry Pi 3/4/5
3. MFRC522 RFID module
4. UART fingerprint sensor
5. HX711 + calibrated load cell
6. Ultrasonic sensor
7. Stepper motor and driver
8. Solenoid actuator
9. Protected power stage, fusing, and relay/driver isolation where required

### Software

1. Arduino IDE 2.x (ESP32 toolchain)
2. Python 3.10+ on Raspberry Pi
3. Firebase project with Realtime Database
4. Linux utilities for audio playback (for example mpg123 or espeak fallback)

## Reproducible Setup Procedure

### A. Flash and Validate ESP32

1. Open ESP32/ration_kiosk_esp32/ration_kiosk_esp32.ino in Arduino IDE.
2. Install required libraries: MFRC522, Adafruit Fingerprint Sensor Library, HX711.
3. Select ESP32 Dev Module and set baud to 115200.
4. Confirm pin mapping against physical wiring.
5. Upload and verify serial startup event ESP32_READY.

### B. Configure Raspberry Pi Runtime

1. Create Python virtual environment.
2. Install dependencies required by current modules (serial, pygame, firebase-admin, qrcode, pillow, gTTS, requests).
3. Place Firebase service account JSON at raspberry_pi/firebase_service_key.json or update path in cloud module.
4. Update raspberry_pi/config.py with project-specific database URL, pricing, UART port, and payment identity.
5. Launch controller from raspberry_pi/main.py.

### C. Configure Firebase

1. Populate beneficiary records with ration card, RFID UID, fingerprint ID, quota, and scheme type.
2. Add database security rules before field testing.
3. Validate read/write privileges using least-privilege principle.

## Calibration and Validation Protocol

For defensible performance reporting, calibrate and evaluate under controlled conditions.

1. Load-cell calibration:
   Use at least three known masses spanning expected dispense range and fit scale factor.
2. Dispense accuracy test:
   For each target mass, run repeated trials and report mean absolute error and standard deviation.
3. Biometric flow reliability:
   Measure false rejection events and timeout rate across user cohorts.
4. End-to-end latency:
   Report timing from session start to dispense completion under free and paid branches.
5. Stock alert validity:
   Confirm threshold crossing behavior against measured hopper levels.

Useful metrics include:

1. Mean dispense error (kg)
2. 95th percentile session duration (s)
3. Successful first-attempt biometric rate (%)
4. Cloud commit success rate (%)
5. Stock alert precision/recall against manual ground truth

## Security, Safety, and Ethical Considerations

1. Identity data is sensitive: store only required biometric references and enforce strict access control.
2. Payment and transaction data require tamper-evident logging and secure transport.
3. Serial protocol should be hardened against malformed or replayed command payloads.
4. Power electronics must include actuator-safe defaults and fault handling on reboot.
5. Inclusion concerns: provide assisted flow for users with fingerprint/RFID acquisition difficulties.

## Limitations

1. Payment confirmation path is currently non-production and must be replaced with verifiable gateway reconciliation.
2. Manual card-number input is currently a stub.
3. No formal automated test suite is committed yet for UART simulation and integration regression.
4. Firebase rule set and dependency lockfile are not yet finalized.

## Roadmap

1. Replace payment placeholder with webhook-verified transaction state machine.
2. Add robust serial parser with checksum/framing and explicit error codes.
3. Implement local offline queue with eventual cloud reconciliation.
4. Introduce automated hardware-in-the-loop and protocol-level integration tests.
5. Add operator analytics dashboard for multi-kiosk monitoring.

## Recommended Citation

If you use this repository in an academic report, thesis, or publication, cite it with commit hash and access date. Suggested BibTeX template:

```bibtex
@misc{ims_dnam_2026,
  title        = {Integrated Mechatronics System for Decentralized Nutritional Asset Management},
  author       = {Project Team},
  year         = {2026},
  howpublished = {Git repository},
  note         = {Accessed: YYYY-MM-DD, commit: <hash>}
}
```

## License and Governance

No license file is currently committed. Add an explicit license (for example MIT, BSD-3-Clause, or Apache-2.0) before external distribution.

## Contact

Add maintainer names, institutional affiliation, and contact channel for deployment collaboration and field validation studies.
