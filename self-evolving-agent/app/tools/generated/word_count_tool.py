def word_count_tool(text: str) -> dict:
    """
    Counts the number of words in a text string.

    Words are determined by splitting the string based on any sequence of
    whitespace characters (spaces, tabs, newlines).

    Args:
        text: The text string to analyze.

    Returns:
        A dictionary containing the word count.
        Example: {"word_count": 5}
    """
    # Using str.split() without arguments handles multiple spaces,
    # leading/trailing spaces, and different types of whitespace
    # (spaces, tabs, newlines) correctly, returning a list of words.
    words = text.split()
    count = len(words)

    return {
        "word_count": count
    }
