import os
import json
from google import genai
from google.genai import types
from app.models.schemas import IntentSchema, SystemDesignSchema, BusinessLogicSchema

class BusinessLogicGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-pro"

    def generate(self, intent: IntentSchema, system_design: SystemDesignSchema) -> BusinessLogicSchema:
        system_instruction = (
            "You are a Product Manager and Systems Engineer. Define the core business logic rules, "
            "such as premium gating, workflow automations, and role restrictions."
        )
        
        prompt = (
            f"Intent:\n{intent.model_dump_json(indent=2)}\n\n"
            f"System Design (Flows):\n{system_design.model_dump_json(indent=2, include={'flows'})}\n\n"
            "Generate the BusinessLogicSchema."
        )
        
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=BusinessLogicSchema,
                temperature=0.1, 
            ),
        )
        
        data = json.loads(response.text)
        return BusinessLogicSchema(**data)
