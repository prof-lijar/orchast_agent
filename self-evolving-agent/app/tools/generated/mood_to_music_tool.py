def mood_to_music_tool(mood: str) -> dict:
    """
    Recommends a music style, playlist theme, or song vibe based on a user-provided mood.

    Args:
        mood: A string describing the user's current emotional state or desired listening atmosphere.

    Returns:
        A dictionary containing the music recommendation.
        - recommendation (str): The suggested music style or vibe.
    """
    if not isinstance(mood, str) or not mood.strip():
        return {"recommendation": "Please describe your mood (e.g., 'Happy', 'Focused', 'Sad') to receive a music recommendation."}

    normalized_mood = mood.lower()

    recommendation = "Easy Listening, General Lo-fi beats, or an eclectic playlist to explore new vibes."

    # Use simple keyword matching to determine the recommendation
    if any(word in normalized_mood for word in ["happy", "energetic", "upbeat", "excited", "party", "joyful"]):
        recommendation = "High-energy Pop, Dance music, or upbeat Funk for a celebratory feel."
    elif any(word in normalized_mood for word in ["sad", "contemplative", "melancholy", "down", "gloomy", "reflective"]):
        recommendation = "Acoustic Indie, Lo-fi Beats, or classical Piano pieces for a thoughtful and reflective mood."
    elif any(word in normalized_mood for word in ["focused", "concentration", "work", "study", "productive", "thinking"]):
        recommendation = "Instrumental Ambient, Cinematic Soundtracks, or Classical Baroque (e.g., Bach) to aid concentration."
    elif any(word in normalized_mood for word in ["calm", "relaxed", "chill", "peaceful", "unwind", "tranquil"]):
        recommendation = "Soft Jazz, gentle Ambient electronic, or nature sounds for a sense of calm."
    elif any(word in normalized_mood for word in ["angry", "aggressive", "frustrated", "intense", "rock"]):
        recommendation = "Heavy Metal, Punk Rock, or high-tempo Trap beats to channel powerful energy."
    elif any(word in normalized_mood for word in ["romantic", "loving", "sensual", "date", "cuddle"]):
        recommendation = "R&B Slow Jams, smooth Soul, or Latin Ballads for a romantic atmosphere."
    elif any(word in normalized_mood for word in ["adventure", "travel", "road trip", "driving"]):
        recommendation = "Classic Rock anthems, Folk revival, or cinematic instrumental scores for the journey."

    return {"recommendation": recommendation}
