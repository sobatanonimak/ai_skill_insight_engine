"""
Vercel Serverless Function - AI Skill Insight Engine API

This file serves as the entrypoint for Vercel deployment.
It exposes the AI skill analysis as an HTTP API endpoint.
"""

import json
import os
import sys

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
    
    # Return full result
    return {
        'success': True,
        'analysis': analysis_result,
        'report': report,
        'metadata': {
            'source_url': skill_url,
            'output_format': output_format
        }
    }


def main(request):
    """
    Vercel Python serverless function handler.
    
    Args:
        request: Vercel request object with method, headers, query, body, etc.
    
    Returns:
        Response dict with statusCode, headers, and body
    """
    # CORS headers
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }
    
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }
    
    # Parse query parameters
    query_params = request.query or {}
    path = request.path or '/'
    
    # Health check endpoint
    if path == '/health':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'status': 'healthy',
                'service': 'AI Skill Insight Engine',
                'version': '1.0'
            })
        }
    
    # Main analysis endpoint
    if path == '/analyze':
        # Handle GET request
        if request.method == 'GET':
            skill_url = query_params.get('url', [None])[0] if isinstance(query_params.get('url'), list) else query_params.get('url')
            output_format = query_params.get('format', ['markdown'])[0] if isinstance(query_params.get('format'), list) else query_params.get('format', 'markdown')
            
            if not skill_url:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing required parameter: url', 'usage': '/analyze?url=<skill_url>&format=<markdown|json|html>'})
                }
            
            # Run analysis
            result = analyze_skill_from_url(skill_url, output_format or 'markdown')
            
            if result.get('success'):
                content_type = 'text/markdown' if output_format == 'markdown' else 'application/json' if output_format == 'json' else 'text/html'
                return {
                    'statusCode': 200,
                    'headers': {**headers, 'Content-Type': content_type},
                    'body': result.get('report', '')
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps(result)
                }
        
        # Handle POST request
        elif request.method == 'POST':
            try:
                # Parse JSON body
                body = json.loads(request.body) if request.body else {}
            except json.JSONDecodeError:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Invalid JSON'})
                }
            
            skill_url = body.get('url')
            output_format = body.get('format', 'markdown')
            
            if not skill_url:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Missing required field: url'})
                }
            
            # Run analysis
            result = analyze_skill_from_url(skill_url, output_format)
            
            if result.get('success'):
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps(result)
                }
            else:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps(result)
                }
    
    # Default: show API usage
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps({
            'service': 'AI Skill Insight Engine',
            'version': '1.0',
            'endpoints': {
                'GET /health': 'Health check',
                'GET /analyze?url=<skill_url>&format=<markdown|json|html>': 'Analyze AI skill',
                'POST /analyze': 'Analyze AI skill with JSON body {"url": "...", "format": "..."}'
            },
            'example': '/analyze?url=https://example.com/skill.md&format=markdown'
        }, indent=2)
    }


# Export handler for Vercel
app = main
