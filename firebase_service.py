# firebase_service.py
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Optional
from datetime import datetime
import os
import base64
import json
import binascii
from config import (
    FIREBASE_PROJECT_ID,
    FIREBASE_CREDENTIALS_PATH,
    FIREBASE_SERVICE_ACCOUNT_JSON,
    FIREBASE_SERVICE_ACCOUNT_JSON_B64,
    FIRESTORE_JOURNAL_ENTRIES_COLLECTION,
    FIRESTORE_EMOTION_ANALYSIS_COLLECTION
)

# Initialize Firebase Admin SDK
_db = None
_firestore_client = None

def _validate_service_account_json(service_account_info: dict) -> None:
    """
    Validate that the service account JSON has required fields.
    
    Args:
        service_account_info: Dictionary containing service account information
        
    Raises:
        ValueError: If required fields are missing
    """
    required_fields = ["type", "project_id", "private_key_id", "private_key", "client_email"]
    missing_fields = [field for field in required_fields if field not in service_account_info]
    
    if missing_fields:
        raise ValueError(
            f"Service account JSON is missing required fields: {', '.join(missing_fields)}. "
            "Please ensure you're using a valid Firebase service account JSON file."
        )
    
    if service_account_info.get("type") != "service_account":
        raise ValueError(
            f"Invalid service account type: {service_account_info.get('type')}. "
            "Expected 'service_account'."
        )

def _load_credentials_from_b64(b64_string: str):
    """
    Load Firebase credentials from base64-encoded JSON string.
    
    Args:
        b64_string: Base64-encoded service account JSON string
        
    Returns:
        Firebase credentials object
        
    Raises:
        ValueError: If decoding or parsing fails
    """
    try:
        # Handle padding issues - base64 strings may have missing padding
        padding = len(b64_string) % 4
        if padding:
            b64_string += '=' * (4 - padding)
        
        decoded_bytes = base64.b64decode(b64_string)
        decoded_str = decoded_bytes.decode("utf-8")
        service_account_info = json.loads(decoded_str)
        
        _validate_service_account_json(service_account_info)
        return credentials.Certificate(service_account_info)
    except (binascii.Error, ValueError) as e:
        raise ValueError(f"Invalid base64 encoding in FIREBASE_SERVICE_ACCOUNT_JSON_B64: {e}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in decoded FIREBASE_SERVICE_ACCOUNT_JSON_B64: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load credentials from FIREBASE_SERVICE_ACCOUNT_JSON_B64: {e}")

def _load_credentials_from_json(json_string: str):
    """
    Load Firebase credentials from JSON string.
    
    Args:
        json_string: Service account JSON string
        
    Returns:
        Firebase credentials object
        
    Raises:
        ValueError: If parsing fails
    """
    try:
        # Some platforms may wrap env var in quotes; handle both cases safely.
        raw = json_string.strip()
        if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
            raw = raw[1:-1]
        
        service_account_info = json.loads(raw)
        _validate_service_account_json(service_account_info)
        return credentials.Certificate(service_account_info)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {e}. "
            "Please ensure the JSON string is properly formatted."
        )
    except Exception as e:
        raise ValueError(f"Failed to load credentials from FIREBASE_SERVICE_ACCOUNT_JSON: {e}")

def _load_credentials_from_path(file_path: str):
    """
    Load Firebase credentials from file path.
    
    Args:
        file_path: Path to service account JSON file
        
    Returns:
        Firebase credentials object
        
    Raises:
        ValueError: If file doesn't exist or loading fails
    """
    if not os.path.exists(file_path):
        raise ValueError(
            f"Credentials file not found at FIREBASE_CREDENTIALS_PATH: {file_path}. "
            "Please ensure the file exists and the path is correct."
        )
    
    if not os.path.isfile(file_path):
        raise ValueError(
            f"FIREBASE_CREDENTIALS_PATH is not a file: {file_path}"
        )
    
    try:
        return credentials.Certificate(file_path)
    except Exception as e:
        raise ValueError(
            f"Failed to load credentials from FIREBASE_CREDENTIALS_PATH '{file_path}': {e}. "
            "Please ensure the file is a valid Firebase service account JSON file."
        )

def init_firebase():
    """
    Initialize Firebase Admin SDK.
    
    Supports three methods of credential configuration (in priority order):
    1. FIREBASE_SERVICE_ACCOUNT_JSON_B64 - Base64-encoded service account JSON (recommended)
    2. FIREBASE_SERVICE_ACCOUNT_JSON - Direct JSON string of service account
    3. FIREBASE_CREDENTIALS_PATH - Path to a service account JSON file
    
    Returns:
        Firestore client instance
        
    Raises:
        ValueError: If credentials are not configured or invalid
    """
    global _firestore_client
    
    if _firestore_client is not None:
        return _firestore_client
    
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        _firestore_client = firestore.client()
        return _firestore_client
    except ValueError:
        # Firebase not initialized, initialize it
        pass
    
    # Initialize credentials - try methods in priority order
    cred = None
    method_used = None
    
    # Method 1: Base64-encoded JSON (recommended for cloud platforms)
    if FIREBASE_SERVICE_ACCOUNT_JSON_B64:
        print("[firebase] Using FIREBASE_SERVICE_ACCOUNT_JSON_B64 (recommended)")
        try:
            cred = _load_credentials_from_b64(FIREBASE_SERVICE_ACCOUNT_JSON_B64)
            method_used = "FIREBASE_SERVICE_ACCOUNT_JSON_B64"
        except ValueError as e:
            raise ValueError(f"Failed to load credentials from FIREBASE_SERVICE_ACCOUNT_JSON_B64: {e}")
    
    # Method 2: Direct JSON string
    elif FIREBASE_SERVICE_ACCOUNT_JSON:
        print("[firebase] Using FIREBASE_SERVICE_ACCOUNT_JSON")
        try:
            cred = _load_credentials_from_json(FIREBASE_SERVICE_ACCOUNT_JSON)
            method_used = "FIREBASE_SERVICE_ACCOUNT_JSON"
        except ValueError as e:
            raise ValueError(f"Failed to load credentials from FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
    
    # Method 3: File path
    elif FIREBASE_CREDENTIALS_PATH:
        print(f"[firebase] Using FIREBASE_CREDENTIALS_PATH: {FIREBASE_CREDENTIALS_PATH}")
        try:
            cred = _load_credentials_from_path(FIREBASE_CREDENTIALS_PATH)
            method_used = "FIREBASE_CREDENTIALS_PATH"
        except ValueError as e:
            raise ValueError(f"Failed to load credentials from FIREBASE_CREDENTIALS_PATH: {e}")
    
    # If no explicit credentials found, try Application Default Credentials (ADC)
    # Only on Google infrastructure to avoid JWT signature errors
    if cred is None:
        is_google_infrastructure = (
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or 
            os.getenv("GCE_METADATA_HOST") or 
            os.getenv("K_SERVICE") or
            os.getenv("GAE_SERVICE") or
            os.getenv("GAE_INSTANCE")
        )
        
        if is_google_infrastructure:
            print("[firebase] Using Application Default Credentials (ADC) - Google infrastructure detected")
            try:
                cred = credentials.ApplicationDefault()
                method_used = "Application Default Credentials (ADC)"
            except Exception as e:
                raise ValueError(
                    f"Failed to use Application Default Credentials: {e}. "
                    "Please set one of: FIREBASE_SERVICE_ACCOUNT_JSON_B64 (recommended), "
                    "FIREBASE_SERVICE_ACCOUNT_JSON, or FIREBASE_CREDENTIALS_PATH."
                )
        else:
            raise ValueError(
                "Firebase credentials not configured. "
                "Please set one of the following environment variables:\n"
                "  1. FIREBASE_SERVICE_ACCOUNT_JSON_B64 (recommended) - Base64-encoded service account JSON\n"
                "  2. FIREBASE_SERVICE_ACCOUNT_JSON - Direct JSON string of service account\n"
                "  3. FIREBASE_CREDENTIALS_PATH - Path to service account JSON file\n\n"
                "Application Default Credentials are not available on this platform."
            )
    
    # Initialize Firebase Admin SDK
    try:
        firebase_admin.initialize_app(cred, {
            'projectId': FIREBASE_PROJECT_ID
        })
        print(f"[firebase] Successfully initialized using {method_used}")
    except Exception as e:
        raise ValueError(
            f"Failed to initialize Firebase Admin SDK: {e}. "
            "Please verify your credentials are valid and have the necessary permissions."
        )
    
    _firestore_client = firestore.client()
    return _firestore_client

def get_firestore_client():
    """Get Firestore client instance."""
    global _firestore_client
    if _firestore_client is None:
        try:
            init_firebase()
        except ValueError as e:
            # Re-raise credential configuration errors
            raise
        except Exception as e:
            error_msg = str(e)
            # Check for JWT/authentication errors
            if "JWT" in error_msg or "invalid_grant" in error_msg or "signature" in error_msg.lower() or "metadata" in error_msg.lower():
                raise ValueError(
                    f"Firebase authentication failed: {error_msg}. "
                    "This usually means credentials are missing or invalid. "
                    "Please run: python check_firebase_config.py to verify your credentials."
                ) from e
            raise
    
    # Verify the client is still valid (in case credentials expired)
    try:
        # Try a simple operation to verify credentials are still valid
        _firestore_client  # Just access it to ensure it exists
    except Exception as e:
        # If client is invalid, reinitialize
        _firestore_client = None
        try:
            init_firebase()
        except Exception as init_error:
            raise ValueError(
                f"Firebase client became invalid: {e}. "
                f"Re-initialization failed: {init_error}. "
                "Please check your Firebase credentials."
            ) from init_error
    
    return _firestore_client

def save_emotion_analysis_to_journal_entry(
    journal_entry_id: str,
    analysis_result: Dict
) -> None:
    """
    Update a journal entry with emotion analysis results.
    
    Args:
        journal_entry_id: The Firestore document ID of the journal entry
        analysis_result: Emotion analysis result dictionary
    """
    db = get_firestore_client()
    
    primary = analysis_result.get("primary_emotion", {})
    secondary = analysis_result.get("secondary_emotion")
    
    # Prepare emotion analysis data
    emotion_data = {
        "emotionAnalysis": {
            "primaryEmotion": primary.get("emotion"),
            "primaryIntensity": primary.get("intensity", 0),
            "primaryConfidence": primary.get("confidence", 0.0),
            "secondaryEmotion": secondary.get("emotion") if secondary else None,
            "secondaryIntensity": secondary.get("intensity") if secondary else None,
            "secondaryConfidence": secondary.get("confidence") if secondary else None,
            "interpretationTag": analysis_result.get("interpretation_tag"),
            "moodRisk": analysis_result.get("mood_risk", False),
            "processedText": analysis_result.get("processed_text"),
            "analyzedAt": firestore.SERVER_TIMESTAMP if hasattr(firestore, 'SERVER_TIMESTAMP') else datetime.now(),
        },
        "updatedAt": firestore.SERVER_TIMESTAMP,
    }
    
    # Update the journal entry document
    db.collection(FIRESTORE_JOURNAL_ENTRIES_COLLECTION).document(journal_entry_id).update(emotion_data)

def save_emotion_analysis_standalone(
    patient_id: str,
    journal_text: str,
    analysis_result: Dict,
    timestamp: Optional[datetime] = None,
    journal_entry_id: Optional[str] = None,
    audio_url: Optional[str] = None
) -> str:
    """
    Save emotion analysis as a standalone document in Firestore.
    
    Args:
        patient_id: Patient identifier
        journal_text: Original journal text
        analysis_result: Emotion analysis result
        timestamp: Entry timestamp (defaults to now)
        journal_entry_id: Optional reference to journal entry document
        audio_url: URL to uploaded audio file (optional)
    
    Returns:
        Entry document ID
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    db = get_firestore_client()
    
    primary = analysis_result.get("primary_emotion", {})
    secondary = analysis_result.get("secondary_emotion")
    
    entry_data = {
        "patientId": patient_id,
        "timestamp": timestamp,
        "journalText": journal_text,
        "processedText": analysis_result.get("processed_text"),
        "primaryEmotion": primary.get("emotion"),
        "primaryIntensity": primary.get("intensity", 0),
        "primaryConfidence": primary.get("confidence", 0.0),
        "secondaryEmotion": secondary.get("emotion") if secondary else None,
        "secondaryIntensity": secondary.get("intensity") if secondary else None,
        "secondaryConfidence": secondary.get("confidence") if secondary else None,
        "interpretationTag": analysis_result.get("interpretation_tag"),
        "moodRisk": analysis_result.get("mood_risk", False),
        "createdAt": firestore.SERVER_TIMESTAMP,
    }
    
    # Add optional fields
    if journal_entry_id:
        entry_data["journalEntryId"] = journal_entry_id
    if audio_url:
        entry_data["audioUrl"] = audio_url
    
    # Add full analysis result for reference
    entry_data["analysisResult"] = analysis_result
    
    # Create document reference
    doc_ref = db.collection(FIRESTORE_EMOTION_ANALYSIS_COLLECTION).document()
    doc_ref.set(entry_data)
    
    return doc_ref.id

def get_emotion_entries(
    patient_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """Get emotion entries for a patient from Firestore."""
    db = get_firestore_client()
    
    # Build query
    query = db.collection(FIRESTORE_EMOTION_ANALYSIS_COLLECTION).where("patientId", "==", patient_id)
    
    if start_date:
        query = query.where("timestamp", ">=", start_date)
    
    if end_date:
        query = query.where("timestamp", "<=", end_date)
    
    # Order by timestamp descending
    query = query.order_by("timestamp", direction=firestore.Query.DESCENDING)
    
    if limit:
        query = query.limit(limit)
    
    # Execute query
    docs = query.stream()
    
    entries = []
    for doc in docs:
        entry = doc.to_dict()
        entry["id"] = doc.id
        
        # Convert Firestore Timestamp to ISO string if needed
        if "timestamp" in entry and hasattr(entry["timestamp"], "isoformat"):
            entry["timestamp"] = entry["timestamp"].isoformat()
        elif isinstance(entry.get("timestamp"), datetime):
            entry["timestamp"] = entry["timestamp"].isoformat()
        
        # Convert created_at if present
        if "createdAt" in entry and hasattr(entry["createdAt"], "isoformat"):
            entry["createdAt"] = entry["createdAt"].isoformat()
        elif isinstance(entry.get("createdAt"), datetime):
            entry["createdAt"] = entry["createdAt"].isoformat()
        
        entries.append(entry)
    
    return entries

def get_journal_entry_by_id(journal_entry_id: str) -> Optional[Dict]:
    """Get a journal entry by its ID."""
    db = get_firestore_client()
    doc = db.collection(FIRESTORE_JOURNAL_ENTRIES_COLLECTION).document(journal_entry_id).get()
    
    if not doc.exists:
        return None
    
    data = doc.to_dict()
    data["id"] = doc.id
    
    # Convert timestamps
    for field in ["timestamp", "createdAt", "updatedAt"]:
        if field in data and hasattr(data[field], "isoformat"):
            data[field] = data[field].isoformat()
        elif isinstance(data.get(field), datetime):
            data[field] = data[field].isoformat()
    
    return data

