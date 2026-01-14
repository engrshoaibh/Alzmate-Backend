# advanced_emotion_analysis.py
"""
Advanced Emotion Analysis Features
FR-SA07: Significant emotion shift detection
FR-SA09: Caregiver notifications for persistent negative emotions
FR-SA10: Mood risk flagging for volatility
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database import get_emotion_entries
from firebase_service import get_firestore_client
from firebase_admin import firestore

# Configuration
NEGATIVE_EMOTIONS = {'sad', 'angry', 'anxious', 'fearful', 'confused', 'frustrated', 'lonely', 'depressed/low mood'}
PERSISTENT_DAYS_THRESHOLD = 3  # N days for FR-SA09
HIGH_INTENSITY_THRESHOLD = 70  # Intensity threshold for high-risk emotions
VOLATILITY_THRESHOLD = 0.4  # Coefficient of variation threshold for volatility

def detect_emotion_shift(
    patient_id: str,
    emotion: str,
    days: int = 7,
    intensity_increase: float = 20.0
) -> Dict:
    """
    Detect significant emotion shift (FR-SA07).
    
    Detects if an emotion's intensity has increased significantly over time.
    
    Args:
        patient_id: Patient identifier
        emotion: Emotion to check
        days: Number of days to analyze
        intensity_increase: Minimum increase in intensity to consider significant
    
    Returns:
        Dictionary with shift detection results
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    entries = get_emotion_entries(patient_id, start_date, end_date)
    
    if len(entries) < 2:
        return {
            'shiftDetected': False,
            'reason': 'Insufficient data',
            'emotion': emotion,
            'entries': len(entries)
        }
    
    # Split entries into two halves (early vs late)
    mid_point = len(entries) // 2
    early_entries = entries[mid_point:]
    late_entries = entries[:mid_point]
    
    # Calculate average intensity for this emotion in each period
    early_intensities = []
    late_intensities = []
    
    for entry in early_entries:
        primary = entry.get("primaryEmotion") or entry.get("primary_emotion")
        secondary = entry.get("secondaryEmotion") or entry.get("secondary_emotion")
        
        if primary == emotion:
            intensity = entry.get("primaryIntensity") or entry.get("primary_intensity", 0)
            early_intensities.append(intensity)
        elif secondary == emotion:
            intensity = entry.get("secondaryIntensity") or entry.get("secondary_intensity", 0)
            early_intensities.append(intensity)
    
    for entry in late_entries:
        primary = entry.get("primaryEmotion") or entry.get("primary_emotion")
        secondary = entry.get("secondaryEmotion") or entry.get("secondary_emotion")
        
        if primary == emotion:
            intensity = entry.get("primaryIntensity") or entry.get("primary_intensity", 0)
            late_intensities.append(intensity)
        elif secondary == emotion:
            intensity = entry.get("secondaryIntensity") or entry.get("secondary_intensity", 0)
            late_intensities.append(intensity)
    
    if not early_intensities or not late_intensities:
        return {
            'shiftDetected': False,
            'reason': 'Emotion not found in both periods',
            'emotion': emotion
        }
    
    early_avg = sum(early_intensities) / len(early_intensities)
    late_avg = sum(late_intensities) / len(late_intensities)
    
    increase = late_avg - early_avg
    shift_detected = increase >= intensity_increase
    
    return {
        'shiftDetected': shift_detected,
        'emotion': emotion,
        'earlyAverage': round(early_avg, 2),
        'lateAverage': round(late_avg, 2),
        'increase': round(increase, 2),
        'threshold': intensity_increase,
        'periodDays': days
    }

def check_persistent_negative_emotions(
    patient_id: str,
    days: int = PERSISTENT_DAYS_THRESHOLD
) -> Dict:
    """
    Check for persistent high-intensity negative emotions (FR-SA09).
    
    Returns:
        Dictionary with persistence status and details
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    entries = get_emotion_entries(patient_id, start_date, end_date)
    
    if len(entries) < days:
        return {
            'persistentNegativeDetected': False,
            'reason': 'Insufficient entries',
            'entries': len(entries),
            'required': days
        }
    
    # Count days with high-intensity negative emotions
    negative_days = set()
    
    for entry in entries:
        primary = entry.get("primaryEmotion") or entry.get("primary_emotion")
        primary_intensity = entry.get("primaryIntensity") or entry.get("primary_intensity", 0)
        secondary = entry.get("secondaryEmotion") or entry.get("secondary_emotion")
        secondary_intensity = entry.get("secondaryIntensity") or entry.get("secondary_intensity", 0)
        
        # Get entry date
        timestamp = entry.get("timestamp")
        if isinstance(timestamp, str):
            try:
                entry_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                continue
        else:
            continue
        
        date_key = entry_date.date().isoformat()
        
        # Check primary emotion
        if primary in NEGATIVE_EMOTIONS and primary_intensity >= HIGH_INTENSITY_THRESHOLD:
            negative_days.add(date_key)
        
        # Check secondary emotion
        if secondary and secondary in NEGATIVE_EMOTIONS and secondary_intensity >= HIGH_INTENSITY_THRESHOLD:
            negative_days.add(date_key)
    
    persistent = len(negative_days) >= days
    
    return {
        'persistentNegativeDetected': persistent,
        'daysWithHighNegativeEmotions': len(negative_days),
        'requiredDays': days,
        'emotions': list(negative_days),
        'threshold': HIGH_INTENSITY_THRESHOLD
    }

def detect_emotion_volatility(
    patient_id: str,
    days: int = 7
) -> Dict:
    """
    Detect emotion volatility (rapid day-to-day changes) (FR-SA10).
    
    Returns:
        Dictionary with volatility status
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    entries = get_emotion_entries(patient_id, start_date, end_date)
    
    if len(entries) < 3:
        return {
            'volatilityDetected': False,
            'reason': 'Insufficient data',
            'entries': len(entries)
        }
    
    # Group entries by date and calculate daily emotion scores
    daily_scores = {}
    
    for entry in entries:
        timestamp = entry.get("timestamp")
        if isinstance(timestamp, str):
            try:
                entry_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                continue
        else:
            continue
        
        date_key = entry_date.date().isoformat()
        
        if date_key not in daily_scores:
            daily_scores[date_key] = []
        
        # Calculate a composite emotion score (negative emotions = negative score)
        primary = entry.get("primaryEmotion") or entry.get("primary_emotion")
        primary_intensity = entry.get("primaryIntensity") or entry.get("primary_intensity", 0)
        
        if primary in NEGATIVE_EMOTIONS:
            score = -primary_intensity
        else:
            score = primary_intensity
        
        daily_scores[date_key].append(score)
    
    # Calculate average daily scores
    daily_averages = {
        date: sum(scores) / len(scores)
        for date, scores in daily_scores.items()
    }
    
    if len(daily_averages) < 3:
        return {
            'volatilityDetected': False,
            'reason': 'Insufficient daily data',
            'days': len(daily_averages)
        }
    
    # Calculate coefficient of variation (standard deviation / mean)
    values = list(daily_averages.values())
    mean = sum(values) / len(values)
    
    if mean == 0:
        return {
            'volatilityDetected': False,
            'reason': 'Zero mean score',
            'mean': mean
        }
    
    variance = sum((x - mean) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    coefficient_of_variation = abs(std_dev / mean) if mean != 0 else 0
    
    volatility_detected = coefficient_of_variation >= VOLATILITY_THRESHOLD
    
    return {
        'volatilityDetected': volatility_detected,
        'coefficientOfVariation': round(coefficient_of_variation, 3),
        'threshold': VOLATILITY_THRESHOLD,
        'meanScore': round(mean, 2),
        'stdDeviation': round(std_dev, 2),
        'daysAnalyzed': len(daily_averages),
        'periodDays': days
    }

def generate_emotion_trend_summary(patient_id: str, days: int = 7) -> Dict:
    """
    Generate emotion trend summary with improving/stable/worsening classification (FR-SA08).
    
    Returns:
        Dictionary with trend classification and details
    """
    from database import get_emotion_trends
    
    trends = get_emotion_trends(patient_id, days)
    
    if trends['total_entries'] == 0:
        return {
            'trend': 'no_data',
            'description': 'No emotion data available',
            'patientId': patient_id
        }
    
    # Analyze trend direction
    # Get emotion intensities over time
    entries = get_emotion_entries(patient_id, None, None, limit=days * 2)
    
    if len(entries) < 2:
        return {
            'trend': 'stable',
            'description': 'Insufficient data for trend analysis',
            'patientId': patient_id
        }
    
    # Calculate average negative emotion intensity
    negative_intensities = []
    for entry in entries:
        primary = entry.get("primaryEmotion") or entry.get("primary_emotion")
        primary_intensity = entry.get("primaryIntensity") or entry.get("primary_intensity", 0)
        
        if primary in NEGATIVE_EMOTIONS:
            negative_intensities.append(primary_intensity)
    
    if not negative_intensities:
        return {
            'trend': 'improving',
            'description': 'No negative emotions detected',
            'patientId': patient_id,
            'averageNegativeIntensity': 0
        }
    
    # Split into early and late periods
    mid = len(negative_intensities) // 2
    early_avg = sum(negative_intensities[mid:]) / len(negative_intensities[mid:]) if mid > 0 else 0
    late_avg = sum(negative_intensities[:mid]) / len(negative_intensities[:mid]) if mid > 0 else 0
    
    if early_avg == 0:
        trend = 'improving'
        description = 'Negative emotions decreasing'
    elif late_avg > early_avg + 10:
        trend = 'worsening'
        description = f'Negative emotions increasing (from {early_avg:.1f} to {late_avg:.1f})'
    elif late_avg < early_avg - 10:
        trend = 'improving'
        description = f'Negative emotions decreasing (from {early_avg:.1f} to {late_avg:.1f})'
    else:
        trend = 'stable'
        description = 'Emotional state remains relatively stable'
    
    return {
        'trend': trend,
        'description': description,
        'patientId': patient_id,
        'averageNegativeIntensity': round(sum(negative_intensities) / len(negative_intensities), 2),
        'earlyAverage': round(early_avg, 2),
        'lateAverage': round(late_avg, 2),
        'totalEntries': trends['total_entries'],
        'moodRiskCount': trends.get('mood_risk_count', 0)
    }

