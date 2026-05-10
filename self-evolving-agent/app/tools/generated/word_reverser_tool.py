def word_reverser_tool(text: str) -> dict:
    """
    Reverses the order of words in an input string, preserving the spelling
    of individual words.

    Args:
        text: The input string whose words are to be reversed.

    Returns:
        A dictionary containing the reversed string under the key 'reversed_text'.
        Returns an empty string for empty or non-string input.
    """
    if text is None or not isinstance(text, str):
        text = ""

    # Use str.split() without arguments to split by any sequence of whitespace
    # and correctly handle leading/trailing/multiple spaces.
    words = text.split()

    # Reverse the order of the word list.
    words.reverse()

    # Join the words back together with a single space separator.
    reversed_text = " ".join(words)

    return {
        "reversed_text": reversed_text
    }
