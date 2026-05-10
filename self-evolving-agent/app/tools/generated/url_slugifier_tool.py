import re
from typing import Dict

def url_slugifier_tool(text: str) -> Dict[str, str]:
    """
    Converts a text string into a URL-safe, lowercase, hyphenated slug.

    The process involves:
    1. Converting the string to lowercase.
    2. Replacing non-alphanumeric characters (excluding spaces) with a single space.
    3. Replacing sequences of spaces with a single hyphen.
    4. Stripping leading and trailing hyphens.

    Args:
        text: The input string to be converted into a slug.

    Returns:
        A dictionary containing the resulting slug.
        Example: {"slug": "my-awesome-blog-post-title"}
    """
    if not isinstance(text, str):
        text = ""

    # 1. Convert to lowercase
    text = text.lower()

    # 2. Replace unwanted characters (not a-z, 0-9, or whitespace) with a space.
    # This removes punctuation and symbols, ensuring only space separates words/numbers.
    cleaned_text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # 3. Replace sequences of whitespace with a single hyphen.
    # We use re.sub for this to handle multiple spaces collapsed into one hyphen.
    slug = re.sub(r'\s+', '-', cleaned_text)

    # 4. Strip leading/trailing hyphens which might result from step 3 if the input 
    # started or ended with spaces or punctuation.
    slug = slug.strip('-')
    
    return {"slug": slug}
