import base64
from flask import current_app
import requests
import json
from openai import OpenAI

def get_mock_tasks():
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

def get_mock_recognition():
    """Return mock recognition when OpenAI API key is not available"""
    return {
        "animal": "Demo Animal",
        "details": {
            "habitat": "Demo habitat information",
            "diet": "Demo diet information",
            "behavior": "Demo behavior information",
            "interesting_facts": ["Demo fact 1", "Demo fact 2"]
        }
    }

def generate_tasks(location_info):
    api_key = current_app.config.get('OPENAI_API_KEY')
    
    if not api_key:
        return get_mock_tasks()
        
    prompt = f"""Given the location {location_info}, suggest:
    - 3 daily animal spotting tasks (common animals)
    - 2 weekly animal spotting tasks (rarer animals)
    that would be realistic to find in this area. Return as JSON."""
    
    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI API: {str(e)}")
        return get_mock_tasks()

def recognize_animal(image_path):
    api_key = current_app.config.get('OPENAI_API_KEY')
    
    if not api_key:
        return get_mock_recognition()
        
    try:
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
        Be specific but concise. Ensure all fields are filled with accurate information."""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
                    ]
                }
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI API: {str(e)}")
        return get_mock_recognition()
