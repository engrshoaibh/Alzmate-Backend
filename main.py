# main.py
from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import tempfile
import os
from emotion_model import analyze_emotion
from database import (
    save_emotion_analysis,
    get_emotion_entries,
    get_emotion_trends,
    get_daily_emotion_summary
)
from cloudinary_service import upload_audio_file, upload_audio_from_bytes
from progress_tracking import (
    calculate_weekly_score,
    generate_weekly_report,
    get_patient_state,
    detect_decline
)
from advanced_emotion_analysis import (
    detect_emotion_shift,
    check_persistent_negative_emotions,
    detect_emotion_volatility,
    generate_emotion_trend_summary
)
from combined_analysis import generate_combined_weekly_report

app = FastAPI(
    title="AlzMate Emotion Analysis API",
    description="Emotion-based sentiment analysis for voice journal entries",
    version="1.0.0"
)

class EmotionRequest(BaseModel):
    patient_id: str
    journal_text: str
    timestamp: Optional[str] = None  # ISO format datetime string
    journal_entry_id: Optional[str] = None  # Optional: link to existing journal entry

class EmotionResponse(BaseModel):
    patient_id: str
    entry_id: Optional[str] = None
    timestamp: str
    analysis: dict
    audio_url: Optional[str] = None

@app.post("/analyze-emotion", response_model=EmotionResponse)
async def analyze_emotion_endpoint(req: EmotionRequest):
    """
    Analyze emotion from journal text.
    
    Processes the text, detects emotions, calculates intensity,
    and stores the result in Firestore.
    """
    try:
        # Parse timestamp if provided
        timestamp = None
        if req.timestamp:
            try:
                timestamp = datetime.fromisoformat(req.timestamp.replace('Z', '+00:00'))
            except:
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()
        
        # Analyze emotion
        result = analyze_emotion(req.journal_text, preprocess=True)
        
        # Save to Firestore
        entry_id = save_emotion_analysis(
            patient_id=req.patient_id,
            journal_text=req.journal_text,
            analysis_result=result,
            timestamp=timestamp,
            journal_entry_id=req.journal_entry_id
        )
        
        return EmotionResponse(
            patient_id=req.patient_id,
            entry_id=entry_id,
            timestamp=timestamp.isoformat(),
            analysis=result,
            audio_url=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing emotion: {str(e)}")

@app.post("/analyze-emotion-with-audio")
async def analyze_emotion_with_audio(
    patient_id: str = Form(...),
    journal_text: str = Form(...),
    timestamp: Optional[str] = Form(None),
    journal_entry_id: Optional[str] = Form(None),
    audio_file: Optional[UploadFile] = File(None)
):
    """
    Analyze emotion from journal text with optional audio file upload.
    
    If audio_file is provided, uploads it to Cloudinary and includes the URL in the response.
    """
    try:
        # Parse timestamp if provided
        parsed_timestamp = None
        if timestamp:
            try:
                parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                parsed_timestamp = datetime.now()
        else:
            parsed_timestamp = datetime.now()
        
        # Analyze emotion
        result = analyze_emotion(journal_text, preprocess=True)
        
        # Handle audio file upload if provided
        audio_url = None
        if audio_file and audio_file.filename:
            try:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(audio_file.filename)[1]) as tmp_file:
                    content = await audio_file.read()
                    tmp_file.write(content)
                    tmp_file_path = tmp_file.name
                
                # Upload to Cloudinary
                audio_url = upload_audio_file(
                    file_path=tmp_file_path,
                    user_id=patient_id,
                    entry_id=journal_entry_id
                )
                
                # Clean up temporary file
                os.unlink(tmp_file_path)
            except Exception as e:
                print(f"Warning: Failed to upload audio file: {e}")
                # Continue without audio URL
        
        # Save to Firestore
        entry_id = save_emotion_analysis(
            patient_id=patient_id,
            journal_text=journal_text,
            analysis_result=result,
            timestamp=parsed_timestamp,
            journal_entry_id=journal_entry_id,
            audio_url=audio_url
        )
        
        return {
            "patient_id": patient_id,
            "entry_id": entry_id,
            "timestamp": parsed_timestamp.isoformat(),
            "analysis": result,
            "audio_url": audio_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing emotion: {str(e)}")

@app.get("/emotion-entries/{patient_id}")
def get_entries(
    patient_id: str,
    start_date: Optional[str] = Query(None, description="Start date in ISO format"),
    end_date: Optional[str] = Query(None, description="End date in ISO format"),
    limit: Optional[int] = Query(None, description="Maximum number of entries to return")
):
    """Get emotion analysis entries for a patient."""
    try:
        start = None
        end = None
        
        if start_date:
            start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        entries = get_emotion_entries(patient_id, start, end, limit)
        
        return {
            "patient_id": patient_id,
            "count": len(entries),
            "entries": entries
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving entries: {str(e)}")

@app.get("/emotion-trends/{patient_id}")
def get_trends(
    patient_id: str,
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze")
):
    """
    Get emotion trends for a patient over specified days.
    
    Returns:
    - Emotion counts and frequencies
    - Average intensities
    - Mood risk statistics
    - Trend insights (e.g., "sadness appears 4/7 days")
    """
    try:
        trends = get_emotion_trends(patient_id, days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving trends: {str(e)}")

@app.get("/daily-summary/{patient_id}")
def get_daily_summary(
    patient_id: str,
    date: Optional[str] = Query(None, description="Date in ISO format (YYYY-MM-DD)")
):
    """
    Get emotion summary for a specific day.
    
    Returns emotion counts, intensities, and mood risk for the day.
    """
    try:
        target_date = None
        if date:
            target_date = datetime.fromisoformat(date)
        
        summary = get_daily_emotion_summary(patient_id, target_date)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving daily summary: {str(e)}")

@app.get("/weekly-summary/{patient_id}")
def get_weekly_summary(patient_id: str):
    """
    Get weekly emotion summary with insights.
    
    Example output:
    - "This week shows high anxiety and increasing low mood"
    - Daily breakdown
    - Emotion frequency charts data
    """
    try:
        trends = get_emotion_trends(patient_id, days=7)
        
        # Generate summary insights
        insights = []
        
        if trends["total_entries"] > 0:
            # Find most common emotions
            top_emotions = sorted(
                trends["trends"],
                key=lambda x: x["count"],
                reverse=True
            )[:3]
            
            if top_emotions:
                emotion_names = [e["emotion"] for e in top_emotions]
                insight = f"This week shows "
                insight += ", ".join(emotion_names[:-1])
                if len(emotion_names) > 1:
                    insight += f" and {emotion_names[-1]}"
                else:
                    insight += emotion_names[0]
                insights.append(insight)
            
            # Check for increasing trends (simplified - would need more data for real trend analysis)
            high_intensity_emotions = [
                e for e in trends["trends"]
                if e["average_intensity"] >= 60
            ]
            
            if high_intensity_emotions:
                high_emotions = [e["emotion"] for e in high_intensity_emotions]
                insights.append(f"High intensity emotions detected: {', '.join(high_emotions)}")
            
            if trends["mood_risk_count"] > 0:
                insights.append(
                    f"Mood risk detected in {trends['mood_risk_count']} entries "
                    f"({trends['mood_risk_percentage']}%)"
                )
        
        return {
            **trends,
            "summary_insights": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving weekly summary: {str(e)}")

# ==================== PROGRESS TRACKING ENDPOINTS ====================

@app.get("/progress/weekly-score/{patient_id}")
def get_weekly_score(patient_id: str):
    """
    Calculate and return weekly cognitive performance score (FR-PT07).
    
    Returns:
    - Weekly score (0-100)
    - Patient state (stable/mild_decline/moderate_decline/high_risk)
    - Task breakdown
    """
    try:
        score_data = calculate_weekly_score(patient_id)
        score_data['patientState'] = get_patient_state(score_data['score'])
        return score_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating weekly score: {str(e)}")

@app.get("/progress/weekly-report/{patient_id}")
def get_weekly_progress_report(patient_id: str):
    """
    Generate weekly progress report (FR-PT15).
    
    Includes:
    - Weekly score and patient state
    - Trend analysis
    - Missed task breakdown
    - Decline detection
    """
    try:
        report = generate_weekly_report(patient_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating progress report: {str(e)}")

@app.get("/progress/decline-detection/{patient_id}")
def check_decline(patient_id: str):
    """
    Check for cognitive decline (FR-PT11, FR-PT12).
    
    Compares current score with baseline and detects decline.
    """
    try:
        current_score_data = calculate_weekly_score(patient_id)
        decline_info = detect_decline(patient_id, current_score_data['score'])
        return {
            **decline_info,
            'currentScore': current_score_data['score']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting decline: {str(e)}")

# ==================== ADVANCED EMOTION ANALYSIS ENDPOINTS ====================

@app.get("/emotion/shift-detection/{patient_id}")
def detect_emotion_shift_endpoint(
    patient_id: str,
    emotion: str = Query(..., description="Emotion to check for shift"),
    days: int = Query(7, description="Number of days to analyze"),
    intensity_increase: float = Query(20.0, description="Minimum intensity increase threshold")
):
    """
    Detect significant emotion shift (FR-SA07).
    
    Detects if an emotion's intensity has increased significantly over time.
    """
    try:
        result = detect_emotion_shift(patient_id, emotion, days, intensity_increase)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting emotion shift: {str(e)}")

@app.get("/emotion/persistent-negative/{patient_id}")
def check_persistent_negative_endpoint(
    patient_id: str,
    days: int = Query(3, description="Number of consecutive days to check")
):
    """
    Check for persistent high-intensity negative emotions (FR-SA09).
    
    Returns information about persistent negative emotions that may require caregiver attention.
    """
    try:
        result = check_persistent_negative_emotions(patient_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking persistent negative emotions: {str(e)}")

@app.get("/emotion/volatility/{patient_id}")
def detect_volatility_endpoint(
    patient_id: str,
    days: int = Query(7, description="Number of days to analyze")
):
    """
    Detect emotion volatility - rapid day-to-day changes (FR-SA10).
    
    Flags mood risk when emotion volatility is high.
    """
    try:
        result = detect_emotion_volatility(patient_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting volatility: {str(e)}")

@app.get("/emotion/trend-summary/{patient_id}")
def get_emotion_trend_summary_endpoint(
    patient_id: str,
    days: int = Query(7, description="Number of days to analyze")
):
    """
    Get emotion trend summary with improving/stable/worsening classification (FR-SA08).
    """
    try:
        result = generate_emotion_trend_summary(patient_id, days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating trend summary: {str(e)}")

# ==================== COMBINED ANALYSIS ENDPOINTS ====================

@app.get("/combined/weekly-report/{patient_id}")
def get_combined_weekly_report(patient_id: str):
    """
    Generate combined weekly report (FR-COM01, FR-COM02).
    
    Includes:
    - Progress tracking (cognitive performance score)
    - Emotion analysis (trends, persistent negative emotions)
    - Combined risk assessment
    - Recommendations
    """
    try:
        report = generate_combined_weekly_report(patient_id)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating combined report: {str(e)}")

@app.get("/")
def root():
    """API root endpoint."""
    return {
        "message": "AlzMate Emotion Analysis & Progress Tracking API",
        "version": "2.0.0",
        "endpoints": {
            "emotion_analysis": {
                "analyze": "/analyze-emotion",
                "analyze_with_audio": "/analyze-emotion-with-audio",
                "entries": "/emotion-entries/{patient_id}",
                "trends": "/emotion-trends/{patient_id}",
                "daily_summary": "/daily-summary/{patient_id}",
                "weekly_summary": "/weekly-summary/{patient_id}",
                "shift_detection": "/emotion/shift-detection/{patient_id}",
                "persistent_negative": "/emotion/persistent-negative/{patient_id}",
                "volatility": "/emotion/volatility/{patient_id}",
                "trend_summary": "/emotion/trend-summary/{patient_id}"
            },
            "progress_tracking": {
                "weekly_score": "/progress/weekly-score/{patient_id}",
                "weekly_report": "/progress/weekly-report/{patient_id}",
                "decline_detection": "/progress/decline-detection/{patient_id}"
            },
            "combined_analysis": {
                "combined_report": "/combined/weekly-report/{patient_id}"
            }
        }
    }
