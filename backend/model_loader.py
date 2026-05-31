from backend.config import settings
from backend.logger import logger
from scripts.create_embeddings import get_embeddings_model

_model_cache = None

def get_cached_embedder():
    """Returns a singleton cached instance of the embedding model."""
    global _model_cache
    if _model_cache is None:
        logger.info("Initializing embedding model cache...")
        _model_cache = get_embeddings_model(settings.EMBEDDING_MODEL_NAME)
    return _model_cache
