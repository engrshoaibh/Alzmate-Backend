# example_usage.py
"""
Example usage of the emotion analysis API.
This script demonstrates how to use the emotion analysis functions directly.
"""

from emotion_model import analyze_emotion
from database import save_emotion_analysis, get_emotion_trends, get_daily_emotion_summary
from datetime import datetime

def example_analyze_emotion():
    """Example: Analyze emotion from text."""
    print("=" * 60)
    print("Example 1: Analyze Emotion")
    print("=" * 60)
    
    # Example 1: Negative emotions
    text1 = "I don't know why I keep forgetting things. It makes me angry and I feel hopeless."
    print(f"\nText: {text1}")
    result1 = analyze_emotion(text1)
    print(f"\nPrimary Emotion: {result1['primary_emotion']['emotion']} "
          f"(Intensity: {result1['primary_emotion']['intensity']}/100)")
    if result1['secondary_emotion']:
        print(f"Secondary Emotion: {result1['secondary_emotion']['emotion']} "
              f"(Intensity: {result1['secondary_emotion']['intensity']}/100)")
    print(f"Interpretation: {result1['interpretation_tag']}")
    print(f"Mood Risk: {result1['mood_risk']}")
    
    # Example 2: Positive emotions
    text2 = "Today was nice. I talked to my son and felt calm."
    print(f"\n\nText: {text2}")
    result2 = analyze_emotion(text2)
    print(f"\nPrimary Emotion: {result2['primary_emotion']['emotion']} "
          f"(Intensity: {result2['primary_emotion']['intensity']}/100)")
    if result2['secondary_emotion']:
        print(f"Secondary Emotion: {result2['secondary_emotion']['emotion']} "
              f"(Intensity: {result2['secondary_emotion']['intensity']}/100)")
    print(f"Interpretation: {result2['interpretation_tag']}")
    print(f"Mood Risk: {result2['mood_risk']}")

def example_save_and_retrieve():
    """Example: Save analysis and retrieve trends."""
    print("\n\n" + "=" * 60)
    print("Example 2: Save Analysis and Get Trends")
    print("=" * 60)
    
    patient_id = "example_patient_001"
    
    # Save some example entries
    texts = [
        "I don't know why I keep forgetting things. It makes me angry and I feel hopeless.",
        "Today was nice. I talked to my son and felt calm.",
        "I'm confused about what day it is. Everything feels strange.",
        "Feeling lonely today. No one called or visited.",
        "Had a good day. Went for a walk and felt happy.",
    ]
    
    print(f"\nSaving {len(texts)} entries for patient {patient_id}...")
    for i, text in enumerate(texts):
        result = analyze_emotion(text)
        entry_id = save_emotion_analysis(
            patient_id=patient_id,
            journal_text=text,
            analysis_result=result,
            timestamp=datetime.now()
        )
        print(f"  Entry {i+1} saved (ID: {entry_id})")
    
    # Get trends
    print(f"\nGetting trends for patient {patient_id}...")
    trends = get_emotion_trends(patient_id, days=7)
    
    print(f"\nTotal Entries: {trends['total_entries']}")
    print(f"Mood Risk Count: {trends['mood_risk_count']} ({trends['mood_risk_percentage']}%)")
    print("\nEmotion Trends:")
    for trend in trends['trends']:
        print(f"  {trend['emotion'].capitalize()}: {trend['count']} entries, "
              f"avg intensity {trend['average_intensity']:.1f}/100")
    
    # Get daily summary
    print(f"\nGetting daily summary for patient {patient_id}...")
    daily = get_daily_emotion_summary(patient_id)
    print(f"Date: {daily['date']}")
    print(f"Total Entries: {daily['total_entries']}")
    print(f"Mood Risk: {daily['mood_risk']}")
    print("Emotions:")
    for emotion in daily['emotions']:
        print(f"  {emotion['emotion'].capitalize()}: {emotion['count']} entries, "
              f"avg intensity {emotion['avg_intensity']:.1f}/100")

if __name__ == "__main__":
    # Run examples
    example_analyze_emotion()
    example_save_and_retrieve()
    
    print("\n\n" + "=" * 60)
    print("Examples completed!")
    print("=" * 60)
    print("\nTo start the API server, run:")
    print("  uvicorn main:app --reload")

