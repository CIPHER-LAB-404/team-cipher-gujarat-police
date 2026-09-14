# SENTINEL: Solution Presentation Deck Outline
## Gujarat Police Innovation Challenge 2026

**Slide 1: Title Slide**
- **Title**: SENTINEL — Statewide CCTV Integration & AI Intelligence Grid
- **Subtitle**: Unified Spatio-Temporal Video Management & Proactive Law Enforcement System
- **Team**: [Your Team Name / Startup Name]
- **Category**: [Category 1: Students/Startups OR Category 2: Industry/Enterprise]
- **Target Initiative**: Gujarat Police / Home Department, Government of Gujarat

---

**Slide 2: Problem Statement & Ground Reality**
- **The Challenge**: 26 Government Departments operating 80,000+ isolated CCTV cameras with disparate VMS platforms, vendors (Hikvision, Dahua, Axis, CP Plus), and retention policies (7–15 days).
- **The Operational Bottleneck**: Police teams cannot seamlessly track suspect vehicles crossing district boundaries (spanning ~1,000 km).
- **The Disconnect**: Critical police databases (eGujCop, VAHAN, SARTHI, NAFIS) operate in isolation from live video surveillance.

---

**Slide 3: Proposed Architecture (Hybrid Model 1 + Model 2/3)**
- **Open, Vendor-Neutral & Standards-Based**: Zero vendor lock-in; ingests standard RTSP over TCP, ONVIF, WebSockets, and VMS APIs.
- **Model 1 (Foundational Registry & GIS)**: Live visibility and health audit over all 80,000+ camera assets across Gujarat.
- **Model 2/3 (Unified Stream Aggregator & Middleware)**: High-speed ingestion without disrupting existing departmental VMS installations.

---

**Slide 4: Core Technical Innovations**
1. **Monotonic PTS Synchronization**: Frame-accurate vehicle speed and velocity estimation using presentation timestamps.
2. **Deep-Learning ANPR & Tracking**: Robust recognition on high-speed highways, night-vision, and blurred plates with Indian syntax validation.
3. **Spatio-Temporal Route Reconstruction**: Instant visual breadcrumb mapping of suspect travel paths across multiple departmental camera nodes.

---

**Slide 5: Live Test Scenario Demonstration (Jury Benchmark)**
- **Scenario**: Target Vehicle `GJ01ER4492` (White Mahindra Scorpio - Wanted in Armed Robbery Case).
- **Demonstrated Results**:
  - Automatically detected across 5 consecutive camera nodes (ISKCON ➔ Pakwan ➔ Kudasan ➔ CH-0 Circle ➔ Aslali Toll Plaza).
  - Traversed 78.4 km with accurate timestamped trajectory and speed calculations.
  - Sub-second real-time audio-visual alert triggered upon watchlist match.

---

**Slide 6: Scalability Strategy for 80,000 Cameras**
- **Hybrid Edge-Fog Architecture**: AI inference at 33 District Control Rooms reduces central network bandwidth by **95%** (transmitting metadata JSON rather than raw continuous video).
- **Tiered Storage Optimization**: Hot NVMe for active incident buffers, Ceph Object Storage for 45-day retention, and cold archive for court evidence.

---

**Slide 7: Database & Interoperability Integrations**
- **eGujCop (CCTNS)**: Auto-matching against active FIR warrants and missing persons.
- **VAHAN / SARTHI**: Flagging fake plates, stolen vehicles, and commercial transport violations.
- **Public-Private Federation**: Framework to securely onboard private CCTV feeds (malls, banks, housing societies).

---

**Slide 8: Cybersecurity, Privacy & Chain of Custody**
- **Security Protocols**: TLS 1.3 in transit, AES-256 at rest, strict RBAC by police rank and jurisdiction.
- **Forensic Integrity**: Cryptographically signed audit trails and timestamped exports conforming to Section 65B Indian Evidence Act standards.

---

**Slide 9: Rollout Roadmap for Gujarat**
- **Month 1–2**: Deployment of Registry & GIS Layer across all 26 departments (Model 1).
- **Month 3–4**: Onboarding of major highway corridors (NH-48, SG Highway) and border checkposts (Dahod, Valsad).
- **Month 5–6**: Statewide scaling to 80,000+ cameras with district command centers.

---

**Slide 10: Conclusion & Business Impact**
- **Operational Transformation**: Reduces suspect tracking time from days to seconds.
- **Cost Efficiency**: Leverages existing camera infrastructure without requiring multi-crore hardware replacements.
- **Public Safety**: Proactive deterrence and enhanced security across Gujarat's cities, highways, and borders.
