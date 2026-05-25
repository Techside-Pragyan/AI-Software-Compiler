import os
import json
from pydantic import BaseModel, ValidationError
from google import genai
from google.genai import types

class RepairEngine:
    def __init__(self, api_key: str = None, max_retries: int = 3):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.0-flash"
        self.max_retries = max_retries
        self.metrics = {"retries": 0, "failures": []}

    def repair_and_validate(self, raw_json_or_dict, schema_class: BaseModel, validation_context: str = "", custom_validator=None):
        """
        Attempts to parse data into the Pydantic schema. If validation fails,
        uses the LLM to repair ONLY the broken parts based on the ValidationError.
        """
        current_data = raw_json_or_dict
        if isinstance(current_data, dict):
            current_data = json.dumps(current_data)
            
        for attempt in range(self.max_retries + 1):
            try:
                data = json.loads(current_data)
                # Validation Engine: Pydantic naturally validates types and structures here
                valid_schema = schema_class(**data)
                
                # Cross-reference Validation
                if custom_validator:
                    custom_validator(valid_schema)
                
                return valid_schema
            
            except (ValidationError, json.JSONDecodeError, ValueError) as e:
                self.metrics["failures"].append({"attempt": attempt, "error": str(e), "schema": schema_class.__name__})
                if attempt == self.max_retries:
                    raise Exception(f"Failed to repair {schema_class.__name__} after {self.max_retries} retries. Final error: {str(e)}")
                
                self.metrics["retries"] += 1
                
                # Selective Repair Engine Logic
                repair_prompt = (
                    f"You are a strict JSON repair engine.\n"
                    f"The following configuration failed schema validation or cross-reference checks for {schema_class.__name__}.\n\n"
                    f"CONTEXT:\n{validation_context}\n\n"
                    f"ERROR DETAILS:\n{str(e)}\n\n"
                    f"BROKEN DATA:\n{current_data}\n\n"
                    f"Fix ONLY the specific fields causing the error. Preserve all valid outputs."
                )
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=repair_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=schema_class,
                        temperature=0.0, # Deterministic repair
                    ),
                )
                current_data = response.text
