from app.models.schemas import ApplicationConfigSchema
from app.compiler.intent import IntentExtractor
from app.compiler.schema import SchemaGenerator
from app.engine.repair import RepairEngine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompilerPipeline:
    def __init__(self, api_key: str = None):
        self.intent_extractor = IntentExtractor(api_key=api_key)
        self.schema_generator = SchemaGenerator(api_key=api_key)
        self.repair_engine = RepairEngine(api_key=api_key)

    def compile(self, prompt: str) -> ApplicationConfigSchema:
        logger.info("Stage 1: Extracting Intent...")
        intent = self.intent_extractor.extract_intent(prompt)
        
        logger.info("Stage 3: Generating Application Schemas...")
        raw_schema_json = self.schema_generator.generate_application_config_raw(intent)
        
        logger.info("Validation & Repair Engine: Checking Outputs...")
        final_config = self.repair_engine.repair_and_validate(raw_schema_json)
        
        logger.info(f"Compilation Successful! Retries used: {self.repair_engine.metrics['retries']}")
        return final_config
