#!/usr/bin/env python3
"""
Example: Web Crawling for RAG System

This script demonstrates how to integrate web crawling with your existing RAG system.
It shows how to crawl websites and add the content to your vector store.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.agent.rag_utils.web_crawler import crawl_website_for_rag
from app.agent.rag_utils.retriever import fhir_api_docs_store


async def example_crawl_and_integrate():
    """Example: Crawl a website and integrate with existing RAG system."""
    
    print("=== Web Crawling Integration Example ===")
    
    # Example 1: Crawl a small documentation site
    print("\n1. Crawling a small documentation site...")
    
    documents = await crawl_website_for_rag(
        base_url="https://httpbin.org/",
        max_pages=5,
        delay=1.0,
        include_patterns=[r'/'],
        exclude_patterns=[r'/image', r'/xml', r'/json'],
        chunk_size=800,
        chunk_overlap=100
    )
    
    print(f"   Extracted {len(documents)} document chunks")
    
    # Show some examples
    for i, doc in enumerate(documents[:2]):
        print(f"   Document {i+1}: {doc.metadata.get('title', 'No title')}")
        print(f"   URL: {doc.metadata.get('url', 'No URL')}")
        print(f"   Content preview: {doc.page_content[:100]}...")
    
    # Example 2: Add to vector store (commented out to avoid modifying production data)
    print("\n2. Adding documents to vector store...")
    print("   (This step is commented out to avoid modifying production data)")
    
    # Uncomment the following lines to actually add documents to your vector store:
    # fhir_api_docs_store.add_documents(documents=documents)
    # print(f"   Successfully added {len(documents)} documents to vector store")
    
    # Example 3: Test retrieval (if documents were added)
    print("\n3. Testing retrieval from vector store...")
    print("   (This step requires documents to be added to the vector store)")
    
    # Uncomment the following lines to test retrieval:
    # retriever = fhir_api_docs_store.as_retriever(
    #     search_type="similarity_score_threshold",
    #     search_kwargs={"score_threshold": 0.1, "k": 3}
    # )
    # results = retriever.invoke("web crawling documentation")
    # print(f"   Retrieved {len(results)} relevant documents")
    
    return documents


async def example_custom_crawling():
    """Example: Custom crawling with specific patterns."""
    
    print("\n=== Custom Crawling Example ===")
    
    # Example: Crawl only documentation pages from a site
    documents = await crawl_website_for_rag(
        base_url="https://python.langchain.com/",
        max_pages=10,  # Small number for demo
        delay=1.0,
        include_patterns=[r'/docs/how_to/', r'/docs/conceptual/'],
        exclude_patterns=[r'/api/', r'#', r'\?', r'/downloads/'],
        chunk_size=1000,
        chunk_overlap=200
    )
    
    print(f"Extracted {len(documents)} document chunks from LangChain docs")
    
    # Show examples
    for i, doc in enumerate(documents[:3]):
        print(f"\n{i+1}. {doc.metadata.get('title', 'No title')}")
        print(f"   URL: {doc.metadata.get('url', 'No URL')}")
        print(f"   Content: {doc.page_content[:150]}...")
    
    return documents


async def example_api_integration():
    """Example: How to use the API endpoints."""
    
    print("\n=== API Integration Example ===")
    
    print("You can use the following API endpoints:")
    print()
    print("1. Crawl a website (background processing):")
    print("   POST /v1/crawl-web")
    print("   {")
    print('     "base_url": "https://example.com/",')
    print('     "max_pages": 50,')
    print('     "delay": 1.0,')
    print('     "include_patterns": ["/docs/", "/guides/"],')
    print('     "exclude_patterns": ["/api/", "#", "\\\\?"]')
    print("   }")
    print()
    print("2. Use predefined presets:")
    print("   POST /v1/crawl-web/preset/langchain_docs")
    print("   POST /v1/crawl-web/preset/taiwan_fhir")
    print("   POST /v1/crawl-web/preset/fhir_spec")
    print()
    print("3. Synchronous crawling (for small sites):")
    print("   POST /v1/crawl-web/sync")
    print("   (Same request body as /v1/crawl-web)")


async def main():
    """Run all examples."""
    
    print("Web Crawling for RAG System - Examples")
    print("=" * 50)
    
    try:
        # Example 1: Basic crawling and integration
        await example_crawl_and_integrate()
        
        # Example 2: Custom crawling patterns
        await example_custom_crawling()
        
        # Example 3: API integration
        await example_api_integration()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install beautifulsoup4 httpx requests-html")
        print("2. Run the test script: python test_web_crawler.py")
        print("3. Start your FastAPI server and try the API endpoints")
        print("4. Check the WEB_CRAWLING_README.md for detailed documentation")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nMake sure you have installed the required dependencies:")
        print("pip install beautifulsoup4 httpx requests-html")


if __name__ == "__main__":
    asyncio.run(main()) 