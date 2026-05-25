import os
import json
from google import genai
from google.genai import types
from app.models.schemas import IntentSchema, UiSchema, ApiSchema, AuthRulesSchema

class AuthRulesGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-pro"

    def generate(self, intent: IntentSchema, ui_schema: UiSchema, api_schema: ApiSchema) -> AuthRulesSchema:
        system_instruction = (
            "You are a strict security architect. Generate authorization rules (AuthRulesSchema) based on the "
            "roles defined in the intent. Specify which UI routes and API endpoints are allowed for each role."
        )
        
        prompt = (
            f"Intent (Roles):\n{intent.model_dump_json(indent=2, include={'roles'})}\n\n"
            f"UI Pages (Routes):\n{ui_schema.model_dump_json(indent=2, include={'pages'})}\n\n"
            f"API Endpoints:\n{api_schema.model_dump_json(indent=2, include={'endpoints'})}\n\n"
            "Generate the AuthRulesSchema."
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=AuthRulesSchema,
                temperature=0.1, 
            ),
        )
        
        data = json.loads(response.text)
        return AuthRulesSchema(**data)
