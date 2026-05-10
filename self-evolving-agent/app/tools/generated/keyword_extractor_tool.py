import re
import string
from collections import Counter
from typing import List, Dict

def keyword_extractor_tool(text: str) -> Dict[str, List[str]]:
    """
    Extracts relevant keywords from a block of text by normalizing and tokenizing the input.

    This function processes the input text by converting it to lowercase, removing punctuation,
    filtering out common English stopwords, and returning the top 10 most frequent remaining
    unique words as keywords.

    Args:
        text: The input text block from which to extract keywords.

    Returns:
        A dictionary containing the extracted keywords.
        Example: {"keywords": ["word1", "word2"]}
    """
    if not isinstance(text, str) or not text:
        return {"keywords": []}

    # Define a basic set of common English stopwords
    STOPWORDS = set([
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'and', 'or', 'but', 'in', 'on', 'at',
        'for', 'with', 'by', 'of', 'to', 'from', 'as', 'it', 'its', 'he', 'she', 'they',
        'we', 'you', 'i', 'me', 'my', 'your', 'this', 'that', 'these', 'those', 'be', 'has',
        'had', 'do', 'does', 'did', 'not', 'can', 'will', 'just', 'so', 'up', 'down', 'out',
        'about', 'all', 'any', 'most', 'other', 'some', 'such', 'no', 'only', 'own', 'very',
        'than', 'then', 'when', 'where', 'why', 'how', 'if', 'what', 'which', 'who'
    ])

    # 1. Normalize and Clean Text
    text_lower = text.lower()

    # Remove punctuation by replacing it with spaces
    translator = str.maketrans(string.punctuation, ' ' * len(string.punctuation))
    text_cleaned = text_lower.translate(translator)

    # 2. Tokenize using regex to find sequences of alphanumeric characters
    tokens = re.findall(r'\b\w+\b', text_cleaned)

    # 3. Filter and Count
    filtered_tokens = []
    for token in tokens:
        # Filter out stopwords and tokens that are too short (usually noise, unless in stoplist)
        if token and token not in STOPWORDS and len(token) > 1:
            filtered_tokens.append(token)

    word_counts = Counter(filtered_tokens)

    # 4. Select Top Keywords
    # Select the top 10 most common unique words
    top_items = word_counts.most_common(10)
    keywords = [item[0] for item in top_items]

    return {"keywords": keywords}
