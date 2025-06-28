# Web Crawling for RAG System

This document explains how to use the web crawling functionality to automatically discover and load content from entire websites into your RAG system.

## Overview

The web crawling system provides three main approaches for loading web content:

1. **Custom WebCrawler**: Full control over crawling behavior with automatic URL discovery
2. **WebBaseLoader with Sitemap**: Simple approach for websites with XML sitemaps
3. **UnstructuredLoader**: Advanced content extraction for complex page layouts

## Features

- ✅ **Automatic URL discovery**: Follows links to find all pages on a domain
- ✅ **Content filtering**: Include/exclude URLs based on regex patterns
- ✅ **Rate limiting**: Respects server resources with configurable delays
- ✅ **Metadata preservation**: Tracks URLs, titles, and crawl information
- ✅ **Integration ready**: Works with your existing RAG vector store
- ✅ **Multiple extraction methods**: HTML parsing, sitemap loading, unstructured extraction
- ✅ **Idempotent operations**: Prevents duplicate documents when crawling the same site multiple times

## Idempotent Behavior

### **Database-Based Duplicate Detection** 🔄

The enhanced vector store (`IdempotentPGVector`) uses **proper database-based duplicate detection** that persists across application restarts and works in distributed environments:

```python
# Safe to run multiple times - duplicates are automatically skipped
documents = await crawl_website_for_rag(base_url="https://example.com/")
fhir_api_docs_store.add_documents_idempotent(documents=documents)

# Running the same crawl again won't create duplicates
documents = await crawl_website_for_rag(base_url="https://example.com/")
fhir_api_docs_store.add_documents_idempotent(documents=documents)  # Skips duplicates
```

### **How It Works**

1. **Database Table**: Creates a `document_hashes` table to track unique documents
2. **Hash Generation**: Each document is hashed based on content and key metadata
3. **Database Check**: Before adding, checks if the hash exists in the database
4. **PostgreSQL ON CONFLICT**: Uses `ON CONFLICT DO NOTHING` for true idempotency
5. **Persistent State**: Duplicate detection persists across application restarts

### **Database Schema**

The system creates a tracking table:
```sql
CREATE TABLE document_hashes (
    id SERIAL PRIMARY KEY,
    document_hash VARCHAR(32) UNIQUE NOT NULL,
    url VARCHAR(500),
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### **Hash Generation**

Documents are considered duplicates if they have:
- Same content (`page_content`)
- Same key metadata (`url`, `title`, `path`, `method`, `section`, `name`)

```python
# These would be considered the same document
doc1 = Document(
    page_content="FHIR API documentation",
    metadata={"url": "https://example.com/fhir", "title": "FHIR Docs"}
)
doc2 = Document(
    page_content="FHIR API documentation", 
    metadata={"url": "https://example.com/fhir", "title": "FHIR Docs"}
)
# Hash: same → Duplicate detected and skipped

# These would be considered different documents
doc3 = Document(
    page_content="FHIR API documentation",
    metadata={"url": "https://example.com/fhir/v2", "title": "FHIR v2 Docs"}
)
# Hash: different → New document added
```

### **Key Advantages**

✅ **Persistent**: Works across application restarts  
✅ **Distributed**: No in-memory state, works in multi-instance deployments  
✅ **Efficient**: Uses database indexes for fast lookups  
✅ **Reliable**: Uses PostgreSQL's ACID properties  
✅ **Scalable**: Handles large numbers of documents  

### **Testing Idempotent Behavior**

Run the database-based test script:

```bash
python test_database_idempotent.py
```

This will test:
- Adding documents for the first time
- Adding the same documents again (should skip)
- Adding documents without duplicate checking
- Mix of new and existing documents
- Persistence across simulated restarts
- Document statistics

## Quick Start

### 1. Basic Web Crawling

```python
from app.agent.rag_utils.web_crawler import crawl_website_for_rag

# Crawl a website and get documents ready for RAG
documents = await crawl_website_for_rag(
    base_url="https://example.com/",
    max_pages=50,
    delay=1.0,
    include_patterns=[r'/docs/', r'/guides/'],
    exclude_patterns=[r'/api/', r'#', r'\?']
)

# Add to your vector store
fhir_api_docs_store.add_documents(documents=documents)
```

### 2. Using the API Endpoint

```bash
# Crawl a website using the API
curl -X POST "http://localhost:8000/v1/crawl-web" \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://example.com/",
    "max_pages": 50,
    "delay": 1.0,
    "include_patterns": ["/docs/", "/guides/"],
    "exclude_patterns": ["/api/", "#", "\\?"]
  }'

# Use predefined presets
curl -X POST "http://localhost:8000/v1/crawl-web/preset/langchain_docs"
curl -X POST "http://localhost:8000/v1/crawl-web/preset/taiwan_fhir"
```

### 3. Custom Crawler with Full Control

```python
from app.agent.rag_utils.web_crawler import WebCrawler

# Create a custom crawler
crawler = WebCrawler(
    base_url="https://example.com/",
    max_pages=100,
    delay=1.0,
    include_patterns=[r'/docs/', r'/specifications/'],
    exclude_patterns=[r'/api/', r'#', r'\?'],
    respect_robots_txt=True
)

# Crawl the website
async with crawler:
    documents = await crawler.crawl()

# Process documents
for doc in documents:
    print(f"Title: {doc.metadata['title']}")
    print(f"URL: {doc.metadata['url']}")
    print(f"Content: {doc.page_content[:200]}...")
```

## API Endpoints

### POST `/v1/crawl-web`

Crawl a website and add content to the RAG system (background processing).

**Request Body:**
```json
{
  "base_url": "https://example.com/",
  "max_pages": 50,
  "delay": 1.0,
  "include_patterns": ["/docs/", "/guides/"],
  "exclude_patterns": ["/api/", "#", "\\?"],
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "collection_name": null
}
```

**Response:**
```json
{
  "message": "Web crawling started in background. Check logs for progress.",
  "documents_processed": 0,
  "chunks_created": 0,
  "urls_crawled": []
}
```

### POST `/v1/crawl-web/sync`

Crawl a website synchronously (for smaller sites or testing).

### POST `/v1/crawl-web/preset/{preset_name}`

Use predefined crawling configurations:

- `langchain_docs`: LangChain documentation
- `taiwan_fhir`: Taiwan FHIR documentation  
- `fhir_spec`: HL7 FHIR specification

## Configuration Options

### Crawler Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | str | Required | Starting URL for crawling |
| `max_pages` | int | 50 | Maximum number of pages to crawl |
| `delay` | float | 1.0 | Delay between requests (seconds) |
| `include_patterns` | List[str] | None | Regex patterns for URLs to include |
| `exclude_patterns` | List[str] | None | Regex patterns for URLs to exclude |
| `chunk_size` | int | 1000 | Size of text chunks for splitting |
| `chunk_overlap` | int | 200 | Overlap between chunks |

### URL Filtering Examples

```python
# Only crawl documentation pages
include_patterns=[r'/docs/', r'/guides/', r'/tutorials/']

# Exclude API pages, anchors, and query parameters
exclude_patterns=[r'/api/', r'#', r'\?', r'/admin/']

# Only crawl specific sections
include_patterns=[r'/fhir/', r'/specifications/']
exclude_patterns=[r'/downloads/', r'/images/']
```

## Examples

### 1. Crawl LangChain Documentation

```python
from app.agent.rag_utils.web_crawler import example_crawl_langchain_docs

documents = await example_crawl_langchain_docs()
print(f"Extracted {len(documents)} document chunks")
```

### 2. Crawl Taiwan FHIR Documentation

```python
from app.agent.rag_utils.web_crawler import example_crawl_taiwan_fhir_docs

documents = await example_crawl_taiwan_fhir_docs()
print(f"Extracted {len(documents)} document chunks")
```

### 3. Use Sitemap Loader

```python
from app.agent.rag_utils.web_crawler import WebLoaderFactory

loader = WebLoaderFactory.create_sitemap_loader(
    sitemap_url="https://example.com/sitemap.xml",
    requests_per_second=1
)
documents = loader.load()
```

### 4. Advanced Content Extraction

```python
from app.agent.rag_utils.web_crawler import WebLoaderFactory

urls = [
    "https://example.com/page1",
    "https://example.com/page2"
]

loader = WebLoaderFactory.create_unstructured_loader(urls)
documents = loader.load()
```

## Integration with Existing RAG System

The web crawling functionality integrates seamlessly with your existing RAG system:

```python
from app.agent.rag_utils.retriever import fhir_api_docs_store
from app.agent.rag_utils.web_crawler import crawl_website_for_rag

# Crawl website and get documents
documents = await crawl_website_for_rag(
    base_url="https://twcore.mohw.gov.tw/",
    max_pages=50,
    include_patterns=[r'/docs/', r'/specifications/']
)

# Add to existing vector store
fhir_api_docs_store.add_documents(documents=documents)

# Now your RAG agent can retrieve from both FHIR API docs and web content
```

## Testing

Run the test script to see the web crawler in action:

```bash
python test_web_crawler.py
```

This will test:
- Basic web crawling functionality
- LangChain documentation crawling
- Taiwan FHIR documentation crawling
- Sitemap loading
- Custom pattern filtering

## Best Practices

### 1. Be Respectful to Servers

```python
# Use appropriate delays
delay=2.0  # For government/academic sites
delay=1.0  # For commercial sites
delay=0.5  # For your own sites
```

### 2. Filter URLs Appropriately

```python
# Focus on relevant content
include_patterns=[r'/docs/', r'/specifications/', r'/guides/']

# Avoid irrelevant content
exclude_patterns=[r'/api/', r'/admin/', r'/login/', r'#', r'\?']
```

### 3. Set Reasonable Limits

```python
# For testing
max_pages=10

# For production
max_pages=100  # Adjust based on site size
```

### 4. Monitor Crawling Progress

```python
# Check logs for progress
logger.info(f"Crawling: {url}")
logger.info(f"Extracted content from {url} ({len(content)} chars)")
```

## Troubleshooting

### Common Issues

1. **No documents extracted**: Check if the website uses JavaScript rendering
2. **Rate limiting**: Increase the delay between requests
3. **Blocked by robots.txt**: Set `respect_robots_txt=False` (use responsibly)
4. **Large sites**: Reduce `max_pages` or use more specific include patterns

### Debug Mode

Enable debug logging to see detailed crawling information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Dependencies

Make sure you have the required packages installed:

```bash
pip install beautifulsoup4 httpx requests-html langchain-community
```

## Security Considerations

- Always respect `robots.txt` files
- Use appropriate rate limiting
- Be mindful of server resources
- Consider legal implications of crawling
- Don't crawl private or sensitive content

## Future Enhancements

Potential improvements for the web crawling system:

1. **JavaScript rendering**: Support for SPA websites
2. **Authentication**: Handle login-protected content
3. **Incremental crawling**: Only crawl new/updated pages
4. **Distributed crawling**: Multiple crawler instances
5. **Content deduplication**: Remove duplicate content
6. **Advanced filtering**: Content-based filtering
7. **Crawl scheduling**: Automated periodic crawling 