"""
Vercel Serverless Function - AI Skill Insight Engine API

This file serves as the entrypoint for Vercel deployment.
It exposes the AI skill analysis as an HTTP API endpoint.
"""

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import core modules
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetcher import fetch_content_from_url, FetcherError
from parser import parse_content, ParserError
from analyzer import analyze_skill_description, AnalyzerError
from generator import generate_markdown_report, generate_json_output, generate_html_report, GeneratorError


class APIHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for AI Skill Insight Engine API"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # Health check endpoint
        if parsed_path.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {'status': 'healthy', 'service': 'AI Skill Insight Engine'}
            self.wfile.write(json.dumps(response).encode())
            return
        
        # Main analysis endpoint
        if parsed_path.path == '/analyze':
            query_params = parse_qs(parsed_path.query)
            
            # Get URL parameter
            skill_url = query_params.get('url', [None])[0]
            output_format = query_params.get('format', ['markdown'])[0]
            
            if not skill_url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error = {'error': 'Missing required parameter: url'}
                self.wfile.write(json.dumps(error).encode())
                return
            
            # Run analysis
            try:
                result = analyze_skill_from_url(skill_url, output_format)
                
                if result.get('success'):
                    self.send_response(200)
                    content_type = 'text/markdown' if output_format == 'markdown' else 'application/json' if output_format == 'json' else 'text/html'
                    self.send_header('Content-Type', content_type)
                    self.end_headers()
                    self.wfile.write(result.get('report', '').encode())
                else:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
            
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error = {'error': str(e)}
                self.wfile.write(json.dumps(error).encode())
                return
        
        # Default: show usage
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        usage = {
            'service': 'AI Skill Insight Engine',
            'version': '1.0',
            'endpoints': {
                '/health': 'GET - Health check',
                '/analyze?url=<skill_url>&format=<markdown|json|html>': 'GET - Analyze AI skill'
            },
            'example': '/analyze?url=https://example.com/skill.md&format=markdown'
        }
        self.wfile.write(json.dumps(usage, indent=2).encode())
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/analyze':
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            
            try:
                data = json.loads(body)
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error = {'error': 'Invalid JSON'}
                self.wfile.write(json.dumps(error).encode())
                return
            
            skill_url = data.get('url')
            output_format = data.get('format', 'markdown')
            
            if not skill_url:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error = {'error': 'Missing required field: url'}
                self.wfile.write(json.dumps(error).encode())
                return
            
            # Run analysis
            try:
                result = analyze_skill_from_url(skill_url, output_format)
                
                if result.get('success'):
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
                else:
                    self.send_response(500)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode())
            
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error = {'error': str(e)}
                self.wfile.write(json.dumps(error).encode())
                return
        
        # Default
        self.send_response(404)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        error = {'error': 'Not found'}
        self.wfile.write(json.dumps(error).encode())
    
    def log_message(self, format, *args):
        """Override to suppress default logging"""
        pass


def analyze_skill_from_url(skill_url: str, output_format: str = 'markdown') -> dict:
    """
    Analyze a skill from URL (same logic as app.py but returns dict).
    
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


# Vercel serverless function handler
def handler(request):
    """Vercel serverless function entrypoint"""
    return APIHandler


# For local testing
if __name__ == "__main__":
    from http.server import HTTPServer
    server = HTTPServer(('localhost', 8000), APIHandler)
    print("Server running at http://localhost:8000")
    server.serve_forever()
