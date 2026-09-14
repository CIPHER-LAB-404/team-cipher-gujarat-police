# TEAM CIPHER: Workflow & Technical Integration Diagrams
## Gujarat Police Innovation Hackathon 2026
**Document Reference**: GP-CIPHER-DIAGRAMS-2026-V1.0  
**Candidate Team**: TEAM CIPHER (Contact: cipherlab404@gmail.com)  
**Authority**: State Crime Records Bureau (SCRB) • Home Department, Government of Gujarat  

---

## 1. End-to-End System Integration Flow

```
+-----------------------------------------------------------------------------------+
|                        26 GOVERNMENT DEPARTMENTS IN GUJARAT                       |
|  Police (32k)  |  GSRTC (14.5k)  |  RTO (9.2k)  |  Municipal (16k)  |  Coastal (3.5k) |
+-----------------------------------------------------------------------------------+
                                         │
                                         │ RTSP over TCP (live.corp8.cloud:8554)
                                         ▼
+-----------------------------------------------------------------------------------+
|                       33 DISTRICT CONTROL ROOMS (EDGE NODES)                      |
|                                                                                   |
|  [Hardware-Accelerated Decoders (NVDEC / VA-API)]                                 |
|                         │                                                         |
|  [Monotonic PTS Presentation Timestamp Normalizer]                                |
|                         │                                                         |
|  [Stage 1: YOLOv8/v11 Multi-Entity Detector (Vehicles, Pedestrians)]              |
|                         │                                                         |
|  [Stage 2: Fast ANPR & Indian License Plate Disambiguation Engine]                |
|                         │                                                         |
|  [Multi-Object Tracking (Kalman / ByteTrack MOT) & Duplicate Suppressor]          |
|                         │                                                         |
|  [Local SQLite WAL Event Cache & 7-Day Rolling Video Storage Buffer]              |
+-----------------------------------------------------------------------------------+
                                         │
                                         │ Lightweight JSON Metadata (<5 kbps per cam)
                                         │ 95.3% Bandwidth Reduction (GSWAN / Fiber)
                                         ▼
+-----------------------------------------------------------------------------------+
|                     CENTRAL STATE DATA CENTER (GANDHINAGAR)                       |
|                                                                                   |
|  [Apache Kafka Real-Time Event Dispatcher (100,000 events/sec)]                   |
|                         │                                                         |
|  [Redis In-Memory Hot Watchlist Cache (eGujCop Warrants & Stolen Hotlists)]       |
|                         │                                                         |
|  [Distributed PostgreSQL 16 + PostGIS (Statewide Geospatial Indexing)]            |
|                         │                                                         |
|  [Elasticsearch 6-Node Full-Text Sighting Cluster]                                |
|                         │                                                         |
|  [Spatio-Temporal Graph Traversal & Vehicle Corridor Reconstructor]               |
+-----------------------------------------------------------------------------------+
                                         │
                                         │ Real-Time WebSockets & TLS 1.3 REST APIs
                                         ▼
+-----------------------------------------------------------------------------------+
|                    GUJARAT POLICE CENTRAL COMMAND & CONTROL DESK                  |
|                                                                                   |
|  • Interactive GIS Tactical Map with 30+ Live State Sandbox Feeds                |
|  • Synchronized Video Wall (Grid 2x2, 3x3, PTZ Priority View)                    |
|  • Live Vision Intelligence Desk (Streaming Plates, Crops & Confidence)           |
|  • Spatio-Temporal Corridor Reconstructor (Sub-250ms Transit Trails)              |
|  • Statutory Section 65B Indian Evidence Act / Section 63 BSA Legal Vault         |
|  • Automated Motor Vehicles Act 1988/2019 e-Challan Issuance Hub                  |
+-----------------------------------------------------------------------------------+
```

---

## 2. Two-Stage Indian ANPR & Vehicle Sentry Pipeline

```
[Raw Incoming Video Frame (1080p @ 25 FPS)]
                     │
                     ▼
       ┌───────────────────────────┐
       │   YOLOv8/v11 AI Detector  │
       └─────────────┬─────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
 ┌───────────────┐       ┌───────────────┐
 │ Vehicle Class │       │  Pedestrian   │
 │ (SUV, Sedan,  │       │ (Gender, ReID,│
 │ Truck, Bus)   │       │ Clothes Color)│
 └───────┬───────┘       └───────┬───────┘
         │                       │
         ▼                       │
 ┌───────────────┐               │
 │ Plate Bounding│               │
 │ Box Crop ROI  │               │
 └───────┬───────┘               │
         │                       │
         ▼                       │
 ┌───────────────┐               │
 │ ResNet OCR    │               │
 │ Character Rec │               │
 └───────┬───────┘               │
         │                       │
         ▼                       │
 ┌───────────────┐               │
 │ MoRTH Syntax  │               │
 │ Disambiguator │               │
 └───────┬───────┘               │
         │                       │
         ▼                       ▼
 ┌───────────────────────────────────────┐
 │ Kalman Filter / ByteTrack MOT Tracker │
 │   Assigns Track ID & Deduplicates     │
 └───────────────────┬───────────────────┘
                     │
                     ▼
 ┌───────────────────────────────────────┐
 │ Sub-Millisecond Watchlist Query       │
 │ Cross-references eGujCop FIR Warrants │
 └───────────────────┬───────────────────┘
                     │
                     ▼
 ┌───────────────────────────────────────┐
 │ Broadcast WebSocket Alert & Save to DB│
 └───────────────────────────────────────┘
```

---

## 3. Spatio-Temporal Route Reconstruction Sequence

```
Investigating Officer             CIPHER API Gateway             PostGIS / SQLite DB             Tactical GIS Map
         │                               │                                │                             │
         │ 1. Enter Target Plate         │                                │                             │
         ├──────────────────────────────>│                                │                             │
         │                               │ 2. Query Sightings             │                             │
         │                               ├───────────────────────────────>│                             │
         │                               │                                │                             │
         │                               │ 3. Return Chronological Trail  │                             │
         │                               │<───────────────────────────────┤                             │
         │                               │                                │                             │
         │                               │ 4. Compute Inter-Node Velocity │                             │
         │                               │    (Delta Distance / Time)     │                             │
         │                               │                                │                             │
         │                               │ 5. Return JSON Trajectory      │                             │
         │<──────────────────────────────┤                                │                             │
         │                               │                                │                             │
         │ 6. Render Trajectory          │                                │                             │
         ├─────────────────────────────────────────────────────────────────────────────────────────────>│
         │                                                                                              │
         │ 7. Draw Animated Breadcrumbs, Stops, and Predicted Police Intercept Point                     │
         │<─────────────────────────────────────────────────────────────────────────────────────────────┤
```

---

## 4. Statutory Legal Evidence (Section 65B / 63 BSA) Workflow

```
[Camera Lens Snapshot / Ingestion Frame]
                   │
                   ▼
[Evidence Capture & Lock Event]
• Freezes video frame buffer and crops license plate ROI
• Gathers camera telemetry: serial number, MAC address, GPS coordinates, calibration timestamp
                   │
                   ▼
[SHA-256 Cryptographic Hash Generation]
• Generates immutable digital fingerprint for video file, plate crop, and route report
• Any modification by even 1 byte alters hash and flags tampering
                   │
                   ▼
[Statutory Certification Generation]
• Auto-populates official certificate under Section 65B Indian Evidence Act 1872 / Section 63 BSA 2023
• Inserts investigating officer details, police station code, and technical custodian certification
                   │
                   ▼
[Tamper-Proof PDF Export & Archival]
• Output ready for direct submission to District Sessions Court and High Court of Gujarat
• Retained in encrypted Cold Storage tier for 365+ days
```
