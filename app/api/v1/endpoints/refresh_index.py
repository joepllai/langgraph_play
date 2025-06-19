import langchain.text_splitter as Textsplitter
import yaml

from langchain.schema.document import Document
from langfuse import observe
from fastapi import BackgroundTasks


from app.api.v1.router import router
from app.agent.rag_utils.retriver import fhir_api_docs_store
from app.utils.apiHelper import ApiHelper
from app.api.v1.models.refresh_index import RefreshIndexQueryParams, IndexTargetEnum


def preprocess_api_doc_yaml(raw_yaml: str) -> list[Document]:

    # Parse the YAML
    try:
        openapi_dict = yaml.safe_load(raw_yaml)
    except yaml.YAMLError as e:
        raise ValueError("Failed to parse OpenAPI YAML") from e

    # Semantic chunking based on top-level OpenAPI sections
    docs: list[Document] = []

    # Chunk each path + method as one document
    for path, methods in openapi_dict.get("paths", {}).items():
        for method, detail in methods.items():
            content = yaml.dump({path: {method: detail}})
            docs.append(
                Document(
                    page_content=content,
                    metadata={"section": "paths", "path": path, "method": method},
                )
            )

    # Optionally add components.schemas
    for schema_name, schema_def in (
        openapi_dict.get("components", {}).get("schemas", {}).items()
    ):
        content = yaml.dump({schema_name: schema_def})
        docs.append(
            Document(
                page_content=content,
                metadata={"section": "schemas", "name": schema_name},
            )
        )
    return docs


def split_docs(docs: list[Document]) -> list[Document]:
    text_splitter = Textsplitter.RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " ", ""],  # Try to split nicely on logical boundaries
    )

    # Flatten and split big documents
    split_docs = []
    for doc in docs:
        if len(doc.page_content) > 1200:
            split_parts = text_splitter.split_text(doc.page_content)
            split_docs.extend(
                [
                    Document(page_content=part, metadata=doc.metadata)
                    for part in split_parts
                ]
            )
        else:
            split_docs.append(doc)
    return split_docs


async def refresh_api_docs():
    raw_yaml = await ApiHelper().getFHIRAPIDocs()
    docs = preprocess_api_doc_yaml(raw_yaml)
    docs_split = split_docs(docs)
    fhir_api_docs_store.add_documents(documents=docs_split)


@observe
@router.get("/refresh_index")
async def refresh_index(
    params: RefreshIndexQueryParams, backgroundtasks: BackgroundTasks
):
    if params.index_target == IndexTargetEnum.API_DOCS:
        backgroundtasks.add_task(refresh_api_docs)
        return {"message": "API docs refresh started in background"}
    else:
        return {}
