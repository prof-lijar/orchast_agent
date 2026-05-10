import re
from typing import List, Dict, Any

def social_media_post_generator_tool(topic: str) -> Dict[str, Any]:
    """
    Generates a complete social media post (headline, body text, and three relevant 
    hashtags) optimized for short-form platforms based on a user-provided topic.
    
    NOTE: This implementation provides a deterministic mock response based on the input
    topic, as it cannot rely on an external language model (LLM) within the safety constraints.

    Args:
        topic: The subject matter or core idea for the social media post.

    Returns:
        A dictionary containing the generated post components:
        - headline (str): A short, engaging title.
        - body_text (str): The main body of the post, simulated to be short.
        - hashtags (List[str]): Three relevant hashtags.
    """
    
    # Handle edge case: None or empty topic
    if not topic or not topic.strip():
        return {
            "headline": "Stay Informed!",
            "body_text": "Always look for new ideas and remember to engage with your audience.",
            "hashtags": ["#DailyInspiration", "#ContentStrategy", "#DigitalMarketing"]
        }

    clean_topic = topic.strip()
    
    # --- 1. Generate Headline ---
    
    # Simple formatting: take the first 50 characters, capitalize, and add emojis
    headline = clean_topic.capitalize()
    if len(headline) > 50:
        headline = headline[:47] + "..."
    headline = f"💡 Quick Read: {headline}"

    # --- 2. Generate Body Text ---
    
    # Generate a short body text template using the topic
    body_text_template = "Did you know? Understanding '{topic}' is key to success! What is your biggest takeaway on this subject?"
    body_text = body_text_template.format(topic=clean_topic)
    
    # Ensure mock body text respects common platform limits (e.g., Twitter 280 chars)
    if len(body_text) > 280:
        body_text = body_text[:277] + "..."

    # --- 3. Generate Hashtags ---
    
    # Simple tokenization: remove punctuation and split into words
    words = re.findall(r'\b\w+\b', clean_topic.lower())
    
    # Filter out common stop words and short/non-alphabetic words
    stop_words = {"the", "a", "an", "is", "of", "for", "and", "to", "in", "with", "on", "it", "or", "what", "we"}
    keywords = [
        word for word in words 
        if word not in stop_words and len(word) > 3 and word.isalpha()
    ]
    
    # Get unique keywords and format them
    unique_keywords = list(set(keywords))
    
    # Define fallback hashtags
    default_hashtags = ["#Insight", "#LearnSomethingNew", "#SocialPost"]

    # Select up to three keywords as hashtags
    hashtags = [f"#{kw}" for kw in unique_keywords[:3]]
    
    # Pad with default hashtags if less than 3 were found
    i = 0
    while len(hashtags) < 3 and i < len(default_hashtags):
        tag_to_add = default_hashtags[i]
        if tag_to_add not in hashtags:
            hashtags.append(tag_to_add)
        i += 1
    
    hashtags = hashtags[:3]
    
    # --- 4. Return Output ---
    return {
        "headline": headline,
        "body_text": body_text,
        "hashtags": hashtags
    }
