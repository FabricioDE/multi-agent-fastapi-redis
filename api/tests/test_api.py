import unittest
from starlette.testclient import TestClient
from main import app  
import asyncio

class TestAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_send_message(self):
        response = self.client.post("/api/v1/agent", json={"message": "Hello", "user_id": 123})
        self.assertEqual(response.status_code, 201)


if __name__ == '__main__':
    unittest.main()