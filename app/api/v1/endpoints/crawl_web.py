"""
Web Crawling API Endpoint

This endpoint allows users to crawl websites and add the content to the RAG system.
It integrates with the existing vector store and provides configuration options for crawling.
"""

from fastapi import BackgroundTasks, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from app.api.v1.router import router
from app.agent.rag_utils.retriever import fhir_api_docs_store
from app.agent.rag_utils.web_crawler import crawl_website_for_rag



class WebCrawlRequest(BaseModel):
    """Request model for web crawling."""
    
    base_url: HttpUrl
    max_pages: int = 50
    delay: float = 1.0
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = None
    chunk_size: int = 1000
    chunk_overlap: int = 200
    collection_name: Optional[str] = None  # Optional: use different collection


class WebCrawlResponse(BaseModel):
    """Response model for web crawling."""
    
    message: str
    documents_processed: int
    chunks_created: int
    urls_crawled: List[str] = []


async def crawl_and_store_documents(
    base_url: str,
    max_pages: int,
    delay: float,
    include_patterns: Optional[List[str]],
    exclude_patterns: Optional[List[str]],
    chunk_size: int,
    chunk_overlap: int,
    collection_name: Optional[str] = None
) -> WebCrawlResponse:
    """
    Crawl a website and store documents in the vector store.
    
    Args:
        base_url: Starting URL for crawling
        max_pages: Maximum number of pages to crawl
        delay: Delay between requests in seconds
        include_patterns: Regex patterns for URLs to include
        exclude_patterns: Regex patterns for URLs to exclude
        chunk_size: Size of text chunks for splitting
        chunk_overlap: Overlap between chunks
        collection_name: Optional collection name (uses default if None)
        
    Returns:
        WebCrawlResponse with crawl results
    """
    try:
        print(f"Starting web crawl for {base_url}")
        
        # Crawl the website
        documents = await crawl_website_for_rag(
            base_url=str(base_url),
            max_pages=max_pages,
            delay=delay,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="No documents were extracted from the website. Check the URL and crawling parameters."
            )
        
        # Store in vector store
        # Note: For now, we're using the existing fhir_api_docs_store
        # In a production system, you might want to create separate collections
        # Use idempotent method to prevent duplicates
        added_ids = fhir_api_docs_store.add_documents_idempotent(documents=documents, check_duplicates=True)
        
        # Extract URLs for response
        urls_crawled = list(set(doc.metadata.get('url', '') for doc in documents if doc.metadata.get('url')))
        
        print(f"Successfully processed {len(documents)} document chunks from {len(urls_crawled)} URLs")
        
        return WebCrawlResponse(
            message="Website crawled and documents added to vector store successfully",
            documents_processed=len(set(doc.metadata.get('url', '') for doc in documents)),
            chunks_created=len(documents),
            urls_crawled=urls_crawled
        )
        
    except Exception as e:
        print(f"Error during web crawling: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to crawl website: {str(e)}"
        )


@router.post("/crawl-web", response_model=WebCrawlResponse)
async def crawl_website(
    request: WebCrawlRequest,
    background_tasks: BackgroundTasks
):
    """
    Crawl a website and add its content to the RAG system.
    
    This endpoint will:
    1. Crawl the specified website starting from the base URL
    2. Extract content from discovered pages
    3. Split content into chunks suitable for RAG
    4. Store the chunks in the vector store for retrieval
    
    The crawling respects:
    - Rate limiting (delay between requests)
    - URL filtering (include/exclude patterns)
    - Domain restrictions (only crawls same domain)
    - Content type filtering (skips non-HTML content)
    """
    
    # Validate request
    if request.max_pages > 200:
        raise HTTPException(
            status_code=400,
            detail="max_pages cannot exceed 200 for safety reasons"
        )
    
    if request.delay < 0.5:
        raise HTTPException(
            status_code=400,
            detail="delay must be at least 0.5 seconds to be respectful to servers"
        )
    
    # Run crawling in background to avoid timeout
    background_tasks.add_task(
        crawl_and_store_documents,
        base_url=str(request.base_url),
        max_pages=request.max_pages,
        delay=request.delay,
        include_patterns=request.include_patterns,
        exclude_patterns=request.exclude_patterns,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        collection_name=request.collection_name
    )
    
    return WebCrawlResponse(
        message="Web crawling started in background. Check logs for progress.",
        documents_processed=0,
        chunks_created=0,
        urls_crawled=[]
    )


@router.post("/crawl-web/sync", response_model=WebCrawlResponse)
async def crawl_website_sync(request: WebCrawlRequest):
    """
    Crawl a website synchronously (for smaller sites or testing).
    
    This is the same as /crawl-web but runs synchronously.
    Use this for testing or small websites (< 20 pages).
    """
    
    # Validate request
    if request.max_pages > 50:
        raise HTTPException(
            status_code=400,
            detail="max_pages cannot exceed 50 for synchronous crawling"
        )
    
    if request.delay < 0.5:
        raise HTTPException(
            status_code=400,
            detail="delay must be at least 0.5 seconds to be respectful to servers"
        )
    
    return await crawl_and_store_documents(
        base_url=str(request.base_url),
        max_pages=request.max_pages,
        delay=request.delay,
        include_patterns=request.include_patterns,
        exclude_patterns=request.exclude_patterns,
        chunk_size=request.chunk_size,
        chunk_overlap=request.chunk_overlap,
        collection_name=request.collection_name
    )


# Predefined crawling configurations for common use cases
PREDEFINED_CONFIGS = {
    "langchain_docs": {
        "base_url": "https://python.langchain.com/docs/",
        "max_pages": 50,
        "delay": 1.0,
        "include_patterns": [r'/docs/how_to/', r'/docs/conceptual/'],
        "exclude_patterns": [r'#', r'\?', r'/api/'],
    },
    "taiwan_fhir": {
        "base_url": "https://twcore.mohw.gov.tw/",
        "max_pages": 100,
        "delay": 2.0,
        "include_patterns": [r'/docs/', r'/specifications/'],
        "exclude_patterns": [r'#', r'\?', r'/api/'],
    },
    "fhir_spec": {
        "base_url": "https://hl7.org/fhir/",
        "max_pages": 200,
        "delay": 1.5,
        "include_patterns": [r'/resource/', r'/datatypes/', r'/extensibility/'],
        "exclude_patterns": [r'#', r'\?', r'/downloads/'],
    }
}


@router.post("/crawl-web/preset/{preset_name}", response_model=WebCrawlResponse)
async def crawl_website_preset(
    preset_name: str,
    background_tasks: BackgroundTasks
):
    """
    Crawl a website using predefined configurations.
    
    Available presets:
    - langchain_docs: LangChain documentation
    - taiwan_fhir: Taiwan FHIR documentation
    - fhir_spec: HL7 FHIR specification
    """
    
    if preset_name not in PREDEFINED_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown preset: {preset_name}. Available presets: {list(PREDEFINED_CONFIGS.keys())}"
        )
    
    config = PREDEFINED_CONFIGS[preset_name]
    
    # Run crawling in background
    background_tasks.add_task(
        crawl_and_store_documents,
        base_url=config["base_url"],
        max_pages=config["max_pages"],
        delay=config["delay"],
        include_patterns=config["include_patterns"],
        exclude_patterns=config["exclude_patterns"],
        chunk_size=1000,
        chunk_overlap=200,
        collection_name=None
    )
    
    return WebCrawlResponse(
        message=f"Started crawling {preset_name} preset in background",
        documents_processed=0,
        chunks_created=0,
        urls_crawled=[]
    ) 