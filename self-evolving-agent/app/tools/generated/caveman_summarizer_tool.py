import string
import re
from typing import Dict

def caveman_summarizer_tool(text: str) -> Dict[str, str]:
    """
    Summarizes input text into simple, funny, and easy-to-understand caveman-style language.

    Args:
        text: The input text string to be summarized.

    Returns:
        A dictionary containing the caveman-style summary.
        Example: {"summary": "Ugh. Me need food. Fire good."}
    """
    if not text or not isinstance(text, str):
        return {"summary": "Ugh. Me not see word. Send more rock drawings. Hah!"}

    # Normalize text to lowercase
    normalized_text = text.lower()
    
    # Simple replacement map (key: complex word/phrase, value: caveman equivalent)
    replacements = {
        # Multi-word phrases
        "artificial intelligence": "fake smart rock",
        "ethical implications": "good bad think",
        "careful consideration": "look long time",
        "rapid advancement": "quick move more",
        "coming days": "later sun",
        "many hours": "long time",
        "cold river": "wet cold spot",
        "went hunting": "look eat",
        "i am thirsty for water": "me need wet",
        "i am thirsty": "me need wet",
        "the sun is hot": "fire sky warm",
        
        # Single words (generally complex)
        "necessitates": "must need",
        "consideration": "think",
        "advancement": "move more",
        "development": "grow big",
        "progress": "go fast",
        "yesterday": "past sun",
        "today": "now sun",
        "tribe": "group family",
        "water": "drink",
        "sun": "fire sky",
        "hot": "warm",
        "large": "big",
        "deer": "meat good",
        "complex": "hard word",
        "ensuring": "make sure",
        "finally caught": "smash big",
        "requiring": "need",
        
        # Articles/prepositions/conjunctions often removed in caveman speech
        " the ": " ",
        " a ": " ",
        " an ": " ",
        " of ": " ",
        " and ": " ",
        " is ": " ",
        " was ": " ",
        " were ": " ",
        " are ": " ",
        " but ": " ",
    }

    # Apply replacements. Sort keys by length descending to prioritize multi-word phrases.
    sorted_keys = sorted(replacements.keys(), key=len, reverse=True)
    
    for key in sorted_keys:
        normalized_text = normalized_text.replace(key, " " + replacements[key] + " ")

    # Clean up remaining punctuation and handle grammar crudely
    clean_text = normalized_text.translate(str.maketrans('', '', string.punctuation.replace('.', '')))
    
    # Condense multiple spaces and remove leading/trailing space
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    # Simple grammar fixes: Pronouns
    clean_text = clean_text.replace(" i ", " me ").replace(" we ", " me group ").replace(" my ", " me ").replace(" we will ", " me group future ")
    
    # Reassemble the summary
    summary_parts = [p for p in clean_text.split() if p] # Filter out empty strings
    
    if not summary_parts:
        return {"summary": "Ugh. Me hit head. No summary. Hah!"}

    summary_string = " ".join(summary_parts)
    
    # Final stylistic touches: capitalize and add flair
    if not summary_string.startswith("ugh"):
        final_summary = "Ugh. " + summary_string.capitalize()
    else:
        final_summary = summary_string.capitalize()
        
    # Ensure it ends forcefully
    if not final_summary.endswith("!") and not final_summary.endswith("."):
        final_summary += "."
        
    final_summary += " Hah!"
    
    return {"summary": final_summary}
