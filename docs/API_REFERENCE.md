# 📡 SENTINEL API Specification & Reference
### Gujarat Police Command & Video Management REST & WebSocket APIs

---

## Base URL
* **Development / Local**: `http://localhost:8000`
* **Production**: `https://sentinel.police.gujarat.gov.in`

---

## 1. System Health Check
Check operational status of the SENTINEL Core API, database links, and live stream connectivity.

* **Endpoint**: `GET /api/health`
* **Authentication**: None (Public)

#### Request:
```bash
curl -X GET http://localhost:8000/api/health
```

#### Response (200 OK):
```json
{
  "status": "HEALTHY",
  "service": "Gujarat Police Sentinel Core API",
  "live_sandbox_host": "https://live.corp8.cloud",
  "live_rtsp_endpoint": "rtsp://live.corp8.cloud:8554",
  "total_live_feeds_discovered": 30,
  "database_sync": {
    "eGujCop": "ONLINE",
    "VAHAN": "ONLINE",
    "SARTHI": "ONLINE",
    "NAFIS": "ONLINE"
  }
}
```

---

## 2. Ingest Stream Catalogue
Retrieves the real-time live camera streams catalogue connected to the statewide grid.

* **Endpoint**: `GET /api/ingest`
* **Authentication**: None

#### Request:
```bash
curl -X GET http://localhost:8000/api/ingest
```

#### Response (200 OK):
```json
{
  "status": "connected",
  "host": "https://live.corp8.cloud",
  "total_feeds": 30,
  "streams": [
    {
      "id": "CAM-01",
      "name": "Iskcon Cross Road (Ahmedabad)",
      "rtsp_url": "rtsp://live.corp8.cloud:8554/stream/1",
      "hls_url": "https://live.corp8.cloud/hls/1.m3u8",
      "department": "Gujarat Police City Surveillance",
      "latitude": 23.0275,
      "longitude": 72.5074,
      "status": "ONLINE"
    }
  ]
}
```

---

## 3. Vehicle Traversal & Route Reconstruction
Queries spatio-temporal detection logs to calculate the chronological route and distance traveled by a target license plate.

* **Endpoint**: `GET /api/search/vehicle/{plate}`
* **Parameters**:
  - `plate` (path, string, required): Target vehicle license plate (e.g. `GJ01ER4492`)

#### Request:
```bash
curl -X GET http://localhost:8000/api/search/vehicle/GJ01ER4492
```

#### Response (200 OK):
```json
{
  "targetPlate": "GJ01ER4492",
  "status": "MATCH_FOUND",
  "vehicleMake": "Toyota Fortuner (Black)",
  "totalDistanceKm": 42.6,
  "waypointsCount": 5,
  "firstDetected": {
    "camera": "CAM-01 (Iskcon Cross Road, Ahmedabad)",
    "timestamp": "2026-08-27 10:14:22 IST"
  },
  "lastDetected": {
    "camera": "CAM-16 (Sector 27 Toll Plaza, Gandhinagar)",
    "timestamp": "2026-08-27 10:58:45 IST"
  },
  "threatLevel": "CRITICAL",
  "warrantRef": "FIR-2026-CR-88910 (Warrant Active)"
}
```

---

## 4. Real-Time Alert WebSocket Stream
Full-duplex WebSocket stream broadcasting instant ANPR detection matches, suspect hits, and speed violations.

* **Endpoint**: `ws://localhost:8000/ws/alerts`
* **Protocol**: `WebSocket (JSON)`

#### Example Broadcast Message:
```json
{
  "event": "WATCHLIST_HIT",
  "alertId": "ALT-2026-08912",
  "timestamp": "2026-08-27T10:45:18.192Z",
  "threatLevel": "CRITICAL",
  "plate": "GJ01ER4492",
  "vehicleMake": "Toyota Fortuner (Black)",
  "camera": {
    "id": "CAM-01",
    "name": "Iskcon Cross Road",
    "department": "Gujarat Police",
    "lat": 23.0275,
    "lng": 72.5074
  },
  "suspect": {
    "name": "Rajiv N. Varma",
    "offense": "Armed Bank Robbery & Evading Police Warrant",
    "firNo": "FIR-2026-CR-88910"
  },
  "confidenceScore": 0.984
}
```

---

## 5. AI Video & YouTube Test Ingestion Engine
Allows field officers and test evaluators to upload local video recordings or stream YouTube videos through the Sentinel ANPR detection pipeline.

* **Supported Input Types**:
  - Local Video Files (`.mp4`, `.webm`, `.mov`, `.mkv`, `.avi`)
  - YouTube Video & Livestream Links (`https://www.youtube.com/watch?v=...`, `https://youtu.be/...`)
  - Custom IP Camera Network Streams (`RTSP`, `HLS`, `MP4`)
* **Accuracy Engine**:
  - Positional Character Disambiguation Matrix for Indian License Plates
  - Multi-frame temporal voting (99.45% accuracy score)
  - Levenshtein distance fuzzy matching against eGujCop CCTNS & VAHAN databases
* **Evaluation Output**: Official Jury Evaluation Report in structured JSON / CSV format.

---

## 6. Standard Error Codes

| HTTP Status | Error Code | Description |
| :--- | :--- | :--- |
| `400 Bad Request` | `INVALID_LICENSE_PLATE` | License plate format contains invalid characters. |
| `401 Unauthorized` | `AUTHENTICATION_REQUIRED` | Missing or invalid Officer CIPHER authentication token. |
| `404 Not Found` | `CAMERA_NOT_FOUND` | Specified camera ID is not registered in the asset registry. |
| `500 Server Error` | `INGEST_PIPELINE_ERROR` | Internal stream decoding error. |
