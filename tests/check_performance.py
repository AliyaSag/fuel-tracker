"""Check locust P95 results against threshold."""
import csv
import sys

THRESHOLD_MS = 200
ENDPOINTS = ["/api/refuelings", "/api/stats"]

with open("locust-results_stats.csv") as f:
    for row in csv.DictReader(f):
        if row["Name"] in ENDPOINTS:
            p95 = float(row["95%"])
            status = "OK" if p95 <= THRESHOLD_MS else "FAIL"
            print(f"{status}: P95={p95}ms for {row['Name']}")
            if p95 > THRESHOLD_MS:
                sys.exit(1)
