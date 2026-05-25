import os
import json
from google import genai
from google.genai import types
from app.models.schemas import IntentSchema, ApplicationConfigSchema

class SchemaGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"

    def generate_application_config_raw(self, intent: IntentSchema) -> str:
        """
        Stage 3: Converts the Intent into raw JSON string for the application schema.
        """
        system_instruction = (
            "You are an expert software architect and full-stack developer. "
            "Given the extracted intent for an application, generate the full technical schemas: "
            "Database Schema, API Schema, UI Schema, and Auth Rules. "
            "The configurations MUST be internally consistent: API endpoints match UI needs, "
            "and database fields match API responses. Ensure valid references across components."
        )
        
        # Include the original intent to be nested inside the resulting ApplicationConfigSchema
        intent_json = intent.model_dump_json(indent=2)
        prompt = f"Application Intent:\n{intent_json}\n\nGenerate the complete ApplicationConfigSchema. Be comprehensive and production-grade."
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ApplicationConfigSchema,
                temperature=0.2, 
            ),
        )
        
        return response.text
