
import sys
from pathlib import Path
import unittest

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from app.app import app

class AppRoutesTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def login(self, username="admin", password="admin123"):
        return self.client.post("/login", data={"username": username, "password": password}, follow_redirects=True)

    def test_login_page(self):
        resp = self.client.get("/login")
        self.assertEqual(resp.status_code, 200)

    def test_authenticated_routes(self):
        self.login()
        for route in ["/", "/dashboard", "/graph", "/governance", "/quality", "/about", "/admin/logs", "/api/summary"]:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 200)

if __name__ == "__main__":
    unittest.main()
