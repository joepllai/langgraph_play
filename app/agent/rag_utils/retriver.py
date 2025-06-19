from langchain_postgres import PGVector
from app.config.agent import PGVectorConfig
from langchain_google_genai import GoogleGenerativeAIEmbeddings

print("Initializing FHIR API docs store...", PGVectorConfig.PSQL_CONNECTION)
embeddings = GoogleGenerativeAIEmbeddings(
    model=PGVectorConfig.FHIRAPIDocs.EMBEDDINGS_MODEL
)
fhir_api_docs_store = PGVector(
    embeddings=embeddings,
    connection=PGVectorConfig.PSQL_CONNECTION,
    collection_name=PGVectorConfig.FHIRAPIDocs.COLLECTION_NAME,
    use_jsonb=PGVectorConfig.FHIRAPIDocs.USE_JSONB,
)

fhir_api_docs_retriever = fhir_api_docs_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.1, "k": 10},
)
