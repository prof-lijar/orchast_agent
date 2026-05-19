import requests
import httpx
import re

def web_search_content_tool(query: str, url: str) -> dict[str, str]:
    """Performs web searches for a given query or extracts rich text content from a provided URL.

    Args:
        query (str): The search query to perform a web search.
        url (str): The URL to extract content from.

    Returns:
        dict[str, str]: A dictionary containing 'search_results' and 'page_content'.
    """
    search_results = ""
    page_content = ""

    # Handle Web Search
    if query and query.strip():
        try:
            # DuckDuckGo HTML endpoint does not require an API key
            search_url = "https://html.duckduckgo.com/html/"
            params = {"q": query}
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(search_url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            html = response.text

            # Basic regex parsing for DuckDuckGo results
            # Matches the result blocks: <a class="result__a" href="...">Title</a> and snippets
            links = re.findall(r'<a class="result__a" href="([^"]+)"', html)
            titles = re.findall(r'<a class="result__a"[^>]*>([^<]+)</a>', html)
            snippets = re.findall(r'<a class="result__snippet">([^<]+)</a>', html)

            results_list = []
            for i in range(min(len(links), len(titles), len(snippets))):
                results_list.append(f"Title: {titles[i].strip()}\nURL: {links[i]}\nSnippet: {snippets[i].strip()}\n")
            
            search_results = "\n".join(results_list) if results_list else "No search results found."
        except Exception as e:
            search_results = f"An error occurred during search: {str(e)}"

    # Handle URL Content Extraction
    if url and url.strip():
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            # Using httpx for content extraction as per dependencies
            with httpx.Client(headers=headers, timeout=10, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()
                html = response.text

            # Clean HTML to extract rich text
            # 1. Remove script and style elements
            html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
            # 2. Remove all remaining HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            # 3. Normalize whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            page_content = text if text else "No readable content found on the page."
        except Exception as e:
            page_content = f"An error occurred while fetching URL content: {str(e)}"

    return {
        "search_results": search_results,
        "page_content": page_content
    }
