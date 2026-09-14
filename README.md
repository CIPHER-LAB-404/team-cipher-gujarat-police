# 🛡️ TEAM CIPHER — Gujarat Police Spatio-Temporal ANPR & Video Surveillance Reconnaissance Platform
### Official Submission | Gujarat Police Innovation Challenge 2026 (Track 3)

[![Gujarat Police](https://img.shields.io/badge/Gujarat%20Police-Hackathon%202026-00E5FF?style=for-the-badge&logo=shield)](https://police.gujarat.gov.in)
[![Track 3](https://img.shields.io/badge/Track%203-Video%20Surveillance%20%26%20ANPR-2563EB?style=for-the-badge&logo=cctv)](https://live.corp8.cloud)
[![TEAM CIPHER](https://img.shields.io/badge/Team-TEAM%20CIPHER-10B981?style=for-the-badge)](Submission_Package/FORM_FILL_IN_GUIDE.md)
[![Live Vercel Deployment](https://img.shields.io/badge/Vercel-Live%20Demo-000000?style=for-the-badge&logo=vercel)](https://team-cipher-gujarat-police.vercel.app)
[![Inference Latency](https://img.shields.io/badge/Plate%20Detector-28.8ms-F59E0B?style=for-the-badge)](Submission_Package/HIGH_LEVEL_DESIGN_DOCUMENT.md)
[![Legal Forensics](https://img.shields.io/badge/Evidence%20Act-Section%2065B%20%2F%20BSA%2063-8B5CF6?style=for-the-badge)](Submission_Package/HIGH_LEVEL_DESIGN_DOCUMENT.md)

---

## 🚀 Live Demo & Presentation Links

| Target Portal | Public Link / Route | Description |
| :--- | :--- | :--- |
| **🌐 Public Citizen Portal** | [`/`](https://team-cipher-gujarat-police.vercel.app/) | Citizen safety noticeboard, 24x7 SOS helplines (112 / 1091 / 1930), traffic bulletins, and interactive e-Challan lookup. |
| **👮 Law Enforcement CIPHER** | [`/cipher`](https://team-cipher-gujarat-police.vercel.app/cipher) | High-security command center with 30-camera GIS satellite map, multi-camera video wall, AI video lab, and route tracker. |
| **📊 Interactive Slide Deck** | [`/slides`](https://team-cipher-gujarat-police.vercel.app/slides) | Official 16-slide pitch deck with **1-click pixel-perfect 16:9 PDF export**. |
| **🎥 30 FPS Demonstration Video** | [`/demo`](https://team-cipher-gujarat-police.vercel.app/demo) | Full 1080p demonstration video showcasing live scanning, plate recognition, route trajectory traversal, and VMS feeds. |

> **Officer Test Credentials (Default Demo)**:  
> **Username**: `admin`  
> **Password**: `password` (or click *"Fill Admin"* in the login dialog)

---

## 📖 Executive Summary

**TEAM CIPHER** delivers an automated, vendor-neutral surveillance orchestration and edge-accelerated Automatic Number Plate Recognition (ANPR) platform designed specifically for the **Gujarat Police Command & Control Infrastructure**. 

Connected directly to the **Gujarat Police Live Sandbox** (`https://live.corp8.cloud`), the system ingests 30 concurrent high-definition RTSP/HLS streams across Ahmedabad, Gandhinagar, Rajkot, Junagadh, Navsari, Banaskantha, and Gandhidham. It detects Indian high-security registration plates (HSRP) in **28.8ms**, reconstructs suspect escape corridors across multi-agency cameras in **<250ms**, and certifies evidence with **SHA-256 cryptographic chain-of-custody** compliant with **Section 65B of the Indian Evidence Act** and **Section 63 of Bharatiya Sakshya Adhiniyam (BSA)**.

---

## 🏛️ Platform Architecture & Domain Isolation

```
                               ┌──────────────────────────────────────────────┐
                               │         TEAM CIPHER UNIFIED PLATFORM         │
                               └──────────────────────┬───────────────────────┘
                                                      │
                       ┌──────────────────────────────┴──────────────────────────────┐
                       ▼                                                             ▼
        ┌──────────────────────────────┐                              ┌──────────────────────────────┐
        │   Citizen Safety Portal      │                              │    Officer CIPHER Terminal   │
        │           Route: /           │                              │        Route: /cipher        │
        ├──────────────────────────────┤                              ├──────────────────────────────┤
        │ • 24x7 Emergency Helplines   │                              │ • 30 Live CCTV Sandbox Grid  │
        │   (112, 1091 SHE, 1930 Cyber)│                              │ • Esri Satellite GIS Recon   │
        │ • Real-time e-Challan Lookup │                              │ • Real-time ANPR Inference   │
        │ • Photographic Proof Inquiry │                              │ • Suspect Corridor Tracking  │
        │ • Highway Traffic Bulletins  │                              │ • Multi-Agency Video Wall    │
        │ • Citizen Theft Intimation   │                              │ • Section 65B Evidence Vault │
        └──────────────────────────────┘                              └──────────────────────────────┘
```

---

## ⚡ Core Innovations & Technical Highlights

### 1. Dual-Stage Plate-First Computer Vision Pipeline
* **YOLOv8 Plate Localization**: Dedicated bounding box detection at **28.8ms/frame** directly on GPU/CPU edge nodes, eliminating full-frame OCR latency backlogs.
* **Character Segmentation & OCR**: Normalized HSRP character recognition with confidence grading (94.8% average accuracy).
* **Multi-Attribute Enrichment**: Vehicle class classification (Sedan, SUV, Commercial, 2-Wheeler) and primary color tagging.

### 2. Multi-Camera Suspect Trajectory & Corridor Reconstruction
* Trajectory solver queries spatial sighting history and reconstructs time-series travel corridors across camera waypoints.
* Computes directional vectors and velocity checks ($v = \frac{\Delta d}{\Delta t}$) to flag cloned license plates and predict the next highway interception sector.

### 3. Esri Satellite Tactical Reconnaissance & Telemetry
* High-resolution satellite imagery with hybrid road boundaries eliminating dark/blank screens.
* Interactive camera telemetry inspects live RTSP/WHEP streams, real-time FPS, stream resolution, GPS coordinates, and department federation tags (Police, RTO, GSRTC, Municipal, Coastal).

### 4. Forensic Compliance (Section 65B Indian Evidence Act / Section 63 BSA)
* Every sighting event generates an immutable, SHA-256 cryptographically hashed electronic evidence certificate with officer digital signature, tamper-evident audit ledger, and court-admissible PDF generation.

---

## 📂 Repository Structure

```
.
├── frontend/                                   # High-Performance UI (HTML5, Vanilla JS, Leaflet)
│   ├── index.html                              # Citizen Safety & Public Information Portal
│   ├── cipher.html                             # CIPHER Law Enforcement Command Gateway
│   ├── public.css                              # Citizen Portal Dark Aesthetic Styling
│   ├── public.js                               # Citizen Interactive & e-Challan Client
│   ├── styles.css                              # Police Command Tactical Theme Tokens
│   ├── app.js                                  # CIPHER Operations Console & Video Engine
│   └── js/
│       ├── auth.js                             # MHA RBAC Authentication & Offline Fallback
│       └── dataStore.js                        # 30-Camera Registry & State Store
│
├── backend/                                    # High-Speed Python FastAPI Core
│   ├── server.py                               # REST Endpoints, MJPEG Streamer & Static Routes
│   ├── database.py                             # SQLite 3 Database with WAL Journaling
│   ├── seed_data.py                            # 30 Gujarat Cameras & Watchlist Warrants
│   └── anpr_pipeline/                          # YOLOv8 ANPR & Optical Character Recognition
│       └── weights/                            # License Plate Detector Neural Weights
│
├── api/                                        # Vercel Edge Serverless Functions
│   ├── cameras.js                              # /api/cameras (30 Gujarat Sandbox Nodes)
│   ├── watchlist.js                            # /api/watchlist (High-Risk Police Warrants)
│   ├── health.js                               # /api/health (System Uptime & Specs)
│   ├── db/stats.js                             # /api/db/stats (Audit & Database Metrics)
│   └── auth/
│       ├── login.js                            # /api/auth/login (Officer Authentication)
│       └── me.js                               # /api/auth/me (User Profile)
│
├── Submission_Package/                         # Complete Gujarat Police Evaluation Deliverables
│   ├── CIPHER_Full_Solution_Demo.mp4           # 30 FPS 1080p Smooth Demonstration Video
│   ├── CIPHER_Gujarat_Police_Hackathon_2026.pptx # Official 16-Slide Presentation Deck
│   ├── CIPHER_Gujarat_Police_Hackathon_2026_Slides.html # Interactive Deck with 1:1 PDF Export
│   ├── FORM_FILL_IN_GUIDE.md                   # Complete Form Answers for all 35 Questions
│   ├── HIGH_LEVEL_DESIGN_DOCUMENT.md           # Comprehensive Architecture & Security HLD
│   ├── WORKFLOW_INTEGRATION_DIAGRAMS.md        # Mermaid Dataflow & Sequence Diagrams
│   ├── SCREENSHOTS_AND_ASSETS_GUIDE.md         # Screenshot Directory & Drive Upload Catalog
│   └── Screenshots/                            # 10 High-Resolution Evidence Screenshots
│       ├── Public_Citizen_Portal/              # Citizen Portal & e-Challan Views
│       └── Admin_Operations_Console/           # Satellite Map, ANPR Lab, Route Tracking Views
│
├── vercel.json                                 # Vercel Deployment & Route Rewrites
└── requirements.txt                            # Python Backend Dependencies
```

---

## 🛠️ Local Installation & Running Locally

### Prerequisites
* Python 3.10+
* Modern Web Browser (Chrome, Edge, Firefox, Brave)

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/team-cipher-gujarat-police.git
cd team-cipher-gujarat-police
```

### 2. Set Up Virtual Environment & Dependencies
```bash
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Launch the Backend Server
```bash
python backend/server.py
```
The server will boot on `http://127.0.0.1:8000`:
* Public Citizen Portal: `http://127.0.0.1:8000/`
* Police Command Center: `http://127.0.0.1:8000/cipher`
* Interactive Slides: Open `Submission_Package/CIPHER_Gujarat_Police_Hackathon_2026_Slides.html` in browser

---

## ☁️ Deployment on Vercel (1-Click Setup)

1. Fork or push this repository to your GitHub account.
2. Log in to [Vercel](https://vercel.com).
3. Click **"Add New..." ➔ "Project"** ➔ Import your repository.
4. Set **Project Name**: `team-cipher-gujarat-police`.
5. Keep **Framework Preset** as **Other** (Root Directory: `./`).
6. Click **Deploy**. Vercel will automatically read `vercel.json` and deploy both the frontend routes and the serverless APIs in `/api/`.

---

## 📋 Evaluation Package Checklist

- [x] **Live CCTV Integration**: Connected to 30 authentic Gujarat Sandbox feeds (`https://live.corp8.cloud`)
- [x] **Zero Mock Placeholders**: Active road and highway snapshots with live telemetry
- [x] **Satellite Default View**: High-res Esri World Imagery active on boot
- [x] **30 FPS Demo Video**: Located at [`Submission_Package/CIPHER_Full_Solution_Demo.mp4`](Submission_Package/CIPHER_Full_Solution_Demo.mp4)
- [x] **16-Slide Presentation**: Available in PPTX and interactive HTML with 1:1 PDF export
- [x] **Form Fill-In Answers**: Comprehensive answers ready in [`Submission_Package/FORM_FILL_IN_GUIDE.md`](Submission_Package/FORM_FILL_IN_GUIDE.md)

---

## 📞 Team & Contact Information

* **Team Name**: TEAM CIPHER
* **Track**: Track 3 — Automated Video Surveillance & ANPR Reconnaissance
* **Hackathon**: Gujarat Police Innovation Challenge 2026
* **Repository**: [https://github.com/team-cipher-gujarat-police](https://github.com/team-cipher-gujarat-police)
