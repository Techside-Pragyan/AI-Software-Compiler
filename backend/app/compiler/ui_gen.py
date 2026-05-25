import os
import json
from google import genai
from google.genai import types
from app.models.schemas import SystemDesignSchema, ApiSchema, UiSchema

class UiSchemaGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"

    def generate(self, system_design: SystemDesignSchema, api_schema: ApiSchema) -> UiSchema:
        system_instruction = (
            "You are an expert Frontend architect. Given the system design and API schema, "
            "generate the UiSchema including pages, layouts, navigation, and components. "
            "Ensure the UI components reference the correct API endpoints from the ApiSchema."
        )
        
        prompt = (
            f"System Design:\n{system_design.model_dump_json(indent=2)}\n\n"
            f"API Schema:\n{api_schema.model_dump_json(indent=2)}\n\n"
            "Generate the UiSchema."
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=UiSchema,
                temperature=0.1, 
            ),
        )
        
        data = json.loads(response.text)
        return UiSchema(**data)
