import string
from typing import Dict, Any

def morse_code_encoder_tool(text: str) -> Dict[str, str]:
    """
    Translates an input string (A-Z, 0-9, and spaces) into its corresponding 
    standard International Morse code representation, using a slash (/) to 
    separate words.

    Args:
        text: The input string containing letters, numbers, and spaces.

    Returns:
        A dictionary containing the generated Morse code string.
        Example: {"morse_code": "...---..."}
    """
    
    MORSE_CODE_MAP = {
        'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 
        'F': '..-.', 'G': '--.', 'H': '....', 'I': '..', 'J': '.---', 
        'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 
        'P': '.--.', 'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 
        'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-', 'Y': '-.--', 
        'Z': '--..',
        '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-', 
        '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.',
        ' ': '/'
    }

    if text is None:
        text = ""

    # Convert the input text to uppercase for uniform mapping
    upper_text = text.upper()
    
    morse_code_parts = []
    
    # Standard International Morse code uses a single space to separate 
    # characters within a word, and a slash (/) to separate words.
    
    # We first replace all whitespace sequences with a single space to handle
    # multiple spaces between words, and then split by the space character.
    
    # Note: If we use the ' ' mapping directly in the loop, we might introduce
    # unnecessary complexity regarding inter-character spacing vs. inter-word spacing.
    # The specification implies character-level encoding where characters are 
    # separated by a space, and words by a slash.
    
    # Let's process word by word.
    
    # Filter out characters that are not in the map (non-alphanumeric, non-space)
    # and convert to upper case.
    cleaned_text = "".join(c for c in upper_text if c in MORSE_CODE_MAP)
    
    if not cleaned_text:
        return {"morse_code": ""}

    # Split the text into words by space, preserving the space characters.
    # A simple way to handle word separation is to iterate character by character
    # and use the '/' mapping for spaces, and a single space for inter-character gaps.
    
    morse_output = []
    for char in cleaned_text:
        if char == ' ':
            # Use the defined word separator '/'
            morse_output.append(MORSE_CODE_MAP[' '])
        else:
            # Map character and append a space for inter-character separation
            morse_output.append(MORSE_CODE_MAP[char])
            morse_output.append(' ')

    # Join the list.
    result = "".join(morse_output).strip()
    
    # Clean up excess spaces or separators potentially created at the ends or 
    # due to multiple spaces being condensed (though 'cleaned_text' handles the latter).
    
    # The spec states "using a slash (/) to separate words."
    # The convention for Morse code is:
    # 1. Elements of a character (. or -) are adjacent.
    # 2. Characters within a word are separated by a short gap (space).
    # 3. Words are separated by a longer gap (seven dot durations, often represented by /).

    # Refined Approach: Split the text by spaces, encode each word, and join with '/'

    words = text.upper().split()
    encoded_words = []

    for word in words:
        encoded_chars = []
        for char in word:
            if 'A' <= char <= 'Z' or '0' <= char <= '9':
                encoded_chars.append(MORSE_CODE_MAP[char])
            # Ignore other characters within the word
        
        if encoded_chars:
            encoded_words.append(" ".join(encoded_chars))

    final_morse_code = "/".join(encoded_words)

    return {"morse_code": final_morse_code}
