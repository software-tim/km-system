import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "km-mcp-phi4"
    version: str = "1.0.0"
    debug: bool = os.getenv('DEBUG', 'false').lower() == 'true'
    port: int = int(os.getenv('PORT', 8001))
    
    phi4_model_name: str = os.getenv('PHI4_MODEL_NAME', 'microsoft/phi-3-mini-4k-instruct')
    max_tokens: int = int(os.getenv('MAX_TOKENS', 1024))
    temperature: float = float(os.getenv('TEMPERATURE', 0.7))
    
    km_docs_service_url: str = os.getenv('KM_DOCS_SERVICE_URL', 'https://km-mcp-sql-docs.azurewebsites.net')
    km_docs_timeout: int = int(os.getenv('KM_DOCS_TIMEOUT', 30))
    
    enable_model_cache: bool = os.getenv('ENABLE_MODEL_CACHE', 'true').lower() == 'true'
    cache_dir: str = os.getenv('CACHE_DIR', './model_cache')
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
