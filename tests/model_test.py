import os
import sys
import unittest
import numpy as np

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from scripts.create_embeddings import get_embeddings_model

class TestVectorSearch(unittest.TestCase):
    def test_mock_embedder(self):
        """Verifies our mock embedding model is robust and deterministic."""
        embedder = get_embeddings_model("mock")
        
        texts = [
            "Purandara Dasa is the father of Carnatic music.",
            "Mayamalavagowla is symmetric."
        ]
        
        vectors = embedder.encode(texts)
        self.assertEqual(vectors.shape, (2, 384))
        
        # Test unit length normalization
        for v in vectors:
            norm = np.linalg.norm(v)
            self.assertAlmostEqual(norm, 1.0, places=4)
            
    def test_vector_similarities(self):
        """Verifies mathematical cosine similarity scoring."""
        v1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        v2 = np.array([1.0, 0.0, 0.0], dtype=np.float32) # Identical
        v3 = np.array([0.0, 1.0, 0.0], dtype=np.float32) # Orthogonal
        
        sim_identical = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        sim_orthogonal = np.dot(v1, v3) / (np.linalg.norm(v1) * np.linalg.norm(v3))
        
        self.assertAlmostEqual(sim_identical, 1.0, places=5)
        self.assertAlmostEqual(sim_orthogonal, 0.0, places=5)

if __name__ == '__main__':
    unittest.main()
