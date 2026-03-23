"""
Vercel Serverless Function - AI Skill Insight Engine API

This file serves as the entrypoint for Vercel deployment.
Uses WSGI-compatible interface for Vercel Python runtime.
"""

import json
import os
import sys
from urllib.parse import parse_qs, urlparse

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetcher import fetch_content_from_url, FetcherError
from parser import parse_content, ParserError
from analyzer import analyze_skill_description, AnalyzerError
from generator import generate_markdown_report, generate_json_output, generate_html_report, GeneratorError


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
    
    # Parse query parameters
    query_params = parse_qs(query_string)
    
    # CORS headers
    headers = [
        ('Content-Type', 'application/json'),
        ('Access-Control-Allow-Origin', '*'),
        ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
        ('Access-Control-Allow-Headers', 'Content-Type')
    ]
    
    # Handle preflight OPTIONS request
    if request_method == 'OPTIONS':
        start_response('200 OK', headers)
        return [b'']
    
    # Health check endpoint
    if path == '/health':
        response_body = {
            'status': 'healthy',
            'service': 'AI Skill Insight Engine',
            'version': '1.0'
        }
        start_response('200 OK', headers)
        return [json.dumps(response_body).encode('utf-8')]
    
    # Main analysis endpoint
    if path == '/analyze':
        if request_method == 'GET':
            # Get URL parameter
            skill_url_list = query_params.get('url', [])
            skill_url = skill_url_list[0] if skill_url_list else None
            output_format = query_params.get('format', ['markdown'])[0]
            
            if not skill_url:
                response_body = {
                    'error': 'Missing required parameter: url',
                    'usage': '/analyze?url=<skill_url>&format=<markdown|json|html>'
                }
                start_response('400 Bad Request', headers)
                return [json.dumps(response_body).encode('utf-8')]
            
            # Run analysis
            result = analyze_skill_from_url(skill_url, output_format)
            
            if result.get('success'):
                content_type = 'text/markdown' if output_format == 'markdown' else 'application/json' if output_format == 'json' else 'text/html'
                headers = [
                    ('Content-Type', content_type),
                    ('Access-Control-Allow-Origin', '*'),
                    ('Access-Control-Allow-Methods', 'GET, POST, OPTIONS'),
                    ('Access-Control-Allow-Headers', 'Content-Type')
                ]
                start_response('200 OK', headers)
                return [result.get('report', '').encode('utf-8')]
            else:
                start_response('500 Internal Server Error', headers)
                return [json.dumps(result).encode('utf-8')]
        
        elif request_method == 'POST':
            # Read request body
            try:
                content_length = int(environ.get('CONTENT_LENGTH', 0))
                request_body = environ['wsgi.input'].read(content_length).decode('utf-8')
                data = json.loads(request_body) if request_body else {}
            except (json.JSONDecodeError, ValueError) as e:
                response_body = {'error': 'Invalid JSON'}
                start_response('400 Bad Request', headers)
                return [json.dumps(response_body).encode('utf-8')]
            
            skill_url = data.get('url')
            output_format = data.get('format', 'markdown')
            
            if not skill_url:
                response_body = {'error': 'Missing required field: url'}
                start_response('400 Bad Request', headers)
                return [json.dumps(response_body).encode('utf-8')]
            
            # Run analysis
            result = analyze_skill_from_url(skill_url, output_format)
            
            if result.get('success'):
                start_response('200 OK', headers)
                return [json.dumps(result).encode('utf-8')]
            else:
                start_response('500 Internal Server Error', headers)
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
        'example': '/analyze?url=https://example.com/skill.md&format=markdown'
    }
    start_response('200 OK', headers)
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
