# emotion_model.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoConfig
import torch
import torch.nn.functional as F
from text_preprocessor import preprocess_text
from typing import Dict, Optional, List
import logging

logger = logging.getLogger(__name__)

# Note: We do NOT import BertForSequenceClassification at module level
# to avoid torchvision compatibility issues. It will be imported lazily
# inside _load_model() when actually needed.

MODEL_NAME = "boltuix/bert-emotion"

# Initialize model and tokenizer as None - will be loaded lazily
_tokenizer = None
_model = None
_labels = None

def _load_model():
    """Load the emotion model and tokenizer."""
    global _tokenizer, _model, _labels
    
    if _model is not None:
        return  # Already loaded
    
    try:
        logger.info(f"Loading emotion model: {MODEL_NAME}")
        
        # Load tokenizer first
        try:
            _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        except Exception as e:
            raise ValueError(
                f"Failed to load tokenizer for model '{MODEL_NAME}': {e}. "
                "Please check your internet connection."
            ) from e
        
        # Load config first to understand the model architecture
        try:
            config = AutoConfig.from_pretrained(MODEL_NAME)
            logger.info(f"Model type: {config.model_type}, Architectures: {getattr(config, 'architectures', 'N/A')}")
        except Exception as e:
            logger.warning(f"Could not load config: {e}, proceeding with default loading")
            config = None
        
        # Try multiple loading strategies
        loading_strategies = [
            # Strategy 1: Use explicit BERT class (most reliable for BERT models)
            {
                "description": "explicit_bert_class",
                "method": "explicit_bert"
            },
            # Strategy 2: Use AutoModel with ignore_mismatched_sizes
            {
                "description": "auto_ignore_mismatch",
                "method": "auto",
                "kwargs": {"ignore_mismatched_sizes": True}
            },
            # Strategy 3: Standard AutoModel loading
            {
                "description": "auto_model",
                "method": "auto",
                "kwargs": {}
            },
            # Strategy 4: With trust_remote_code
            {
                "description": "trust_remote_code",
                "method": "auto",
                "kwargs": {"trust_remote_code": True}
            },
        ]
        
        last_error = None
        for strategy in loading_strategies:
            try:
                logger.info(f"Trying to load model with strategy: {strategy['description']}")
                
                if strategy["method"] == "explicit_bert":
                    # Try loading with explicit BERT class
                    try:
                        from transformers.models.bert.modeling_bert import BertForSequenceClassification
                        if config:
                            _model = BertForSequenceClassification.from_pretrained(
                                MODEL_NAME,
                                config=config
                            )
                        else:
                            _model = BertForSequenceClassification.from_pretrained(MODEL_NAME)
                    except ImportError as import_err:
                        # If we can't import the class, skip this strategy
                        logger.warning(f"Cannot import BertForSequenceClassification: {import_err}")
                        raise import_err
                else:
                    # Use AutoModel
                    _model = AutoModelForSequenceClassification.from_pretrained(
                        MODEL_NAME,
                        **strategy.get("kwargs", {})
                    )
                
                logger.info(f"Successfully loaded model using strategy: {strategy['description']}")
                break  # Success, exit loop
                
            except (ModuleNotFoundError, AttributeError, ImportError) as e:
                last_error = e
                error_str = str(e)
                if "BertForSequenceClassification" in error_str or "Could not import module" in error_str:
                    logger.warning(
                        f"Model loading failed with {type(e).__name__}: {e}. "
                        "Trying alternative loading methods..."
                    )
                continue
            except Exception as e:
                last_error = e
                logger.warning(f"Loading strategy '{strategy['description']}' failed: {e}")
                continue
        
        if _model is None:
            # All strategies failed - try one more time with a workaround
            try:
                logger.info("Attempting final workaround: loading via AutoModel with ignore_mismatched_sizes")
                from transformers import AutoModel
                # Load as base model and add classification head manually if needed
                base_model = AutoModel.from_pretrained(MODEL_NAME)
                config = base_model.config
                
                # Try to get the actual model from the state dict
                _model = AutoModelForSequenceClassification.from_pretrained(
                    MODEL_NAME,
                    ignore_mismatched_sizes=True
                )
            except Exception as final_error:
                # All methods failed
                import transformers
                transformers_version = transformers.__version__
                
                error_msg = (
                    f"Failed to load emotion model '{MODEL_NAME}' after trying all strategies. "
                    f"Last error: {last_error or final_error}. "
                    f"\n\nDetected transformers version: {transformers_version}"
                    "\n\nThis error is commonly caused by transformers 5.0.0 compatibility issues."
                    "\n\nRECOMMENDED FIX:"
                    "\n  Run this command to downgrade transformers:"
                    "\n  pip install 'transformers>=4.35.0,<5.0.0' --upgrade"
                    "\n\nOr run the helper script:"
                    "\n  python fix_transformers_compatibility.py"
                    "\n\nAlternative solutions:"
                    "\n  1. Upgrade transformers: pip install --upgrade transformers"
                    "\n  2. Clear HuggingFace cache: rm -rf ~/.cache/huggingface/"
                    "\n  3. Check model: https://huggingface.co/boltuix/bert-emotion"
                )
                raise ValueError(error_msg) from (last_error or final_error)
        
        _model.eval()
        _labels = _model.config.id2label
        logger.info("Emotion model loaded successfully")
        
    except ValueError:
        # Re-raise ValueError as-is (it already has helpful messages)
        raise
    except Exception as e:
        logger.error(f"Unexpected error loading emotion model: {e}")
        raise ValueError(
            f"Failed to initialize emotion model: {e}. "
            "Please check your internet connection and ensure the model can be downloaded from HuggingFace."
        ) from e

def get_tokenizer():
    """Get the tokenizer, loading it if necessary."""
    if _tokenizer is None:
        _load_model()
    return _tokenizer

def get_model():
    """Get the model, loading it if necessary."""
    if _model is None:
        _load_model()
    return _model

def get_labels():
    """Get the labels, loading the model if necessary."""
    if _labels is None:
        _load_model()
    return _labels

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
    
    # Get tokenizer and model (lazy loading)
    tokenizer = get_tokenizer()
    model = get_model()
    labels = get_labels()
    
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
