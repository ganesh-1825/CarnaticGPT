import re
from backend.logger import logger

class CarnaticResponseFormatter:
    """Format, clean up, and audit generative model answers to ensure consistent,
    polished Markdown rendering and structural uniformity.
    """
    
    def __init__(self):
        logger.info("CarnaticResponseFormatter initialized.")

    def format_response(self, text: str) -> str:
        """Applies multiple formatting filters to sanitize, align, and clean the Markdown text."""
        if not text:
            return ""
            
        formatted = text.strip()
        
        # 1. Ensure all custom-seeded code blocks (like Swaras) have proper spacing
        formatted = re.sub(r'(`[S R G M P D N \d\s]+`)', r' \1 ', formatted)
        
        # 2. Convert raw double line breaks to double newlines for uniform paragraphing
        formatted = re.sub(r'\n{3,}', '\n\n', formatted)
        
        # 3. Standardize bullet spacing (ensure space after - or *)
        formatted = re.sub(r'^(\s*[-*+])([^\s])', r'\1 \2', formatted, flags=re.MULTILINE)
        
        # 4. Enforce uppercase headings in custom subsections
        def capitalize_headings(match):
            heading_prefix = match.group(1)
            heading_text = match.group(2)
            return f"{heading_prefix} {heading_text.upper()}"
            
        formatted = re.sub(r'^(#{2,4})\s*(s\w+|k\w+|m\w+|t\w+)(.*)$', capitalize_headings, formatted, flags=re.MULTILINE)
        
        # 5. Fix double spaces and clean trailing line items
        formatted = re.sub(r'[ \t]+', ' ', formatted)
        formatted = formatted.replace(" \n", "\n")
        
        logger.info("Answer formatting and Markdown auditing complete.")
        return formatted

# Singleton instance
formatter_instance = CarnaticResponseFormatter()

def format_answer(text: str) -> str:
    """Helper shortcut using the singleton Response Formatter."""
    return formatter_instance.format_response(text)
