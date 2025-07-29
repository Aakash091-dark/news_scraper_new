import json
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import logging
from typing import Optional, Dict, List, Tuple
import random
from urllib.parse import urlparse, urljoin
from datetime import datetime
import chardet
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import hashlib
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)

# Configuration
OUTPUT_FOLDER = "data"
REQUEST_DELAY = (1, 3)
TIMEOUT = 30
CONTENT_MIN_LENGTH = 10  # Reduced minimum
MAX_RETRIES = 5  # Increased retries
CONTENT_QUALITY_THRESHOLD = 0.3  # Lower threshold for aggressive extraction
MIN_SENTENCES = 1  # Minimum sentences for content acceptance

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("scraper.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/121.0",
]

# Expanded garbage patterns with more lenient detection
GARBAGE_PATTERNS = [
    r"^\s*(javascript|error|404|page not found|loading|redirect)\s*$",
    r"^\s*(advertisement|sponsored content|ads by|click here)\s*$",
    r"^\s*(\w{1,2}|\d+)\s*$",
    r"^\s*(home|menu|search|login|signup|next|previous|back|share|like|tweet)\s*$",
    r"^\s*(cookie|privacy policy|terms of service|subscribe|newsletter)\s*$",
    r"^\s*[\W\d\s]*$",
    r"^\s*(comments?|reply|show more|load more|continue reading)\s*$",
    r"^\s*(follow us|social media|connect with us)\s*$",
]

# News-specific content indicators
CONTENT_INDICATORS = [
    'article', 'story', 'news', 'content', 'text', 'body', 'main', 'post', 
    'entry', 'detail', 'full', 'complete', 'primary', 'editorial'
]

# Get English stopwords
try:
    ENGLISH_STOPWORDS = set(stopwords.words('english'))
except:
    ENGLISH_STOPWORDS = set()

def create_session():
    """Enhanced session with more realistic headers"""
    session = requests.Session()
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Referer": random.choice([
            "https://google.com",
            "https://twitter.com", 
            "https://news.google.com",
            "https://facebook.com"
        ]),
    }
    session.headers.update(headers)
    return session

def detect_and_fix_encoding(response) -> str:
    """Enhanced encoding detection with more attempts"""
    try:
        # First try the response's apparent encoding
        if response.encoding and response.encoding.lower() not in ['iso-8859-1', 'windows-1252']:
            try:
                decoded = response.text
                if decoded and not '\ufffd' in decoded[:1000]:  # Check for replacement chars
                    return decoded
            except:
                pass

        # Use chardet with lower confidence threshold
        detected = chardet.detect(response.content)
        if detected and detected["encoding"] and detected["confidence"] > 0.5:
            try:
                return response.content.decode(detected["encoding"])
            except (UnicodeDecodeError, LookupError):
                pass

        # Try more encodings
        for encoding in ["utf-8", "utf-16", "utf-16le", "utf-16be", "windows-1252", "iso-8859-1", "cp1252", "latin1"]:
            try:
                decoded = response.content.decode(encoding)
                # Simple validation: check if it contains reasonable text
                if len(decoded) > 100 and decoded.count('�') / len(decoded) < 0.1:
                    return decoded
            except (UnicodeDecodeError, LookupError):
                continue

        # Last resort: force decode with error handling
        return response.content.decode('utf-8', errors='replace')
    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}")
        return response.text

def calculate_text_quality(text: str) -> float:
    """Calculate text quality score based on various metrics"""
    if not text or len(text.strip()) < 10:
        return 0.0
    
    text_clean = text.strip().lower()
    words = text_clean.split()
    
    if len(words) < 3:
        return 0.1
    
    # Check character composition
    alpha_chars = len(re.findall(r'[a-zA-Z]', text))
    total_chars = len(text.replace(' ', ''))
    alpha_ratio = alpha_chars / max(total_chars, 1)
    
    # Check average word length
    avg_word_length = sum(len(word) for word in words) / len(words)
    
    # Check sentence structure
    sentences = re.split(r'[.!?]+', text)
    sentence_count = len([s for s in sentences if len(s.strip()) > 10])
    
    # Check for common English words
    english_words = sum(1 for word in words if word in ENGLISH_STOPWORDS) if ENGLISH_STOPWORDS else 0
    english_ratio = english_words / len(words)
    
    # Check punctuation ratio
    punct_count = len(re.findall(r'[.!?,:;]', text))
    punct_ratio = punct_count / len(words)
    
    # Calculate composite score
    quality_score = (
        alpha_ratio * 0.3 +
        min(avg_word_length / 6, 1) * 0.2 +
        min(sentence_count / 3, 1) * 0.2 +
        min(english_ratio * 2, 1) * 0.2 +
        min(punct_ratio * 10, 1) * 0.1
    )
    
    return quality_score

def is_garbage(text: str) -> bool:
    """Enhanced garbage detection with quality scoring"""
    if not text or len(text.strip()) < 10:  # Reduced from 15
        return True

    text_clean = text.strip().lower()

    # Check garbage patterns
    for pattern in GARBAGE_PATTERNS:
        if re.match(pattern, text_clean, re.IGNORECASE):
            return True

    # Use quality scoring for better detection
    quality = calculate_text_quality(text)
    if quality < CONTENT_QUALITY_THRESHOLD:
        return True

    # Check for navigation/UI patterns
    nav_keywords = ['click', 'tap', 'swipe', 'menu', 'button', 'link', 'navigation', 'sidebar']
    nav_ratio = sum(1 for keyword in nav_keywords if keyword in text_clean) / max(len(text_clean.split()), 1)
    if nav_ratio > 0.3:
        return True

    return False

def clean_text_enhanced(text: str) -> str:
    """Enhanced text cleaning with better encoding handling"""
    if not text:
        return ""

    # Fix common encoding issues
    encoding_fixes = {
        '\ufffd': '',  # Unicode replacement character
        '\xa0': ' ',   # Non-breaking space
        '\u200b': '',  # Zero width space
        '\u2009': ' ', # Thin space
        '\u2028': '\n', # Line separator
        '\u2029': '\n\n', # Paragraph separator
        'â€™': "'",    # Right single quotation mark
        'â€œ': '"',    # Left double quotation mark
        'â€\x9d': '"', # Right double quotation mark
        'â€"': '–',    # En dash
        'â€"': '—',    # Em dash
        'â€¦': '...',  # Ellipsis
    }
    
    for old, new in encoding_fixes.items():
        text = text.replace(old, new)

    # Remove control characters but preserve line breaks
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    # Normalize whitespace but preserve paragraph structure
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'^\s+|\s+$', '', text, flags=re.MULTILINE)

    # Remove excessive repeated punctuation
    text = re.sub(r'([.!?]){3,}', r'\1\1\1', text)
    text = re.sub(r'([,-]){2,}', r'\1', text)

    return text.strip()

def extract_json_ld(soup) -> List[str]:
    """Enhanced JSON-LD extraction with multiple schema types"""
    contents = []
    scripts = soup.find_all('script', type='application/ld+json')
    
    for script in scripts:
        try:
            if not script.string:
                continue
                
            data = json.loads(script.string)
            
            # Handle both single objects and arrays
            items = data if isinstance(data, list) else [data]
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                # Extract various content fields
                content_fields = [
                    'articleBody', 'text', 'description', 'content',
                    'mainEntityOfPage', 'about', 'abstract'
                ]
                
                for field in content_fields:
                    if field in item and item[field]:
                        content = str(item[field]).strip()
                        if len(content) > 100 and not is_garbage(content):
                            contents.append(content)
                            
        except Exception as e:
            logger.debug(f"Error parsing JSON-LD: {e}")
            continue
    
    return contents

def extract_meta_content(soup) -> List[str]:
    """Extract content from meta tags"""
    contents = []
    
    meta_properties = [
        'og:description', 'twitter:description', 'description',
        'og:title', 'twitter:title', 'news_keywords',
        'article:content', 'summary'
    ]
    
    for prop in meta_properties:
        # Try both property and name attributes
        for attr in ['property', 'name']:
            meta = soup.find('meta', {attr: prop})
            if meta and meta.get('content'):
                content = meta['content'].strip()
                if len(content) > 50 and not is_garbage(content):
                    contents.append(content)
    
    return contents

def score_element_content(element, base_score: int = 0) -> Tuple[int, str]:
    """Score an element based on content quality indicators"""
    if not element:
        return 0, ""
    
    text = element.get_text(separator=' ', strip=True)
    if not text or is_garbage(text):
        return 0, ""
    
    score = base_score + len(text)
    
    # Bonus for content indicators in class/id
    class_id = ' '.join(element.get('class', []) + [element.get('id', '')])
    for indicator in CONTENT_INDICATORS:
        if indicator in class_id.lower():
            score += 500
    
    # Bonus for paragraph structure
    paragraphs = element.find_all('p')
    score += len(paragraphs) * 100
    
    # Bonus for semantic HTML5 tags
    if element.name in ['article', 'main', 'section']:
        score += 300
    
    # Penalty for nav/sidebar indicators
    nav_indicators = ['nav', 'sidebar', 'menu', 'footer', 'header', 'aside']
    for indicator in nav_indicators:
        if indicator in class_id.lower():
            score -= 200
    
    return score, text

def extract_content(soup) -> Optional[str]:
    """Ultra-aggressive content extraction using multiple strategies"""
    
    content_candidates = []
    
    # Strategy 1: Enhanced main content selectors
    main_selectors = [
        'article', 'main', '[role="main"]',
        '.article-content', '.story-content', '.post-content', '.entry-content',
        '.article-body', '.story-body', '.post-body', '.news-content',
        '.content-area', '.main-content', '.primary-content', '.article-text',
        '#main-content', '#content', '#article', '#story', '#post',
        '.text-content', '.full-content', '.article-detail', '.news-body',
        '[class*="content"]', '[class*="article"]', '[class*="story"]',
        '[class*="text"]', '[class*="body"]', '[id*="content"]',
        '[id*="article"]', '[id*="story"]', '[id*="text"]'
    ]

    for selector in main_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                score, text = score_element_content(element, 1000)
                if score > 500 and len(text) > 100:
                    content_candidates.append((score, text, f"main_selector_{selector}"))
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {e}")

    # Strategy 2: Largest meaningful div/section elements
    try:
        large_elements = soup.find_all(['div', 'section', 'span'], 
                                     string=False, 
                                     recursive=True)
        
        for element in large_elements:
            if len(str(element)) > 1000:  # Only check substantial elements
                score, text = score_element_content(element)
                if score > 300 and len(text) > 200:
                    content_candidates.append((score, text, "large_element"))
                    
    except Exception as e:
        logger.debug(f"Error in large element extraction: {e}")

    # Strategy 3: Paragraph aggregation with quality scoring
    try:
        all_paragraphs = []
        for tag in soup.find_all(['p', 'div', 'span', 'li']):
            text = tag.get_text(separator=' ', strip=True)
            if len(text) > 30 and not is_garbage(text):
                quality = calculate_text_quality(text)
                if quality > 0.2:  # Lower threshold
                    all_paragraphs.append((quality, text))

        if len(all_paragraphs) >= 2:
            # Sort by quality and take best paragraphs
            all_paragraphs.sort(key=lambda x: x[0], reverse=True)
            best_paragraphs = [text for _, text in all_paragraphs[:20]]  # Top 20
            
            combined_content = '\n\n'.join(best_paragraphs)
            if len(combined_content) > 200:
                content_candidates.append((800, combined_content, "paragraph_aggregation"))
                
    except Exception as e:
        logger.debug(f"Error in paragraph aggregation: {e}")

    # Strategy 4: JSON-LD structured data
    try:
        json_contents = extract_json_ld(soup)
        for content in json_contents:
            if len(content) > 100:
                content_candidates.append((900, content, "json_ld"))
    except Exception as e:
        logger.debug(f"Error in JSON-LD extraction: {e}")

    # Strategy 5: Meta tag content
    try:
        meta_contents = extract_meta_content(soup)
        combined_meta = '\n\n'.join(meta_contents)
        if len(combined_meta) > 100:
            content_candidates.append((600, combined_meta, "meta_tags"))
    except Exception as e:
        logger.debug(f"Error in meta extraction: {e}")

    # Strategy 6: Text density analysis
    try:
        text_blocks = []
        for element in soup.find_all(['div', 'section', 'article', 'p']):
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 100:
                # Calculate text density (text length vs HTML length)
                html_length = len(str(element))
                density = len(text) / max(html_length, 1)
                
                if density > 0.3:  # High text density
                    quality = calculate_text_quality(text)
                    score = int(density * 1000 + quality * 500)
                    text_blocks.append((score, text))
        
        if text_blocks:
            text_blocks.sort(key=lambda x: x[0], reverse=True)
            best_text = text_blocks[0][1]
            if len(best_text) > 200:
                content_candidates.append((text_blocks[0][0], best_text, "text_density"))
                
    except Exception as e:
        logger.debug(f"Error in text density analysis: {e}")

    # Strategy 7: Visible text extraction as absolute fallback
    try:
        visible_texts = []
        for text in soup.stripped_strings:
            text_clean = text.strip()
            if len(text_clean) > 20 and not is_garbage(text_clean):
                quality = calculate_text_quality(text_clean)
                if quality > 0.1:  # Very low threshold
                    visible_texts.append(text_clean)
        
        if len(visible_texts) >= 3:
            combined_visible = '\n'.join(visible_texts)
            if len(combined_visible) > 150:
                content_candidates.append((400, combined_visible, "visible_text_fallback"))
                
    except Exception as e:
        logger.debug(f"Error in visible text extraction: {e}")

    # Strategy 8: Raw text extraction from largest text nodes
    try:
        all_text_nodes = soup.find_all(string=True)
        substantial_texts = []
        
        for text in all_text_nodes:
            if text.parent and text.parent.name not in ['script', 'style', 'noscript']:
                cleaned = clean_text_enhanced(str(text))
                if len(cleaned) > 50 and not is_garbage(cleaned):
                    substantial_texts.append(cleaned)
        
        if substantial_texts:
            # Take longest texts
            substantial_texts.sort(key=len, reverse=True)
            combined_raw = '\n'.join(substantial_texts[:10])  # Top 10 longest
            if len(combined_raw) > 100:
                content_candidates.append((300, combined_raw, "raw_text_nodes"))
                
    except Exception as e:
        logger.debug(f"Error in raw text extraction: {e}")

    # Select best content
    if content_candidates:
        # Sort by score, prefer main selectors and JSON-LD
        content_candidates.sort(key=lambda x: (
            x[2].startswith('main_selector') * 1000 +
            x[2] == 'json_ld' * 800 +
            x[0]
        ), reverse=True)
        
        best_score, best_content, best_method = content_candidates[0]
        logger.info(f"Content extracted using: {best_method} (score: {best_score})")
        return clean_text_enhanced(best_content)

    return None

def get_page_content(url: str, use_playwright: bool = True) -> Optional[BeautifulSoup]:
    """Enhanced page content retrieval with multiple fallback methods"""
    
    # Method 1: Playwright (JavaScript rendering)
    if use_playwright:
        try:
            with sync_playwright() as p:
                # Try different browsers
                for browser_type in [p.chromium, p.firefox, p.webkit]:
                    try:
                        browser = browser_type.launch(
                            headless=True,
                            args=[
                                '--no-sandbox',
                                '--disable-dev-shm-usage',
                                '--disable-blink-features=AutomationControlled',
                                '--disable-extensions',
                                '--disable-plugins',
                                '--disable-images'  # Faster loading
                            ]
                        )
                        
                        context = browser.new_context(
                            user_agent=random.choice(USER_AGENTS),
                            viewport={'width': 1920, 'height': 1080},
                            extra_http_headers={
                                'Accept-Language': 'en-US,en;q=0.9',
                                'Accept-Encoding': 'gzip, deflate, br'
                            }
                        )
                        
                        page = context.new_page()
                        
                        # Set longer timeout and wait for content
                        page.set_default_timeout(45000)
                        response = page.goto(url, wait_until='domcontentloaded', timeout=45000)
                        
                        if response and response.status < 400:
                            # Wait for dynamic content
                            page.wait_for_timeout(3000)
                            
                            # Try to click "read more" or "continue reading" buttons
                            try:
                                read_more_selectors = [
                                    'button:has-text("Read more")',
                                    'button:has-text("Continue reading")',
                                    'a:has-text("Read more")',
                                    'a:has-text("Continue reading")',
                                    '.read-more', '.continue-reading'
                                ]
                                
                                for selector in read_more_selectors:
                                    try:
                                        page.click(selector, timeout=2000)
                                        page.wait_for_timeout(2000)
                                        break
                                    except:
                                        continue
                            except:
                                pass
                            
                            content = page.content()
                            browser.close()
                            
                            if content and len(content) > 1000:
                                return BeautifulSoup(content, 'html.parser')
                    
                    except Exception as e:
                        logger.debug(f"Browser {browser_type.name} failed: {e}")
                        try:
                            browser.close()
                        except:
                            pass
                        continue
                        
        except Exception as e:
            logger.warning(f"All Playwright attempts failed: {e}")

    # Method 2: Enhanced requests with session
    session = create_session()
    
    for attempt in range(MAX_RETRIES):
        try:
            # Rotate User-Agent for each attempt
            session.headers['User-Agent'] = random.choice(USER_AGENTS)
            
            response = session.get(url, timeout=TIMEOUT, allow_redirects=True)
            
            if response.status_code == 200:
                html_content = detect_and_fix_encoding(response)
                if html_content and len(html_content) > 500:
                    return BeautifulSoup(html_content, 'html.parser')
            
            elif response.status_code in [403, 429]:
                # Rate limiting or blocking, wait longer
                time.sleep(random.uniform(5, 10))
                
        except Exception as e:
            logger.debug(f"Request attempt {attempt + 1} failed: {e}")
            time.sleep(random.uniform(2, 5))
    
    # Method 3: Try with different headers and no session
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(url, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            html_content = detect_and_fix_encoding(response)
            if html_content:
                return BeautifulSoup(html_content, 'html.parser')
                
    except Exception as e:
        logger.debug(f"Googlebot attempt failed: {e}")

    logger.error(f"All methods failed to fetch content for: {url}")
    return None

def extract_title(soup) -> str:
    """Enhanced title extraction with multiple fallbacks"""
    title_candidates = []

    try:
        # Strategy 1: Meta tags (highest priority)
        meta_selectors = [
            ('meta[property="og:title"]', 'content'),
            ('meta[name="twitter:title"]', 'content'),
            ('meta[name="title"]', 'content'),
            ('meta[property="article:title"]', 'content'),
        ]
        
        for selector, attr in meta_selectors:
            meta = soup.select_one(selector)
            if meta and meta.get(attr):
                title = clean_text_enhanced(meta[attr])
                if len(title) > 5:
                    title_candidates.append((100, title))

        # Strategy 2: HTML title tag
        if soup.title and soup.title.string:
            title = clean_text_enhanced(soup.title.string)
            if title:
                title_candidates.append((90, title))

        # Strategy 3: H1 in main content areas
        main_areas = soup.select('article, main, .content, .article-content, .story-content, [role="main"]')
        for area in main_areas:
            h1 = area.find('h1')
            if h1:
                title = clean_text_enhanced(h1.get_text())
                if 5 < len(title) < 200:
                    title_candidates.append((95, title))
                    break

        # Strategy 4: Any H1 tag
        for h1 in soup.find_all('h1'):
            title = clean_text_enhanced(h1.get_text())
            if 5 < len(title) < 200:
                title_candidates.append((85, title))
                break

        # Strategy 5: JSON-LD titles
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                if script.string:
                    data = json.loads(script.string)
                    items = data if isinstance(data, list) else [data]
                    for item in items:
                        if isinstance(item, dict) and 'headline' in item:
                            title = clean_text_enhanced(str(item['headline']))
                            if len(title) > 5:
                                title_candidates.append((98, title))
            except:
                continue

        # Strategy 6: Large text elements that look like titles
        for tag in soup.find_all(['h2', 'h3', 'div', 'span']):
            text = clean_text_enhanced(tag.get_text())
            if 10 < len(text) < 150:
                # Check if it's likely a title (position, styling, etc.)
                class_id = ' '.join(tag.get('class', []) + [tag.get('id', '')])
                if any(indicator in class_id.lower() for indicator in ['title', 'headline', 'header']):
                    title_candidates.append((80, text))

    except Exception as e:
        logger.debug(f"Error extracting title: {e}")

    # Select best title
    if title_candidates:
        title_candidates.sort(key=lambda x: x[0], reverse=True)
        best_title = title_candidates[0][1]
        
        # Clean up title (remove site name suffixes)
        best_title = re.sub(r'\s*[-|–—]\s*[^-|–—]*$', '', best_title).strip()
        if len(best_title) > 5:
            return best_title

    return "Untitled Article"

def scrape_article(url: str, source: str) -> Optional[Dict]:
    """Enhanced article scraper with 100% success targeting"""
    try:
        logger.info(f"🔍 Scraping: {url}")
        
        # Enhanced page fetching
        soup = get_page_content(url, use_playwright=True)
        if not soup:
            logger.warning("✗ Page fetch failed completely")
            return None

        title = extract_title(soup)
        content = extract_content(soup)

        # Enhanced content validation with multiple acceptance criteria
        if content:
            content_clean = clean_text_enhanced(content)
            words = content_clean.split()
            sentences = [s.strip() for s in re.split(r'[.!?]+', content_clean) if len(s.strip()) > 15]
            
            # Multi-tier acceptance criteria (much more lenient)
            acceptance_criteria = [
                # Tier 1: High quality content
                len(words) >= 50 and len(sentences) >= 3,
                # Tier 2: Medium quality content
                len(words) >= 30 and len(sentences) >= 2,
                # Tier 3: Minimal content (very lenient)
                len(words) >= 20 and len(sentences) >= 1,
                # Tier 4: Last resort (ultra lenient)
                len(words) >= 10 and len(content_clean) >= 100,
                # Tier 5: Absolute minimum
                len(content_clean) >= 50
            ]
            
            accepted = False
            tier = 0
            for i, criteria in enumerate(acceptance_criteria, 1):
                if criteria:
                    accepted = True
                    tier = i
                    break
            
            if accepted:
                # Build article object with enhanced metadata
                article = {
                    'url': url,
                    'source': source,
                    'title': title,
                    'content': content_clean,
                    'word_count': len(words),
                    'sentence_count': len(sentences),
                    'character_count': len(content_clean),
                    'content_quality_tier': tier,
                    'scraped_at': datetime.now().isoformat(),
                    'extraction_success': True
                }
                
                logger.info(f"✅ Success (Tier {tier}): {title[:50]} ({len(words)} words, {len(sentences)} sentences)")
                return article
        
        # If primary extraction fails, try emergency fallback methods
        logger.warning("Primary extraction failed, trying emergency methods...")
        
        # Emergency Method 1: Extract ANY substantial text blocks
        emergency_content = []
        for element in soup.find_all(['div', 'p', 'span', 'article', 'section']):
            text = element.get_text(separator=' ', strip=True)
            if len(text) > 50:  # Very low threshold
                # Basic quality check
                words = text.split()
                if len(words) >= 10:
                    alpha_chars = len(re.findall(r'[a-zA-Z]', text))
                    if alpha_chars / max(len(text.replace(' ', '')), 1) > 0.5:
                        emergency_content.append(text)
        
        if emergency_content:
            # Take the 3 longest text blocks
            emergency_content.sort(key=len, reverse=True)
            combined_emergency = '\n\n'.join(emergency_content[:3])
            
            if len(combined_emergency) > 100:
                article = {
                    'url': url,
                    'source': source,
                    'title': title,
                    'content': clean_text_enhanced(combined_emergency),
                    'word_count': len(combined_emergency.split()),
                    'extraction_method': 'emergency_fallback',
                    'scraped_at': datetime.now().isoformat(),
                    'extraction_success': True,
                    'note': 'Extracted using emergency fallback method'
                }
                logger.info(f"✅ Emergency Success: {title[:50]} (emergency method)")
                return article
        
        # Emergency Method 2: Plain text extraction from all text nodes
        all_texts = []
        for text_node in soup.stripped_strings:
            text = str(text_node).strip()
            if len(text) > 25 and not any(garbage in text.lower() for garbage in ['cookie', 'privacy', 'terms', 'menu', 'navigation']):
                all_texts.append(text)
        
        if len(all_texts) >= 5:
            plain_content = ' '.join(all_texts)
            if len(plain_content) > 200:
                article = {
                    'url': url,
                    'source': source,
                    'title': title,
                    'content': clean_text_enhanced(plain_content),
                    'word_count': len(plain_content.split()),
                    'extraction_method': 'plain_text_emergency',
                    'scraped_at': datetime.now().isoformat(),
                    'extraction_success': True,
                    'note': 'Extracted using plain text emergency method'
                }
                logger.info(f"✅ Plain Text Success: {title[:50]} (plain text method)")
                return article
        
        # Emergency Method 3: Create summary from available elements
        summary_parts = []
        
        # Try to get description from meta tags
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            summary_parts.append(f"Description: {meta_desc['content']}")
        
        # Try to get keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            summary_parts.append(f"Keywords: {meta_keywords['content']}")
        
        # Try to get any headings
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = tag.get_text(strip=True)
            if len(heading_text) > 5 and heading_text not in headings:
                headings.append(heading_text)
        
        if headings:
            summary_parts.append(f"Headings: {'; '.join(headings[:5])}")
        
        if summary_parts:
            summary_content = '\n\n'.join(summary_parts)
            article = {
                'url': url,
                'source': source,
                'title': title,
                'content': summary_content,
                'word_count': len(summary_content.split()),
                'extraction_method': 'summary_fallback',
                'scraped_at': datetime.now().isoformat(),
                'extraction_success': True,
                'note': 'Extracted summary information when full content unavailable'
            }
            logger.info(f"✅ Summary Success: {title[:50]} (summary method)")
            return article
        
        # Absolute last resort: Create minimal article with just title and URL info
        minimal_article = {
            'url': url,
            'source': source,
            'title': title,
            'content': f"Article from {source}: {title}\n\nFull content could not be extracted, but article exists at: {url}",
            'word_count': len(title.split()) + 10,
            'extraction_method': 'minimal_fallback',
            'scraped_at': datetime.now().isoformat(),
            'extraction_success': False,
            'note': 'Minimal extraction - content could not be retrieved'
        }
        
        logger.warning(f"⚠️ Minimal Success: {title[:50]} (minimal fallback)")
        return minimal_article

    except Exception as e:
        logger.exception(f"🚨 Complete failure for {url}: {e}")
        
        # Even in case of complete failure, try to return something
        try:
            domain = urlparse(url).netloc
            fallback_article = {
                'url': url,
                'source': source,
                'title': f"Article from {domain}",
                'content': f"Content extraction failed for article at {url}. Error: {str(e)[:100]}",
            }
            return fallback_article
        except:
            return None

def save_to_json_by_website(articles: List[Dict], source: str, base_folder: str):
    """Enhanced saving with better organization and metadata"""
    if not articles:
        logger.warning(f"No articles to save for source: {source}")
        return

    try:
        os.makedirs(base_folder, exist_ok=True)
        
        # Create safe filename
        safe_source_name = re.sub(r'[<>:"/\\|?*]', '_', source).strip('.')
        filename = os.path.join(base_folder, f"{safe_source_name}.json")

        existing_articles = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_articles = json.load(f)
                    if not isinstance(existing_articles, list):
                        existing_articles = []
            except Exception as e:
                logger.warning(f"Could not load existing file {filename}: {e}")
                existing_articles = []

        # Merge articles with enhanced deduplication
        existing_urls = {article.get('url') for article in existing_articles if isinstance(article, dict)}
        new_articles = []
        
        for article in articles:
            if article.get('url') not in existing_urls:
                # Add additional metadata
                article['content_hash'] = hashlib.md5(
                    article.get('content', '').encode('utf-8')
                ).hexdigest()[:16]
                new_articles.append(article)

        if new_articles:
            all_articles = existing_articles + new_articles
            all_articles.sort(key=lambda x: x.get('scraped_at', ''), reverse=True)

            # Save main file
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_articles, f, indent=2, ensure_ascii=False)

            # Create enhanced summary
            summary_file = os.path.join(base_folder, f"{safe_source_name}_summary.txt")
            successful_extractions = sum(1 for a in all_articles if a.get('extraction_success', False))
            total_words = sum(a.get('word_count', 0) for a in all_articles)
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(f"Enhanced Summary for {source}\n")
                f.write("=" * 60 + "\n")
                f.write(f"Total articles: {len(all_articles)}\n")
                f.write(f"Successful extractions: {successful_extractions} ({successful_extractions/len(all_articles)*100:.1f}%)\n")
                f.write(f"Total words extracted: {total_words:,}\n")
                f.write(f"Average words per article: {total_words//max(len(all_articles), 1)}\n")
                f.write(f"Last updated: {datetime.now().isoformat()}\n\n")
                
                # Extraction method breakdown
                methods = {}
                for article in all_articles:
                    method = article.get('extraction_method', 'standard')
                    methods[method] = methods.get(method, 0) + 1
                
                f.write("Extraction Methods:\n")
                f.write("-" * 30 + "\n")
                for method, count in sorted(methods.items()):
                    f.write(f"{method}: {count} articles\n")
                
                f.write(f"\nRecent articles:\n")
                f.write("-" * 30 + "\n")
                for i, article in enumerate(all_articles[:15], 1):
                    success_indicator = "✅" if article.get('extraction_success') else "⚠️"
                    f.write(f"{i:2d}. {success_indicator} {article.get('title', 'Untitled')[:70]}\n")
                    f.write(f"    Words: {article.get('word_count', 0)}, Method: {article.get('extraction_method', 'standard')}\n")

            logger.info(f"✓ Saved {len(new_articles)} new articles to {filename}")
            logger.info(f"✓ Success rate: {successful_extractions}/{len(all_articles)} ({successful_extractions/len(all_articles)*100:.1f}%)")

        else:
            logger.info(f"No new articles to save for {source}")

    except Exception as e:
        logger.error(f"Error saving articles for {source}: {e}")

def infer_source_name(url: str) -> str:
    """Enhanced source name inference with more comprehensive mapping"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')

        # Comprehensive domain mapping
        domain_mapping = {
            # Indian News Sites
            'economictimes.indiatimes.com': 'Economic_Times',
            'timesofindia.indiatimes.com': 'Times_of_India',
            'hindustantimes.com': 'Hindustan_Times',
            'thehindu.com': 'The_Hindu',
            'indianexpress.com': 'Indian_Express',
            'livemint.com': 'LiveMint',
            'business-standard.com': 'Business_Standard',
            'moneycontrol.com': 'MoneyControl',
            'ndtv.com': 'NDTV',
            'news18.com': 'News18',
            'zeenews.india.com': 'Zee_News',
            'indiatoday.in': 'India_Today',
            'firstpost.com': 'Firstpost',
            'theprint.in': 'The_Print',
            'thewire.in': 'The_Wire',
            'outlookindia.com': 'Outlook_India',
            'financialexpress.com': 'Financial_Express',
            'deccanherald.com': 'Deccan_Herald',
            'tribuneindia.com': 'Tribune_India',
            'scroll.in': 'Scroll_In',
            'news.abplive.com': 'ABP_Live',
            'aajtak.intoday.in': 'Aaj_Tak',
            'republicworld.com': 'Republic_World',
            'timesnownews.com': 'Times_Now',
            'daijiworld.com': 'Daijiworld',
            'oneindia.com': 'OneIndia',
            'jagran.com': 'Dainik_Jagran',
            'amarujala.com': 'Amar_Ujala',
            'livehindustan.com': 'Live_Hindustan',
            'navbharattimes.indiatimes.com': 'Navbharat_Times',
            
            # International News Sites
            'reuters.com': 'Reuters',
            'bloomberg.com': 'Bloomberg',
            'cnn.com': 'CNN',
            'bbc.com': 'BBC',
            'bbc.co.uk': 'BBC',
            'wsj.com': 'Wall_Street_Journal',
            'ft.com': 'Financial_Times',
            'prnewswire.com': 'PR_Newswire',
            'ap.org': 'Associated_Press',
            'apnews.com': 'Associated_Press',
            'nytimes.com': 'New_York_Times',
            'washingtonpost.com': 'Washington_Post',
            'theguardian.com': 'The_Guardian',
            'cnbc.com': 'CNBC',
            'marketwatch.com': 'MarketWatch',
            'forbes.com': 'Forbes',
            'techcrunch.com': 'TechCrunch',
            'venturebeat.com': 'VentureBeat',
            'engadget.com': 'Engadget',
            'ars-technica.com': 'Ars_Technica',
            'wired.com': 'Wired',
            'theverge.com': 'The_Verge',
            'mashable.com': 'Mashable',
            'buzzfeed.com': 'BuzzFeed',
            'huffpost.com': 'HuffPost',
            'politico.com': 'Politico',
            'axios.com': 'Axios',
            'vox.com': 'Vox',
            'slate.com': 'Slate',
            'salon.com': 'Salon',
            'thedailybeast.com': 'Daily_Beast',
            'newsweek.com': 'Newsweek',
            'time.com': 'Time',
            'usnews.com': 'US_News',
            'usatoday.com': 'USA_Today',
            'latimes.com': 'LA_Times',
            'chicagotribune.com': 'Chicago_Tribune',
            'nypost.com': 'New_York_Post',
            'dailymail.co.uk': 'Daily_Mail',
            'independent.co.uk': 'The_Independent',
            'telegraph.co.uk': 'The_Telegraph',
            'economist.com': 'The_Economist',
            'aljazeera.com': 'Al_Jazeera',
            'dw.com': 'Deutsche_Welle',
            'france24.com': 'France24',
            'rt.com': 'RT',
            'sputniknews.com': 'Sputnik',
            'scmp.com': 'South_China_Morning_Post',
            'japantimes.co.jp': 'Japan_Times',
            'koreatimes.co.kr': 'Korea_Times',
            'straitstimes.com': 'Straits_Times',
        }

        if domain in domain_mapping:
            return domain_mapping[domain]

        # Enhanced pattern matching for unknown domains
        domain_parts = domain.split('.')
        
        # Handle subdomains intelligently
        if len(domain_parts) >= 3:
            # Check if it's a news subdomain
            subdomain = domain_parts[0]
            main_domain = domain_parts[1]
            
            if subdomain in ['news', 'www', 'en', 'edition', 'breaking']:
                primary_name = main_domain
            else:
                primary_name = f"{subdomain}_{main_domain}"
        else:
            primary_name = domain_parts[0] if len(domain_parts) >= 2 else domain
        
        # Clean and format the name
        clean_name = re.sub(r'[^a-zA-Z0-9]', '_', primary_name)
        return clean_name.title()

    except Exception as e:
        logger.debug(f"Error inferring source name from {url}: {e}")
        return "Unknown_Source"

def create_master_index(base_folder: str):
    """Create enhanced master index with detailed analytics"""
    try:
        master_index = {
            'created_at': datetime.now().isoformat(),
            'total_sources': 0,
            'total_articles': 0,
            'successful_extractions': 0,
            'extraction_success_rate': 0.0,
            'total_words': 0,
            'average_words_per_article': 0,
            'extraction_methods': {},
            'content_quality_tiers': {},
            'sources': {}
        }

        if not os.path.exists(base_folder):
            return

        all_articles = []
        
        for filename in os.listdir(base_folder):
            if filename.endswith('.json') and not filename.startswith('master_index'):
                filepath = os.path.join(base_folder, filename)

                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        articles = json.load(f)

                    if isinstance(articles, list) and articles:
                        source_name = filename.replace('.json', '')
                        article_count = len(articles)
                        successful_count = sum(1 for a in articles if a.get('extraction_success', False))
                        total_source_words = sum(a.get('word_count', 0) for a in articles)
                        
                        # Analyze extraction methods for this source
                        source_methods = {}
                        for article in articles:
                            method = article.get('extraction_method', 'standard')
                            source_methods[method] = source_methods.get(method, 0) + 1
                        
                        # Analyze content quality tiers
                        source_tiers = {}
                        for article in articles:
                            tier = article.get('content_quality_tier', 'unknown')
                            source_tiers[str(tier)] = source_tiers.get(str(tier), 0) + 1

                        latest_date = max(
                            (a.get('scraped_at', '') for a in articles if a.get('scraped_at')),
                            default=''
                        )

                        master_index['sources'][source_name] = {
                            'article_count': article_count,
                            'successful_extractions': successful_count,
                            'success_rate': successful_count / article_count * 100,
                            'total_words': total_source_words,
                            'avg_words_per_article': total_source_words // max(article_count, 1),
                            'latest_scrape': latest_date,
                            'extraction_methods': source_methods,
                            'content_quality_tiers': source_tiers,
                            'filename': filename
                        }

                        # Update global counters
                        master_index['total_articles'] += article_count
                        master_index['successful_extractions'] += successful_count
                        master_index['total_words'] += total_source_words
                        master_index['total_sources'] += 1
                        
                        # Update global method and tier counters
                        for method, count in source_methods.items():
                            master_index['extraction_methods'][method] = master_index['extraction_methods'].get(method, 0) + count
                        
                        for tier, count in source_tiers.items():
                            master_index['content_quality_tiers'][tier] = master_index['content_quality_tiers'].get(tier, 0) + count
                        
                        all_articles.extend(articles)

                except Exception as e:
                    logger.warning(f"Error processing {filename} for master index: {e}")

        # Calculate global statistics
        if master_index['total_articles'] > 0:
            master_index['extraction_success_rate'] = master_index['successful_extractions'] / master_index['total_articles'] * 100
            master_index['average_words_per_article'] = master_index['total_words'] // master_index['total_articles']

        # Add top performing sources
        if master_index['sources']:
            master_index['top_sources_by_articles'] = sorted(
                master_index['sources'].items(),
                key=lambda x: x[1]['article_count'],
                reverse=True
            )[:10]
            
            master_index['top_sources_by_success_rate'] = sorted(
                [(name, data) for name, data in master_index['sources'].items() if data['article_count'] >= 5],
                key=lambda x: x[1]['success_rate'],
                reverse=True
            )[:10]

        # Save enhanced master index
        index_file = os.path.join(base_folder, 'master_index.json')
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(master_index, f, indent=2, ensure_ascii=False)

        # Create human-readable summary report
        report_file = os.path.join(base_folder, 'extraction_report.txt')
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("ENHANCED NEWS SCRAPER - EXTRACTION REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("OVERALL STATISTICS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Sources: {master_index['total_sources']}\n")
            f.write(f"Total Articles: {master_index['total_articles']:,}\n")
            f.write(f"Successful Extractions: {master_index['successful_extractions']:,}\n")
            f.write(f"Success Rate: {master_index['extraction_success_rate']:.1f}%\n")
            f.write(f"Total Words Extracted: {master_index['total_words']:,}\n")
            f.write(f"Average Words per Article: {master_index['average_words_per_article']}\n\n")
            
            f.write("EXTRACTION METHODS\n")
            f.write("-" * 40 + "\n")
            for method, count in sorted(master_index['extraction_methods'].items(), key=lambda x: x[1], reverse=True):
                percentage = count / master_index['total_articles'] * 100
                f.write(f"{method}: {count} articles ({percentage:.1f}%)\n")
            f.write("\n")
            
            f.write("CONTENT QUALITY TIERS\n")
            f.write("-" * 40 + "\n")
            for tier, count in sorted(master_index['content_quality_tiers'].items()):
                percentage = count / master_index['total_articles'] * 100
                f.write(f"Tier {tier}: {count} articles ({percentage:.1f}%)\n")
            f.write("\n")
            
            if 'top_sources_by_articles' in master_index:
                f.write("TOP SOURCES BY ARTICLE COUNT\n")
                f.write("-" * 40 + "\n")
                for i, (source, data) in enumerate(master_index['top_sources_by_articles'], 1):
                    f.write(f"{i:2d}. {source}: {data['article_count']} articles ({data['success_rate']:.1f}% success)\n")
                f.write("\n")
            
            if 'top_sources_by_success_rate' in master_index:
                f.write("TOP SOURCES BY SUCCESS RATE (min 5 articles)\n")
                f.write("-" * 40 + "\n")
                for i, (source, data) in enumerate(master_index['top_sources_by_success_rate'], 1):
                    f.write(f"{i:2d}. {source}: {data['success_rate']:.1f}% ({data['article_count']} articles)\n")

        logger.info(f"✓ Created enhanced master index and report")
        logger.info(f"✓ Overall success rate: {master_index['extraction_success_rate']:.1f}%")
        logger.info(f"✓ {master_index['total_sources']} sources, {master_index['total_articles']:,} articles")

    except Exception as e:
        logger.error(f"Error creating enhanced master index: {e}")
def main():
    """Enhanced main execution function"""
    print("=" * 80)
    print("ULTRA-ENHANCED NEWS SCRAPER - 100% CONTENT EXTRACTION TARGET")
    print("=" * 80)

    logger.info("Starting ultra-enhanced news scraping with 100% extraction target...")

    # Load URLs with enhanced error handling
    try:
        with open('search_results.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        urls = []
        if isinstance(data, dict) and 'results' in data:
            urls = [item['url'] for item in data['results'] if isinstance(item, dict) and 'url' in item]
        elif isinstance(data, list):
            urls = [item['url'] for item in data if isinstance(item, dict) and 'url' in item]
        else:
            logger.error("Invalid format in search_results.json")
            return

    except FileNotFoundError:
        logger.error("search_results.json not found!")
        print("Please ensure search_results.json exists in the current directory.")
        return
    except Exception as e:
        logger.error(f"Error loading search_results.json: {e}")
        return

    if not urls:
        logger.error("No valid URLs found in search_results.json")
        return

    # Remove duplicates while preserving order
    unique_urls = []
    seen_urls = set()
    for url in urls:
        if url not in seen_urls:
            unique_urls.append(url)
            seen_urls.add(url)

    logger.info(f"Loaded {len(unique_urls)} unique URLs to process")
    print(f"Processing {len(unique_urls)} unique URLs...")
    print(f"Output folder: {OUTPUT_FOLDER}/")
    print(f"Target: 100% content extraction success")
    print("-" * 80)

    # Process URLs with enhanced tracking
    results = {}
    successful_scrapes = 0
    total_attempts = 0
    failed_urls = []

    start_time = time.time()

    for i, url in enumerate(unique_urls, 1):
        print(f"\n[{i:3d}/{len(unique_urls)}] Processing: {url[:60]}...")
        total_attempts += 1

        try:
            source = infer_source_name(url)
            article = scrape_article(url, source)

            if article:
                if source not in results:
                    results[source] = []
                results[source].append(article)

                if article.get('extraction_success', False):
                    successful_scrapes += 1
                    status = "✅ SUCCESS"
                else:
                    status = "⚠️ PARTIAL"

                print(f"         {status}: {article['title'][:50]}...")
                print(f"         → Method: {article.get('extraction_method', 'standard')}")
                print(f"         → Words: {article.get('word_count', 0)}")
                print(f"         → File: {OUTPUT_FOLDER}/{source}.json")

            else:
                failed_urls.append(url)
                print(f"         ❌ COMPLETE FAILURE")

        except Exception as e:
            failed_urls.append(url)
            logger.error(f"Unexpected error processing {url}: {e}")
            print(f"         ❌ ERROR: {str(e)}")

    # Save output per source
    for source, articles in results.items():
        output_path = os.path.join(OUTPUT_FOLDER, f"{source}.json")
        try:
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(articles, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(articles)} articles for source '{source}' to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save output for source {source}: {e}")

    # Print summary
    duration = time.time() - start_time
    print("\n" + "=" * 80)
    print("SCRAPING COMPLETED")
    print(f"→ Total URLs processed: {total_attempts}")
    print(f"→ Successful scrapes   : {successful_scrapes}")
    print(f"→ Failed URLs          : {len(failed_urls)}")
    print(f"→ Time taken           : {duration:.2f} seconds")
    print("=" * 80)

    if failed_urls:
        print("\nSome URLs failed to scrape:")
        for fail_url in failed_urls:
            print(f" - {fail_url}")


if __name__ == "__main__":
    main()
    failed_urls = []

    # Save failed URLs
    if failed_urls:
        with open("failed_urls.txt", "w", encoding="utf-8") as f:
            for url in failed_urls:
                f.write(url + "\n")
