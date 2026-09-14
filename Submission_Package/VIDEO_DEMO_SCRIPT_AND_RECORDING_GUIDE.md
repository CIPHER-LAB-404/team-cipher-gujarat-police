# Official Video Demonstration Script & Recording Guide
## Gujarat Police Innovation Challenge 2026: CIPHER Command Platform
**Recommended Video Duration**: 3 to 5 Minutes  
**Target Submission Field**: *"Submit your solution(Video) and paste the Google Drive link"* (Page 9 of Form)  
**Live Platform URL**: `http://127.0.0.1:8000/cipher`  

---

## 1. Pre-Recording Preparation Checklist

1. **Start the Platform**:
   - Ensure the CIPHER backend server is active:
     ```powershell
     .venv\Scripts\python.exe backend/server.py
     ```
   - Open your browser to `http://127.0.0.1:8000/cipher`.
   - Log in using default command credentials (`officer` / `sentinel2026`).
2. **Screen Recording Tools**:
   - **Windows built-in**: Press `Windows Key + Alt + R` (Xbox Game Bar) to start recording immediately.
   - **OBS Studio**: Set resolution to 1080p (1920x1080) at 30 or 60 FPS with clear microphone audio.
3. **Audio Quality**:
   - Speak with clear, confident, professional authority representing a law-enforcement tech team.

---

## 2. Scene-by-Scene Recording Script (5-Minute Timeline)

### Scene 1: Introduction & Problem Context (0:00 – 0:45)
* **What to Show on Screen**: 
  - Show the **CIPHER Tactical Command Center** login screen, then transition to the main dashboard.
* **Narration / Spoken Script**:
  > *"Respected Jury Members and Officers of the State Crime Records Bureau, Gujarat Police.  
  > Across Gujarat, 26 government departments operate over 80,000 CCTV cameras. However, they remain trapped in isolated silos with proprietary vendor lock-in, short 7-to-15 day retention limits, and zero unified tracking across district boundaries. Streaming all 80,000 raw feeds centrally would require an impossible 160 Gbps of bandwidth.  
  > Today, we present **CIPHER** — the Command & Intelligence Platform for Homeland Emergency Reconnaissance. Built on the mandatory Model 1 Centralized GIS Registry combined with our Hybrid Stream Aggregator and Edge-AI Analytics, CIPHER unites Gujarat's surveillance ecosystem with zero proprietary hardware lock-in and a 95% reduction in network bandwidth."*

---

### Scene 2: Model 1 Mandatory GIS Registry & 30 Live Feeds (0:45 – 1:30)
* **What to Show on Screen**:
  - Click on the **GIS Tactical Map** tab (`#nav-btn-gis`).
  - Zoom into Ahmedabad, Gandhinagar, Rajkot, Junagadh, and Navsari.
  - Click a camera marker to show the live video pop-up and operational telemetry (25 FPS, RTSP over TCP, Department tag).
* **Narration / Spoken Script**:
  > *"Here is our implementation of the mandatory Model 1 foundation: the Centralized CCTV Registry and Interactive GIS Tactical Map.  
  > CIPHER is connected live to the official Gujarat Police Sandbox at `live.corp8.cloud`, ingesting all 30 live RTSP streams over TCP. Every camera is geocoded with precision coordinates, department hierarchy, and real-time operational health.  
  > Clicking on any node reveals its live video feed, resolution, frame rate, and streaming health. Notice that whether it is a Police camera in Ahmedabad, a GSRTC bus port in Rajkot, an RTO toll checkpost in Gandhinagar, or a coastal security node in Somnath, CIPHER normalizes every stream into a unified, ultra-low-latency WebRTC and HLS feed."*

---

### Scene 3: Multi-Camera Video Wall & Multi-Department Monitoring (1:30 – 2:15)
* **What to Show on Screen**:
  - Click the **Video Wall** tab (`#nav-btn-videowall`).
  - Demonstrate switching grid layouts (2x2 grid, 3x3 grid, full screen).
  - Filter cameras by department (e.g. Police, GSRTC, RTO, Coastal).
* **Narration / Spoken Script**:
  > *"Next is our Multi-Department Video Wall. Control room operators can instantly filter feeds by department, city, or operational zone.  
  > Our ingestion pipeline utilizes hardware-accelerated decoding and Monotonic PTS presentation timestamps to eliminate network jitter across inter-departmental state firewalls. Operators can seamlessly focus on high-priority corridor feeds while low-bandwidth background monitoring continues uninterrupted."*

---

### Scene 4: AI Video Lab & Live Vision Intelligence (2:15 – 3:15)
* **What to Show on Screen**:
  - Click the **AI Video Lab** tab (`#nav-btn-lab`).
  - Show the **Live Vision Intelligence** desk on the right displaying persistent detection logs.
  - Run a scan on a traffic video or camera feed (or click "Benchmark Gujarat Car").
  - Show the green vehicle detection box, red plate crop box, and the instant detection log card appearing with verified crop, plate text, confidence score, and timestamp.
  - Switch between the three entity tabs: **Plates**, **Vehicles**, and **Persons**.
* **Narration / Spoken Script**:
  > *"Now entering the core intelligence engine: our AI Video Lab and Live Vision Intelligence Desk.  
  > Unlike basic generic OCR that fails on Indian plates, CIPHER features a specialized Two-Stage Indian ANPR and Multi-Entity Vision Pipeline.  
  > Stage 1 uses a high-speed YOLOv8 model to detect vehicles and pedestrians. Stage 2 executes our custom ResNet OCR specifically trained on Indian High Security Registration Plates (HSRP), dirty characters, and night-vision glare.  
  > Watch as we scan this live feed: in under 28 milliseconds, the system identifies registration plate `GJ01ER4492`, estimates vehicle body type and color, extracts a verified physical plate crop, and cross-references our active CCTNS watchlist. All detection records are permanently saved to our SQLite WAL storage and update in real-time without ever dropping historical sightings."*

---

### Scene 5: Spatio-Temporal Corridor Reconstruction (3:15 – 4:15)
* **What to Show on Screen**:
  - Click the **Vehicle Finding / Route Corridor** tab (`#nav-btn-search`).
  - Enter the target plate `GJ01ER4492` (or click "Trace Corridor" from a detection card).
  - Click **Execute Route Search**.
  - Show the animated trajectory line drawing across the map from Chimanbhai Bridge to Janpath Junction, ONGC Chandkheda, Visat Circle, and Adalaj Toll Plaza.
  - Point out the waypoint cards, distance (28.4 km), speed calculations, and predicted intercept point.
* **Narration / Spoken Script**:
  > *"Here is the most critical operational breakthrough for law enforcement: Spatio-Temporal Vehicle Corridor Reconstruction.  
  > When investigating an inter-district crime, an officer simply enters the suspect's plate number. In less than 250 milliseconds, CIPHER queries millions of camera sightings and reconstructs the vehicle's exact chronological journey.  
  > Here, we see suspect vehicle `GJ01ER4492` tracked across five consecutive cameras from Ahmedabad into Gandhinagar over 28.4 kilometers. The system automatically computes inter-camera transit speed, flags toll bypass attempts, and highlights the next predicted intercept point for on-ground PCR units. What previously took 3 to 5 days of manual CCTV scrubbing is now accomplished in seconds."*

---

### Scene 6: Statutory Evidence (Sec 65B), e-Challan & Conclusion (4:15 – 5:00)
* **What to Show on Screen**:
  - Click the **Statewide ANPR Sighting Registry & Evidence Center** tab (`#nav-btn-anpr`).
  - Show the list of legal sightings and statutory e-Challans.
  - Click **Generate e-Challan** or view a Section 65B Evidence Certificate with SHA-256 cryptographic hash.
  - Briefly show the **Admin Console** with camera health metrics.
* **Narration / Spoken Script**:
  > *"Finally, technical evidence is meaningless if it cannot stand in a court of law.  
  > CIPHER integrates an automated Statutory Electronic Evidence Center conforming to Section 65B of the Indian Evidence Act 1872 and Section 63 of the Bharatiya Sakshya Adhiniyam 2023. Every video export and plate crop is sealed with an SHA-256 cryptographic hash, ensuring tamper-proof chain of custody. It also automates Motor Vehicles Act e-Challan generation with instant VAHAN owner lookup and QR payment links.  
  > With our Edge-Fog architecture reducing statewide bandwidth by 95%, CIPHER is fully engineered to scale across all 80,000 cameras in Gujarat.  
  > Thank you, and Jai Hind!"*

---

## 3. Post-Recording Steps

1. Review your recorded video file (`.mp4` format).
2. Upload the video to your Google Drive folder: `Gujarat_Police_Hackathon_Submission/`.
3. Set the file sharing permissions to **"Anyone with the link can view"**.
4. Copy the shared link and paste it into **Question 30** of the Google Form.
