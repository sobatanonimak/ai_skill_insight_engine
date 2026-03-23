"""
Analyzer Module - Analyzes AI skill descriptions using Pollinations AI API

This module integrates with Pollinations AI to analyze skill descriptions,
extract key information, and provide insights.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AnalyzerError(Exception):
    """Custom exception for analyzer errors"""
    pass


# Pollinations API Configuration
POLLINATIONS_API_KEY = os.getenv('POLLINATION_API_KEY', '')
POLLINATIONS_MODEL = os.getenv('POLLINATION_MODEL', 'pollinations/gemini-search')
POLLINATIONS_API_URL = "https://text.pollinations.ai/openai"


def analyze_skill_description(skill_text: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze an AI skill description using Pollinations AI.
    
    Args:
        skill_text: The skill description text to analyze
        custom_prompt: Optional custom prompt (uses default if not provided)
    
    Returns:
        Dictionary containing analysis results:
        - summary: str
        - functionalities: list
        - use_cases: list
        - improvement_suggestions: list
        - raw_response: str (full API response)
        - error: str (if any error occurred)
    """
    if not skill_text:
        raise AnalyzerError("Skill text cannot be empty")
    
    if not POLLINATIONS_API_KEY:
        raise AnalyzerError("Pollinations API key not configured. Set POLLINATION_API_KEY environment variable.")
    
    # Default prompt for skill analysis
    default_prompt = """You are an AI Skill Analysis Expert. Analyze the following AI skill description carefully.

Your task is to provide a structured analysis with the following sections:

1. **Summary**: A concise 2-3 sentence overview of the skill's main purpose.
2. **Key Functionalities**: List 3-5 primary capabilities or actions of this skill.
3. **Potential Use Cases**: List 3-5 practical scenarios where this skill could be applied.
4. **Improvement Suggestions**: Provide 2-3 actionable suggestions for enhancing this skill or integrating it with other tools.

Format your response as a valid JSON object with these exact keys:
- "summary" (string)
- "functionalities" (array of strings)
- "use_cases" (array of strings)
- "improvement_suggestions" (array of strings)

AI Skill Description to Analyze:
'''
{skill_text}
'''

Respond ONLY with the JSON object, no additional text."""

    prompt = custom_prompt or default_prompt
    prompt = prompt.format(skill_text=skill_text[:15000])  # Limit text to avoid token limits
    
    try:
        # Prepare API request
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {POLLINATIONS_API_KEY}'
        }
        
        payload = {
            'model': POLLINATIONS_MODEL,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are an expert AI skill analyst. Respond with structured JSON only.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,  # Lower temperature for more consistent output
            'max_tokens': 2000
        }
        
        # Make API request
        response = requests.post(POLLINATIONS_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        # Parse response
        api_response = response.json()
        
        # Extract content from response
        if 'choices' in api_response and len(api_response['choices']) > 0:
            content = api_response['choices'][0]['message']['content']
            
            # Try to parse as JSON
            try:
                # Remove markdown code blocks if present
                content = content.replace('```json', '').replace('```', '').strip()
                analysis_result = json.loads(content)
                
                return {
                    'success': True,
                    'summary': analysis_result.get('summary', 'No summary available'),
                    'functionalities': analysis_result.get('functionalities', []),
                    'use_cases': analysis_result.get('use_cases', []),
                    'improvement_suggestions': analysis_result.get('improvement_suggestions', []),
                    'raw_response': content,
                    'model_used': POLLINATIONS_MODEL,
                    'tokens_used': api_response.get('usage', {})
                }
            
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw text
                return {
                    'success': True,
                    'summary': 'Analysis completed (JSON parsing failed, see raw_response)',
                    'functionalities': [],
                    'use_cases': [],
                    'improvement_suggestions': [],
                    'raw_response': content,
                    'model_used': POLLINATIONS_MODEL,
                    'tokens_used': api_response.get('usage', {})
                }
        else:
            raise AnalyzerError(f"Unexpected API response format: {api_response}")
    
    except requests.exceptions.Timeout:
        raise AnalyzerError("API request timed out")
    except requests.exceptions.ConnectionError as e:
        raise AnalyzerError(f"Connection error: {str(e)}")
    except requests.exceptions.HTTPError as e:
        raise AnalyzerError(f"API error {response.status_code}: {str(e)}")
    except Exception as e:
        raise AnalyzerError(f"Analysis failed: {str(e)}")


def get_available_models() -> list:
    """
    Get list of available Pollinations models.
    
    Returns:
        List of available model names
    """
    # Common Pollinations models
    return [
        'pollinations/gemini-search',
        'pollinations/kimi',
        'pollinations/deepseek',
        'pollinations/glm',
        'pollinations/claude-haiku',
        'pollinations/openai'
    ]


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for a given text.
    
    Args:
        text: Input text
    
    Returns:
        Estimated token count
    """
    # Rough estimation: ~4 characters per token
    return len(text) // 4


if __name__ == "__main__":
    # Test the analyzer
    test_skill = """
    This is a weather skill that fetches current weather data and forecasts.
    It supports multiple locations and provides temperature, humidity, and wind information.
    Users can get hourly and daily forecasts.
    """
    
    if POLLINATIONS_API_KEY:
        try:
            result = analyze_skill_description(test_skill)
            print(f"Analysis successful!")
            print(f"Summary: {result['summary']}")
            print(f"Functionalities: {result['functionalities']}")
        except AnalyzerError as e:
            print(f"Error: {e}")
    else:
        print("No API key configured. Set POLLINATION_API_KEY environment variable.")
