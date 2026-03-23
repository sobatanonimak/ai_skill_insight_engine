"""
AI Skill Insight Engine - Main Application

This application analyzes AI skill descriptions using Pollinations AI
and provides structured insights including summaries, functionalities,
use cases, and improvement suggestions.

Usage:
    python app.py <skill_url> [--output <output_file>] [--format <markdown|json|html>]
"""

import sys
import os
import argparse
from typing import Optional

# Import local modules
from fetcher import fetch_content_from_url, FetcherError
from parser import parse_content, ParserError
from analyzer import analyze_skill_description, AnalyzerError
from generator import (
    generate_markdown_report,
    generate_json_output,
    generate_html_report,
    GeneratorError
)


def analyze_skill_from_url(
    skill_url: str,
    output_file: Optional[str] = None,
    output_format: str = 'markdown'
) -> dict:
    """
    Main function to analyze a skill from URL.
    
    Args:
        skill_url: URL of the skill documentation
        output_file: Optional file path to save the report
        output_format: Output format ('markdown', 'json', 'html')
    
    Returns:
        Dictionary containing the full analysis result
    """
    print(f"🔍 Analyzing skill from: {skill_url}")
    print("-" * 50)
    
    # Step 1: Fetch content
    print("📥 Fetching content...")
    try:
        fetch_result = fetch_content_from_url(skill_url)
        print(f"✓ Successfully fetched {len(fetch_result['content'])} characters")
    except FetcherError as e:
        print(f"✗ Fetch error: {e}")
        return {'success': False, 'error': f"Fetch failed: {str(e)}"}
    
    # Step 2: Parse content
    print("📄 Parsing content...")
    try:
        parse_result = parse_content(
            fetch_result['content'],
            fetch_result['content_type']
        )
        print(f"✓ Parsed text: {parse_result['metadata']['word_count']} words")
    except ParserError as e:
        print(f"✗ Parse error: {e}")
        return {'success': False, 'error': f"Parse failed: {str(e)}"}
    
    # Step 3: Analyze with Pollinations AI
    print("🤖 Analyzing with Pollinations AI...")
    try:
        analysis_result = analyze_skill_description(parse_result['parsed_text'])
        print(f"✓ Analysis complete (Model: {analysis_result.get('model_used', 'Unknown')})")
        if 'tokens_used' in analysis_result:
            tokens = analysis_result['tokens_used']
            print(f"  Tokens used: {tokens.get('total_tokens', 'N/A')}")
    except AnalyzerError as e:
        print(f"✗ Analysis error: {e}")
        return {'success': False, 'error': f"Analysis failed: {str(e)}"}
    
    # Step 4: Generate report
    print("📝 Generating report...")
    try:
        if output_format == 'json':
            report = generate_json_output(analysis_result, skill_url)
        elif output_format == 'html':
            report = generate_html_report(analysis_result, skill_url)
        else:
            report = generate_markdown_report(analysis_result, skill_url)
        
        print(f"✓ Report generated ({len(report)} characters)")
    except GeneratorError as e:
        print(f"✗ Generation error: {e}")
        return {'success': False, 'error': f"Report generation failed: {str(e)}"}
    
    # Step 5: Save or display report
    if output_file:
        print(f"💾 Saving to: {output_file}")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"✓ Report saved successfully")
        except IOError as e:
            print(f"✗ Save error: {e}")
            return {'success': False, 'error': f"Save failed: {str(e)}"}
    else:
        print("\n" + "=" * 50)
        print("REPORT PREVIEW:")
        print("=" * 50)
        print(report[:2000])  # Preview first 2000 characters
        if len(report) > 2000:
            print(f"\n... ({len(report) - 2000} more characters)")
    
    print("\n" + "=" * 50)
    print("✅ Analysis complete!")
    print("=" * 50)
    
    # Return full result
    return {
        'success': True,
        'analysis': analysis_result,
        'report': report,
        'metadata': {
            'source_url': skill_url,
            'output_file': output_file,
            'output_format': output_format
        }
    }


def main():
    """Main entry point for CLI"""
    parser = argparse.ArgumentParser(
        description='AI Skill Insight Engine - Analyze AI skills using Pollinations AI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app.py https://example.com/skill.md
  python app.py https://example.com/skill.md --output report.md
  python app.py https://example.com/skill.md --output report.json --format json
  python app.py https://example.com/skill.md --output report.html --format html
        """
    )
    
    parser.add_argument(
        'skill_url',
        help='URL of the AI skill documentation to analyze'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Output file path (default: display in terminal)'
    )
    
    parser.add_argument(
        '--format', '-f',
        choices=['markdown', 'json', 'html'],
        default='markdown',
        help='Output format (default: markdown)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Run analysis
    result = analyze_skill_from_url(
        args.skill_url,
        args.output,
        args.format
    )
    
    # Exit with appropriate code
    sys.exit(0 if result.get('success') else 1)


if __name__ == "__main__":
    main()
