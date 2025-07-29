# advanced_text_spider.py
import scrapy
from scrapy.http import Request
from scrapy.utils.response import open_in_browser
from urllib.parse import urljoin, urlparse
import re
import json
import logging
from datetime import datetime
import hashlib
import time
import random

class AdvancedTextSpider(scrapy.Spider):
    name = 'advanced_text_extractor'
    
    # Custom settings for the spider
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 16,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 408, 429],
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
            'scrapy_user_agents.middlewares.RandomUserAgentMiddleware': 400,
        },
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 2.0,
    }
    
    # User agents for rotation
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    ]
    
    def __init__(self, urls=None, output_format='json', extract_links=False, max_depth=1, *args, **kwargs):
        super(AdvancedTextSpider, self).__init__(*args, **kwargs)
        
        # Initialize parameters
        self.start_urls = []
        self.output_format = output_format.lower()
        self.extract_links = extract_links.lower() == 'true' if isinstance(extract_links, str) else extract_links
        self.max_depth = int(max_depth)
        self.visited_urls = set()
        
        # Process URLs
        if urls:
            if isinstance(urls, str):
                # Handle single URL or comma-separated URLs
                if ',' in urls:
                    self.start_urls = [url.strip() for url in urls.split(',')]
                else:
                    self.start_urls = [urls.strip()]
            elif isinstance(urls, list):
                self.start_urls = urls
        
        # Validation
        if not self.start_urls:
            raise ValueError("No URLs provided. Use -a urls='http://example.com' or urls='url1,url2,url3'")
        
        self.logger.info(f"Starting spider with {len(self.start_urls)} URLs")
        self.logger.info(f"Extract links: {self.extract_links}, Max depth: {self.max_depth}")
    
    def start_requests(self):
        """Generate initial requests with custom headers and metadata"""
        for url in self.start_urls:
            yield Request(
                url=url,
                callback=self.parse,
                headers=self.get_random_headers(),
                meta={
                    'depth': 0,
                    'start_time': time.time(),
                    'original_url': url
                },
                dont_filter=False,
                errback=self.handle_error
            )
    
    def get_random_headers(self):
        """Generate random headers to avoid detection"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def parse(self, response):
        """Main parsing method with comprehensive text extraction"""
        url = response.url
        depth = response.meta.get('depth', 0)
        start_time = response.meta.get('start_time', time.time())
        processing_time = time.time() - start_time
        
        self.logger.info(f"Processing: {url} (depth: {depth})")
        
        # Mark URL as visited
        self.visited_urls.add(url)
        
        # Extract comprehensive text content
        extracted_data = self.extract_comprehensive_text(response)
        
        # Add metadata
        extracted_data.update({
            'url': url,
            'domain': urlparse(url).netloc,
            'depth': depth,
            'timestamp': datetime.now().isoformat(),
            'processing_time_seconds': round(processing_time, 2),
            'response_status': response.status,
            'content_type': response.headers.get('Content-Type', '').decode('utf-8', errors='ignore'),
            'content_length': len(response.body),
            'url_hash': hashlib.md5(url.encode()).hexdigest()
        })
        
        yield extracted_data
        
        # Extract and follow links if enabled
        if self.extract_links and depth < self.max_depth:
            yield from self.extract_and_follow_links(response, depth)
    
    def extract_comprehensive_text(self, response):
        """Extract text using multiple strategies for maximum coverage"""
        
        # Strategy 1: Main content selectors
        main_content_selectors = [
            'main', 'article', '[role="main"]', '.main-content', 
            '.content', '.post-content', '.entry-content', '.article-content'
        ]
        
        main_text = ""
        for selector in main_content_selectors:
            elements = response.css(selector)
            if elements:
                main_text = self.clean_text(' '.join(elements.css('*::text').getall()))
                if len(main_text) > 100:  # Reasonable content length
                    break
        
        # Strategy 2: Paragraph-based extraction
        paragraphs = response.css('p::text').getall()
        paragraph_text = self.clean_text(' '.join(paragraphs))
        
        # Strategy 3: Full body text (fallback)
        body_text = self.clean_text(' '.join(response.css('body *::text').getall()))
        
        # Strategy 4: Specific content extraction
        title = self.clean_text(response.css('title::text').get() or '')
        meta_description = self.clean_text(
            response.css('meta[name="description"]::attr(content)').get() or ''
        )
        
        # Headings extraction
        headings = {
            'h1': [self.clean_text(h) for h in response.css('h1::text').getall()],
            'h2': [self.clean_text(h) for h in response.css('h2::text').getall()],
            'h3': [self.clean_text(h) for h in response.css('h3::text').getall()],
        }
        
        # Links extraction
        links = []
        for link in response.css('a'):
            href = link.css('::attr(href)').get()
            text = self.clean_text(link.css('::text').get() or '')
            if href and text:
                absolute_url = urljoin(response.url, href)
                links.append({
                    'url': absolute_url,
                    'text': text,
                    'is_external': urlparse(absolute_url).netloc != urlparse(response.url).netloc
                })
        
        # Choose the best text content
        best_text = main_text if len(main_text) > len(paragraph_text) else paragraph_text
        if len(best_text) < 200 and len(body_text) > len(best_text):
            best_text = body_text
        
        # Structured JSON-LD extraction
        json_ld_data = self.extract_json_ld(response)
        
        return {
            'title': title,
            'meta_description': meta_description,
            'main_content': best_text,
            'paragraph_content': paragraph_text,
            'full_body_text': body_text[:5000] if len(body_text) > 5000 else body_text,  # Limit size
            'headings': headings,
            'links': links[:50],  # Limit number of links
            'word_count': len(best_text.split()) if best_text else 0,
            'character_count': len(best_text) if best_text else 0,
            'json_ld': json_ld_data,
            'images': self.extract_images(response),
        }
    
    def extract_json_ld(self, response):
        """Extract structured data from JSON-LD"""
        json_ld_scripts = response.css('script[type="application/ld+json"]::text').getall()
        json_ld_data = []
        
        for script in json_ld_scripts:
            try:
                data = json.loads(script.strip())
                json_ld_data.append(data)
            except json.JSONDecodeError:
                continue
        
        return json_ld_data
    
    def extract_images(self, response):
        """Extract image information"""
        images = []
        for img in response.css('img'):
            src = img.css('::attr(src)').get()
            alt = img.css('::attr(alt)').get()
            if src:
                absolute_src = urljoin(response.url, src)
                images.append({
                    'src': absolute_src,
                    'alt': self.clean_text(alt or ''),
                })
        return images[:20]  # Limit number of images
    
    def extract_and_follow_links(self, response, current_depth):
        """Extract and follow internal links"""
        domain = urlparse(response.url).netloc
        
        # Extract all links
        links = response.css('a::attr(href)').getall()
        
        for link in links:
            absolute_url = urljoin(response.url, link)
            parsed_url = urlparse(absolute_url)
            
            # Only follow links from the same domain and not already visited
            if (parsed_url.netloc == domain and 
                absolute_url not in self.visited_urls and
                self.is_valid_url(absolute_url)):
                
                yield Request(
                    url=absolute_url,
                    callback=self.parse,
                    headers=self.get_random_headers(),
                    meta={
                        'depth': current_depth + 1,
                        'start_time': time.time(),
                        'original_url': response.meta.get('original_url', response.url)
                    },
                    dont_filter=False,
                    errback=self.handle_error
                )
    
    def is_valid_url(self, url):
        """Check if URL is valid for scraping"""
        invalid_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.css', '.js', '.xml', '.zip']
        invalid_patterns = ['mailto:', 'tel:', 'javascript:', '#']
        
        # Check for invalid extensions
        if any(url.lower().endswith(ext) for ext in invalid_extensions):
            return False
        
        # Check for invalid patterns
        if any(pattern in url.lower() for pattern in invalid_patterns):
            return False
        
        return True
    
    def clean_text(self, text):
        """Clean and normalize extracted text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common unwanted characters
        text = re.sub(r'[^\w\s\-.,!?;:()\[\]{}"\']', '', text)
        
        return text
    
    def handle_error(self, failure):
        """Handle request errors"""
        self.logger.error(f"Request failed: {failure.request.url}")
        self.logger.error(f"Error: {failure.value}")
        
        # You can implement custom error handling here
        # For example, saving failed URLs to retry later
        yield {
            'url': failure.request.url,
            'error': str(failure.value),
            'timestamp': datetime.now().isoformat(),
            'status': 'failed'
        }

# Pipeline for custom data processing
class TextProcessingPipeline:
    def __init__(self):
        self.processed_items = 0
    
    def process_item(self, item, spider):
        # Custom processing logic
        self.processed_items += 1
        
        # Add processing metadata
        item['processing_id'] = self.processed_items
        item['spider_name'] = spider.name
        
        # You can add custom text processing here
        # For example: sentiment analysis, keyword extraction, etc.
        
        return item

# Custom middleware for enhanced functionality
class SmartDownloaderMiddleware:
    def __init__(self):
        self.stats = {}
    
    def process_request(self, request, spider):
        # Add custom request processing
        request.meta['download_timeout'] = 30
        return None
    
    def process_response(self, request, response, spider):
        # Add response processing
        if response.status == 200:
            self.stats[response.url] = {
                'status': response.status,
                'size': len(response.body)
            }
        return response

# Settings file content (save as settings.py)
SETTINGS_CONTENT = '''
# Scrapy settings for advanced text extraction

BOT_NAME = 'advanced_text_extractor'

SPIDER_MODULES = ['advanced_text_spider']
NEWSPIDER_MODULE = 'advanced_text_spider'

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure pipelines
ITEM_PIPELINES = {
    'advanced_text_spider.TextProcessingPipeline': 300,
}

# Configure middlewares
DOWNLOADER_MIDDLEWARES = {
    'advanced_text_spider.SmartDownloaderMiddleware': 543,
}

# Configure delays and concurrency
DOWNLOAD_DELAY = 1
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8

# Configure AutoThrottle
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'

# Configure retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429, 403]

# Configure request fingerprinting
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# Logging
LOG_LEVEL = 'INFO'
'''

# Usage examples and CLI commands
USAGE_EXAMPLES = '''
# Usage Examples:

# 1. Single URL extraction
scrapy crawl advanced_text_extractor -a urls="https://example.com" -o output.json

# 2. Multiple URLs
scrapy crawl advanced_text_extractor -a urls="https://example.com,https://another.com" -o output.csv

# 3. Extract with link following
scrapy crawl advanced_text_extractor -a urls="https://example.com" -a extract_links=true -a max_depth=2 -o output.json

# 4. Custom output format
scrapy crawl advanced_text_extractor -a urls="https://example.com" -o output.jsonl

# 5. With custom settings
scrapy crawl advanced_text_extractor -a urls="https://example.com" -s DOWNLOAD_DELAY=2 -s CONCURRENT_REQUESTS=8

# Installation requirements:
# pip install scrapy scrapy-user-agents

# Run with logging:
scrapy crawl advanced_text_extractor -a urls="https://example.com" -L INFO -o output.json

# Save specific fields only:
scrapy crawl advanced_text_extractor -a urls="https://example.com" -o output.csv -t csv
'''

if __name__ == "__main__":
    # print("Advanced Scrapy Text Extractor")
    # print("=" * 50)
    print(USAGE_EXAMPLES)