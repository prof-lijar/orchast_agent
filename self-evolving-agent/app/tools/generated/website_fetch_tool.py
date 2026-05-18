import requests
import re

def website_fetch_tool(url: str) -> dict:
    """
    Fetches the content and metadata from a specified URL.

    Args:
        url (str): The URL of the website to fetch.

    Returns:
        dict: A dictionary containing the status, title, content, and metadata of the page.
    """
    result = {
        "status": "unknown",
        "title": "",
        "content": "",
        "metadata": {}
    }

    if not url:
        result["status"] = "error: empty URL provided"
        return result

    try:
        # Use a common User-Agent to avoid being blocked by some websites
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers, timeout=10)
        result["status"] = f"{response.status_code} {response.reason}"
        
        if response.status_code != 200:
            return result

        html_content = response.text

        # Extract Title
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if title_match:
            result["title"] = title_match.group(1).strip()

        # Extract Metadata
        # Matches <meta name="..." content="..."> and <meta property="..." content="...">
        meta_tags = re.findall(r'<meta\s+(?:name|property)=["\'](.*?)["\']\s+content=["\'](.*?)["\']', html_content, re.IGNORECASE)
        for key, value in meta_tags:
            result["metadata"][key] = value

        # Extract Content
        # Remove scripts and styles
        clean_text = re.sub(r'<(script|style).*?>.*?</\1>', ' ', html_content, flags=re.DOTALL | re.IGNORECASE)
        # Remove all HTML tags
        clean_text = re.sub(r'<[^>]*>', ' ', clean_text)
        # Normalize whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        result["content"] = clean_text

    except requests.exceptions.RequestException as e:
        result["status"] = f"error: {str(e)}"
    except Exception as e:
        result["status"] = f"unexpected error: {str(e)}"

    return result
