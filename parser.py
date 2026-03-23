"""
Parser Module - Cleans and extracts text from fetched content

This module handles parsing HTML, Markdown, and plain text
to extract clean, analyzable content.
"""

from typing import Dict, Any, Optional
from bs4 import BeautifulSoup


class ParserError(Exception):
    """Custom exception for parser errors"""
    pass


def parse_content(content: str, content_type: str = 'text/html') -> Dict[str, Any]:
    """
    Parse and clean content based on its type.
    
    Args:
        content: Raw content string
        content_type: MIME type of the content (e.g., 'text/html', 'text/markdown')
    
    Returns:
        Dictionary containing:
        - success: bool
        - parsed_text: str (cleaned text)
        - metadata: dict (optional metadata extracted)
        - error: str (if any error occurred)
    """
    if not content:
        raise ParserError("Content cannot be empty")
    
    try:
        if 'html' in content_type:
            parsed_text = _parse_html(content)
        elif 'markdown' in content_type or 'md' in content_type:
            parsed_text = _parse_markdown(content)
        else:
            # Plain text - just clean whitespace
            parsed_text = _clean_text(content)
        
        # Extract basic metadata
        metadata = {
            'char_count': len(parsed_text),
            'word_count': len(parsed_text.split()),
            'line_count': len(parsed_text.splitlines())
        }
        
        return {
            'success': True,
            'parsed_text': parsed_text,
            'metadata': metadata
        }
    
    except Exception as e:
        raise ParserError(f"Parsing failed: {str(e)}")


def _parse_html(html_content: str) -> str:
    """
    Parse HTML content and extract readable text.
    
    Args:
        html_content: Raw HTML string
    
    Returns:
        Cleaned text content
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Remove script and style elements
    for script in soup(['script', 'style', 'nav', 'header', 'footer']):
        script.decompose()
    
    # Get text
    text = soup.get_text(separator=' ', strip=True)
    
    return _clean_text(text)


def _parse_markdown(markdown_content: str) -> str:
    """
    Parse Markdown content (basic cleaning).
    
    Args:
        markdown_content: Raw Markdown string
    
    Returns:
        Cleaned text content
    """
    # For now, just clean the text
    # Could use a markdown parser library for more advanced parsing
    return _clean_text(markdown_content)


def _clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Raw text string
    
    Returns:
        Cleaned text with normalized whitespace
    """
    # Replace multiple whitespace with single space
    import re
    text = re.sub(r'\s+', ' ', text)
    
    # Remove common artifacts
    text = text.replace('\\n', ' ').replace('\\t', ' ')
    
    # Strip leading/trailing whitespace
    return text.strip()


def extract_code_blocks(content: str) -> list:
    """
    Extract code blocks from content (useful for skill examples).
    
    Args:
        content: Parsed text content
    
    Returns:
        List of code blocks found
    """
    import re
    # Match markdown code blocks
    code_blocks = re.findall(r'```(?:\w+)?\n(.*?)```', content, re.DOTALL)
    return code_blocks


def extract_urls(content: str) -> list:
    """
    Extract URLs from content.
    
    Args:
        content: Text content
    
    Returns:
        List of URLs found
    """
    import re
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    return re.findall(url_pattern, content)


if __name__ == "__main__":
    # Test the parser
    test_html = "<html><body><h1>Test</h1><p>Hello World!</p></body></html>"
    result = parse_content(test_html, 'text/html')
    print(f"Parsed text: {result['parsed_text']}")
    print(f"Metadata: {result['metadata']}")
