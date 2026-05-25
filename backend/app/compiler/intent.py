import os
from google import genai
from google.genai import types
from app.models.schemas import IntentSchema

class IntentExtractor:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash" # Use a capable model for complex extraction

    def extract_intent(self, prompt: str) -> IntentSchema:
        """
        Converts a natural language prompt into a structured IntentSchema.
        """
        system_instruction = (
            "You are an expert AI system architect and compiler. Your job is to take a natural language "
            "product requirement and extract the core intent into a structured JSON format. "
            "Extract the app type, main modules, entities, user roles, and workflows."
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=IntentSchema,
                temperature=0.1, # Keep deterministic
            ),
        )
        
        # Pydantic validation is inherently applied because response_schema is passed,
        # but let's parse it explicitly to ensure we return the Pydantic object
        import json
        data = json.loads(response.text)
        return IntentSchema(**data)
