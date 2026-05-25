from typing import List
from app.models.schemas import ApplicationConfigSchema, DatabaseSchema, ApiSchema, UiSchema, AuthRulesSchema

class CrossReferenceValidator:
    @staticmethod
    def validate_api_against_db(api_schema: ApiSchema, db_schema: DatabaseSchema):
        if not db_schema.tables:
            return
        
        # Check if endpoints referencing database tables exist
        table_names = {t.name.lower() for t in db_schema.tables}
        # Just ensure there are endpoints. Deeper structural checks can be added here.
        if len(api_schema.endpoints) == 0 and len(table_names) > 0:
            raise ValueError("Database has tables but no API endpoints were generated.")
        
    @staticmethod
    def validate_ui_against_api(ui_schema: UiSchema, api_schema: ApiSchema):
        # Ensure UI pages exist if APIs are generated
        if len(api_schema.endpoints) > 0 and len(ui_schema.pages) == 0:
             raise ValueError("API endpoints generated but no UI pages found.")
        
        # Check if UI components refer to missing layouts
        for page in ui_schema.pages:
            if not page.layout:
                raise ValueError(f"Page '{page.name}' is missing a layout definition.")
        
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
