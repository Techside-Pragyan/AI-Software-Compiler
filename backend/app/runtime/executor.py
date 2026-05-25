from typing import Any, Dict
from app.models.schemas import ApiSchema

class RuntimeExecutor:
    """
    A simple runtime executor to simulate the generated API endpoints dynamically.
    This acts as a mock backend for the generated UI to hit.
    """
    def __init__(self, api_schema: ApiSchema):
        self.api_schema = api_schema
        self.mock_db = {}
        
    def execute_request(self, method: str, path: str, payload: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Simulates an API request based on the generated ApiSchema.
        """
        endpoint = next((e for e in self.api_schema.endpoints if e.path == path and e.method.upper() == method.upper()), None)
        
        if not endpoint:
            return {"status": "error", "message": "Endpoint not found", "code": 404}
            
        if method.upper() == "GET":
            # Simulate fetching
            resource_name = path.strip("/").split("/")[-1]
            return {"status": "success", "data": self.mock_db.get(resource_name, [])}
            
        if method.upper() == "POST":
            # Simulate creation
            resource_name = path.strip("/").split("/")[-1]
            if resource_name not in self.mock_db:
                self.mock_db[resource_name] = []
            
            record = payload or {}
            record["id"] = len(self.mock_db[resource_name]) + 1
            self.mock_db[resource_name].append(record)
            
            return {"status": "success", "data": record}
            
        return {"status": "error", "message": "Method not implemented in simulation runtime", "code": 501}
