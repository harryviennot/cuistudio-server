from openai import OpenAI
from app.config import Settings
import json

def parse_recipe(text: str) -> dict:
    client = OpenAI(api_key=Settings.OPENAI_API_KEY, organization=Settings.OPENAI_ORGANIZATION_ID, project=Settings.OPENAI_PROJECT_ID)

    prompt = f"""You are a recipe extraction assistant.

Your task is to extract the recipe information from the following raw text (which may include a video transcript, OCR text, and description). The input may be incomplete or unstructured. Please infer and estimate values where reasonable. If something is not mentioned or not obvious, leave it as an empty string ("") or an empty list ([]). Return the result in strict JSON format, no extra explanation.
Return **only** the JSON object. Do not wrap it in quotes, markdown, or a code block. Return valid, raw JSON syntax that can be parsed directly.
Correct format:
{{
  "title": "...",
  ...
}}
Input:
{text}

Output format:
{{
  "title": "",
  "description": "",
  "ingredients": [
    {{
      "name": "",
      "quantity": ""
    }}
  ],
  "nutrition": {{
    "calories": "",
    "protein": "",
    "carbohydrates": "",
    "fat": "",
    "fiber": ""
  }},
  "prep_time": "",
  "cook_time": "",
  "total_time": "",
  "servings": "",
  "instructions": ["", "..."],
  "tags": ["", "..."]
}}"""

    response = client.chat.completions.create(
        model=Settings.GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=Settings.GPT_TEMPERATURE,
        response_format={"type": "json_object"}
    )

    try:
        return json.loads(response.choices[0].message.content)  
    except json.JSONDecodeError:
        return response.choices[0].message.content