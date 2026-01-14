# progress_tracking.py
"""
Progress Tracking Module - FR-PT01 to FR-PT16
Calculates weekly cognitive performance scores based on task completion.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from firebase_service import get_firestore_client
from firebase_admin import firestore
# SERVER_TIMESTAMP is handled by firestore module

# Task type weights (as per specification)
TASK_WEIGHTS = {
    'medication': 3,
    'appointment': 3,
    'meal': 2,
    'brain_training': 2,  # From game_scores collection
    'journal': 1,  # Optional
}

# Patient state thresholds
STATE_THRESHOLDS = {
    'stable': (80, 100),
    'mild_decline': (60, 79),
    'moderate_decline': (40, 59),
    'high_risk': (0, 39),
}

# Decline detection parameters
DECLINE_THRESHOLD_POINTS = 15  # X points drop
DECLINE_CONSECUTIVE_WEEKS = 2  # Y consecutive weeks

# Collections
REMINDERS_COLLECTION = 'reminders'
GAME_SCORES_COLLECTION = 'game_scores'
JOURNAL_ENTRIES_COLLECTION = 'journal_entries'
PROGRESS_SCORES_COLLECTION = 'progress_scores'
PROGRESS_BASELINES_COLLECTION = 'progress_baselines'

def get_reminders_for_period(
    patient_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict]:
    """Get all reminders for a patient in a date range."""
    db = get_firestore_client()
    
    query = db.collection(REMINDERS_COLLECTION)\
        .where('userId', '==', patient_id)\
        .where('time', '>=', start_date)\
        .where('time', '<=', end_date)\
        .stream()
    
    reminders = []
    for doc in query:
        data = doc.to_dict()
        data['id'] = doc.id
        reminders.append(data)
    
    return reminders

def get_brain_training_sessions(
    patient_id: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict]:
    """Get brain training sessions (game scores) for a patient in a date range."""
    db = get_firestore_client()
    
    query = db.collection(GAME_SCORES_COLLECTION)\
        .where('userId', '==', patient_id)\
        .where('playedAt', '>=', start_date)\
        .where('playedAt', '<=', end_date)\
        .stream()
    
    sessions = []
    for doc in query:
        data = doc.to_dict()
        data['id'] = doc.id
        sessions.append(data)
    
    return sessions

def calculate_task_points(reminders: List[Dict], brain_sessions: List[Dict]) -> Tuple[float, float]:
    """
    Calculate earned points and total possible points for a period.
    
    Returns:
        (earned_points, total_possible_points)
    """
    earned_points = 0.0
    total_possible_points = 0.0
    
    # Process reminders
    for reminder in reminders:
        task_type = reminder.get('type', '').lower()
        
        # Map reminder types to our task types
        if task_type in ['medication', 'appointment', 'meal']:
            weight = TASK_WEIGHTS.get(task_type, 1)
            total_possible_points += weight
            
            if reminder.get('isCompleted', False):
                earned_points += weight
            elif reminder.get('isMissed', False):
                # Missed = 0 points
                pass
            # Pending tasks don't count yet
    
    # Process brain training sessions
    # Count each session as a task
    brain_weight = TASK_WEIGHTS.get('brain_training', 2)
    
    # Total possible: assume 1 session per day is expected
    days_in_period = (datetime.now() - (datetime.now() - timedelta(days=7))).days + 1
    total_possible_points += days_in_period * brain_weight
    
    # Earned: count completed sessions
    earned_points += len(brain_sessions) * brain_weight
    
    return earned_points, total_possible_points

def calculate_weekly_score(patient_id: str, week_start: Optional[datetime] = None) -> Dict:
    """
    Calculate weekly cognitive performance score (FR-PT07).
    
    Args:
        patient_id: Patient identifier
        week_start: Start of the week (defaults to 7 days ago)
    
    Returns:
        Dictionary with score, breakdown, and details
    """
    if week_start is None:
        week_start = datetime.now() - timedelta(days=7)
    
    week_end = datetime.now()
    
    # Get reminders and brain training sessions
    reminders = get_reminders_for_period(patient_id, week_start, week_end)
    brain_sessions = get_brain_training_sessions(patient_id, week_start, week_end)
    
    # Calculate points
    earned_points, total_possible_points = calculate_task_points(reminders, brain_sessions)
    
    # Calculate score
    if total_possible_points == 0:
        score = 0.0
    else:
        score = (earned_points / total_possible_points) * 100
    
    # Breakdown by task type
    breakdown = {
        'medication': {'completed': 0, 'missed': 0, 'total': 0, 'points_earned': 0, 'points_possible': 0},
        'appointment': {'completed': 0, 'missed': 0, 'total': 0, 'points_earned': 0, 'points_possible': 0},
        'meal': {'completed': 0, 'missed': 0, 'total': 0, 'points_earned': 0, 'points_possible': 0},
        'brain_training': {'completed': len(brain_sessions), 'total': 7, 'points_earned': len(brain_sessions) * 2, 'points_possible': 7 * 2},
    }
    
    # Count reminders by type
    for reminder in reminders:
        task_type = reminder.get('type', '').lower()
        if task_type in breakdown:
            breakdown[task_type]['total'] += 1
            if reminder.get('isCompleted', False):
                breakdown[task_type]['completed'] += 1
                breakdown[task_type]['points_earned'] += TASK_WEIGHTS.get(task_type, 1)
            elif reminder.get('isMissed', False):
                breakdown[task_type]['missed'] += 1
            breakdown[task_type]['points_possible'] += TASK_WEIGHTS.get(task_type, 1)
    
    return {
        'patientId': patient_id,
        'weekStart': week_start.isoformat(),
        'weekEnd': week_end.isoformat(),
        'score': round(score, 2),
        'earnedPoints': round(earned_points, 2),
        'totalPossiblePoints': round(total_possible_points, 2),
        'breakdown': breakdown,
        'calculatedAt': datetime.now().isoformat()
    }

def get_patient_state(score: float) -> str:
    """
    Assign patient functional state label based on score (FR-PT09).
    
    Returns:
        State label: 'stable', 'mild_decline', 'moderate_decline', or 'high_risk'
    """
    if score >= 80:
        return 'stable'
    elif score >= 60:
        return 'mild_decline'
    elif score >= 40:
        return 'moderate_decline'
    else:
        return 'high_risk'

def save_weekly_score(patient_id: str, score_data: Dict) -> str:
    """Save weekly score to Firestore (FR-PT08)."""
    db = get_firestore_client()
    
    # Add patient state
    score_data['patientState'] = get_patient_state(score_data['score'])
    
    # Create document
    doc_ref = db.collection(PROGRESS_SCORES_COLLECTION).document()
    doc_ref.set({
        **score_data,
        'createdAt': firestore.SERVER_TIMESTAMP,
    })
    
    return doc_ref.id

def get_baseline_score(patient_id: str, baseline_weeks: int = 4) -> Optional[float]:
    """
    Calculate baseline score from first N weeks (FR-PT10).
    
    Args:
        patient_id: Patient identifier
        baseline_weeks: Number of weeks to use for baseline (default: 4)
    
    Returns:
        Average baseline score or None if insufficient data
    """
    db = get_firestore_client()
    
    # Get oldest scores
    query = db.collection(PROGRESS_SCORES_COLLECTION)\
        .where('patientId', '==', patient_id)\
        .order_by('weekStart')\
        .limit(baseline_weeks)\
        .stream()
    
    scores = []
    for doc in query:
        data = doc.to_dict()
        if 'score' in data:
            scores.append(data['score'])
    
    if len(scores) < 2:  # Need at least 2 weeks
        return None
    
    return sum(scores) / len(scores)

def detect_decline(patient_id: str, current_score: float) -> Dict:
    """
    Detect decline by comparing with baseline (FR-PT11, FR-PT12).
    
    Returns:
        Dictionary with decline status and details
    """
    baseline = get_baseline_score(patient_id)
    
    if baseline is None:
        return {
            'declineDetected': False,
            'reason': 'Insufficient baseline data',
            'baseline': None,
            'currentScore': current_score,
            'difference': None
        }
    
    difference = baseline - current_score
    
    decline_detected = difference >= DECLINE_THRESHOLD_POINTS
    
    # Check consecutive weeks
    if decline_detected:
        db = get_firestore_client()
        recent_scores = db.collection(PROGRESS_SCORES_COLLECTION)\
            .where('patientId', '==', patient_id)\
            .order_by('weekStart', direction=firestore.Query.DESCENDING)\
            .limit(DECLINE_CONSECUTIVE_WEEKS)\
            .stream()
        
        recent_score_list = []
        for doc in recent_scores:
            data = doc.to_dict()
            if 'score' in data:
                recent_score_list.append(data['score'])
        
        # Check if all recent scores are below threshold
        if len(recent_score_list) >= DECLINE_CONSECUTIVE_WEEKS:
            all_below_threshold = all(
                (baseline - score) >= DECLINE_THRESHOLD_POINTS
                for score in recent_score_list
            )
            decline_detected = all_below_threshold
    
    return {
        'declineDetected': decline_detected,
        'baseline': baseline,
        'currentScore': current_score,
        'difference': round(difference, 2),
        'threshold': DECLINE_THRESHOLD_POINTS,
        'consecutiveWeeks': DECLINE_CONSECUTIVE_WEEKS if decline_detected else 0
    }

def generate_weekly_report(patient_id: str) -> Dict:
    """
    Generate weekly progress report (FR-PT15).
    
    Includes:
    - Weekly score
    - Patient state
    - Trend analysis
    - Missed task breakdown
    - Decline detection
    """
    # Calculate current week score
    current_score_data = calculate_weekly_score(patient_id)
    current_score = current_score_data['score']
    
    # Get patient state
    patient_state = get_patient_state(current_score)
    
    # Detect decline
    decline_info = detect_decline(patient_id, current_score)
    
    # Get trend (compare with previous week)
    db = get_firestore_client()
    previous_week_start = datetime.now() - timedelta(days=14)
    previous_scores = db.collection(PROGRESS_SCORES_COLLECTION)\
        .where('patientId', '==', patient_id)\
        .where('weekStart', '>=', previous_week_start)\
        .order_by('weekStart', direction=firestore.Query.DESCENDING)\
        .limit(2)\
        .stream()
    
    previous_score = None
    for doc in previous_scores:
        data = doc.to_dict()
        if 'score' in data and data.get('weekStart') != current_score_data['weekStart']:
            previous_score = data['score']
            break
    
    # Determine trend
    if previous_score is None:
        trend = 'no_data'
        trend_description = 'Insufficient data for trend analysis'
    elif current_score > previous_score + 5:
        trend = 'improving'
        trend_description = f'Score improved by {current_score - previous_score:.1f} points'
    elif current_score < previous_score - 5:
        trend = 'declining'
        trend_description = f'Score decreased by {previous_score - current_score:.1f} points'
    else:
        trend = 'stable'
        trend_description = 'Score remains relatively stable'
    
    # Save current score
    score_id = save_weekly_score(patient_id, current_score_data)
    
    # Generate report
    report = {
        'patientId': patient_id,
        'reportDate': datetime.now().isoformat(),
        'weekStart': current_score_data['weekStart'],
        'weekEnd': current_score_data['weekEnd'],
        'weeklyScore': current_score,
        'patientState': patient_state,
        'stateDescription': {
            'stable': 'Routine intact - patient is functioning well',
            'mild_decline': 'Mild decline risk - needs attention',
            'moderate_decline': 'Moderate decline risk - frequent misses',
            'high_risk': 'High risk - requires high supervision'
        }.get(patient_state, 'Unknown state'),
        'trend': trend,
        'trendDescription': trend_description,
        'previousScore': previous_score,
        'breakdown': current_score_data['breakdown'],
        'declineDetection': decline_info,
        'scoreId': score_id
    }
    
    return report

