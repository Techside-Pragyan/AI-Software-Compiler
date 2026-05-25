import os
import json
from google import genai
from google.genai import types
from app.models.schemas import IntentSchema, SystemDesignSchema

class SystemDesignGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-pro"

    def generate(self, intent: IntentSchema) -> SystemDesignSchema:
        system_instruction = (
            "You are an expert AI system architect. Convert the structured intent into a full application architecture. "
            "Generate entities, workflows, services, architecture modules, role flows, business workflows, and component hierarchy. "
            "The system design must feel production-ready, include scalability considerations, and modular separation."
        )
        
        intent_json = intent.model_dump_json(indent=2)
        prompt = f"Application Intent:\n{intent_json}\n\nGenerate the complete SystemDesignSchema."
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=SystemDesignSchema,
                temperature=0.1, 
            ),
        )
        
        data = json.loads(response.text)
        return SystemDesignSchema(**data)
