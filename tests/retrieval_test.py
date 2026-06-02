import os
import sys
import unittest

# Ensure project root is visible
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))

from backend.rag import execute_rag_pipeline

class TestRetrievalPipeline(unittest.TestCase):
    def test_explain_bhairavi_retrieval(self):
        """Verifies that asking to explain Bhairavi retrieves Raga Lakshana with High Confidence."""
        query = "Explain Bhairavi"
        result = execute_rag_pipeline(query)
        
        # Verify result contains output response and citations
        self.assertIn("response", result)
        self.assertIn("citations", result)
        self.assertTrue(len(result["citations"]) > 0, "No citations were retrieved for Bhairavi query!")
        
        # Get top citation
        top_citation = result["citations"][0]
        
        # Validate expected book source
        # Can match either book_name directly or in source path
        book_name = top_citation.get("book_name", "")
        source_path = top_citation.get("source", "")
        
        self.assertTrue(
            "Raga Lakshana" in book_name or "Raga_Lakshana" in source_path or "raga_knowledge_base" in source_path or "Raga Knowledge Base" in book_name,
            f"Expected source to be Raga Lakshana or Knowledge Base, got Book Name: '{book_name}' / Source: '{source_path}'"
        )
        
        # Validate confidence rating
        confidence = top_citation.get("confidence", "")
        self.assertEqual(
            confidence, "High Confidence",
            f"Expected High Confidence retrieval, got: '{confidence}'"
        )
        
        print("\n=== Retrieval Test Passed Successfully! ===")
        print(f"Query: '{query}'")
        print(f"Top Source: '{book_name}' ({source_path})")
        print(f"Confidence: '{confidence}'")
        print("===========================================\n")

if __name__ == '__main__':
    unittest.main()
