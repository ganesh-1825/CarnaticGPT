import os
import sys
import logging

# Ensure project root is in sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logger(name):
    """Sets up a standardized logger for all CarnaticGPT ingestion scripts."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Check if handlers already exist to prevent duplicate logging
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console output
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File output
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analytics')
        os.makedirs(log_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(log_dir, 'pipeline.log'), encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

def ensure_directory_structure():
    """Initializes the complete directory tree required by CarnaticGPT."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    dirs = [
        'data/books/South_Indian_Music',
        'data/books/Ragas',
        'data/books/Composers',
        'data/books/Music_History',
        'data/books/Instruments',
        'data/books/Journals',
        'data/books/Research_Papers',
        'data/books/Dictionary',
        'data/extracted_text/South_Indian_Music',
        'data/extracted_text/Ragas',
        'data/extracted_text/Composers',
        'data/extracted_text/History',
        'data/extracted_text/Instruments',
        'data/extracted_text/Journals',
        'data/cleaned_text',
        'data/chunks',
        'data/generated_QA',
        'data/datasets',
        'data/embeddings',
        'models/base_model',
        'models/fine_tuned_model',
        'models/embedding_model',
        'vectorDB/faiss_index',
        'vectorDB/metadata',
        'backend',
        'frontend',
        'analytics',
        'tests',
        'deployment',
        'assets/images',
        'assets/logos',
        'assets/demo_audio'
    ]
    
    for d in dirs:
        path = os.path.join(base_dir, d)
        os.makedirs(path, exist_ok=True)
        # Create a .gitkeep to preserve directory in version control
        with open(os.path.join(path, '.gitkeep'), 'a') as f:
            pass

if __name__ == '__main__':
    ensure_directory_structure()
    logger = setup_logger("Utils")
    logger.info("CarnaticGPT directory tree initialized successfully.")
