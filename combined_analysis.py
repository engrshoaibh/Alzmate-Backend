# combined_analysis.py
"""
Combined Analysis Module
FR-COM01: Include emotion trends in progress report
FR-COM02: Raise risk level if both task-performance decline and high negative emotion persistence are detected
"""

from datetime import datetime
from typing import Dict, Optional
from progress_tracking import generate_weekly_report, get_patient_state
from advanced_emotion_analysis import (
    check_persistent_negative_emotions,
    generate_emotion_trend_summary,
    detect_emotion_volatility
)
from database import get_emotion_trends
from notification_service import notify_caregivers_combined_risk

def generate_combined_weekly_report(patient_id: str) -> Dict:
    """
    Generate combined weekly report with both progress tracking and emotion analysis (FR-COM01).
    
    Returns:
        Comprehensive report with both cognitive performance and emotional state
    """
    # Get progress report
    progress_report = generate_weekly_report(patient_id)
    
    # Get emotion trends
    emotion_trends = get_emotion_trends(patient_id, days=7)
    emotion_summary = generate_emotion_trend_summary(patient_id, days=7)
    
    # Check for persistent negative emotions
    persistent_negative = check_persistent_negative_emotions(patient_id)
    
    # Check for volatility
    volatility = detect_emotion_volatility(patient_id)
    
    # Assess combined risk
    risk_assessment = assess_combined_risk(progress_report, emotion_summary, persistent_negative)
    
    # Combine reports
    combined_report = {
        **progress_report,
        'emotionAnalysis': {
            'trendSummary': emotion_summary,
            'weeklyTrends': emotion_trends,
            'persistentNegativeEmotions': persistent_negative,
            'volatility': volatility
        },
        'combinedRiskAssessment': risk_assessment
    }
    
    # Send notifications if high risk
    if risk_assessment.get('combinedRiskLevel') in ['high', 'critical']:
        try:
            notify_caregivers_combined_risk(patient_id, risk_assessment)
        except Exception as e:
            # Log error but don't fail the report generation
            print(f"Error sending notifications: {e}")
    
    return combined_report

def assess_combined_risk(
    progress_report: Dict,
    emotion_summary: Dict,
    persistent_negative: Dict
) -> Dict:
    """
    Assess combined risk level (FR-COM02).
    
    Raises risk level if both:
    - Task performance decline detected
    - High negative emotion persistence detected
    """
    # Check for performance decline
    decline_detected = progress_report.get('declineDetection', {}).get('declineDetected', False)
    patient_state = progress_report.get('patientState', 'stable')
    
    # Check for persistent negative emotions
    persistent_negative_detected = persistent_negative.get('persistentNegativeDetected', False)
    
    # Check emotion trend
    emotion_trend = emotion_summary.get('trend', 'stable')
    
    # Determine combined risk level
    base_risk = {
        'stable': 'low',
        'mild_decline': 'medium',
        'moderate_decline': 'high',
        'high_risk': 'critical'
    }.get(patient_state, 'medium')
    
    # Raise risk if both conditions are met
    if decline_detected and persistent_negative_detected:
        if base_risk == 'low':
            combined_risk = 'medium'
        elif base_risk == 'medium':
            combined_risk = 'high'
        elif base_risk == 'high':
            combined_risk = 'critical'
        else:
            combined_risk = 'critical'
        
        risk_raised = True
        risk_reason = 'Both functional decline and persistent negative emotions detected'
    elif decline_detected:
        combined_risk = base_risk
        risk_raised = False
        risk_reason = 'Functional decline detected, but emotional state is stable'
    elif persistent_negative_detected:
        if base_risk == 'low':
            combined_risk = 'medium'
            risk_raised = True
        else:
            combined_risk = base_risk
            risk_raised = False
        risk_reason = 'Persistent negative emotions detected, but functional performance is stable'
    else:
        combined_risk = base_risk
        risk_raised = False
        risk_reason = 'No significant issues detected'
    
    # Additional check for worsening emotion trend
    if emotion_trend == 'worsening' and combined_risk in ['low', 'medium']:
        if combined_risk == 'low':
            combined_risk = 'medium'
        elif combined_risk == 'medium':
            combined_risk = 'high'
        risk_reason += '; Emotion trend is worsening'
    
    return {
        'combinedRiskLevel': combined_risk,
        'baseRiskLevel': base_risk,
        'riskRaised': risk_raised,
        'reason': risk_reason,
        'declineDetected': decline_detected,
        'persistentNegativeDetected': persistent_negative_detected,
        'emotionTrend': emotion_trend,
        'recommendation': get_risk_recommendation(combined_risk)
    }

def get_risk_recommendation(risk_level: str) -> str:
    """Get recommendation based on risk level."""
    recommendations = {
        'low': 'Continue monitoring. Patient is functioning well.',
        'medium': 'Increased monitoring recommended. Schedule check-in with caregiver.',
        'high': 'Immediate attention required. Consider medical consultation.',
        'critical': 'Urgent intervention needed. Contact healthcare provider immediately.'
    }
    return recommendations.get(risk_level, 'Monitor closely.')

