import os
import json
from google import genai
from google.genai import types
from app.models.schemas import IntentSchema, SystemDesignSchema, DatabaseSchema

class DatabaseSchemaGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"

    def generate(self, intent: IntentSchema, system_design: SystemDesignSchema) -> DatabaseSchema:
        system_instruction = (
            "You are an expert database architect. Given the intent and system design, "
            "generate a robust DatabaseSchema with tables, fields, relationships, and indexes. "
            "Use clear, production-grade naming conventions and constraints."
        )
        
        prompt = (
            f"Intent:\n{intent.model_dump_json(indent=2)}\n\n"
            f"System Design:\n{system_design.model_dump_json(indent=2)}\n\n"
            "Generate the DatabaseSchema."
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=DatabaseSchema,
                temperature=0.1, 
            ),
        )
        
        data = json.loads(response.text)
        return DatabaseSchema(**data)
