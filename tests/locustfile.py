"""Load tests for Fuel Tracker API."""
from locust import HttpUser, between, task


class FuelTrackerUser(HttpUser):
    wait_time = between(1, 3)
    headers = {"X-Device-Id": "load-test-device"}

    @task(3)
    def list_refuelings(self):
        self.client.get("/api/refuelings", headers=self.headers)

    @task(1)
    def get_stats(self):
        self.client.get("/api/stats", headers=self.headers)

    @task(1)
    def healthcheck(self):
        self.client.get("/api/health")
