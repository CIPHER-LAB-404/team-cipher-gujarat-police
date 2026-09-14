import sys
import os
import re

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from server import app

def run_api_tests():
    print("=== Starting FastApi End-to-End API Integration Tests ===")
    client = TestClient(app)

    # 1. Test Camera Catalogue API (Requirements 4, 16, 19)
    print("\n1. Testing GET /api/cameras ...")
    resp = client.get("/api/cameras")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data["status"] == "success"
    cams = data["cameras"]
    assert len(cams) > 0, "Cameras catalogue is empty!"
    print(f"   -> Loaded {len(cams)} cameras.")

    # Verify credentials security (Requirement 4)
    for c in cams:
        for k in ["rtsp_url", "url", "stream_url"]:
            val = str(c.get(k, ""))
            assert "@" not in val, f"Credential leaked in camera {c.get('camera_id')}: {val}"
    print("   -> RTSP Credential Sanitization: VERIFIED! No passwords leaked.")

    first_cam = cams[0]
    cam_id = first_cam["camera_id"]
    print(f"   -> Sample Camera: {cam_id} ({first_cam.get('name')}), Status: {first_cam.get('status')}")
    assert "codec" in first_cam, "Missing codec in camera record"
    assert "resolution" in first_cam, "Missing resolution in camera record"

    # 2. Test Camera Health API (Requirement 23)
    print(f"\n2. Testing GET /api/cameras/{cam_id}/health ...")
    h_resp = client.get(f"/api/cameras/{cam_id}/health")
    assert h_resp.status_code == 200
    h_data = h_resp.json()
    assert h_data["status"] == "success"
    h = h_data["health"]
    print(f"   -> Camera Health Status: {h['status']}, Codec: {h['codec']}, Res: {h['resolution']}")
    assert "reconnect_count" in h
    assert "received_fps" in h

    # 3. Test Camera Start/Stop API (Requirements 5, 6, 8)
    print(f"\n3. Testing POST /api/cameras/{cam_id}/start ...")
    start_resp = client.post(f"/api/cameras/{cam_id}/start")
    assert start_resp.status_code in (200, 201), f"Unexpected status {start_resp.status_code}"
    start_data = start_resp.json()
    print("   -> Start response:", start_data)

    # Idempotent start
    start_resp_2 = client.post(f"/api/cameras/{cam_id}/start")
    assert start_resp_2.status_code in (200, 201)
    print("   -> Idempotent Start response:", start_resp_2.json())

    # Stop stream
    print(f"\n4. Testing POST /api/cameras/{cam_id}/stop ...")
    stop_resp = client.post(f"/api/cameras/{cam_id}/stop")
    assert stop_resp.status_code == 200
    print("   -> Stop response:", stop_resp.json())

    # 4. Test Vehicle Search API (Requirements 3, 18)
    print("\n5. Testing GET /api/vehicles/search?plate=GJ01AB1234 ...")
    s_resp = client.get("/api/vehicles/search?plate=GJ01AB1234")
    assert s_resp.status_code == 200
    s_data = s_resp.json()
    assert s_data["status"] == "success"
    assert s_data["totalMatches"] > 0, "Vehicle GJ01AB1234 not found!"
    matched_veh = s_data["vehicles"][0]
    gvid = matched_veh["global_vehicle_id"]
    print(f"   -> Found Vehicle! GVID: {gvid}, Plate: {matched_veh['plate']}")

    # 5. Test Global Vehicle Details API (Requirement 3)
    print(f"\n6. Testing GET /api/vehicles/{gvid} ...")
    v_resp = client.get(f"/api/vehicles/{gvid}")
    assert v_resp.status_code == 200
    v_data = v_resp.json()
    assert v_data["status"] == "success"
    veh = v_data["vehicle"]
    print(f"   -> GlobalVehicle Details: Plate={veh['plate']}, Class={veh.get('vehicle_class')}, Hits={veh.get('camera_hits')}")

    # 6. Test Vehicle Route API (Requirements 3, 11, 12, 17, 18)
    print(f"\n7. Testing GET /api/vehicles/{gvid}/route ...")
    r_resp = client.get(f"/api/vehicles/{gvid}/route")
    assert r_resp.status_code == 200
    r_data = r_resp.json()
    timeline = r_data["timeline"]
    assert len(timeline) >= 3, f"Expected at least 3 waypoints in route, got {len(timeline)}"
    print(f"   -> Route has {len(timeline)} checkpoints across Gujarat state cameras.")

    pts_prev = -1.0
    for node in timeline:
        print(f"      Checkpoint #{node['sequence']}: {node['camera_id']} ({node['camera_name']}) at PTS {node['source_pts_ms']} ms")
        assert node["source_pts_ms"] > pts_prev, "Checkpoints NOT sorted strictly by source_pts_ms!"
        pts_prev = node["source_pts_ms"]
        assert node["latitude"] != 0 and node["longitude"] != 0
        assert "snapshot" in node
    print("   -> Strict PTS Ordering & Spatial Waypoints: VERIFIED!")

    print("\nALL END-TO-END FASTAPI TESTS PASSED SUCCESSFULLY! [OK]")

if __name__ == "__main__":
    run_api_tests()
