import base64
from flask import current_app
import requests

def generate_tasks(location_info):
    prompt = f"""Given the location {location_info}, suggest:
    - 3 daily animal spotting tasks (common animals)
    - 2 weekly animal spotting tasks (rarer animals)
    that would be realistic to find in this area. Return as JSON."""
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {current_app.config['OPENAI_API_KEY']}",
            "Content-Type": "application/json"
        },
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
    )
    
    return response.json()["choices"][0]["message"]["content"]

def recognize_animal(image_path):
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {current_app.config['OPENAI_API_KEY']}",
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
