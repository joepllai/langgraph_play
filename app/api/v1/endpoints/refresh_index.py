import langchain.text_splitter as Textsplitter

from langchain.schema.document import Document
from langfuse import observe


from app.api.v1.router import router
from app.agent.rag_utils.retriver import fhir_api_docs_store
from app.utils.apiHelper import ApiHelper

@observe
@router.get("/refresh_twcore_index")
async def refresh_index():
    docs = await ApiHelper().getFHIRAPIDocs()
    textSplitter = Textsplitter.RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    docs_split = textSplitter.split_documents(
        [Document(page_content=docs, metadata={"source": "openapi"})]
    )
    fhir_api_docs_store.add_documents(documents=docs_split)
