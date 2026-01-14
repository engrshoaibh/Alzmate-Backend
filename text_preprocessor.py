# text_preprocessor.py
import re
from typing import List

# Common filler words to remove
FILLER_WORDS = {
    'um', 'uh', 'er', 'ah', 'eh', 'hmm', 'hm', 'like', 'you know',
    'well', 'so', 'actually', 'basically', 'literally', 'sort of',
    'kind of', 'i mean', 'you see', 'right', 'okay', 'ok'
}

def preprocess_text(text: str) -> str:
    """
    Preprocess journal text by:
    1. Cleaning filler words
    2. Removing repeated characters
    3. Removing extra spaces
    4. Normalizing text (case, punctuation)
    """
    if not text or not text.strip():
        return ""
    
    # Convert to lowercase for normalization
    text = text.lower()
    
    # Remove filler words (case-insensitive)
    words = text.split()
    filtered_words = []
    for word in words:
        # Remove punctuation for comparison
        clean_word = re.sub(r'[^\w]', '', word)
        if clean_word not in FILLER_WORDS:
            filtered_words.append(word)
    
    text = ' '.join(filtered_words)
    
    # Remove repeated characters (more than 2 consecutive same characters)
    # e.g., "sooo" -> "soo", "happyyy" -> "happyy"
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    
    # Remove extra spaces (multiple spaces to single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing spaces
    text = text.strip()
    
    # Normalize punctuation spacing
    text = re.sub(r'\s+([,.!?;:])', r'\1', text)
    text = re.sub(r'([,.!?;:])\s*([,.!?;:])', r'\1\2', text)
    
    return text

def clean_filler_words(text: str) -> str:
    """Remove filler words from text."""
    words = text.split()
    filtered_words = []
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word.lower())
        if clean_word not in FILLER_WORDS:
            filtered_words.append(word)
    return ' '.join(filtered_words)

def remove_repeated_chars(text: str) -> str:
    """Remove excessive repeated characters."""
    return re.sub(r'(.)\1{2,}', r'\1\1', text)

def normalize_spaces(text: str) -> str:
    """Normalize whitespace."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

