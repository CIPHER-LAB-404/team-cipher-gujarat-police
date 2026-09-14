# 🔐 SENTINEL Security, Compliance & Governance Blueprint
### Law Enforcement Data Protection Standard (IT Act 2000 & Digital Personal Data Protection Act)

---

## 1. Statutory & Regulatory Compliance
SENTINEL is architected to comply strictly with the statutory mandates governing Indian Law Enforcement Agencies:
1. **Information Technology Act, 2000 (Section 43A, 66B, 69, 79)**: Safe harbor rules, data retention mandates, and lawful surveillance interception guidelines.
2. **Digital Personal Data Protection Act (DPDP), 2023**: Law enforcement exemption handling, purpose limitation, and strict citizen privacy boundaries.
3. **MHA (Ministry of Home Affairs) Cyber Security Guidelines**: Network segmentation, air-gapped critical networks, and CCTNS inter-operability standards.

---

## 2. Access Control & Officer Authentication

### 2.1. Domain & Physical Route Isolation
* The public citizen interface (`/`) and officer intelligence console (`/cipher`) are isolated on separate routing layers.
* Public facing templates and JavaScript bundles **never expose internal API endpoints, officer credentials, or administrative URL routes**.

### 2.2. Officer Authentication Gateway (`/cipher`)
* Access is guarded by high-entropy token authentication.
* Sessions are maintained exclusively in encrypted `sessionStorage` (`CIPHER_AUTH_TOKEN`).
* Explicit **"Lock Terminal"** command terminates the active cryptographic session and purges local storage before redirecting to the safe public surface.

---

## 3. Cryptographic & Network Security

| Protection Layer | Implementation Mechanism | Standard |
| :--- | :--- | :--- |
| **In-Transit Encryption** | Transport Layer Security (TLS 1.3) with HSTS forced redirect | AES-256-GCM |
| **RTSP Video Feeds** | Secure RTSP-over-TLS (RTSPS) & WebRTC SRTP | AES-128-CTR |
| **WebSocket Alerts** | Secure WebSockets (`wss://`) with token authorization | WSS / TLS 1.3 |
| **Citizen e-Intimations** | SHA-256 integrity hash attached to every generated ticket ref (`GJP-2026-XXXX`) | FIPS 180-4 |

---

## 4. Tamper-Proof Audit Logging & Non-Repudiation
Every officer action inside the CIPHER command console is logged to an append-only audit trail containing:
1. `Officer_ID` and authenticated Badge Number.
2. Exact UTC and IST Timestamp.
3. Originating Terminal IP and MAC Address.
4. Target License Plate queried and Reason for Investigation.
5. Snapshot hash of the evidence retrieved.
