import re
from typing import Dict, Any

def first_n_sentence_summary_tool(text: str, num_sentences: int) -> Dict[str, str]:
    """
    Extracts the first N sentences from an input text using simple sentence 
    boundary detection based on common punctuation (. ! ?).

    Args:
        text (str): The input text to summarize.
        num_sentences (int): The number of sentences (N) to extract.

    Returns:
        Dict[str, str]: A dictionary containing the extracted summary 
                        under the key 'summary'.
    """
    # Handle empty or invalid inputs
    if not text or num_sentences <= 0:
        return {"summary": ""}

    # Strip leading/trailing whitespace from the entire text
    text = text.strip()
    
    if not text:
        return {"summary": ""}

    # Use regex to split the text into sentences.
    # The pattern splits on one or more whitespace characters that immediately 
    # follow a sentence-ending punctuation mark (period, exclamation, question mark).
    # The lookbehind assertion (?<=[.?!]) ensures the punctuation is kept with the sentence.
    sentences = re.split(r'(?<=[.?!])\s+', text)

    # Clean up and filter out potential empty strings resulting from the split
    sentences = [s.strip() for s in sentences if s.strip()]

    # Extract the first N sentences
    selected_sentences = sentences[:num_sentences]

    # Join the selected sentences back into a single string, separated by a space
    summary = " ".join(selected_sentences)

    return {"summary": summary}
