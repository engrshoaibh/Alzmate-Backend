# AlzMate Emotion Analysis & Progress Tracking Backend

Comprehensive emotion-based sentiment analysis and cognitive performance tracking API for the AlzMate application.

## Features

### Emotion Analysis (Part A)
- **Text Preprocessing**: Cleans filler words, repeated characters, and normalizes text
- **Emotion Detection**: Detects specific emotions (happy, sad, angry, anxious, fearful, confused, frustrated, calm, lonely, depressed/low mood)
- **Multi-Emotion Output**: Returns primary and secondary emotions
- **Intensity Scoring**: 0-100 scale for emotion intensity
- **Interpretation Tags**: Human-readable tags (e.g., "high distress", "mild confusion")
- **Mood Risk Detection**: Flags entries with high-intensity negative emotions
- **Database Storage**: Firebase Firestore for storing analysis results
- **Trend Analysis**: Daily and weekly emotion trends with insights
- **Advanced Features**:
  - Emotion shift detection (FR-SA07)
  - Persistent negative emotion alerts (FR-SA09)
  - Emotion volatility detection (FR-SA10)
  - Trend summary with improving/stable/worsening classification (FR-SA08)

### Progress Tracking (Part B)
- **Task Completion Tracking**: Monitors medication, appointments, meals, and brain training
- **Weekly Score Calculation**: 0-100 cognitive performance score (FR-PT07)
- **Patient State Classification**: Stable / Mild Decline / Moderate Decline / High Risk (FR-PT09)
- **Baseline Tracking**: Establishes baseline from first 4 weeks (FR-PT10)
- **Decline Detection**: Detects score drops ≥15 points for 2+ consecutive weeks (FR-PT11, FR-PT12)
- **Weekly Reports**: Comprehensive progress reports with breakdowns (FR-PT15)

### Combined Analysis (Part C)
- **Integrated Reports**: Combines emotion trends with progress tracking (FR-COM01)
- **Combined Risk Assessment**: Raises risk level when both decline and negative emotions detected (FR-COM02)
- **Caregiver Notifications**: Automatic alerts for high-risk situations

## Installation

1. Create a virtual environment (if not already created):
```bash
python -m venv env
```

2. Activate the virtual environment:
```bash
# Windows
env\Scripts\activate

# Linux/Mac
source env/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Local Development

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### Production (Render.com)

**Start Command:**
```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Build Command:**
```bash
pip install -r requirements.txt
```

See `RENDER_DEPLOYMENT.md` for detailed deployment instructions.

### API Endpoints

#### 1. Analyze Emotion
**POST** `/analyze-emotion`

Analyze emotion from journal text.

**Request Body:**
```json
{
  "patient_id": "patient123",
  "journal_text": "I don't know why I keep forgetting things. It makes me angry and I feel hopeless.",
  "timestamp": "2024-01-15T10:30:00",  // Optional
  "journal_entry_id": "abc123"  // Optional: link to existing journal entry
}
```

#### 1b. Analyze Emotion with Audio Upload
**POST** `/analyze-emotion-with-audio`

Analyze emotion from journal text and upload audio file to Cloudinary.

**Request (multipart/form-data):**
- `patient_id`: Patient ID (required)
- `journal_text`: Journal text (required)
- `timestamp`: ISO timestamp (optional)
- `journal_entry_id`: Journal entry ID (optional)
- `audio_file`: Audio file (optional)

**Example (curl):**
```bash
curl -X POST "http://localhost:8000/analyze-emotion-with-audio" \
  -F "patient_id=patient123" \
  -F "journal_text=I don't know why I keep forgetting things..." \
  -F "audio_file=@recording.mp3"
```

**Response:**
```json
{
  "patient_id": "patient123",
  "entry_id": 1,
  "timestamp": "2024-01-15T10:30:00",
  "analysis": {
    "primary_emotion": {
      "emotion": "angry",
      "confidence": 0.7234,
      "intensity": 72,
      "interpretation_tag": "high distress"
    },
    "secondary_emotion": {
      "emotion": "depressed/low mood",
      "confidence": 0.6612,
      "intensity": 66,
      "interpretation_tag": "moderate low mood"
    },
    "interpretation_tag": "high distress",
    "mood_risk": true,
    "processed_text": "i don't know why i keep forgetting things. it makes me angry and i feel hopeless."
  }
}
```

#### 2. Get Emotion Entries
**GET** `/emotion-entries/{patient_id}`

Get all emotion analysis entries for a patient.

**Query Parameters:**
- `start_date` (optional): Start date in ISO format
- `end_date` (optional): End date in ISO format
- `limit` (optional): Maximum number of entries to return

**Example:**
```
GET /emotion-entries/patient123?start_date=2024-01-01&limit=10
```

#### 3. Get Emotion Trends
**GET** `/emotion-trends/{patient_id}`

Get emotion trends over specified days.

**Query Parameters:**
- `days` (default: 7): Number of days to analyze (1-365)

**Example:**
```
GET /emotion-trends/patient123?days=7
```

**Response:**
```json
{
  "patient_id": "patient123",
  "period_days": 7,
  "total_entries": 7,
  "emotion_counts": {
    "angry": 4,
    "sad": 2,
    "calm": 1
  },
  "average_intensities": {
    "angry": 65.0,
    "sad": 55.0,
    "calm": 70.0
  },
  "mood_risk_count": 3,
  "mood_risk_percentage": 42.9,
  "trends": [
    {
      "emotion": "angry",
      "count": 4,
      "percentage": 57.1,
      "average_intensity": 65.0,
      "description": "Angry appears 4/7 entries (avg intensity 65.0/100)"
    }
  ]
}
```

#### 4. Get Daily Summary
**GET** `/daily-summary/{patient_id}`

Get emotion summary for a specific day.

**Query Parameters:**
- `date` (optional): Date in ISO format (YYYY-MM-DD), defaults to today

**Example:**
```
GET /daily-summary/patient123?date=2024-01-15
```

#### 5. Get Weekly Summary
**GET** `/weekly-summary/{patient_id}`

Get weekly emotion summary with insights.

**Example:**
```
GET /weekly-summary/patient123
```

**Response includes:**
- All trend data for the past 7 days
- Summary insights (e.g., "This week shows high anxiety and increasing low mood")

#### 6. Detect Emotion Shift
**GET** `/emotion/shift-detection/{patient_id}`

Detect significant emotion shift over time (FR-SA07).

**Query Parameters:**
- `emotion`: Emotion to check (required)
- `days`: Number of days to analyze (default: 7)
- `intensity_increase`: Minimum intensity increase threshold (default: 20.0)

**Example:**
```
GET /emotion/shift-detection/patient123?emotion=sad&days=7&intensity_increase=20
```

#### 7. Check Persistent Negative Emotions
**GET** `/emotion/persistent-negative/{patient_id}`

Check for persistent high-intensity negative emotions (FR-SA09).

**Query Parameters:**
- `days`: Number of consecutive days to check (default: 3)

**Example:**
```
GET /emotion/persistent-negative/patient123?days=3
```

#### 8. Detect Emotion Volatility
**GET** `/emotion/volatility/{patient_id}`

Detect emotion volatility - rapid day-to-day changes (FR-SA10).

**Query Parameters:**
- `days`: Number of days to analyze (default: 7)

**Example:**
```
GET /emotion/volatility/patient123?days=7
```

#### 9. Get Emotion Trend Summary
**GET** `/emotion/trend-summary/{patient_id}`

Get emotion trend summary with improving/stable/worsening classification (FR-SA08).

**Query Parameters:**
- `days`: Number of days to analyze (default: 7)

**Example:**
```
GET /emotion/trend-summary/patient123?days=7
```

### Progress Tracking Endpoints

#### 10. Get Weekly Score
**GET** `/progress/weekly-score/{patient_id}`

Calculate and return weekly cognitive performance score (FR-PT07).

**Example:**
```
GET /progress/weekly-score/patient123
```

**Response:**
```json
{
  "patientId": "patient123",
  "weekStart": "2024-01-08T00:00:00",
  "weekEnd": "2024-01-15T00:00:00",
  "score": 69.3,
  "earnedPoints": 70.0,
  "totalPossiblePoints": 101.0,
  "patientState": "mild_decline",
  "breakdown": {
    "medication": {"completed": 10, "missed": 4, "total": 14, ...},
    "appointment": {"completed": 0, "missed": 1, "total": 1, ...},
    "meal": {"completed": 18, "missed": 3, "total": 21, ...},
    "brain_training": {"completed": 2, "total": 7, ...}
  }
}
```

#### 11. Get Weekly Progress Report
**GET** `/progress/weekly-report/{patient_id}`

Generate comprehensive weekly progress report (FR-PT15).

**Example:**
```
GET /progress/weekly-report/patient123
```

**Response includes:**
- Weekly score and patient state
- Trend analysis (improving/stable/declining)
- Missed task breakdown
- Decline detection results

#### 12. Check Decline Detection
**GET** `/progress/decline-detection/{patient_id}`

Check for cognitive decline by comparing with baseline (FR-PT11, FR-PT12).

**Example:**
```
GET /progress/decline-detection/patient123
```

### Combined Analysis Endpoints

#### 13. Get Combined Weekly Report
**GET** `/combined/weekly-report/{patient_id}`

Generate combined weekly report with both progress tracking and emotion analysis (FR-COM01, FR-COM02).

**Example:**
```
GET /combined/weekly-report/patient123
```

**Response includes:**
- Progress tracking data (score, state, trends)
- Emotion analysis (trends, persistent negative, volatility)
- Combined risk assessment
- Recommendations

## Database

The API uses **Firebase Firestore** to store all emotion analysis results. The database integrates with your existing Flutter app's Firestore collections.

### Firebase Configuration

Set the following environment variables:

```bash
# Required: Firebase Project ID
export FIREBASE_PROJECT_ID="your-project-id"

# Option 1: Path to service account JSON file
export FIREBASE_CREDENTIALS_PATH="/path/to/service-account-key.json"

# Option 2: Service account JSON as string (for cloud deployments)
export FIREBASE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
```

### Firestore Collections

**journal_entries** collection:
- Emotion analysis results can be stored directly in journal entries via the `emotionAnalysis` field
- When `journal_entry_id` is provided, the analysis is added to the existing journal entry

**emotion_analysis** collection (standalone):
- `id`: Document ID
- `patientId`: Patient identifier
- `timestamp`: Entry timestamp
- `journalText`: Original journal text
- `processedText`: Preprocessed text
- `primaryEmotion`: Primary emotion label
- `primaryIntensity`: Primary emotion intensity (0-100)
- `primaryConfidence`: Primary emotion confidence score
- `secondaryEmotion`: Secondary emotion label (nullable)
- `secondaryIntensity`: Secondary emotion intensity (nullable)
- `secondaryConfidence`: Secondary emotion confidence (nullable)
- `interpretationTag`: Human-readable interpretation
- `moodRisk`: Boolean flag for mood risk
- `journalEntryId`: Optional reference to journal entry document
- `audioUrl`: Optional URL to uploaded audio file
- `createdAt`: Record creation timestamp

### Cloudinary Configuration

The API uses **Cloudinary** for file uploads (matching your Flutter app configuration).

Set the following environment variables (optional, defaults match your Flutter app):

```bash
export CLOUDINARY_CLOUD_NAME="dkiqc4jru"
export CLOUDINARY_API_KEY="659932293576982"
export CLOUDINARY_API_SECRET="1f7M0nZpCLZ1F7ytj1CYwaV2xo8"
export CLOUDINARY_UPLOAD_PRESET="alzMate"
```

## Emotion Labels

The system detects the following emotions:
- `happy`
- `sad`
- `angry`
- `anxious`
- `fearful`
- `confused`
- `frustrated`
- `calm`
- `lonely`
- `depressed/low mood`

## Text Preprocessing

The preprocessing pipeline:
1. Removes filler words (um, uh, er, like, you know, etc.)
2. Removes excessive repeated characters (sooo → soo)
3. Normalizes whitespace
4. Normalizes punctuation spacing
5. Converts to lowercase

## Mood Risk Detection

Mood risk is flagged when:
- Primary negative emotion intensity >= 70, OR
- Secondary negative emotion intensity >= 60

Negative emotions: sad, angry, anxious, fearful, confused, frustrated, lonely, depressed/low mood

## API Documentation

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example Usage with cURL

```bash
# Analyze emotion
curl -X POST "http://localhost:8000/analyze-emotion" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_id": "patient123",
    "journal_text": "Today was nice. I talked to my son and felt calm."
  }'

# Get trends
curl "http://localhost:8000/emotion-trends/patient123?days=7"

# Get weekly summary
curl "http://localhost:8000/weekly-summary/patient123"
```

