from langchain_postgres import PGVector
from app.config.agent import PGVectorConfig
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_core.retrievers import BaseRetriever
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine


print("Initializing FHIR API docs store...", PGVectorConfig.PSQL_CONNECTION)

class AsyncRetrieverWrapper(BaseRetriever):
    def __init__(self, retriever):
        self.retriever = retriever

    async def ainvoke(self, query, config=None):
        loop = asyncio.get_event_loop()
        # Run the sync invoke in a thread pool to avoid blocking
        return await loop.run_in_executor(None, self.retriever.invoke, query, config)

    def invoke(self, query, config=None):
        return self.retriever.invoke(query, config)

    async def aget_relevant_documents(self, query, **kwargs):
        return await self.ainvoke(query)

    def get_relevant_documents(self, query, **kwargs):
        return self.invoke(query)

    def _get_relevant_documents(self, query, **kwargs):
        # Required by BaseRetriever, just call the sync method
        return self.get_relevant_documents(query, **kwargs)



embeddings = GoogleGenerativeAIEmbeddings(
    model=PGVectorConfig.FHIRAPIDocs.EMBEDDINGS_MODEL
)

# Use the asyncpg or psycopg driver for async
# For psycopg3 (recommended for new projects):
async_engine = create_async_engine(
    PGVectorConfig.ASYNC_PSQL_CONNECTION,  # e.g., "postgresql+psycopg://user:pass@host:port/db"
    echo=False,
)

# Use the enhanced PGVector with proper database-based duplicate detection
fhir_api_docs_store = PGVector(
    embeddings=embeddings,
    connection=async_engine,
    collection_name=PGVectorConfig.FHIRAPIDocs.COLLECTION_NAME,
    use_jsonb=PGVectorConfig.FHIRAPIDocs.USE_JSONB,
)

fhir_api_docs_retriever = fhir_api_docs_store.as_retriever(
    search_type="similarity_score_threshold",
    search_kwargs={"score_threshold": 0.1, "k": 10},
)

#fhir_api_docs_retriever = AsyncRetrieverWrapper(fhir_api_docs_retriever)
