import os

from app.config.database import DatabaseConfig


class AzureFoundryConfig:
    API_KEY = os.getenv("AZURE_INFERENCE_CREDENTIAL", "example")
    BASE_URL = os.getenv("AZURE_INFERENCE_ENDPOINT", "https://cdp-ai-foundry.openai.azure.com/")
    API_VERSION= os.getenv("AZURE_FOUNDRY_API_VERSION", "2024-12-01-preview")
    MODEL = os.getenv("AZURE_FOUNDRY_MODEL", "gpt-4o")
    TEMPERATURE = int(os.getenv("AZURE_FOUNDRY_TEMPERATURE", 0))

class AOCConfig:
    API_KEY = os.getenv("ASUS_API_KEY")
    ASSISTANT_ID = os.getenv("AOCC_ASSISTANT_ID", "1")
    SERVICE = os.getenv("AOCC_SERVICE_ID", "azure")
    VERSION = os.getenv("AOCC_VERSION", "gpt4o")
    TIMEOUT = int(os.getenv("AOCC_TIEMOUT", 45))  # Timeout in seconds


class EmbeddingsConfig:
    EMBEDDINGS_MODEL = "models/text-embedding-004"  # Embeddings model to use
    EMBEDDINGS_BATCH_SIZE = 32  # Batch size for embeddings generation
    EMBEDDINGS_MAX_TOKENS = 8192  # Maximum tokens for embeddings input
    EMBEDDINGS_TIMEOUT = 30  # Timeout for embeddings generation in seconds


class PGVectorConfig:
    PSQL_CONNECTION = f"postgresql+psycopg://{DatabaseConfig.PSQL_USER}:{DatabaseConfig.PSQL_PASSWORD}@{DatabaseConfig.PSQL_HOSTNAME}:{DatabaseConfig.PSQL_PORT}/{DatabaseConfig.PSQL_VECTOR_STORE_DB}"

    class FHIRAPIDocs:
        COLLECTION_NAME = "fhir-api-docs"
        EMBEDDINGS_MODEL = "models/text-embedding-004"  # Embeddings model to use
        USE_JSONB = True  # Use JSONB for storage in PostgreSQL
