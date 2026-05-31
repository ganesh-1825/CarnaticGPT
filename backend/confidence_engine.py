from backend.logger import logger

class CarnaticConfidenceEngine:
    """Evaluates and tags retrieval scores with clear confidence tiers: High, Medium, or Low."""
    
    # Thresholds for classification
    HIGH_THRESHOLD = 0.85
    MEDIUM_THRESHOLD = 0.60
    LOW_THRESHOLD = 0.40

    def __init__(self):
        logger.info("CarnaticConfidenceEngine initialized.")

    def evaluate(self, score: float) -> str:
        """Categorizes a numeric similarity/rerank score into a confidence level."""
        if score >= self.HIGH_THRESHOLD:
            return "High Confidence"
        elif score >= self.MEDIUM_THRESHOLD:
            return "Medium Confidence"
        elif score >= self.LOW_THRESHOLD:
            return "Low Confidence"
        else:
            return "No highly relevant source found"


# Singleton instance
confidence_engine_instance = CarnaticConfidenceEngine()

def calculate_confidence(score: float) -> str:
    """Convenience helper using the singleton CarnaticConfidenceEngine."""
    return confidence_engine_instance.evaluate(score)
