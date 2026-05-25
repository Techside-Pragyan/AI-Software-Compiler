import os
import json
from google import genai
from google.genai import types
from app.models.schemas import SystemDesignSchema, DatabaseSchema, ApiSchema

class ApiSchemaGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-pro"

    def generate(self, system_design: SystemDesignSchema, db_schema: DatabaseSchema) -> ApiSchema:
        system_instruction = (
            "You are an expert API architect. Given the system design and database schema, "
            "generate the ApiSchema including endpoints, methods, request/response structures, and auth requirements. "
            "Ensure endpoints accurately reflect the database fields and relationships."
        )
        
        prompt = (
            f"System Design:\n{system_design.model_dump_json(indent=2)}\n\n"
            f"Database Schema:\n{db_schema.model_dump_json(indent=2)}\n\n"
            "Generate the ApiSchema."
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=ApiSchema,
                temperature=0.1, 
            ),
        )
        
        data = json.loads(response.text)
        return ApiSchema(**data)
