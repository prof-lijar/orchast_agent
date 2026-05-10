import re


def word_count_tool(text: str) -> dict:
    """Count the number of words in a text string.

    Args:
        text: The text to count words in.

    Returns:
        A dict with word_count (integer).
    """
    words = re.findall(r"\b\w+\b", text)
    return {"word_count": len(words)}
