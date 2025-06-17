from langchain_postgres import PGVector
from app.config.agent import PGVectorConfig

print("Initializing FHIR API docs store...", PGVectorConfig.PSQL_CONNECTION)
fhir_api_docs_store = PGVector(
    embeddings=PGVectorConfig.FHIRAPIDocs.EMBEDDINGS_MODEL,
    connection=PGVectorConfig.PSQL_CONNECTION,
    collection_name=PGVectorConfig.FHIRAPIDocs.COLLECTION_NAME,
    use_jsonb=PGVectorConfig.FHIRAPIDocs.USE_JSONB,
)

fhir_api_docs_retriever = fhir_api_docs_store.as_retriever()
