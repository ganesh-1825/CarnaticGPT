import os
import sys
import re
import glob
from utils import setup_logger

logger = setup_logger("TextCleaner")

def clean_text_content(text):
    """Sanitizes raw text: normalizes whitespace, cleans common headers,
    removes strange characters, and prepares content for semantic chunking.
    """
    if not text:
        return ""
        
    # Remove recurring PDF headers/footers (like page numbers or book titles)
    text = re.sub(r'(?i)Page \d+ of \d+', '', text)
    text = re.sub(r'(?i)CARNATIC\s*MUSIC\s*MANUAL', '', text)
    
    # Standardize strange quotes and characters
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    
    # Normalize multiple newlines and spaces
    text = re.sub(r'[ \t]+', ' ', text) # Single space tabs
    text = re.sub(r'\n\s*\n+', '\n\n', text) # Maximum double spacing
    
    return text.strip()

def run_cleaning():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, 'data', 'extracted_text')
    output_dir = os.path.join(base_dir, 'data', 'cleaned_text')
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all extracted text files recursively
    files = glob.glob(os.path.join(input_dir, "**", "*.txt"), recursive=True)
    cleaned_count = 0
    
    for file_path in files:
        # Keep subfolder structure relative to extracted_text
        rel_path = os.path.relpath(file_path, input_dir)
        out_path = os.path.join(output_dir, rel_path)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            cleaned = clean_text_content(content)
            
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(cleaned)
                
            logger.info(f"Cleaned and saved: {rel_path}")
            cleaned_count += 1
        except Exception as e:
            logger.error(f"Failed to clean file {file_path}: {e}")
            
    logger.info(f"Pipeline: Cleaning complete. Cleaned {cleaned_count} files.")

if __name__ == '__main__':
    run_cleaning()
