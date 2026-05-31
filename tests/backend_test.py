import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure backend visible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from backend.server import app

class TestBackendAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        
    def test_health_endpoint(self):
        """Verifies API health endpoint is online."""
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertIn("indexed_documents", data)
        
    def test_stats_endpoint(self):
        """Verifies stats endpoint is working."""
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_vectors", data)
        self.assertIn("active_sessions", data)
        
    def test_chat_sessions_flow(self):
        """Test chat sessions listing, creation, and deletion."""
        # Create session
        res_create = self.client.post("/api/chat/sessions")
        self.assertEqual(res_create.status_code, 200)
        sid = res_create.json()["session_id"]
        self.assertTrue(sid)
        
        # List sessions
        res_list = self.client.get("/api/chat/sessions")
        self.assertEqual(res_list.status_code, 200)
        sessions = res_list.json()["sessions"]
        self.assertTrue(any(s["id"] == sid for s in sessions))
        
        # Delete session
        res_del = self.client.delete(f"/api/chat/sessions/{sid}")
        self.assertEqual(res_del.status_code, 200)
        
if __name__ == '__main__':
    unittest.main()

