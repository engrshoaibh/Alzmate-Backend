# notification_service.py
"""
Caregiver Notification Service
FR-SA09: Notify caregivers when high-intensity negative emotions persist
FR-PT13: Notify caregivers when decline is detected
FR-PT14: Notify caregivers immediately when appointment is missed
"""

from typing import List, Dict, Optional
from firebase_service import get_firestore_client, get_journal_entry_by_id
from firebase_admin import firestore

# Firestore collections
USERS_COLLECTION = 'users'
NOTIFICATIONS_COLLECTION = 'notifications'

def get_patient_caregivers(patient_id: str) -> List[str]:
    """Get list of caregiver IDs for a patient."""
    db = get_firestore_client()
    
    patient_doc = db.collection(USERS_COLLECTION).document(patient_id).get()
    if not patient_doc.exists:
        return []
    
    data = patient_doc.to_dict()
    caregiver_ids = data.get('caregiverIds', [])
    
    return caregiver_ids if isinstance(caregiver_ids, list) else []

def create_notification(
    recipient_id: str,
    title: str,
    message: str,
    notification_type: str,
    priority: str = 'medium',
    data: Optional[Dict] = None
) -> str:
    """
    Create a notification in Firestore.
    
    Args:
        recipient_id: User ID of the notification recipient
        title: Notification title
        message: Notification message
        notification_type: Type of notification (e.g., 'emotion_alert', 'decline_alert', 'appointment_missed')
        priority: Priority level ('low', 'medium', 'high', 'urgent')
        data: Additional data to include
    
    Returns:
        Notification document ID
    """
    db = get_firestore_client()
    
    notification_data = {
        'recipientId': recipient_id,
        'title': title,
        'message': message,
        'type': notification_type,
        'priority': priority,
        'read': False,
        'createdAt': firestore.SERVER_TIMESTAMP,
        'data': data or {}
    }
    
    doc_ref = db.collection(NOTIFICATIONS_COLLECTION).document()
    doc_ref.set(notification_data)
    
    return doc_ref.id

def notify_caregivers_emotion_alert(
    patient_id: str,
    emotion_details: Dict
) -> List[str]:
    """
    Notify caregivers about persistent negative emotions (FR-SA09).
    
    Args:
        patient_id: Patient ID
        emotion_details: Dictionary with emotion alert details
    
    Returns:
        List of notification IDs created
    """
    caregiver_ids = get_patient_caregivers(patient_id)
    
    if not caregiver_ids:
        return []
    
    # Get patient name
    db = get_firestore_client()
    patient_doc = db.collection(USERS_COLLECTION).document(patient_id).get()
    patient_name = patient_doc.to_dict().get('name', 'Patient') if patient_doc.exists else 'Patient'
    
    notification_ids = []
    
    for caregiver_id in caregiver_ids:
        title = f"Emotion Alert: {patient_name}"
        message = (
            f"{patient_name} has been experiencing persistent high-intensity negative emotions "
            f"({emotion_details.get('daysWithHighNegativeEmotions', 0)} days). "
            f"Please check in with them."
        )
        
        notification_id = create_notification(
            recipient_id=caregiver_id,
            title=title,
            message=message,
            notification_type='emotion_alert',
            priority='high',
            data={
                'patientId': patient_id,
                'patientName': patient_name,
                'emotionDetails': emotion_details
            }
        )
        
        notification_ids.append(notification_id)
    
    return notification_ids

def notify_caregivers_decline_alert(
    patient_id: str,
    decline_details: Dict
) -> List[str]:
    """
    Notify caregivers when decline is detected (FR-PT13).
    
    Args:
        patient_id: Patient ID
        decline_details: Dictionary with decline detection details
    
    Returns:
        List of notification IDs created
    """
    caregiver_ids = get_patient_caregivers(patient_id)
    
    if not caregiver_ids:
        return []
    
    # Get patient name
    db = get_firestore_client()
    patient_doc = db.collection(USERS_COLLECTION).document(patient_id).get()
    patient_name = patient_doc.to_dict().get('name', 'Patient') if patient_doc.exists else 'Patient'
    
    notification_ids = []
    
    for caregiver_id in caregiver_ids:
        title = f"Decline Alert: {patient_name}"
        message = (
            f"{patient_name}'s cognitive performance score has declined by "
            f"{decline_details.get('difference', 0):.1f} points from baseline. "
            f"Current score: {decline_details.get('currentScore', 0):.1f}/100. "
            f"Please review their progress report."
        )
        
        notification_id = create_notification(
            recipient_id=caregiver_id,
            title=title,
            message=message,
            notification_type='decline_alert',
            priority='high',
            data={
                'patientId': patient_id,
                'patientName': patient_name,
                'declineDetails': decline_details
            }
        )
        
        notification_ids.append(notification_id)
    
    return notification_ids

def notify_caregivers_appointment_missed(
    patient_id: str,
    appointment_details: Dict
) -> List[str]:
    """
    Notify caregivers immediately when appointment is missed (FR-PT14).
    
    Args:
        patient_id: Patient ID
        appointment_details: Dictionary with appointment details
    
    Returns:
        List of notification IDs created
    """
    caregiver_ids = get_patient_caregivers(patient_id)
    
    if not caregiver_ids:
        return []
    
    # Get patient name
    db = get_firestore_client()
    patient_doc = db.collection(USERS_COLLECTION).document(patient_id).get()
    patient_name = patient_doc.to_dict().get('name', 'Patient') if patient_doc.exists else 'Patient'
    
    appointment_title = appointment_details.get('title', 'Appointment')
    appointment_time = appointment_details.get('time', '')
    
    notification_ids = []
    
    for caregiver_id in caregiver_ids:
        title = f"Missed Appointment: {patient_name}"
        message = (
            f"{patient_name} missed an appointment: {appointment_title} "
            f"(scheduled for {appointment_time}). "
            f"Please follow up."
        )
        
        notification_id = create_notification(
            recipient_id=caregiver_id,
            title=title,
            message=message,
            notification_type='appointment_missed',
            priority='urgent',
            data={
                'patientId': patient_id,
                'patientName': patient_name,
                'appointmentDetails': appointment_details
            }
        )
        
        notification_ids.append(notification_id)
    
    return notification_ids

def notify_caregivers_combined_risk(
    patient_id: str,
    risk_assessment: Dict
) -> List[str]:
    """
    Notify caregivers about combined risk (functional decline + emotional distress).
    
    Args:
        patient_id: Patient ID
        risk_assessment: Dictionary with combined risk assessment
    
    Returns:
        List of notification IDs created
    """
    caregiver_ids = get_patient_caregivers(patient_id)
    
    if not caregiver_ids:
        return []
    
    risk_level = risk_assessment.get('combinedRiskLevel', 'medium')
    
    # Only notify for high or critical risk
    if risk_level not in ['high', 'critical']:
        return []
    
    # Get patient name
    db = get_firestore_client()
    patient_doc = db.collection(USERS_COLLECTION).document(patient_id).get()
    patient_name = patient_doc.to_dict().get('name', 'Patient') if patient_doc.exists else 'Patient'
    
    notification_ids = []
    
    for caregiver_id in caregiver_ids:
        title = f"High Risk Alert: {patient_name}"
        message = (
            f"{patient_name} is showing signs of both functional decline and emotional distress. "
            f"Risk level: {risk_level.upper()}. "
            f"{risk_assessment.get('recommendation', 'Please review their combined report.')}"
        )
        
        notification_id = create_notification(
            recipient_id=caregiver_id,
            title=title,
            message=message,
            notification_type='combined_risk_alert',
            priority='urgent' if risk_level == 'critical' else 'high',
            data={
                'patientId': patient_id,
                'patientName': patient_name,
                'riskAssessment': risk_assessment
            }
        )
        
        notification_ids.append(notification_id)
    
    return notification_ids

