# IoT Glucose Monitor - Daily Development Log

## 2025-08-19 - Day 1: Project Initiation & Architecture Design

### Hardware Architecture Selection
**MCU**: STM32L4 series (ultra-low power, 32-bit ARM Cortex-M4)
- Power consumption: 36 µA/MHz in Run mode, 1.28 µA in Stop 2 mode
- Integrated security features (TrustZone, hardware crypto)
- 512KB Flash, 160KB SRAM sufficient for firmware + data logging

**Glucose Sensor**: Electrochemical glucose oxidase sensor
- Abbott FreeStyle Libre sensor technology approach
- Sensitivity: 0.1 nA/(mg/dL)
- Linear range: 20-500 mg/dL
- Warm-up time: <60 minutes

**Connectivity Stack**:
- Primary: Bluetooth 5.0 LE (nRF52840 companion chip)
- Secondary: WiFi 802.11 b/g/n (ESP32-C3)
- Backup: Cellular IoT (Quectel BG96 NB-IoT/Cat-M1)

**Power Management**:
- Primary: 230 mAh Li-ion pouch cell
- Solar harvesting: 2cm² amorphous silicon panel
- Target: 14-day operation without charging

### Software Architecture
```
├── Application Layer
│   ├── Glucose Algorithm (Kalman filtering)
│   ├── Alarm Management (hypo/hyperglycemia)
│   └── Data Logger (local SQLite)
├── Communication Layer  
│   ├── BLE GATT Server (glucose service UUID 0x1808)
│   ├── WiFi Manager (OTA updates)
│   └── Cloud Sync (AWS IoT Core via MQTT)
├── Security Layer
│   ├── TLS 1.3 encryption
│   ├── Device identity (X.509 certificates)
│   └── Secure element (ATECC608A)
└── Hardware Abstraction Layer
    ├── Sensor drivers (SPI glucose sensor)
    ├── Power management (smart charging)
    └── Real-time clock (backup domain)
```

### Regulatory Classification
**FDA Class**: II Medical Device (510(k) required)
**Predicate Device**: Dexcom G6 (K173220)
**Standards Required**:
- IEC 62304: Medical device software lifecycle
- ISO 14971: Risk management 
- IEC 60601-1: General safety requirements
- ISO 10993: Biological evaluation

### Risk Analysis Initiation
**High-risk items identified**:
1. Sensor accuracy (HARM: incorrect insulin dosing)
2. Alarm reliability (HARM: missed hypoglycemia)
3. Data integrity (HARM: treatment decisions on corrupt data)
4. Cybersecurity (HARM: data breach, device manipulation)

### Next Steps (Day 2)
- [ ] Complete detailed glucose algorithm design
- [ ] Create sensor calibration protocol
- [ ] Design PCB layout (4-layer, impedance controlled)
- [ ] Setup development environment (PlatformIO + ESP-IDF)
- [ ] Begin FDA Q-Sub preparation

### Issues Encountered
- **Sensor supplier lead time**: 12 weeks for custom glucose sensors
- **Mitigation**: Source development sensors from multiple vendors
- **Power budget concern**: Initial calculations show 16-day life, need optimization

### Code Commits Today
- `feat: Initial STM32L4 HAL setup with low-power configuration`
- `feat: Bluetooth LE glucose service implementation (UUID 0x1808)`
- `docs: Architecture decision records for MCU and sensor selection`

### Test Results
**Power Consumption Baseline**:
- Deep sleep mode: 1.2 µA (meets target)
- Active measurement: 340 µA for 30 seconds every 5 minutes
- BLE advertising: 15 µA average (1 second intervals)
- **Projected battery life**: 16.2 days (exceeds 14-day requirement)

### Regulatory Notes
- Scheduled FDA Q-Sub meeting for 2025-09-15
- Need to complete substantial equivalence comparison vs Dexcom G6
- ISO 13485 audit scheduled for Q4 2025