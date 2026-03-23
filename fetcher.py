"""
Fetcher Module - Retrieves content from URLs

This module handles fetching content from web URLs, particularly
AI skill documentation pages.
"""

import requests
from typing import Optional, Dict, Any


class FetcherError(Exception):
    """Custom exception for fetcher errors"""
    pass


def fetch_content_from_url(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Fetch content from a given URL.
    
    Args:
        url: The URL to fetch content from
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Dictionary containing:
        - success: bool
        - content: str (the fetched content)
        - content_type: str (e.g., 'text/html', 'text/markdown')
        - error: str (if any error occurred)
    
    Raises:
        FetcherError: If the URL is invalid or fetching fails
    """
    if not url:
        raise FetcherError("URL cannot be empty")
    
    if not url.startswith(('http://', 'https://')):
        raise FetcherError("URL must start with http:// or https://")
    
    headers = {
        'User-Agent': 'AI Skill Insight Engine/1.0 (compatible; Pollinations AI App)',
        'Accept': 'text/html,application/xhtml+xml,application/xml,text/plain,*/*'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        content_type = response.headers.get('Content-Type', 'text/plain').split(';')[0].strip()
        
        return {
            'success': True,
            'content': response.text,
            'content_type': content_type,
            'url': url,
            'status_code': response.status_code
        }
    
    except requests.exceptions.Timeout:
        raise FetcherError(f"Request timed out after {timeout} seconds")
    except requests.exceptions.ConnectionError as e:
        raise FetcherError(f"Connection error: {str(e)}")
    except requests.exceptions.HTTPError as e:
        raise FetcherError(f"HTTP error {response.status_code}: {str(e)}")
    except requests.exceptions.RequestException as e:
        raise FetcherError(f"Request failed: {str(e)}")


def fetch_from_multiple_sources(urls: list) -> list:
    """
    Fetch content from multiple URLs.
    
    Args:
        urls: List of URLs to fetch
    
    Returns:
        List of fetch results (success or error for each URL)
    """
    results = []
    for url in urls:
        try:
            result = fetch_content_from_url(url)
            results.append(result)
        except FetcherError as e:
            results.append({
                'success': False,
                'url': url,
                'error': str(e)
            })
    return results


if __name__ == "__main__":
    # Test the fetcher
    test_url = "https://www.moltbook.com/skill.md"
    try:
        result = fetch_content_from_url(test_url)
        print(f"Successfully fetched {len(result['content'])} characters from {test_url}")
        print(f"Content type: {result['content_type']}")
    except FetcherError as e:
        print(f"Error: {e}")
