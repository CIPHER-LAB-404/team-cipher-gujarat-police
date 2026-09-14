"""
=============================================================================
Test Suite 3: Reporting, e-Challan Generation & Section 65B Evidence System
=============================================================================
Verifies:
1. Sighting query filters (Date, Camera ID, State Code, Watchlist status)
2. Section 65B Indian Evidence Act (1872) & Sec 63 BSA (2023) Digital Certificate
3. SHA-256 cryptographic hash seal over electronic surveillance logs
4. Statutory e-Challan creation with Motor Vehicles Act 1988/2019 legal sections
5. e-Challan payment and settlement audit trail
6. Streaming CSV & JSON ANPR exports
7. Complete Law Enforcement Incident Dossier assembly
=============================================================================
"""

import unittest
import sys
import os
import json
import csv
import io
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import db
from fastapi.testclient import TestClient
import server


class TestReportingAndEvidenceSystem(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(server.app)

        # Seed sample detection with standard Indian format: GJ 01 TE ####
        num_suffix = 1000 + (int(time.time() * 100) % 8999)
        self.sample_plate = f"GJ01TE{num_suffix}"
        db.add_watchlist_item({
            "id": f"WL-TEST-{num_suffix}",
            "plate": self.sample_plate,
            "vehicleMake": "Hyundai Creta SX (White)",
            "vehicleClass": "SUV",
            "threatLevel": "HIGH",
            "category": "Test Sentry Warrant",
            "registeredOwner": "Shri Arvindbhai Patel"
        })
        self.detection_id = db.record_detection({
            "cameraId": "CAM-01",
            "plate": self.sample_plate,
            "rawPlate": self.sample_plate,
            "confidence": 0.985,
            "vehicleType": "SUV",
            "vehicleColor": "White",
            "bbox": [100, 200, 300, 250],
            "vehicleBbox": [50, 50, 500, 400],
            "trackId": 42,
            "isWatchlistHit": True,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S IST")
        })

    def tearDown(self):
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist WHERE id LIKE 'WL-TEST-%' OR plate = ?;", (self.sample_plate,))
            cursor.execute("DELETE FROM echallans WHERE plate = ?;", (self.sample_plate,))
            cursor.execute("DELETE FROM detections WHERE plate = ?;", (self.sample_plate,))
            conn.commit()

    def test_filtered_detections_query(self):
        """Verifies multi-parameter detection queries."""
        # Query by plate state code 'GJ'
        dets = db.get_filtered_detections(state_code="GJ", limit=10)
        self.assertGreater(len(dets), 0)
        for d in dets:
            self.assertTrue(d["plate"].startswith("GJ"))

        # Query by camera
        cam_dets = db.get_filtered_detections(camera_id="CAM-01", limit=10)
        self.assertGreater(len(cam_dets), 0)
        for d in cam_dets:
            self.assertEqual(d["camera_id"], "CAM-01")

        # Query watchlist only
        wl_dets = db.get_filtered_detections(watchlist_only=True, limit=10)
        self.assertGreater(len(wl_dets), 0)
        for d in wl_dets:
            self.assertEqual(d["is_watchlist_hit"], 1)

    def test_section_65b_certificate_generation(self):
        """Generates authentic Section 65B Indian Evidence Act certificate with SHA-256 seal."""
        cert = db.generate_section_65b_certificate(
            plate=self.sample_plate,
            officer_name="Superintendent V. K. Jadeja",
            badge_no="GP-SP-2026",
            terminal_id="HQ-COMMAND-01"
        )
        self.assertIn("SEC65B-GJ-2026-", cert["certificateId"])
        self.assertEqual(cert["targetVehicle"]["plate"], self.sample_plate)
        self.assertGreater(cert["targetVehicle"]["totalSightingsCertified"], 0)

        # Verify cryptographic seal
        sha256 = cert["systemIntegrityDeclaration"]["evidenceHashSHA256"]
        self.assertEqual(len(sha256), 64)
        self.assertTrue(cert["systemIntegrityDeclaration"]["digitalSeal"].startswith("SHA256:"))

        # Verify legal declaration text cites Indian Evidence Act & BSA
        decl = cert["legalDeclarationText"]
        self.assertIn("Section 65B of the Indian Evidence Act, 1872", decl)
        self.assertIn("Bharatiya Sakshya Adhiniyam, 2023", decl)
        self.assertIn(sha256, decl)

    def test_echallan_record_and_settlement(self):
        """Creates an e-challan, queries it, and processes simulated payment."""
        challan_data = {
            "plate": self.sample_plate,
            "ownerName": "Shri Arvindbhai Patel",
            "vehicleMake": "Hyundai Creta SX (White)",
            "vehicleClass": "SUV",
            "violation": "Over-speeding (84 km/h in 60 zone)",
            "statutorySection": "Sec 112/183 Motor Vehicles Act",
            "fineAmount": 2000,
            "cameraId": "CAM-01",
            "location": "Iskcon Cross Road, Ahmedabad",
            "radarSpeed": "84 KM/H",
            "speedLimit": "60 KM/H"
        }
        c_no = db.record_echallan(challan_data)
        self.assertTrue(c_no.startswith("ECH-GJ-2026-"))

        # Verify retrieval
        chs = db.get_all_echallans(plate=self.sample_plate)
        self.assertGreater(len(chs), 0)
        found = next(c for c in chs if c["challanNo"] == c_no)
        self.assertEqual(found["status"], "UNPAID")
        self.assertEqual(found["fineAmount"], 2000)

        # Process payment
        paid = db.pay_echallan(c_no, txn_id="TXN-SBI-TEST-999")
        self.assertIsNotNone(paid)
        self.assertEqual(paid["status"], "PAID")
        self.assertEqual(paid["txn_id"], "TXN-SBI-TEST-999")

    def test_api_anpr_export_csv_and_json(self):
        """Tests FastAPI /api/reports/anpr/export endpoint for both CSV and JSON."""
        # JSON format
        resp_json = self.client.get("/api/reports/anpr/export?format=json")
        self.assertEqual(resp_json.status_code, 200)
        data = resp_json.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("records", data)
        self.assertGreater(data["totalRecords"], 0)

        # CSV format
        resp_csv = self.client.get("/api/reports/anpr/export?format=csv")
        self.assertEqual(resp_csv.status_code, 200)
        self.assertIn("text/csv", resp_csv.headers["content-type"])
        reader = csv.reader(io.StringIO(resp_csv.text))
        rows = list(reader)
        header = rows[0]
        self.assertIn("Sighting_ID", header)
        self.assertIn("Plate_Number", header)
        self.assertIn("Section_65B_Hash", header)
        self.assertGreater(len(rows), 1)

    def test_api_echallan_generation_endpoint(self):
        """Tests FastAPI /api/reports/echallan/generate endpoint."""
        payload = {
            "plate": self.sample_plate,
            "violationType": "RED_LIGHT",
            "cameraId": "CAM-04",
            "fineAmount": 1000
        }
        resp = self.client.post("/api/reports/echallan/generate", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "SUCCESS")
        ch = data["challan"]
        self.assertEqual(ch["plate"], self.sample_plate)
        self.assertEqual(ch["amount"], 1000)
        self.assertIn("Sec 184 Motor Vehicles Act", ch["statutoryOffense"])

    def test_api_echallan_pay_endpoint(self):
        """Tests FastAPI /api/reports/echallan/pay settlement endpoint."""
        # First generate a challan
        gen_payload = {
            "plate": self.sample_plate,
            "violationType": "SPEEDING",
            "fineAmount": 2000
        }
        gen_resp = self.client.post("/api/reports/echallan/generate", json=gen_payload)
        self.assertEqual(gen_resp.status_code, 200)
        c_no = gen_resp.json()["challan"]["challanNo"]

        # Pay the challan via the endpoint
        pay_resp = self.client.post("/api/reports/echallan/pay", json={"challanNo": c_no})
        self.assertEqual(pay_resp.status_code, 200)
        pay_data = pay_resp.json()
        self.assertEqual(pay_data["status"], "SUCCESS")
        self.assertIn("txnId", pay_data)

    def test_api_incident_dossier_endpoint(self):
        """Tests FastAPI /api/reports/incident-dossier/{plate} endpoint."""
        resp = self.client.get(f"/api/reports/incident-dossier/{self.sample_plate}")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["targetPlate"], self.sample_plate)
        self.assertIn("sightingHistory", data)
        self.assertIn("section65BCertificate", data)
        self.assertTrue(data["isWatchlistHit"])


if __name__ == "__main__":
    unittest.main()
