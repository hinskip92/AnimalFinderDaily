import base64
from flask import current_app
import requests
import json
from openai import OpenAI
from typing import Dict, Any, Optional


def generate_tasks(location_info: Dict[str, str]) -> Dict[str, list]:
    """Generate animal spotting tasks based on location"""
    api_key = current_app.config.get('OPENAI_API_KEY')

    if not api_key:
        raise ValueError("OpenAI API key is required")

    # Ensure location info is properly encoded
    location_str = json.dumps(location_info, ensure_ascii=False)
    prompt = f"""Return a JSON response with daily and weekly animal spotting tasks for the following location: {location_str}. 
    Include 3 common animals for daily tasks and 2 rare animals for weekly tasks that would be realistic to find in this area."""

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            response_format={"type": "json_object"}
        )

        if not response.choices[0].message.content:
            raise ValueError("Empty response from OpenAI")

        return json.loads(response.choices[0].message.content)
    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
        raise


def recognize_animal(image_path: str) -> Dict[str, Any]:
    """Recognize animal in image and provide detailed information"""
    api_key = current_app.config.get('OPENAI_API_KEY')

    if not api_key:
        raise ValueError("OpenAI API key is required")

    try:
        # Ensure proper encoding for image data
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        client = OpenAI(api_key=api_key)
        system_prompt = """You are an expert wildlife identifier. Analyze the image and provide detailed information about any animals present. 
        Return the response in JSON format."""
        
        user_prompt = """Please identify the animal in this image and provide detailed information in JSON format with the following structure:
{
    "animal": "Name of the animal",
    "details": {
        "habitat": "Natural habitat and geographical distribution",
        "diet": "Feeding habits and typical food sources",
        "behavior": "Notable behavioral characteristics",
        "interesting_facts": ["3-4 interesting facts about the animal"]
    }
}"""

        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        if not response.choices[0].message.content:
            raise ValueError("Empty response from OpenAI")

        result = json.loads(response.choices[0].message.content)

        # Validate response structure
        if not isinstance(result, dict) or 'animal' not in result or 'details' not in result:
            raise ValueError("Invalid response format from OpenAI")

        # Ensure all required fields are present
        details = result['details']
        required_fields = ['habitat', 'diet', 'behavior', 'interesting_facts']
        if not all(field in details for field in required_fields):
            raise ValueError("Missing required fields in OpenAI response")

        return result

    except Exception as e:
        current_app.logger.error(f"Error calling OpenAI API: {str(e)}", exc_info=True)
        raise