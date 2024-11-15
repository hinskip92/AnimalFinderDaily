import base64
from flask import current_app
import requests
import json
from openai import OpenAI
from typing import Dict, Any, Optional

def get_mock_tasks() -> Dict[str, list]:
    """Return mock tasks when OpenAI API key is not available"""
    return {
        "daily": [
            "Common Pigeon",
            "House Sparrow",
            "Gray Squirrel"
        ],
        "weekly": [
            "Red-tailed Hawk",
            "Great Blue Heron"
        ]
    }

def get_mock_recognition() -> Dict[str, Any]:
    """Return mock recognition when OpenAI API key is not available"""
    return {
        "animal": "Demo Animal",
        "details": {
            "habitat": "Natural habitat information",
            "diet": "Diet information", 
            "behavior": "Behavior patterns",
            "interesting_facts": ["Fact 1", "Fact 2"]
        }
    }

def generate_tasks(location_info: Dict[str, str]) -> Dict[str, list]:
    """Generate animal spotting tasks based on location"""
    api_key = current_app.config.get('OPENAI_API_KEY')
    
    if not api_key:
        return get_mock_tasks()
    
    # Ensure location info is properly encoded
    location_str = json.dumps(location_info, ensure_ascii=False)
    prompt = f"""Given the location {location_str}, suggest:
    - 3 daily animal spotting tasks (common animals)
    - 2 weekly animal spotting tasks (rarer animals)
    that would be realistic to find in this area. Return as JSON with 'daily' and 'weekly' arrays."""
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user", 
                "content": prompt.encode('utf-8').decode('utf-8')
            }],
            response_format={"type": "json_object"}
        )
        
        if not response.choices[0].message.content:
            raise ValueError("Empty response from OpenAI")
            
        try:
            return json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse OpenAI response: {str(e)}")
            return get_mock_tasks()
    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
        return get_mock_tasks()

def recognize_animal(image_path: str) -> Dict[str, Any]:
    """Recognize animal in image and provide detailed information"""
    api_key = current_app.config.get('OPENAI_API_KEY')
    
    if not api_key:
        return get_mock_recognition()
        
    try:
        # Ensure proper encoding for image data
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
        client = OpenAI(api_key=api_key)
        prompt = """Analyze this image and provide detailed information about the animal in the following JSON format:
        {
            "animal": "Name of the animal",
            "details": {
                "habitat": "Natural habitat and geographical distribution",
                "diet": "Feeding habits and typical food sources",
                "behavior": "Notable behavioral characteristics",
                "interesting_facts": ["3-4 interesting facts about the animal"]
            }
        }
        Be specific but concise. Ensure all fields are filled with accurate information.""".encode('utf-8').decode('utf-8')

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        if not response.choices[0].message.content:
            raise ValueError("Empty response from OpenAI")
            
        try:
            result = json.loads(response.choices[0].message.content)
            
            # Validate response structure
            if not isinstance(result, dict) or 'animal' not in result or 'details' not in result:
                raise ValueError("Invalid response format from OpenAI")
                
            return result
        except json.JSONDecodeError as e:
            current_app.logger.error(f"Failed to parse OpenAI response: {str(e)}")
            return get_mock_recognition()
            
    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
        return get_mock_recognition()
