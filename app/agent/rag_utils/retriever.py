from langchain_postgres import PGVector
from app.config.agent import PGVectorConfig
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import asyncio

print("Initializing FHIR API docs store...", PGVectorConfig.PSQL_CONNECTION)

class AsyncRetrieverWrapper:
    def __init__(self, retriever):
        self.retriever = retriever

    async def ainvoke(self, query, config=None):
        loop = asyncio.get_event_loop()
        # Run the sync invoke in a thread pool to avoid blocking
        return await loop.run_in_executor(None, self.retriever.invoke, query, config)

    def invoke(self, query, config=None):
        return self.retriever.invoke(query, config)


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

fhir_api_docs_retriever = AsyncRetrieverWrapper(fhir_api_docs_retriever)
