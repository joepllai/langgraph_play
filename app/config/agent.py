from app.config.database import DatabaseConfig


class TextSplittingConfig:
    TEXT_SPLITTING_MODEL = "gemini-2.5-flash"  # Model to use for text splitting
    TEXT_SPLITTING_MAX_TOKENS = 8192  # Maximum tokens for text splitting input
    TEXT_SPLITTING_TIMEOUT = 30  # Timeout for text splitting in seconds
    TEXT_SPLITTING_BATCH_SIZE = 32  # Batch size for text splitting
    TEXT_SPLITTING_OVERLAP = 100  # Overlap in tokens for text splitting
    TEXT_SPLITTING_MIN_LENGTH = 50  # Minimum length of text chunks after splitting
    TEXT_SPLITTING_MAX_LENGTH = 1000  # Maximum length of text chunks after splitting


class EmbeddingsConfig:
    EMBEDDINGS_MODEL = "models/gemini-embedding-exp-03-07"  # Embeddings model to use
    EMBEDDINGS_BATCH_SIZE = 32  # Batch size for embeddings generation
    EMBEDDINGS_MAX_TOKENS = 8192  # Maximum tokens for embeddings input
    EMBEDDINGS_TIMEOUT = 30  # Timeout for embeddings generation in seconds


class PGVectorConfig:
    PSQL_CONNECTION = f"postgresql+psycopg://{DatabaseConfig.PSQL_USER}:{DatabaseConfig.PSQL_PASSWORD}@{DatabaseConfig.PSQL_HOSTNAME}/${DatabaseConfig.PSQL_VECTOR_STORE_DB}"

    class FHIRAPIDocs:
        COLLECTION_NAME = "fhir-api-docs"
        EMBEDDINGS_MODEL = (
            "models/gemini-embedding-exp-03-07"  # Embeddings model to use
        )
        USE_JSONB = True  # Use JSONB for storage in PostgreSQL
