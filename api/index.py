"""
Vercel Serverless Function - AI Skill Insight Engine API

This file serves as the entrypoint for Vercel deployment.
Uses WSGI-compatible interface for Vercel Python runtime.
Includes rate limiting to prevent abuse.
"""

import json
import os
import sys
import time
import hashlib
from urllib.parse import parse_qs, urlparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetcher import fetch_content_from_url, FetcherError
from parser import parse_content, ParserError
from analyzer import analyze_skill_description, AnalyzerError
from generator import generate_markdown_report, generate_json_output, generate_html_report, GeneratorError

# Rate Limiting Configuration
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
RATE_LIMIT_MAX_REQUESTS = 100  # Max requests per hour per IP
RATE_LIMIT_HEADER = 'X-RateLimit-'

# API Key Authentication
# Optional: Set FRONTEND_API_KEY to restrict access to specific frontend only
FRONTEND_API_KEY = os.environ.get('FRONTEND_API_KEY', None)

# Simple in-memory rate limiter (for serverless, this resets per deployment)
# For production, consider using Redis or similar
rate_limit_store = {}


def get_client_ip(environ):
    """Extract client IP from WSGI environ"""
    # Check for forwarded headers (Vercel/proxy)
    forwarded_for = environ.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(',')[0].strip()
    
    # Fall back to remote address
    return environ.get('REMOTE_ADDR', 'unknown')


def get_rate_limit_key(ip):
    """Generate rate limit key from IP"""
    # Use hash to anonymize IP
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def check_rate_limit(ip):
    """
    Check if request is within rate limit.
    
    Returns:
        tuple: (allowed: bool, remaining: int, reset_time: int)
    """
    current_time = time.time()
    key = get_rate_limit_key(ip)
    
    # Clean old entries and get/create current entry
    if key in rate_limit_store:
        entry = rate_limit_store[key]
        # Remove requests outside the window
        entry['requests'] = [
            req_time for req_time in entry['requests']
            if current_time - req_time < RATE_LIMIT_WINDOW
        ]
    else:
        entry = {'requests': []}
        rate_limit_store[key] = entry
    
    # Check if limit exceeded
    request_count = len(entry['requests'])
    remaining = max(0, RATE_LIMIT_MAX_REQUESTS - request_count)
    
    # Calculate reset time (end of current window)
    if entry['requests']:
        oldest_request = min(entry['requests'])
        reset_time = int(oldest_request + RATE_LIMIT_WINDOW)
    else:
        reset_time = int(current_time + RATE_LIMIT_WINDOW)
    
    if request_count >= RATE_LIMIT_MAX_REQUESTS:
        return False, 0, reset_time
    
    # Record this request
    entry['requests'].append(current_time)
    remaining = max(0, RATE_LIMIT_MAX_REQUESTS - len(entry['requests']))
    
    return True, remaining, reset_time


def validate_api_key(environ):
    """
    Validate API key from request headers.
    
    Returns:
        tuple: (valid: bool, error_message: str or None)
    """
    # If FRONTEND_API_KEY is not set, skip validation (open access)
    if not FRONTEND_API_KEY:
        return True, None
    
    # Get API key from headers
    api_key = environ.get('HTTP_X_API_KEY', '')
    
    if not api_key:
        return False, 'Missing API key. Please provide X-API-Key header.'
    
    if api_key != FRONTEND_API_KEY:
        return False, 'Invalid API key.'
    
    return True, None


def analyze_skill_from_url(skill_url: str, output_format: str = 'markdown') -> dict:
    """
    Analyze a skill from URL.
    
    Args:
        skill_url: URL of the skill documentation
        output_format: Output format ('markdown', 'json', 'html')
    
    Returns:
        Dictionary containing the full analysis result
    """
    # Step 1: Fetch content
    try:
        fetch_result = fetch_content_from_url(skill_url)
    except FetcherError as e:
        return {'success': False, 'error': f"Fetch failed: {str(e)}"}
    
    # Step 2: Parse content
    try:
        parse_result = parse_content(fetch_result['content'], fetch_result['content_type'])
    except ParserError as e:
        return {'success': False, 'error': f"Parse failed: {str(e)}"}
    
    # Step 3: Analyze with Pollinations AI
    try:
        analysis_result = analyze_skill_description(parse_result['parsed_text'])
    except AnalyzerError as e:
        return {'success': False, 'error': f"Analysis failed: {str(e)}"}
    
    # Step 4: Generate report
    try:
        if output_format == 'json':
            report = generate_json_output(analysis_result, skill_url)
        elif output_format == 'html':
            report = generate_html_report(analysis_result, skill_url)
        else:
            report = generate_markdown_report(analysis_result, skill_url)
    except GeneratorError as e:
        return {'success': False, 'error': f"Report generation failed: {str(e)}"}
    
    return {
        'success': True,
        'analysis': analysis_result,
        'report': report,
        'metadata': {
            'source_url': skill_url,
            'output_format': output_format
        }
    }


def application(environ, start_response):
    """
    WSGI application handler for Vercel Python runtime.
    
    Args:
        environ: WSGI environment dict
        start_response: WSGI start_response callable
    
    Returns:
        List of response body bytes
    """
    # Get request method and path
    request_method = environ.get('REQUEST_METHOD', 'GET')
    path = environ.get('PATH_INFO', '/')
    query_string = environ.get('QUERY_STRING', '')
    client_ip = get_client_ip(environ)
    
    # Parse query parameters
    query_params = parse_qs(query_string)
    
    # Base headers (without rate limit headers yet)
    base_headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type, X-API-Key')
    ]
    
    # Handle preflight OPTIONS request
    if request_method == 'OPTIONS':
        start_response('200 OK', base_headers)
        return [b'']
    
    # Health check endpoint (no rate limit)
    if path == '/health':
        response_body = {
            'status': 'healthy',
            'service': 'AI Skill Insight Engine',
            'version': '1.0'
        }
        start_response('200 OK', base_headers)
        return [json.dumps(response_body).encode('utf-8')]
    
    # Rate limiting and API key validation for /analyze endpoint
    if path == '/analyze':
        # Check rate limit
        allowed, remaining, reset_time = check_rate_limit(client_ip)
        
        # Add rate limit headers to all responses
        rate_limit_headers = base_headers + [
            (f'{RATE_LIMIT_HEADER}Limit', str(RATE_LIMIT_MAX_REQUESTS)),
            (f'{RATE_LIMIT_HEADER}Remaining', str(remaining)),
            (f'{RATE_LIMIT_HEADER}Reset', str(reset_time))
        ]
        
        if not allowed:
            # Rate limit exceeded
            response_body = {
                'error': 'Rate limit exceeded',
                'message': f'Maximum {RATE_LIMIT_MAX_REQUESTS} requests per hour',
                'retry_after': reset_time - int(time.time())
            }
            start_response('429 Too Many Requests', rate_limit_headers)
            return [json.dumps(response_body).encode('utf-8')]
        
        # Validate API key (if enabled)
        api_key_valid, api_key_error = validate_api_key(environ)
        if not api_key_valid:
            response_body = {
                'error': 'Authentication failed',
                'message': api_key_error,
                'rate_limit': {
                    'limit': RATE_LIMIT_MAX_REQUESTS,
                    'remaining': remaining,
                    'reset': reset_time
                }
            }
            start_response('401 Unauthorized', rate_limit_headers)
            return [json.dumps(response_body).encode('utf-8')]
        
        if request_method == 'GET':
            # Get URL parameter
            skill_url_list = query_params.get('url', [])
            skill_url = skill_url_list[0] if skill_url_list else None
            output_format = query_params.get('format', ['markdown'])[0]
            
            if not skill_url:
                response_body = {
                    'error': 'Missing required parameter: url',
                    'usage': '/analyze?url=<skill_url>&format=<markdown|json|html>',
                    'rate_limit': {
                        'limit': RATE_LIMIT_MAX_REQUESTS,
                        'remaining': remaining,
                        'reset': reset_time
                    }
                }
                start_response('400 Bad Request', rate_limit_headers)
                return [json.dumps(response_body).encode('utf-8')]
            
            # Run analysis
            result = analyze_skill_from_url(skill_url, output_format)
            
            if result.get('success'):
                content_type = 'text/markdown' if output_format == 'markdown' else 'application/json' if output_format == 'json' else 'text/html'
                headers = [
                    ('Content-Type', content_type),
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type'),
                    (f'{RATE_LIMIT_HEADER}Limit', str(RATE_LIMIT_MAX_REQUESTS)),
                    (f'{RATE_LIMIT_HEADER}Remaining', str(remaining)),
                    (f'{RATE_LIMIT_HEADER}Reset', str(reset_time))
                ]
                start_response('200 OK', headers)
                return [result.get('report', '').encode('utf-8')]
            else:
                start_response('500 Internal Server Error', rate_limit_headers)
                return [json.dumps(result).encode('utf-8')]
        
        elif request_method == 'POST':
            # Read request body
            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                request_body = environ['wsgi.input'].read(content_length).decode('utf-8')
                data = json.loads(request_body) if request_body else {}
            except (json.JSONDecodeError, ValueError) as e:
                response_body = {
                    'error': 'Invalid JSON',
                    'rate_limit': {
                        'limit': RATE_LIMIT_MAX_REQUESTS,
                        'remaining': remaining,
                        'reset': reset_time
                    }
                }
                start_response('400 Bad Request', rate_limit_headers)
                return [json.dumps(response_body).encode('utf-8')]
            
            skill_url = data.get('url')
            output_format = data.get('format', 'markdown')
            
            if not skill_url:
                response_body = {
                    'error': 'Missing required field: url',
                    'rate_limit': {
                        'limit': RATE_LIMIT_MAX_REQUESTS,
                        'remaining': remaining,
                        'reset': reset_time
                    }
                }
                start_response('400 Bad Request', rate_limit_headers)
                return [json.dumps(response_body).encode('utf-8')]
            
            # Run analysis
            result = analyze_skill_from_url(skill_url, output_format)
            
            if result.get('success'):
                start_response('200 OK', rate_limit_headers)
                return [json.dumps(result).encode('utf-8')]
            else:
                start_response('500 Internal Server Error', rate_limit_headers)
                return [json.dumps(result).encode('utf-8')]
    
    # Default: show API usage
    response_body = {
        'service': 'AI Skill Insight Engine',
        'version': '1.0',
        'endpoints': {
            'GET /health': 'Health check',
            'GET /analyze?url=<skill_url>&format=<markdown|json|html>': 'Analyze AI skill',
            'POST /analyze': 'Analyze AI skill with JSON body {"url": "...", "format": "..."}'
        },
        'example': '/analyze?url=https://example.com/skill.md&format=markdown',
        'rate_limit': {
            'limit': RATE_LIMIT_MAX_REQUESTS,
            'window': f'{RATE_LIMIT_WINDOW} seconds (1 hour)',
            'note': 'Rate limiting is per IP address'
        }
    }
    start_response('200 OK', base_headers)
    return [json.dumps(response_body, indent=2).encode('utf-8')]


# For local testing with ASGI servers
async def asgi_app(scope, receive, send):
    """ASGI wrapper for local testing"""
    if scope['type'] == 'http':
        # Convert ASGI to WSGI-like environ
        environ = {
            'REQUEST_METHOD': scope['method'],
            'PATH_INFO': scope['path'],
            'QUERY_STRING': scope.get('query_string', '').decode(),
            'CONTENT_TYPE': scope.get('headers', []),
            'wsgi.input': scope.get('body', b''),
        }
        
        # Simple response
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [[b'content-type', b'application/json']],
        })
        await send({
            'type': 'http.response.body',
            'body': b'{"status": "ok"}',
        })
