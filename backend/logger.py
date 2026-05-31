import os
import logging
from logging.handlers import RotatingFileHandler

def get_logger(name="CarnaticGPT-Server"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')
        
        # Stream Handler
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        
        # File Handler
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'analytics')
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, 'server.log')
        
        fh = RotatingFileHandler(log_path, maxBytes=10*1024*1024, backupCount=5, encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

logger = get_logger()
