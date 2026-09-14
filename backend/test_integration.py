import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))
from database import db
from camera_manager import CameraManager, STREAM_STATUS

def test_db_vehicle_journey():
    print("=== Testing Database Vehicle Journey Deduplication and Ordering ===")
    matches = db.search_global_vehicles_by_plate("GJ01AB1234")
    print(f"1. Search 'GJ01AB1234': found {len(matches)} match(es).")
    assert len(matches) > 0, "No match found for GJ01AB1234!"
    gv = matches[0]
    gvid = gv["global_vehicle_id"]
    print(f"   GVID: {gvid}, Plate: {gv['plate']}, Hits: {gv.get('camera_hits', 1)}")

    veh_data = db.get_global_vehicle(gvid)
    assert veh_data is not None, f"Could not retrieve GlobalVehicle {gvid}"
    print(f"2. Retrieved GlobalVehicle: {veh_data['plate']} - {veh_data.get('vehicle_class', 'Car')}")

    route = db.get_vehicle_route(gvid)
    assert route["status"] == "SUCCESS", f"Route status unexpected: {route['status']}"
    assert len(route["timeline"]) == 3, f"Expected 3 corridor nodes, got {len(route['timeline'])}"
    print(f"3. Retrieved Chronological Journey Route: {len(route['timeline'])} waypoints.")

    pts_prev = -1.0
    for node in route["timeline"]:
        print(f"   Node #{node['sequence']}: {node['camera_id']} ({node['camera_name']}) at PTS {node['source_pts_ms']} ms - Time: {node['timestamp']}")
        assert node["source_pts_ms"] > pts_prev, "Route points are NOT strictly ordered by source_pts_ms!"
        pts_prev = node["source_pts_ms"]
    print("   -> STRICT PTS ORDERING VERIFIED: OK!")

def test_camera_manager_lifecycle():
    print("\n=== Testing CameraManager State, Worker Limits, and Idempotency ===")
    cm = CameraManager(db_instance=db, max_active_streams=5)
    cm.start_workers() # Workers start, but NO streams auto-connect (Requirement 5, 24)
    print("1. CameraManager initialized. Active streams count:", cm.get_active_stream_count())
    assert cm.get_active_stream_count() == 0, "Expected 0 active streams on startup!"

    # Test Idempotent Start
    res1 = cm.start_stream("CAM-01")
    print("2. Starting CAM-01:", res1)
    assert res1["status"] in ("SUCCESS", "STARTING", "ONLINE"), f"Unexpected status {res1['status']}"

    res2 = cm.start_stream("CAM-01")
    print("3. Starting CAM-01 again (Idempotent):", res2)
    assert res2["status"] in ("ALREADY_ACTIVE", "SUCCESS", "STARTING", "ONLINE"), "Idempotent start failed!"
    assert cm.get_active_stream_count() == 1, "Duplicate worker created for CAM-01!"

    # Test Stop
    stop_res = cm.stop_stream("CAM-01")
    print("4. Stopping CAM-01:", stop_res)
    assert cm.get_active_stream_count() == 0, "Stream not stopped properly!"

    # Test Max Streams Limit
    print("5. Testing MAX_ACTIVE_STREAMS limit (max=5)...")
    for i in range(1, 6):
        cid = f"CAM-0{i}"
        r = cm.start_stream(cid)
        assert r["status"] in ("SUCCESS", "STARTING", "ONLINE"), f"Failed to start {cid}: {r}"
    print(f"   Active count after 5 starts: {cm.get_active_stream_count()}")
    assert cm.get_active_stream_count() == 5

    # 6th should be rejected
    r6 = cm.start_stream("CAM-06")
    print("6. Attempting 6th stream (CAM-06):", r6)
    assert r6["status"] == "RESOURCE_LIMIT_REACHED", f"Expected RESOURCE_LIMIT_REACHED, got {r6}"
    print("   -> RESOURCE_LIMIT_REACHED properly enforced! OK!")

    cm.stop_workers()
    print("7. Stopped all workers cleanly.")

if __name__ == "__main__":
    test_db_vehicle_journey()
    test_camera_manager_lifecycle()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY! [OK]")
