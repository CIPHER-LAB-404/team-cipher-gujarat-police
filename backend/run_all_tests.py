#!/usr/bin/env python3
"""
=============================================================================
Gujarat Police Sentinel - Master Automated Test Runner
=============================================================================
Executes full regression test suites across:
1. Syntax & Positional Disambiguation Engine (MoRTH / CMVR Standard)
2. Multi-Line Two-Tier Plate OCR & Row Clustering Pipeline
3. Sighting Reporting, Statutory e-Challan & Section 65B Evidence System
4. Live ANPR Detector, Benchmark Inference & Watchlist Correlation
=============================================================================
"""

import unittest
import sys
import os
import time

# Set TESTING environment variable to prevent network streaming threads
os.environ["TESTING"] = "1"

# Ensure backend and root directories are in python search path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
for p in [CURRENT_DIR, ROOT_DIR, os.path.join(CURRENT_DIR, "tests")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from test_syntax_validator import TestIndianPlateSyntaxValidator
from test_ocr_multiline import TestMultiLinePlateProcessor
from test_reporting_and_evidence import TestReportingAndEvidenceSystem
from test_anpr_detector_live import TestANPRDetectorLive


def run_master_test_suite():
    print("=" * 80)
    print("  GUJARAT POLICE SENTINEL - MASTER ANPR & REPORTING VERIFICATION SUITE")
    print("=" * 80)
    print(f"  Execution Time : {time.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print(f"  Python Version : {sys.version.split()[0]} ({sys.executable})")
    print(f"  Target Platform: State CCTV Command & Control Grid")
    print("=" * 80 + "\n")

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    test_modules = [
        ("Indian Syntax & Slot Disambiguation", loader.loadTestsFromTestCase(TestIndianPlateSyntaxValidator)),
        ("Multi-Line Plate Row Slicing & OCR", loader.loadTestsFromTestCase(TestMultiLinePlateProcessor)),
        ("Section 65B Evidence & e-Challan Reporting", loader.loadTestsFromTestCase(TestReportingAndEvidenceSystem)),
        ("Live ANPR Pipeline & Benchmark Detection", loader.loadTestsFromTestCase(TestANPRDetectorLive)),
    ]

    total_tests = 0
    total_failures = 0
    total_errors = 0
    suite_results = []

    start_master_time = time.perf_counter()

    for name, test_case_suite in test_modules:
        count = test_case_suite.countTestCases()
        total_tests += count
        t0 = time.perf_counter()
        runner = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
        res = runner.run(test_case_suite)
        elapsed = time.perf_counter() - t0

        n_fail = len(res.failures)
        n_err = len(res.errors)
        total_failures += n_fail
        total_errors += n_err

        status = "PASSED" if (n_fail == 0 and n_err == 0) else "FAILED"
        suite_results.append({
            "name": name,
            "count": count,
            "passed": count - n_fail - n_err,
            "failed": n_fail,
            "errors": n_err,
            "time_sec": round(elapsed, 3),
            "status": status
        })

    master_elapsed = round(time.perf_counter() - start_master_time, 2)

    # Print Formatted Executive Table
    print(f"{'Component / Test Suite':<45} | {'Tests':<6} | {'Passed':<6} | {'Failed':<6} | {'Time (s)':<8} | {'Status'}")
    print("-" * 88)
    for sr in suite_results:
        st_symbol = "[OK] PASS" if sr["status"] == "PASSED" else "[!] FAIL"
        print(f"{sr['name']:<45} | {sr['count']:<6} | {sr['passed']:<6} | {sr['failed']:<6} | {sr['time_sec']:<8.3f} | {st_symbol}")
    print("-" * 88)
    total_passed = total_tests - total_failures - total_errors
    print(f"{'TOTAL COMPREHENSIVE SUITE':<45} | {total_tests:<6} | {total_passed:<6} | {total_failures + total_errors:<6} | {master_elapsed:<8.2f} | {'SUCCESS' if total_failures == 0 else 'ALERT'}")
    print("=" * 88 + "\n")

    if total_failures == 0 and total_errors == 0:
        print(">> ALL SYSTEMS VERIFIED: 100% PASSING RATE ACROSS ALL ANPR MODULES <<\n")
        return 0
    else:
        print(f">> WARNING: {total_failures + total_errors} test(s) failed or encountered errors <<\n")
        return 1


if __name__ == "__main__":
    exit_code = run_master_test_suite()
    sys.exit(exit_code)
