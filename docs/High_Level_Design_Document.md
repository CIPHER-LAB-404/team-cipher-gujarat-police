# High-Level Design (HLD) Technical Architecture Document
## Gujarat Police Innovation Challenge 2026: SENTINEL Platform
**Document Reference**: GP-SENTINEL-HLD-2026-V1.0  
**Target Scale**: Statewide Deployment across ~80,000+ CCTV Cameras & 26 Departments  
**Live Proving Ground**: Sentinel Sandbox Grid (`https://live.corp8.cloud` / 30 Live RTP/RTSP Streams)

---

## 1. Executive Summary
The **SENTINEL** platform is an open, scalable, vendor-neutral, and high-throughput Video Management and AI Video Analytics platform designed specifically to integrate 26 heterogeneous departmental CCTV ecosystems across Gujarat. Validated against the live Sentinel Sandbox (`https://live.corp8.cloud`) across 30 live departmental camera feeds (including Ahmedabad, Gandhinagar, Rajkot, Junagadh, Navsari, Banaskantha, Bilimora, and Gandhidham), SENTINEL empowers Gujarat Police with automated real-time alerts, proactive threat detection, and instant cross-camera vehicle trajectory reconstruction.

---

## 2. High-Level System Architecture

```
                               ┌────────────────────────────────────────────────────────┐
                               │     Gujarat Police Central Command & Control Center    │
                               │   (GIS Tactical Map, Multi-Cam Wall, Incident Hub)     │
                               └───────────────────────────┬────────────────────────────┘
                                                           │ HTTPS / WSS / WebRTC
                               ┌───────────────────────────▼────────────────────────────┐
                               │           API Gateway & Federation Layer               │
                               │         (Kong / NGINX, OAuth2, RBAC, Rate-Limiting)    │
                               └─────────────┬───────────────────────────┬──────────────┘
                                             │                           │
                     ┌───────────────────────▼─────────┐       ┌─────────▼──────────────────────────┐
                     │   Spatio-Temporal Query Engine  │       │     Real-Time Alert Dispatcher     │
                     │  • Vehicle Route Reconstruction │       │    (Kafka Event Stream + WebSockets)│
                     │  • Cross-Camera Traversal Graph │       │    • Sub-second Threat Notification │
                     │  • GIS Breadcrumb Interpolation │       │    • PCR Van 108 Dispatch Relay    │
                     └───────────────────────┬─────────┘       └─────────┬──────────────────────────┘
                                             │                           │
                               ┌─────────────▼───────────────────────────▼──────────────┐
                               │               Core Data & Metadata Storage             │
                               │  • PostgreSQL + PostGIS (Camera GIS Registry & Logs)   │
                               │  • Elasticsearch (ANPR Plate Search & Full-Text)       │
                               │  • Redis (Real-time Watchlist Cache & Session Store)   │
                               │  • Distributed S3 / Ceph (Tiered Video Clip Evidence)  │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                               ┌───────────────────────────▼────────────────────────────┐
                               │          AI Video Analytics & Inference Pipeline       │
                               │  • YOLOv8 / YOLOv11 Vehicle & Person Detection         │
                               │  • Fast ANPR (Indian License Plate OCR Engine)         │
                               │  • DeepSORT / ByteTrack Multi-Object Tracking (MOT)    │
                               │  • Watchlist Cross-Referencing (eGujCop, VAHAN, AFIS)  │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
                               ┌───────────────────────────▼────────────────────────────┐
                               │        Stream Ingestion & Normalization Layer          │
                               │  • Live RTP/RTSP over TCP (rtsp://live.corp8.cloud:8554)│
                               │  • Hardware Accelerated Decoders (NVDEC, VA-API)       │
                               │  • Monotonic PTS Presentation Timestamp Normalizer     │
                               └───────────────────────────┬────────────────────────────┘
                                                           │
        ┌───────────────────┬──────────────────────────────┼──────────────────────────────┬───────────────────┐
        ▼                   ▼                              ▼                              ▼                   ▼
 [Police VMS]        [GSRTC Depots]                 [RTO Checkposts]               [Civil Supplies]     [Municipal Cams]
 (32,000 Cams)       (14,500 Cams)                  (9,200 Cams)                   (11,000 Cams)        (16,000 Cams)
```

---

## 3. Proving Ground Integration (`https://live.corp8.cloud`)

SENTINEL is connected to and consumes the 30 active sandbox endpoints published by Gujarat Police:
- **Streaming Catalogue API**: Dynamic discovery via `https://live.corp8.cloud/api/ingest`.
- **RTSP Streams**: `rtsp://live.corp8.cloud:8554/stream/1` to `rtsp://live.corp8.cloud:8554/stream/30`.
- **Protocol Enforcement**: Forced TCP transport (`rtsp_transport=tcp`) to ensure zero packet drop across state firewall boundaries.
- **Monotonic PTS Clock**: Presentation timestamp extraction via `CAP_PROP_POS_MSEC` ensuring accurate frame-by-frame velocity calculations.

---

## 4. Scalability, Bandwidth & Storage Sizing (~80,000 Cameras)

### 4.1 Bandwidth Optimization Strategy (Edge vs Central)
Streaming 80,000 raw 1080p video feeds centrally would require ~160 Gbps of dedicated bandwidth. SENTINEL utilizes a **Hybrid Edge-Fog-Central Architecture**:
1. **Edge/District Level (Fog Ingestion)**:
   - AI metadata extraction (ANPR text, vehicle color, timestamps, bounding box crops) is computed at 33 District Control Rooms (DCRs) or Edge Appliances.
   - Bandwidth consumption per camera drops from **2 Mbps (Raw Video)** to **< 5 kbps (Metadata/JSON)**.
2. **On-Demand Central Video Pull**:
   - High-definition live video feeds are only streamed to the Central State Command Center (Gandhinagar) when requested by operators or triggered by a Critical Watchlist Alert.

### 4.2 Multi-Tiered Storage Architecture
| Storage Tier | Technology | Retention Period | Content Stored |
| :--- | :--- | :--- | :--- |
| **Hot Storage** | NVMe SSD Cluster + Redis | 1 to 7 Days | Real-time metadata, active incident buffers, high-confidence plate crops |
| **Warm Storage** | Ceph Distributed Object / S3 | 8 to 45 Days | Continuous video recordings for high-priority junction cameras |
| **Cold / Archive** | LTO Tape / S3 Glacier | 46 to 365+ Days | Critical FIR evidence clips, forensic trial records, audit trails |

---

## 5. Cybersecurity & Governance
* **End-to-End Encryption**: TLS 1.3 for all web and API communications; AES-256 encryption at rest for video archives and database storage.
* **Role-Based Access Control (RBAC)**: Strict permission boundaries by Department (Police, Transport, RTO, Municipal) and Rank.
* **Tamper-Proof Audit Logging**: Immutable cryptographic audit log tracking every user query, video playback, and export action for judicial chain-of-custody compliance.
