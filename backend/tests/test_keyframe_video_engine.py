import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from anpr_detector import anpr_engine
from database import db


class TestKeyframeVideoEngine(unittest.TestCase):
    def test_1_fps_keyframe_extraction(self):
        video_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "real_traffic_cam01.mp4"))
        self.assertTrue(os.path.exists(video_path), f"Video file not found at {video_path}")

        # Run 1-second keyframe ANPR detection
        res = anpr_engine.process_full_video_file(
            video_path,
            camera_id="CAM-01-TEST",
            sample_interval_sec=1.0
        )

        self.assertEqual(res.get("status"), "success")
        self.assertGreater(res.get("totalFramesAnalyzed", 0), 0)
        self.assertGreater(res.get("durationSec", 0), 0)

        # Check detections list structure
        detections = res.get("detections", [])
        print(f"\n[+] Total Frames Analyzed: {res.get('totalFramesAnalyzed')}")
        print(f"[+] Video Duration: {res.get('durationSec')}s")
        print(f"[+] Total Vehicle Detections: {len(detections)}")

        for d in detections:
            self.assertIn("plate", d)
            self.assertIn("confidence", d)
            self.assertIn("ptsSec", d)
            self.assertIn("isWatchlistHit", d)
            print(f"  -> Plate: {d['plate']} | Conf: {d['confidence']} | PTS: {d['ptsSec']}s")


if __name__ == "__main__":
    unittest.main()
