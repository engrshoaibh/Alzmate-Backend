# emotion_model.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import torch.nn.functional as F
from text_preprocessor import preprocess_text
from typing import Dict, Optional, List

MODEL_NAME = "boltuix/bert-emotion"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
model.eval()

labels = model.config.id2label

# Emotion mapping to standardize labels
EMOTION_MAPPING = {
    'joy': 'happy',
    'happiness': 'happy',
    'sadness': 'sad',
    'sad': 'sad',
    'anger': 'angry',
    'angry': 'angry',
    'fear': 'fearful',
    'fearful': 'fearful',
    'anxiety': 'anxious',
    'anxious': 'anxious',
    'confusion': 'confused',
    'confused': 'confused',
    'frustration': 'frustrated',
    'frustrated': 'frustrated',
    'calm': 'calm',
    'loneliness': 'lonely',
    'lonely': 'lonely',
    'depression': 'depressed/low mood',
    'depressed': 'depressed/low mood',
    'low mood': 'depressed/low mood',
}

# Required emotions from specification
REQUIRED_EMOTIONS = {
    'happy', 'sad', 'angry', 'anxious', 'fearful', 
    'confused', 'frustrated', 'calm', 'lonely', 'depressed/low mood'
}

def get_interpretation_tag(emotion: str, intensity: int) -> str:
    """Generate interpretation tag based on emotion and intensity."""
    intensity_level = "high" if intensity >= 70 else "moderate" if intensity >= 50 else "mild"
    
    emotion_tags = {
        'happy': f"{intensity_level} positive mood",
        'sad': f"{intensity_level} sadness",
        'angry': f"{intensity_level} distress",
        'anxious': f"{intensity_level} anxiety",
        'fearful': f"{intensity_level} fear",
        'confused': f"{intensity_level} confusion",
        'frustrated': f"{intensity_level} frustration",
        'calm': f"{intensity_level} calmness",
        'lonely': f"{intensity_level} loneliness",
        'depressed/low mood': f"{intensity_level} low mood"
    }
    
    return emotion_tags.get(emotion.lower(), f"{intensity_level} {emotion}")

def normalize_emotion_label(label: str) -> str:
    """Normalize emotion label to match required emotions."""
    label_lower = label.lower()
    
    # Direct mapping
    if label_lower in EMOTION_MAPPING:
        return EMOTION_MAPPING[label_lower]
    
    # Check if it contains any of our required emotions
    for req_emotion in REQUIRED_EMOTIONS:
        if req_emotion in label_lower or label_lower in req_emotion:
            return req_emotion
    
    # Default mapping based on common patterns
    if 'joy' in label_lower or 'happy' in label_lower:
        return 'happy'
    elif 'sad' in label_lower or 'sorrow' in label_lower:
        return 'sad'
    elif 'angry' in label_lower or 'rage' in label_lower:
        return 'angry'
    elif 'anxious' in label_lower or 'anxiety' in label_lower:
        return 'anxious'
    elif 'fear' in label_lower:
        return 'fearful'
    elif 'confus' in label_lower:
        return 'confused'
    elif 'frustrat' in label_lower:
        return 'frustrated'
    elif 'calm' in label_lower or 'peace' in label_lower:
        return 'calm'
    elif 'lonely' in label_lower or 'alone' in label_lower:
        return 'lonely'
    elif 'depress' in label_lower or 'low' in label_lower:
        return 'depressed/low mood'
    
    # Return original if no match
    return label

def analyze_emotion(text: str, preprocess: bool = True) -> Dict:
    """
    Analyze emotion from text with preprocessing and enhanced output.
    
    Args:
        text: Input text to analyze
        preprocess: Whether to preprocess text (default: True)
    
    Returns:
        Dictionary with primary_emotion, secondary_emotion, intensity, 
        interpretation tags, and mood_risk flag
    """
    if not text or not text.strip():
        return {
            "primary_emotion": {
                "emotion": "neutral",
                "confidence": 0.0,
                "intensity": 0
            },
            "secondary_emotion": None,
            "interpretation_tag": "no emotion detected",
            "mood_risk": False
        }
    
    # Preprocess text
    if preprocess:
        processed_text = preprocess_text(text)
        if not processed_text or not processed_text.strip():
            processed_text = text  # Fallback to original if preprocessing removes everything
    else:
        processed_text = text
    
    # Tokenize and predict
    inputs = tokenizer(
        processed_text, 
        return_tensors="pt", 
        truncation=True,
        max_length=512,
        padding=True
    )
    
    with torch.no_grad():
        outputs = model(**inputs)
    
    probs = F.softmax(outputs.logits, dim=1)[0]

    # Collect all emotion results
    results = []
    for i, score in enumerate(probs):
        original_label = labels[i]
        normalized_label = normalize_emotion_label(original_label)
        intensity = int(score.item() * 100)
        
        results.append({
            "emotion": normalized_label,
            "original_label": original_label,
            "confidence": round(score.item(), 4),
            "intensity": intensity
        })

    # Sort by confidence
    results.sort(key=lambda x: x["confidence"], reverse=True)

    # Get primary emotion
    primary = results[0]
    primary["interpretation_tag"] = get_interpretation_tag(primary["emotion"], primary["intensity"])

    # Get secondary emotion (if confidence >= 0.1 or intensity >= 30)
    secondary = None
    if len(results) > 1 and (results[1]["confidence"] >= 0.1 or results[1]["intensity"] >= 30):
        secondary = results[1]
        secondary["interpretation_tag"] = get_interpretation_tag(secondary["emotion"], secondary["intensity"])

    # Determine mood risk
    # High risk if primary negative emotion intensity >= 70 or secondary >= 60
    negative_emotions = {'sad', 'angry', 'anxious', 'fearful', 'confused', 
                        'frustrated', 'lonely', 'depressed/low mood'}
    
    primary_is_negative = primary["emotion"] in negative_emotions
    secondary_is_negative = secondary and secondary["emotion"] in negative_emotions if secondary else False
    
    mood_risk = (
        (primary_is_negative and primary["intensity"] >= 70) or
        (secondary_is_negative and secondary and secondary["intensity"] >= 60)
    )

    return {
        "primary_emotion": primary,
        "secondary_emotion": secondary,
        "interpretation_tag": primary["interpretation_tag"],
        "mood_risk": mood_risk,
        "processed_text": processed_text if preprocess else None
    }
