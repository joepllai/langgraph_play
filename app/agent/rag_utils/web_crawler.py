"""
Web Crawler for RAG System

This module provides comprehensive web crawling capabilities for loading content
from entire websites into your RAG system. It supports automatic URL discovery,
content extraction, and integration with your existing vector store.
"""

import asyncio
import time
import re
import logging
from typing import List, Set, Optional, Dict, Any
from urllib.parse import urljoin, urlparse, urlunparse

from langchain_community.document_loaders import WebBaseLoader, UnstructuredURLLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebCrawler:
    """
    A comprehensive web crawler that can discover and load content from entire websites.
    
    Features:
    - Automatic URL discovery through link extraction
    - Content extraction using multiple methods
    - Rate limiting and polite crawling
    - URL filtering and exclusion patterns
    - Metadata preservation
    """
    
    def __init__(
        self,
        base_url: str,
        max_pages: int = 100,
        delay: float = 1.0,
        timeout: int = 10,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        respect_robots_txt: bool = True
    ):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.max_pages = max_pages
        self.delay = delay
        self.timeout = timeout
        self.include_patterns = include_patterns or []
        self.exclude_patterns = exclude_patterns or []
        self.respect_robots_txt = respect_robots_txt
        
        self.discovered_urls: Set[str] = set()
        self.visited_urls: Set[str] = set()
        self.documents: List[Document] = []
        
        # Initialize HTTP client
        self.client = httpx.AsyncClient(timeout=timeout)
        
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    def _should_crawl_url(self, url: str) -> bool:
        """Check if a URL should be crawled based on patterns and domain."""
        parsed = urlparse(url)
        
        # Only crawl same domain
        if parsed.netloc != self.domain:
            return False
        
        # Skip non-HTTP(S) URLs
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # Skip common non-content URLs
        skip_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.xml']
        if any(url.lower().endswith(ext) for ext in skip_extensions):
            return False
        
        # Apply include patterns
        if self.include_patterns:
            if not any(re.search(pattern, url) for pattern in self.include_patterns):
                return False
        
        # Apply exclude patterns
        if any(re.search(pattern, url) for pattern in self.exclude_patterns):
            return False
        
        return True
    
    async def _extract_links(self, url: str, html_content: str) -> Set[str]:
        """Extract all links from an HTML page."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(url, href)
            
            # Clean URL (remove fragments, query params if needed)
            parsed = urlparse(absolute_url)
            clean_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))
            
            if self._should_crawl_url(clean_url):
                links.add(clean_url)
        
        return links
    
    async def _extract_content(self, url: str, html_content: str) -> Optional[Document]:
        """Extract content from an HTML page and create a Document."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract title
            title = soup.find('title')
            title_text = title.get_text().strip() if title else ""
            
            # Extract main content (prioritize main, article, or body)
            content_selectors = ['main', 'article', '[role="main"]', 'body']
            content_element = None
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    break
            
            if not content_element:
                content_element = soup.body or soup
            
            # Extract text content
            text_content = content_element.get_text(separator='\n', strip=True)
            
            # Clean up whitespace
            text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
            text_content = re.sub(r'\s+', ' ', text_content).strip()
            
            if not text_content or len(text_content) < 50:  # Skip very short content
                return None
            
            # Create document with metadata
            metadata = {
                'url': url,
                'title': title_text,
                'domain': self.domain,
                'crawled_at': time.time(),
                'content_length': len(text_content)
            }
            
            return Document(page_content=text_content, metadata=metadata)
            
        except Exception as e:
            logger.warning(f"Failed to extract content from {url}: {e}")
            return None
    
    async def _crawl_page(self, url: str) -> Optional[Document]:
        """Crawl a single page and extract content."""
        try:
            logger.info(f"Crawling: {url}")
            
            response = await self.client.get(url)
            response.raise_for_status()
            
            # Check if it's HTML content
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.info(f"Skipping non-HTML content: {url}")
                return None
            
            html_content = response.text
            
            # Extract content
            document = await self._extract_content(url, html_content)
            
            # Extract links for discovery
            if document:
                new_links = await self._extract_links(url, html_content)
                self.discovered_urls.update(new_links)
            
            return document
            
        except Exception as e:
            logger.warning(f"Failed to crawl {url}: {e}")
            return None
    
    async def crawl(self) -> List[Document]:
        """
        Crawl the website starting from base_url.
        
        Returns:
            List[Document]: List of documents extracted from the website
        """
        logger.info(f"Starting crawl of {self.base_url}")
        
        # Start with the base URL
        urls_to_crawl = [self.base_url]
        
        while urls_to_crawl and len(self.visited_urls) < self.max_pages:
            # Get next URL to crawl
            current_url = urls_to_crawl.pop(0)
            
            if current_url in self.visited_urls:
                continue
            
            # Crawl the page
            document = await self._crawl_page(current_url)
            
            if document:
                self.documents.append(document)
                logger.info(f"Extracted content from {current_url} ({len(document.page_content)} chars)")
            
            self.visited_urls.add(current_url)
            
            # Add newly discovered URLs to the queue
            new_urls = [url for url in self.discovered_urls 
                       if url not in self.visited_urls and url not in urls_to_crawl]
            urls_to_crawl.extend(new_urls[:self.max_pages - len(self.visited_urls)])
            
            # Rate limiting
            if self.delay > 0:
                await asyncio.sleep(self.delay)
        
        logger.info(f"Crawl completed. Visited {len(self.visited_urls)} pages, extracted {len(self.documents)} documents")
        return self.documents


class WebLoaderFactory:
    """
    Factory class for creating different types of web loaders based on requirements.
    """
    
    @staticmethod
    def create_sitemap_loader(sitemap_url: str, requests_per_second: int = 1) -> WebBaseLoader:
        """
        Create a WebBaseLoader for websites with XML sitemaps.
        
        Args:
            sitemap_url: URL to the sitemap.xml file
            requests_per_second: Rate limiting for requests
            
        Returns:
            WebBaseLoader configured for sitemap loading
        """
        return WebBaseLoader(
            web_paths=[sitemap_url],
            requests_per_second=requests_per_second,
            continue_on_failure=True,
        )
    
    @staticmethod
    def create_unstructured_loader(urls: List[str]) -> UnstructuredURLLoader:
        """
        Create an UnstructuredURLLoader for advanced content extraction.
        
        Args:
            urls: List of URLs to extract content from
            
        Returns:
            UnstructuredURLLoader for sophisticated content extraction
        """
        return UnstructuredURLLoader(urls=urls)
    
    @staticmethod
    def create_custom_crawler(
        base_url: str,
        max_pages: int = 100,
        delay: float = 1.0,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> WebCrawler:
        """
        Create a custom WebCrawler for full website crawling.
        
        Args:
            base_url: Starting URL for crawling
            max_pages: Maximum number of pages to crawl
            delay: Delay between requests in seconds
            include_patterns: Regex patterns for URLs to include
            exclude_patterns: Regex patterns for URLs to exclude
            
        Returns:
            WebCrawler instance
        """
        return WebCrawler(
            base_url=base_url,
            max_pages=max_pages,
            delay=delay,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )


async def crawl_website_for_rag(
    base_url: str,
    max_pages: int = 50,
    delay: float = 1.0,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> List[Document]:
    """
    Convenience function to crawl a website and prepare documents for RAG.
    
    Args:
        base_url: Starting URL for crawling
        max_pages: Maximum number of pages to crawl
        delay: Delay between requests in seconds
        include_patterns: Regex patterns for URLs to include
        exclude_patterns: Regex patterns for URLs to exclude
        chunk_size: Size of text chunks for splitting
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of processed documents ready for vector store
    """
    
    # Create and run crawler
    crawler = WebLoaderFactory.create_custom_crawler(
        base_url=base_url,
        max_pages=max_pages,
        delay=delay,
        include_patterns=include_patterns,
        exclude_patterns=exclude_patterns
    )
    
    async with crawler:
        documents = await crawler.crawl()
    
    # Split documents for RAG
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    
    split_documents = []
    for doc in documents:
        if len(doc.page_content) > chunk_size + chunk_overlap:
            split_parts = text_splitter.split_text(doc.page_content)
            split_documents.extend([
                Document(page_content=part, metadata=doc.metadata)
                for part in split_parts
            ])
        else:
            split_documents.append(doc)
    
    logger.info(f"Processed {len(documents)} documents into {len(split_documents)} chunks")
    return split_documents


# Example usage functions
async def example_crawl_langchain_docs():
    """Example: Crawl LangChain documentation."""
    return await crawl_website_for_rag(
        base_url="https://python.langchain.com/docs/",
        max_pages=20,
        delay=1.0,
        include_patterns=[r'/docs/how_to/', r'/docs/conceptual/'],
        exclude_patterns=[r'#', r'\?', r'/api/'],
    )


async def example_crawl_taiwan_fhir_docs():
    """Example: Crawl Taiwan FHIR documentation."""
    return await crawl_website_for_rag(
        base_url="https://twcore.mohw.gov.tw/",
        max_pages=50,
        delay=2.0,  # Be extra polite to government servers
        include_patterns=[r'/docs/', r'/specifications/'],
        exclude_patterns=[r'#', r'\?', r'/api/'],
    )


if __name__ == "__main__":
    # Example usage
    async def main():
        print("Crawling LangChain docs...")
        docs = await example_crawl_langchain_docs()
        print(f"Extracted {len(docs)} document chunks")
        
        for i, doc in enumerate(docs[:3]):
            print(f"\n{i+1}. {doc.metadata['title']} ({doc.metadata['url']})")
            print(f"   Content: {doc.page_content[:200]}...")
    
    asyncio.run(main()) 