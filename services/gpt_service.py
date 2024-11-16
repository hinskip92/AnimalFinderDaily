import base64
import logging
from flask import current_app
import json
from openai import OpenAI
from pydantic import BaseModel
from typing import Dict, Any, List

# Set up logging to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def generate_tasks(location_info: Dict[str, str]) -> Dict[str, list]:
    """Generate animal spotting tasks based on location using Structured Outputs."""
    api_key = current_app.config.get('OPENAI_API_KEY')

    if not api_key:
        logger.warning("API key is not configured. Using mock tasks.")
        return get_mock_tasks()

    # Ensure location info is properly encoded
    location_str = json.dumps(location_info, ensure_ascii=False)
    prompt = (
        f"Given the location {location_str}, suggest 3 daily animal spotting tasks "
        f"(common animals) and 2 weekly animal spotting tasks (rarer animals) that would "
        f"be realistic to find in this area."
    )

    try:
        client = OpenAI(api_key=api_key)

        # Define the expected response schema using Pydantic
        class TaskResponse(BaseModel):
            daily: List[str]
            weekly: List[str]

        # Use GPT-4 with response_format
        completion = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that returns responses in JSON format."
                },
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )

        response_text = completion.choices[0].message.content
        result = TaskResponse.parse_raw(response_text)

        # Convert the Pydantic model to a dictionary
        logger.info("Successfully generated tasks.")
        return result.dict()

    except Exception as e:
        logger.error(f"Error calling OpenAI API for generate_tasks: {str(e)}", exc_info=True)
        return get_mock_tasks()

def recognize_animal(image_path: str) -> Dict[str, Any]:
    """Recognize animal in image and provide detailed information using Vision capabilities."""
    api_key = current_app.config.get('OPENAI_API_KEY')

    if not api_key:
        logger.warning("API key is not configured. Using mock recognition data.")
        return get_mock_recognition()

    try:
        # Read and encode the image
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        client = OpenAI(api_key=api_key)

        # Define the expected response schema using Pydantic
        class AnimalDetails(BaseModel):
            habitat: str
            diet: str
            behavior: str
            interesting_facts: List[str]

        class AnimalRecognitionResponse(BaseModel):
            animal: str
            details: AnimalDetails

        # Prepare the messages
        system_prompt = (
            "You are an expert wildlife identifier. Analyze the image and provide detailed information "
            "about any animals present. Return the response in JSON format."
        )
        user_prompt = "Please identify the animal in this image and provide detailed information."

        # Include the image in the user message
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        },
                    },
                ],
            },
        ]

        # Use GPT-4 Vision
        completion = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )

        response_text = completion.choices[0].message.content
        result = AnimalRecognitionResponse.parse_raw(response_text)

        # Convert the Pydantic model to a dictionary
        logger.info("Successfully recognized animal.")
        return result.dict()

    except Exception as e:
        logger.error(f"Error calling OpenAI API for recognize_animal: {str(e)}", exc_info=True)
        return get_mock_recognition()

def get_mock_tasks() -> Dict[str, list]:
    """Return mock tasks when OpenAI API call fails."""
    logger.debug("Returning mock tasks.")
    return {
        "daily": ["Spot a squirrel", "Observe a robin", "Find a butterfly"],
        "weekly": ["See a fox", "Find a hawk"]
    }

def get_mock_recognition() -> Dict[str, Any]:
    """Return mock recognition data when OpenAI API call fails."""
    logger.debug("Returning mock recognition data.")
    return {
        "animal": "Elephant",
        "details": {
            "habitat": "Savannahs, forests, deserts, and marshes",
            "diet": "Herbivorous, feeding on grasses, fruits, and bark",
            "behavior": "Known for their intelligence, memory, and strong social bonds",
            "interesting_facts": [
                "Elephants are the largest land animals on Earth.",
                "They have a highly developed brain and show a wide variety of behaviors.",
                "An elephant's trunk has over 40,000 muscles."
            ]
        }
    }
