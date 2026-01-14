# firebase_service.py
import firebase_admin
from firebase_admin import credentials, firestore
from typing import List, Dict, Optional
from datetime import datetime
import json
from config import (
    FIREBASE_PROJECT_ID,
    FIREBASE_CREDENTIALS_PATH,
    FIREBASE_SERVICE_ACCOUNT_JSON,
    FIRESTORE_JOURNAL_ENTRIES_COLLECTION,
    FIRESTORE_EMOTION_ANALYSIS_COLLECTION
)

# Initialize Firebase Admin SDK
_db = None
_firestore_client = None

def init_firebase():
    """Initialize Firebase Admin SDK."""
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
    
    # Initialize credentials
    cred = None
    if FIREBASE_CREDENTIALS_PATH:
        cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
    elif FIREBASE_SERVICE_ACCOUNT_JSON:
        service_account_info = json.loads(FIREBASE_SERVICE_ACCOUNT_JSON)
        cred = credentials.Certificate(service_account_info)
    elif FIREBASE_PROJECT_ID:
        # Use default credentials (for Google Cloud environments)
        cred = credentials.ApplicationDefault()
    
    if cred is None:
        raise ValueError(
            "Firebase credentials not configured. "
            "Set FIREBASE_CREDENTIALS_PATH, FIREBASE_SERVICE_ACCOUNT_JSON, or FIREBASE_PROJECT_ID"
        )
    
    # Initialize Firebase Admin
    firebase_admin.initialize_app(cred, {
        'projectId': FIREBASE_PROJECT_ID
    })
    
    _firestore_client = firestore.client()
    return _firestore_client

def get_firestore_client():
    """Get Firestore client instance."""
    global _firestore_client
    if _firestore_client is None:
        init_firebase()
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

