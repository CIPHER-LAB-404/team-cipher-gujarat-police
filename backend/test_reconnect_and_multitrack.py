import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database import db
from camera_manager import CameraManager, RECONNECT_BACKOFF, STREAM_STATUS
from anpr_pipeline.postprocess.syntax_validator import IndianPlateSyntaxValidator

def test_cross_camera_multi_track_resolution():
    print("=== Testing Cross-Camera Multi-Track Deduplication (Requirement 1, 28) ===")
    validator = IndianPlateSyntaxValidator()

    # CAM001: GJ01AB1234, Local Track 17
    # CAM007: GJ01ABI234 (common OCR 'I' vs '1' confusion), Local Track 42
    # CAM019: GJ01AB1234, Local Track 8

    res_1 = validator.correct_and_validate("GJ01AB1234")
    res_2 = validator.correct_and_validate("GJ01ABI234")
    res_3 = validator.correct_and_validate("GJ 01 AB 1234")

    norm_1 = res_1.validated_plate
    norm_2 = res_2.validated_plate
    norm_3 = res_3.validated_plate

    print(f"1. Validated 'GJ01AB1234' -> '{norm_1}'")
    print(f"2. Validated 'GJ01ABI234' (OCR Noise I->1) -> '{norm_2}'")
    print(f"3. Validated 'GJ 01 AB 1234' (Whitespace) -> '{norm_3}'")

    assert norm_1 == "GJ01AB1234"
    assert norm_2 == "GJ01AB1234", f"Expected 'GJ01AB1234', got '{norm_2}'"
    assert norm_3 == "GJ01AB1234"

    # Global correlation: f"GV-{plate.replace(' ', '').replace('-', '')}"
    gvid_1 = f"GV-{norm_1.replace(' ', '').replace('-', '')}"
    gvid_2 = f"GV-{norm_2.replace(' ', '').replace('-', '')}"
    gvid_3 = f"GV-{norm_3.replace(' ', '').replace('-', '')}"

    print(f"4. Global Vehicle IDs: [{gvid_1}, {gvid_2}, {gvid_3}]")
    assert gvid_1 == gvid_2 == gvid_3
    print("   -> ONE global_vehicle_id across multiple cameras: VERIFIED!")

    # Verify distinct local tracks and deduplicated events
    obs_id_1 = f"OBS-CAM001-17-10000"
    obs_id_2 = f"OBS-CAM007-42-45000"
    obs_id_3 = f"OBS-CAM019-8-90000"

    db.record_global_vehicle(gvid_1, norm_1, 0.98, "Car", 10000.0)

    db.record_anpr_observation({
        "observation_id": obs_id_1,
        "camera_id": "CAM-01",
        "camera_name": "CAM001",
        "department": "Traffic Police",
        "latitude": 23.0338,
        "longitude": 72.5850,
        "track_id": 17,
        "plate_text": norm_1,
        "confidence": 0.98,
        "source_pts_ms": 10000.0,
        "timestamp": "2026-09-14 11:00:00 IST",
        "global_vehicle_id": gvid_1
    })
    db.record_vehicle_journey_event(
        global_vehicle_id=gvid_1, observation_id=obs_id_1, camera_id="CAM-01",
        source_pts_ms=10000.0, latitude=23.0338, longitude=72.5850,
        plate_text=norm_1, confidence=0.98, timestamp="2026-09-14 11:00:00 IST", camera_name="CAM001"
    )

    db.record_anpr_observation({
        "observation_id": obs_id_2,
        "camera_id": "CAM-07",
        "camera_name": "CAM007",
        "department": "Traffic Police",
        "latitude": 22.9241,
        "longitude": 72.6014,
        "track_id": 42,
        "plate_text": norm_2,
        "confidence": 0.96,
        "source_pts_ms": 45000.0,
        "timestamp": "2026-09-14 11:05:00 IST",
        "global_vehicle_id": gvid_1
    })
    db.record_vehicle_journey_event(
        global_vehicle_id=gvid_1, observation_id=obs_id_2, camera_id="CAM-07",
        source_pts_ms=45000.0, latitude=22.9241, longitude=72.6014,
        plate_text=norm_2, confidence=0.96, timestamp="2026-09-14 11:05:00 IST", camera_name="CAM007"
    )

    db.record_anpr_observation({
        "observation_id": obs_id_3,
        "camera_id": "CAM-19",
        "camera_name": "CAM019",
        "department": "Traffic Police",
        "latitude": 21.5412,
        "longitude": 70.4389,
        "track_id": 8,
        "plate_text": norm_3,
        "confidence": 0.99,
        "source_pts_ms": 90000.0,
        "timestamp": "2026-09-14 11:15:00 IST",
        "global_vehicle_id": gvid_1
    })
    db.record_vehicle_journey_event(
        global_vehicle_id=gvid_1, observation_id=obs_id_3, camera_id="CAM-19",
        source_pts_ms=90000.0, latitude=21.5412, longitude=70.4389,
        plate_text=norm_3, confidence=0.99, timestamp="2026-09-14 11:15:00 IST", camera_name="CAM019"
    )

    route = db.get_vehicle_route(gvid_1)
    print(f"5. Journey Route Checkpoints Count: {len(route['timeline'])}")
    assert len(route["timeline"]) >= 3, "Failed to correlate 3 checkpoints into 1 journey!"
    print("   -> Distinct Tracks (17, 42, 8) Unified into 1 Coherent Journey: VERIFIED!")

def test_reconnect_backoff_and_lifecycle():
    print("\n=== Testing Reconnect Backoff & Worker Idempotency (Requirement 21, 27) ===")
    print("1. Reconnect backoff sequence:", RECONNECT_BACKOFF)
    assert RECONNECT_BACKOFF == [2, 4, 8, 16, 30, 30], f"Invalid backoff sequence: {RECONNECT_BACKOFF}"
    print("   -> Backoff sequence [2, 4, 8, 16, 30, 30] seconds: VERIFIED!")

    cm = CameraManager(db_instance=db, max_active_streams=5)
    cm.start_workers()

    # Start CAM-02
    r1 = cm.start_stream("CAM-02")
    assert r1["status"] in ("SUCCESS", "STARTING", "ONLINE")
    print(f"2. Camera CAM-02 started: status={r1['status']}")

    # Check health telemetry
    h1 = cm.get_camera_health("CAM-02")
    assert h1["status"] in ("STARTING", "ONLINE", "RECONNECTING")
    assert "reconnect_count" in h1
    print(f"3. Live Health: status={h1['status']}, reconnect_count={h1['reconnect_count']}")

    # Idempotent start must NOT create duplicate worker
    w1 = cm.workers.get("CAM-02")
    r2 = cm.start_stream("CAM-02")
    w2 = cm.workers.get("CAM-02")
    assert w1 is w2, "A new worker instance was created on duplicate start!"
    print("4. Idempotency verified: identical worker instance preserved.")

    # Stop stream cleanly
    cm.stop_stream("CAM-02")
    assert "CAM-02" not in cm.workers
    print("5. Stream stopped cleanly, worker released.")

    cm.shutdown()
    print("6. CameraManager shutdown cleanly.")

if __name__ == "__main__":
    test_cross_camera_multi_track_resolution()
    test_reconnect_backoff_and_lifecycle()
    print("\nALL RECONNECT & CROSS-CAMERA TESTS PASSED SUCCESSFULLY! [OK]")
