from typing import List
from app.models.schemas import ApplicationConfigSchema, DatabaseSchema, ApiSchema, UiSchema, AuthRulesSchema

class CrossReferenceValidator:
    @staticmethod
    def validate_api_against_db(api_schema: ApiSchema, db_schema: DatabaseSchema):
        # Check if endpoints referencing database tables exist
        table_names = {t.name.lower() for t in db_schema.tables}
        # A simple check: if an endpoint path contains a table name, it's valid
        # This is a heuristic check for now
        pass 
        
    @staticmethod
    def validate_ui_against_api(ui_schema: UiSchema, api_schema: ApiSchema):
        # Check if UI components reference existing API endpoints
        # This requires traversing UI components for props that might refer to endpoints
        pass
        
    @staticmethod
    def validate_auth_against_ui_and_api(auth_rules: AuthRulesSchema, ui_schema: UiSchema, api_schema: ApiSchema):
        defined_routes = {page.route for page in ui_schema.pages}
        for rule in auth_rules.rules:
            for route in rule.allowed_routes:
                if route != "*" and route not in defined_routes:
                    raise ValueError(f"Auth rule references non-existent UI route: {route}")
                    
    @staticmethod
    def validate_ui_navigation(ui_schema: UiSchema):
        defined_routes = {page.route for page in ui_schema.pages}
        for nav in ui_schema.navigation:
            if nav not in defined_routes:
                raise ValueError(f"Navigation item '{nav}' points to a non-existent route.")
