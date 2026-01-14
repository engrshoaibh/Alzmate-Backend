# database.py
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from firebase_service import (
    save_emotion_analysis_standalone,
    save_emotion_analysis_to_journal_entry,
    get_emotion_entries as firestore_get_emotion_entries,
    get_journal_entry_by_id
)

def init_database():
    """Initialize database (Firebase initialization is handled in firebase_service)."""
    # Firebase initialization is handled in firebase_service.init_firebase()
    pass

def save_emotion_analysis(
    patient_id: str,
    journal_text: str,
    analysis_result: Dict,
    timestamp: Optional[datetime] = None,
    journal_entry_id: Optional[str] = None,
    audio_url: Optional[str] = None
) -> str:
    """
    Save emotion analysis result to Firestore.
    
    If journal_entry_id is provided, updates the journal entry document.
    Otherwise, creates a standalone emotion analysis document.
    
    Args:
        patient_id: Patient identifier
        journal_text: Original journal text
        analysis_result: Emotion analysis result
        timestamp: Entry timestamp (defaults to now)
        journal_entry_id: Optional journal entry document ID to update
        audio_url: Optional URL to uploaded audio file
    
    Returns:
        Entry document ID
    """
    if journal_entry_id:
        # Update existing journal entry with emotion analysis
        save_emotion_analysis_to_journal_entry(journal_entry_id, analysis_result)
        return journal_entry_id
    else:
        # Create standalone emotion analysis document
        return save_emotion_analysis_standalone(
            patient_id=patient_id,
            journal_text=journal_text,
            analysis_result=analysis_result,
            timestamp=timestamp,
            journal_entry_id=journal_entry_id,
            audio_url=audio_url
        )

def get_emotion_entries(
    patient_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: Optional[int] = None
) -> List[Dict]:
    """Get emotion entries for a patient from Firestore."""
    return firestore_get_emotion_entries(patient_id, start_date, end_date, limit)

def get_emotion_trends(
    patient_id: str,
    days: int = 7
) -> Dict:
    """Get emotion trends for a patient over specified days."""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    entries = get_emotion_entries(patient_id, start_date, end_date)
    
    if not entries:
        return {
            "patient_id": patient_id,
            "period_days": days,
            "total_entries": 0,
            "emotion_counts": {},
            "average_intensities": {},
            "mood_risk_count": 0,
            "trends": []
        }
    
    # Count emotions
    emotion_counts = {}
    emotion_intensities = {}
    mood_risk_count = 0
    
    for entry in entries:
        # Handle both camelCase (Firestore) and snake_case formats
        primary = entry.get("primaryEmotion") or entry.get("primary_emotion")
        primary_intensity = entry.get("primaryIntensity") or entry.get("primary_intensity", 0)
        secondary = entry.get("secondaryEmotion") or entry.get("secondary_emotion")
        secondary_intensity = entry.get("secondaryIntensity") or entry.get("secondary_intensity", 0)
        
        # Count primary emotions
        if primary:
            emotion_counts[primary] = emotion_counts.get(primary, 0) + 1
            if primary not in emotion_intensities:
                emotion_intensities[primary] = []
            emotion_intensities[primary].append(primary_intensity)
        
        # Count secondary emotions
        if secondary:
            emotion_counts[secondary] = emotion_counts.get(secondary, 0) + 1
            if secondary not in emotion_intensities:
                emotion_intensities[secondary] = []
            emotion_intensities[secondary].append(secondary_intensity)
        
        if entry.get("moodRisk") or entry.get("mood_risk"):
            mood_risk_count += 1
    
    # Calculate averages
    average_intensities = {
        emotion: sum(intensities) / len(intensities)
        for emotion, intensities in emotion_intensities.items()
    }
    
    # Generate trend insights
    trends = []
    total_entries = len(entries)
    
    for emotion, count in emotion_counts.items():
        percentage = (count / total_entries) * 100
        avg_intensity = average_intensities.get(emotion, 0)
        
        trend_text = f"{emotion.capitalize()} appears {count}/{total_entries} entries "
        trend_text += f"(avg intensity {avg_intensity:.1f}/100)"
        
        trends.append({
            "emotion": emotion,
            "count": count,
            "percentage": round(percentage, 1),
            "average_intensity": round(avg_intensity, 1),
            "description": trend_text
        })
    
    # Sort by count descending
    trends.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "patient_id": patient_id,
        "period_days": days,
        "total_entries": total_entries,
        "emotion_counts": emotion_counts,
        "average_intensities": average_intensities,
        "mood_risk_count": mood_risk_count,
        "mood_risk_percentage": round((mood_risk_count / total_entries) * 100, 1) if total_entries > 0 else 0,
        "trends": trends,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }

def get_daily_emotion_summary(
    patient_id: str,
    date: Optional[datetime] = None
) -> Dict:
    """Get emotion summary for a specific day."""
    if date is None:
        date = datetime.now()
    
    start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)
    
    entries = get_emotion_entries(patient_id, start_date, end_date)
    
    if not entries:
        return {
            "patient_id": patient_id,
            "date": date.date().isoformat(),
            "total_entries": 0,
            "emotions": [],
            "mood_risk": False
        }
    
    emotion_summary = {}
    has_mood_risk = False
    
    for entry in entries:
        # Handle both camelCase (Firestore) and snake_case formats
        primary = entry.get("primaryEmotion") or entry.get("primary_emotion")
        primary_intensity = entry.get("primaryIntensity") or entry.get("primary_intensity", 0)
        
        if primary:
            if primary not in emotion_summary:
                emotion_summary[primary] = {
                    "emotion": primary,
                    "count": 0,
                    "max_intensity": 0,
                    "avg_intensity": 0,
                    "intensities": []
                }
            
            emotion_summary[primary]["count"] += 1
            emotion_summary[primary]["intensities"].append(primary_intensity)
            emotion_summary[primary]["max_intensity"] = max(
                emotion_summary[primary]["max_intensity"],
                primary_intensity
            )
        
        if entry.get("moodRisk") or entry.get("mood_risk"):
            has_mood_risk = True
    
    # Calculate averages
    for emotion_data in emotion_summary.values():
        intensities = emotion_data["intensities"]
        emotion_data["avg_intensity"] = sum(intensities) / len(intensities) if intensities else 0
        del emotion_data["intensities"]  # Remove raw intensities from output
    
    emotions = sorted(
        emotion_summary.values(),
        key=lambda x: x["count"],
        reverse=True
    )
    
    return {
        "patient_id": patient_id,
        "date": date.date().isoformat(),
        "total_entries": len(entries),
        "emotions": emotions,
        "mood_risk": has_mood_risk
    }

# Initialize database on import
# Note: Firebase initialization happens lazily when first accessed
# init_database()  # Commented out - Firebase initializes on first use

