import requests
import re
import urllib.parse
from html import unescape
from typing import Dict, List


def web_search_tool(query: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Queries the web using DuckDuckGo and returns real search results
    with titles, URLs, and snippets.

    Args:
        query: The search term or phrase.

    Returns:
        A dictionary with a 'search_results' list. Each result has
        'title', 'url', and 'snippet' keys.
    """
    if not query or not isinstance(query, str) or query.strip() == "":
        return {"search_results": []}

    headers = {"User-Agent": "Mozilla/5.0 (compatible; WebSearchTool/1.0)"}
    params = {"q": query.strip()}

    try:
        resp = requests.get(
            "https://html.duckduckgo.com/html/",
            params=params,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"search_results": [], "error": f"{type(e).__name__}: {e}"}

    results: List[Dict[str, str]] = []

    link_pattern = re.compile(
        r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
        re.DOTALL,
    )
    snippet_pattern = re.compile(
        r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
        re.DOTALL,
    )

    links = link_pattern.findall(resp.text)
    snippets = snippet_pattern.findall(resp.text)

    for i, (raw_url, raw_title) in enumerate(links):
        title = unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()

        if "//duckduckgo.com/l/" in raw_url:
            parsed_qs = urllib.parse.parse_qs(
                urllib.parse.urlparse(raw_url).query
            )
            url = parsed_qs.get("uddg", [raw_url])[0]
        else:
            url = raw_url

        snippet = ""
        if i < len(snippets):
            snippet = unescape(re.sub(r"<[^>]+>", "", snippets[i])).strip()

        results.append({"title": title, "url": url, "snippet": snippet})

    return {"search_results": results}
