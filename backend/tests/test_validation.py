import unittest
from app.models.schemas import DatabaseSchema, TableSchema, ApiSchema, ApiEndpointSchema, UiSchema, UiPageSchema
from app.validators.cross_reference import CrossReferenceValidator

class TestCrossReferenceValidator(unittest.TestCase):
    def test_validate_api_against_db_success(self):
        db_schema = DatabaseSchema(tables=[TableSchema(name="users", fields=[], relationships=[], indexes=[])])
        api_schema = ApiSchema(endpoints=[ApiEndpointSchema(method="GET", path="/api/users", description="", protected=False)])
        
        # Should not raise exception
        try:
            CrossReferenceValidator.validate_api_against_db(api_schema, db_schema)
        except ValueError:
            self.fail("validate_api_against_db raised ValueError unexpectedly!")

    def test_validate_api_against_db_failure(self):
        db_schema = DatabaseSchema(tables=[TableSchema(name="users", fields=[], relationships=[], indexes=[])])
        api_schema = ApiSchema(endpoints=[])
        
        with self.assertRaises(ValueError):
            CrossReferenceValidator.validate_api_against_db(api_schema, db_schema)
            
    def test_validate_ui_against_api_failure(self):
        api_schema = ApiSchema(endpoints=[ApiEndpointSchema(method="GET", path="/api/users", description="", protected=False)])
        ui_schema = UiSchema(pages=[], navigation=[])
        
        with self.assertRaises(ValueError):
            CrossReferenceValidator.validate_ui_against_api(ui_schema, api_schema)

if __name__ == '__main__':
    unittest.main()
