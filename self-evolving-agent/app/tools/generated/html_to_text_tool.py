import re
from typing import Dict, Any

def html_to_text_tool(html_content: str) -> Dict[str, str]:
    """
    Extracts the plain text content from an HTML string, removing all tags, 
    scripts, and styles.

    Args:
        html_content: The input HTML string.

    Returns:
        A dictionary containing the extracted plain text content under the 
        key 'text_content'.
    """
    if not html_content:
        return {"text_content": ""}

    # 1. Remove comments
    text = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)

    # 2. Remove script and style tags and their content
    text = re.sub(r'<script\b[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style\b[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)

    # 3. Replace block-level tags with a newline character to preserve basic structure
    # This helps separate content that was in different paragraphs or divs.
    # A heuristic list of block tags: p, div, br, h1-h6, li, blockquote, article, section, footer, header
    text = re.sub(r'</?(div|p|br|h[1-6]|li|blockquote|article|section|footer|header)\b[^>]*>', '\n', text, flags=re.IGNORECASE)

    # 4. Replace remaining tags with a space
    text = re.sub(r'<[^>]+>', ' ', text)

    # 5. Replace HTML entities (e.g., &nbsp;, &gt;)
    # A basic conversion for common entities
    text = text.replace('&nbsp;', ' ')
    text = text.replace('&amp;', '&')
    text = text.replace('&lt;', '<')
    text = text.replace('&gt;', '>')
    text = text.replace('&quot;', '"')
    text = text.replace('&apos;', "'")
    
    # Simple removal of other entities like &#xxx;
    text = re.sub(r'&#?\w+;', ' ', text)

    # 6. Normalize whitespace: replace multiple newlines/spaces with a single space or newline
    # Consolidate multiple newlines into a maximum of two (to simulate paragraph breaks)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Consolidate spaces and tabs
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Trim leading/trailing whitespace from each line and the overall result
    text = '\n'.join([line.strip() for line in text.split('\n')]).strip()
    
    return {"text_content": text}
