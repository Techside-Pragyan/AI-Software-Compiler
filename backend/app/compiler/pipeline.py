import logging
from app.models.schemas import ApplicationConfigSchema
from app.compiler.intent import IntentExtractor
from app.compiler.system_design import SystemDesignGenerator
from app.compiler.database_gen import DatabaseSchemaGenerator
from app.compiler.api_gen import ApiSchemaGenerator
from app.compiler.ui_gen import UiSchemaGenerator
from app.compiler.auth_gen import AuthRulesGenerator
from app.compiler.logic_gen import BusinessLogicGenerator
from app.engine.repair import RepairEngine
from app.validators.cross_reference import CrossReferenceValidator
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompilerPipeline:
    def __init__(self, api_key: str = None):
        self.intent_extractor = IntentExtractor(api_key=api_key)
        self.system_design_generator = SystemDesignGenerator(api_key=api_key)
        self.database_generator = DatabaseSchemaGenerator(api_key=api_key)
        self.api_generator = ApiSchemaGenerator(api_key=api_key)
        self.ui_generator = UiSchemaGenerator(api_key=api_key)
        self.auth_generator = AuthRulesGenerator(api_key=api_key)
        self.logic_generator = BusinessLogicGenerator(api_key=api_key)
        self.repair_engine = RepairEngine(api_key=api_key)

    def compile(self, prompt: str) -> ApplicationConfigSchema:
        start_time = time.time()
        
        # 1. Intent Extraction
        logger.info("Stage 1: Extracting Intent...")
        intent = self.intent_extractor.extract_intent(prompt)
        
        # 2. System Design
        logger.info("Stage 2: Generating System Design...")
        system_design = self.system_design_generator.generate(intent)
        
        # 3. Database Schema
        logger.info("Stage 3: Generating Database Schema...")
        db_raw = self.database_generator.generate(intent, system_design)
        db_schema = self.repair_engine.repair_and_validate(
            raw_json_or_dict=db_raw.model_dump_json(),
            schema_class=type(db_raw)
        )
        
        # 4. API Schema
        logger.info("Stage 4: Generating API Schema...")
        api_raw = self.api_generator.generate(system_design, db_schema)
        api_schema = self.repair_engine.repair_and_validate(
            raw_json_or_dict=api_raw.model_dump_json(),
            schema_class=type(api_raw),
            validation_context=f"Database Schema: {db_schema.model_dump_json()}",
            custom_validator=lambda s: CrossReferenceValidator.validate_api_against_db(s, db_schema)
        )
        
        # 5. UI Schema
        logger.info("Stage 5: Generating UI Schema...")
        ui_raw = self.ui_generator.generate(system_design, api_schema)
        ui_schema = self.repair_engine.repair_and_validate(
            raw_json_or_dict=ui_raw.model_dump_json(),
            schema_class=type(ui_raw),
            validation_context=f"API Schema: {api_schema.model_dump_json()}",
            custom_validator=lambda s: CrossReferenceValidator.validate_ui_navigation(s)
        )
        
        # 6. Auth Rules
        logger.info("Stage 6: Generating Auth Rules...")
        auth_raw = self.auth_generator.generate(intent, ui_schema, api_schema)
        auth_rules = self.repair_engine.repair_and_validate(
            raw_json_or_dict=auth_raw.model_dump_json(),
            schema_class=type(auth_raw),
            validation_context=f"UI Routes: {ui_schema.model_dump_json()}",
            custom_validator=lambda s: CrossReferenceValidator.validate_auth_against_ui_and_api(s, ui_schema, api_schema)
        )
        
        # 7. Business Logic
        logger.info("Stage 7: Generating Business Logic...")
        logic_raw = self.logic_generator.generate(intent, system_design)
        business_logic = self.repair_engine.repair_and_validate(
            raw_json_or_dict=logic_raw.model_dump_json(),
            schema_class=type(logic_raw)
        )
        
        logger.info(f"Compilation Successful in {time.time() - start_time:.2f}s!")
        
        return ApplicationConfigSchema(
            intent=intent,
            system_design=system_design,
            database_schema=db_schema,
            api_schema=api_schema,
            ui_schema=ui_schema,
            auth_rules=auth_rules,
            business_logic=business_logic
        )
