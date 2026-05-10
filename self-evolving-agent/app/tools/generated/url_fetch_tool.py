import requests
from typing import Dict

def url_fetch_tool(url: str) -> Dict[str, str]:
    """
    Fetches the text content of a specified URL using an HTTP GET request.

    Args:
        url: The URL to fetch content from.

    Returns:
        A dictionary containing the fetched content or an error message.
        The key is 'content'.
    """
    # Input validation: check for string type and non-empty content after stripping whitespace
    if not isinstance(url, str) or not url.strip():
        return {"content": "Error: URL input cannot be empty or invalid."}

    # Set request parameters for safety and compatibility
    headers = {
        # Identify the tool for server administrators
        'User-Agent': 'Mozilla/5.0 (compatible; URLFetchTool/1.0)'
    }
    timeout = 10  # seconds timeout

    try:
        # Perform the HTTP GET request
        response = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        
        # Raise an exception for bad status codes (4xx or 5xx)
        response.raise_for_status()

        # Return the text content of the response
        return {"content": response.text}

    except requests.exceptions.RequestException as e:
        # Handle all request-related errors (ConnectionError, Timeout, HTTPError, etc.)
        # Provide detailed error information including the type of exception
        error_type = type(e).__name__
        return {"content": f"Error fetching URL '{url}': {error_type} - {e}"}
    except Exception as e:
        # Catch unexpected errors
        error_type = type(e).__name__
        return {"content": f"An unexpected error occurred: {error_type} - {e}"}
