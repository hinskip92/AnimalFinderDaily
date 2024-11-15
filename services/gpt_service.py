import base64
from flask import current_app
import requests

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
    return "This is a demo response. In live mode, GPT-4 Vision would analyze your image and identify the animal."

def generate_tasks(location_info):
    api_key = current_app.config.get('OPENAI_API_KEY')
    
    if not api_key:
        return get_mock_tasks()
        
    prompt = f"""Given the location {location_info}, suggest:
    - 3 daily animal spotting tasks (common animals)
    - 2 weekly animal spotting tasks (rarer animals)
    that would be realistic to find in this area. Return as JSON."""
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }
        )
        return response.json()["choices"][0]["message"]["content"]
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
            
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "What animal is in this image?"},
                            {"type": "image_url", "image_url": f"data:image/jpeg;base64,{base64_image}"}
                        ]
                    }
                ]
            }
        )
        
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI API: {str(e)}")
        return get_mock_recognition()
