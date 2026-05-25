import os
import json
from pydantic import ValidationError
from google import genai
from google.genai import types
from app.models.schemas import ApplicationConfigSchema

class RepairEngine:
    def __init__(self, api_key: str = None, max_retries: int = 3):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)
        self.model_name = "gemini-2.5-pro"
        self.max_retries = max_retries
        self.metrics = {"retries": 0, "failures": []}

    def repair_and_validate(self, raw_json_or_dict, schema_class=ApplicationConfigSchema):
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
                self._validate_cross_references(valid_schema)
                
                return valid_schema
            
            except (ValidationError, json.JSONDecodeError, ValueError) as e:
                self.metrics["failures"].append({"attempt": attempt, "error": str(e)})
                if attempt == self.max_retries:
                    raise Exception(f"Failed to repair after {self.max_retries} retries. Final error: {str(e)}")
                
                self.metrics["retries"] += 1
                
                # Repair Engine Logic
                repair_prompt = (
                    f"You are a strict JSON repair engine.\n"
                    f"The following configuration failed schema validation or cross-reference checks.\n\n"
                    f"ERROR DETAILS:\n{str(e)}\n\n"
                    f"BROKEN DATA:\n{current_data}\n\n"
                    f"Fix ONLY the specific fields causing the error. Preserve all valid outputs. Ensure valid references between UI components and API/DB."
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

    def _validate_cross_references(self, schema: ApplicationConfigSchema):
        """
        Advanced validation to detect missing references across DB, API, and UI layers.
        """
        # Validate UI Navigation against UI Pages
        defined_routes = {page.route for page in schema.ui_schema.pages}
        for nav in schema.ui_schema.navigation:
            if nav not in defined_routes:
                raise ValueError(f"Navigation item '{nav}' points to a non-existent route.")
                
        # Additional cross-referencing can be added here (e.g., Auth rule routes must exist)
        for rule in schema.auth_rules:
            for route in rule.allowed_routes:
                if route != "*" and route not in defined_routes:
                    pass # Warning or soft error
