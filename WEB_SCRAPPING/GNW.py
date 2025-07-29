import json
import requests
from bs4 import BeautifulSoup
import time
import os
import re
import logging
from typing import Optional, Dict, List
import random
from urllib.parse import urlparse
from datetime import datetime
import chardet
from playwright.sync_api import sync_playwright

# Configuration
OUTPUT_FOLDER = "data"  # Changed from "scraped_news" to "data"
REQUEST_DELAY = (1, 3)
TIMEOUT = 30
CONTENT_MIN_LENGTH = 5
MAX_RETRIES = 3

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
]

# Improved garbage patterns
GARBAGE_PATTERNS = [
    r"^\s*(javascript|error|404|page not found|loading|redirect)\s*$",
    r"^\s*(advertisement|sponsored content|ads by|click here)\s*$",
    r"^\s*(\w{1,2}|\d+)\s*$",
    r"^\s*(home|menu|search|login|signup|next|previous|back|share|like|tweet)\s*$",
    r"^\s*(cookie|privacy policy|terms of service|subscribe|newsletter)\s*$",
    r"^\s*[\W\d\s]*$",  # Only symbols, numbers, and whitespace
]


def create_session():
    session = requests.Session()
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "DNT": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Referer": random.choice(
            [
                "https://google.com",
                "https://twitter.com",
                "https://news.google.com",
            ]
        ),
    }
    session.headers.update(headers)
    return session


def detect_and_fix_encoding(response) -> str:
    """Detect and fix encoding issues"""
    try:
        # First try the response's apparent encoding
        if response.encoding and response.encoding.lower() != "iso-8859-1":
            return response.text

        # Use chardet to detect encoding
        detected = chardet.detect(response.content)
        if detected and detected["encoding"] and detected["confidence"] > 0.7:
            try:
                return response.content.decode(detected["encoding"])
            except (UnicodeDecodeError, LookupError):
                pass

        # Try common encodings
        for encoding in ["utf-8", "utf-16", "windows-1252", "iso-8859-1"]:
            try:
                return response.content.decode(encoding)
            except (UnicodeDecodeError, LookupError):
                continue

        # Fallback to response.text with error handling
        return response.text
    except Exception as e:
        logger.warning(f"Encoding detection failed: {e}")
        return response.text


def is_garbage(text: str) -> bool:
    """Improved garbage detection"""
    if not text or len(text.strip()) < 15:
        return True

    text_clean = text.strip().lower()

    # Check garbage patterns
    for pattern in GARBAGE_PATTERNS:
        if re.match(pattern, text_clean, re.IGNORECASE):
            return True

    # Check character composition
    alpha_chars = len(re.findall(r"[a-zA-Z]", text))
    total_chars = len(text.replace(" ", ""))

    if total_chars > 0 and (alpha_chars / total_chars) < 0.3:
        return True

    # Check for meaningful words
    words = text_clean.split()
    if len(words) < 3:
        return True

    # Check if most words are very short (likely navigation/UI elements)
    short_words = sum(1 for word in words if len(word) <= 2)
    if len(words) > 0 and (short_words / len(words)) > 0.7:
        return True

    return False


def clean_text(text: str) -> str:
    """Enhanced text cleaning"""
    if not text:
        return ""

    # Fix encoding issues
    text = text.replace("\ufffd", "")  # Unicode replacement character
    text = text.replace("\xa0", " ")  # Non-breaking space
    text = text.replace("\u200b", "")  # Zero width space

    # Remove control characters
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # Fix common encoding artifacts
    text = re.sub(r"â€™", "'", text)  # Right single quotation mark
    text = re.sub(r"â€œ|â€\x9d", '"', text)  # Left/right double quotation marks
    text = re.sub(r'â€"', "–", text)  # En dash
    text = re.sub(r'â€"', "—", text)  # Em dash

    # Normalize whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    text = re.sub(r"^\s+|\s+$", "", text, flags=re.MULTILINE)

    return text.strip()


def extract_content_improved(soup):
    """Improved content extraction with better filtering"""

    # Remove problematic elements
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "nav",
            "header",
            "footer",
            "aside",
            "iframe",
            "form",
            "button",
        ]
    ):
        tag.decompose()

    # Remove elements with navigation-related classes/ids
    nav_patterns = [
        "nav",
        "menu",
        "sidebar",
        "footer",
        "header",
        "breadcrumb",
        "social",
        "share",
        "comment",
        "ad",
        "advertisement",
        "promo",
    ]
    for pattern in nav_patterns:
        for element in soup.find_all(attrs={"class": re.compile(pattern, re.I)}):
            element.decompose()
        for element in soup.find_all(attrs={"id": re.compile(pattern, re.I)}):
            element.decompose()

    content_candidates = []

    # Strategy 1: Article/main content containers
    main_selectors = [
        "article",
        "main",
        '[role="main"]',
        ".article-content",
        ".story-content",
        ".post-content",
        ".entry-content",
        ".article-body",
        ".story-body",
        ".post-body",
        ".news-content",
        ".content-area",
        ".main-content",
        ".primary-content",
        "#main-content",
        "#content",
        "#article",
        "#story",
    ]

    for selector in main_selectors:
        try:
            elements = soup.select(selector)
            for element in elements:
                # Extract paragraphs and meaningful text blocks
                paragraphs = []

                # Get all text-containing elements
                for tag in element.find_all(
                    ["p", "div", "span", "h1", "h2", "h3", "h4", "h5", "h6"]
                ):
                    text = tag.get_text(separator=" ", strip=True)
                    if text and len(text) > 30 and not is_garbage(text):
                        # Check if this text is not already included in a parent
                        is_duplicate = False
                        for existing in paragraphs:
                            if text in existing or existing in text:
                                if len(text) > len(existing):
                                    paragraphs.remove(existing)
                                else:
                                    is_duplicate = True
                                break

                        if not is_duplicate:
                            paragraphs.append(text)

                if len(paragraphs) >= 2:
                    content = "\n\n".join(paragraphs)
                    content = clean_text(content)
                    if len(content) > CONTENT_MIN_LENGTH:
                        content_candidates.append(
                            (content, len(content), "main_selector")
                        )
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {e}")

    # Strategy 2: Find the largest meaningful text block
    try:
        all_paragraphs = []
        for tag in soup.find_all(["p", "div"]):
            text = tag.get_text(separator=" ", strip=True)
            if text and len(text) > 40 and not is_garbage(text):
                # Check for meaningful content indicators
                words = text.split()
                if len(words) >= 8:
                    all_paragraphs.append(text)

        if len(all_paragraphs) >= 2:
            # Remove duplicates
            unique_paragraphs = []
            seen = set()

            for para in all_paragraphs:
                para_signature = para.lower()[:150]  # First 150 chars for comparison
                if para_signature not in seen:
                    seen.add(para_signature)
                    unique_paragraphs.append(para)

            if len(unique_paragraphs) >= 2:
                content = "\n\n".join(unique_paragraphs)
                content = clean_text(content)
                if len(content) > CONTENT_MIN_LENGTH:
                    content_candidates.append(
                        (content, len(content), "paragraph_extraction")
                    )
    except Exception as e:
        logger.debug(f"Error in paragraph extraction: {e}")

    # Strategy 3: Try to find content by common patterns
    try:
        content_patterns = [
            'div[class*="story"]',
            'div[class*="article"]',
            'div[class*="content"]',
            'div[class*="text"]',
            'div[class*="body"]',
            'section[class*="content"]',
            'div[id*="story"]',
            'div[id*="article"]',
            'div[id*="content"]',
        ]

        for pattern in content_patterns:
            elements = soup.select(pattern)
            for element in elements:
                text = element.get_text(separator=" ", strip=True)
                if text and len(text) > 200:
                    # Split into sentences and clean
                    sentences = re.split(r"[.!?]+", text)
                    good_sentences = []

                    for sentence in sentences:
                        sentence = sentence.strip()
                        if len(sentence) > 25 and not is_garbage(sentence):
                            good_sentences.append(sentence)

                    if len(good_sentences) >= 3:
                        content = ". ".join(good_sentences)
                        if not content.endswith("."):
                            content += "."
                        content = clean_text(content)
                        if len(content) > CONTENT_MIN_LENGTH:
                            content_candidates.append(
                                (content, len(content), "pattern_match")
                            )
    except Exception as e:
        logger.debug(f"Error in pattern extraction: {e}")

    # Return the best content (longest with good quality indicators)
    if content_candidates:
        # Sort by length and prefer main selectors
        content_candidates.sort(
            key=lambda x: (x[2] == "main_selector", x[1]), reverse=True
        )
        return content_candidates[0][0]

    return None


def get_page_content(
    url: str, retries: int = MAX_RETRIES, use_playwright: bool = False
) -> Optional[BeautifulSoup]:
    """Fetch page content using requests or Playwright (for JS-rendered pages)."""
    for attempt in range(retries):
        try:
            if use_playwright:
                from playwright.sync_api import sync_playwright

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(url, timeout=30000)
                    html = page.content()
                    browser.close()
                    return BeautifulSoup(html, "html.parser")

            # Default requests-based method
            session = create_session()
            if attempt > 0:
                session.headers.update({"Referer": "https://www.google.com/"})

            resp = session.get(url, timeout=10)
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")

        except Exception as e:
            logger.warning(f"Retry {attempt+1}/{retries} failed for {url}: {e}")
            time.sleep(2)
    return None


def extract_title(soup) -> str:
    """Enhanced title extraction"""
    title_candidates = []

    try:
        # Title tag
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            if title:
                title_candidates.append(title)

        # Meta tags
        for prop in ["og:title", "twitter:title"]:
            meta = soup.find("meta", property=prop) or soup.find(
                "meta", attrs={"name": prop}
            )
            if meta and meta.get("content"):
                title_candidates.append(meta["content"].strip())

        # H1 tags in main content areas
        main_areas = soup.select(
            "article, main, .content, .article-content, .story-content"
        )
        for area in main_areas:
            h1 = area.find("h1")
            if h1:
                text = h1.get_text(strip=True)
                if text and 5 < len(text) < 200:
                    title_candidates.append(text)
                    break  # Prefer first h1 in main content

        # Fallback to any h1
        if not any(len(t) > 10 for t in title_candidates):
            for h1 in soup.find_all("h1"):
                text = h1.get_text(strip=True)
                if text and 5 < len(text) < 200:
                    title_candidates.append(text)
                    break

    except Exception as e:
        logger.debug(f"Error extracting title: {e}")

    # Clean and return best title
    for title in title_candidates:
        title = clean_text(title)
        if title and len(title) > 5:
            # Remove site name suffixes
            title = re.sub(r"\s*[-|–]\s*[^-|–]*$", "", title).strip()
            if title and len(title) > 5:
                return title

    return "Untitled Article"


# config.py or top-of-file constants
CONTENT_MIN_LENGTH = 5  # Lowered
SHORT_CONTENT_LINES = 2  # Minimum good lines if content is short


def scrape_article(url: str, source: str) -> Optional[Dict]:
    """High-reliability article scraper using layered fallback and heuristics."""
    try:
        logger.info(f"🔍 Scraping: {url}")
        soup = get_page_content(url, use_playwright=True)
        if not soup:
            logger.warning("✗ Page fetch failed.")
            return None

        title = extract_title(soup)
        content = extract_content_improved(soup)

        # ── Tier 1: Full content check ──────────────────────────────
        if content and len(content.strip()) >= CONTENT_MIN_LENGTH:
            words = content.split()
            if len(words) >= 20:
                sentences = re.split(r"[.!?]+", content)
                if sum(len(s.strip()) > 20 for s in sentences) >= 2:
                    return _build_article(url, source, title, content)

        # ── Tier 2: Structured JSON-LD ─────────────────────────────
        json_ld_content = extract_json_ld(soup)
        if json_ld_content and len(json_ld_content.split()) > 20:
            return _build_article(
                url, source, title, json_ld_content, note="From JSON-LD"
            )

        # ── Tier 3: Paragraph fallback ─────────────────────────────
        paragraphs = soup.find_all("p")
        clean_paragraphs = [
            p.get_text(strip=True)
            for p in paragraphs
            if len(p.get_text(strip=True)) > 40 and not is_garbage(p.get_text())
        ]
        if len(clean_paragraphs) >= SHORT_CONTENT_LINES:
            combined = "\n".join(clean_paragraphs[:SHORT_CONTENT_LINES])
            return _build_article(
                url, source, title, combined, short=True, note="From <p> fallback"
            )

        # ── Tier 4: Semantic scoring ───────────────────────────────
        scored = semantic_paragraph_filter(paragraphs)
        if scored:
            combined = "\n".join(scored[:SHORT_CONTENT_LINES])
            return _build_article(
                url, source, title, combined, short=True, note="From semantic scoring"
            )

        # ── Tier 5: Visible text fallback ──────────────────────────
        visible = [t.strip() for t in soup.stripped_strings if len(t.strip()) > 40]
        if len(visible) >= SHORT_CONTENT_LINES:
            combined = "\n".join(visible[:SHORT_CONTENT_LINES])
            return _build_article(
                url,
                source,
                title,
                combined,
                short=True,
                note="From visible text fallback",
            )

        logger.error("❌ No valid content found after all attempts.")
        return None

    except Exception as e:
        logger.exception(f"🚨 Error scraping {url}: {e}")
        return None


def _build_article(url, source, title, content, short=False, note=None):
    words = content.split()
    base = {
        "url": url,
        "source": source,
        "title": title,
        "scraped_at": datetime.now().isoformat(),
        "content_length": len(content),
        "word_count": len(words),
    }
    if short:
        base["short_content"] = content.splitlines()
    else:
        base["content"] = content.strip()
        base["sentence_count"] = len(re.split(r"[.!?]+", content))
    if note:
        base["note"] = note
    logger.info(
        f"✅ Scraped ({'short' if short else 'full'}): {title[:50]} ({len(words)} words)"
    )
    return base


def semantic_paragraph_filter(paragraphs):
    # Very basic scoring for now
    scored = []
    for p in paragraphs:
        text = p.get_text(strip=True)
        if len(text) < 40 or is_garbage(text):
            continue
        score = len(text) + text.count(".") * 5
        scored.append((score, text))
    scored.sort(reverse=True)
    return [text for _, text in scored[:5]]


def extract_json_ld(soup):
    scripts = soup.find_all("script", type="application/ld+json")
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict) and "articleBody" in data:
                return data["articleBody"]
        except:
            continue
    return ""


def save_to_json_by_website(articles: List[Dict], source: str, base_folder: str):
    """Enhanced saving with website-specific organization in 'data' folder"""
    if not articles:
        logger.warning(f"No articles to save for source: {source}")
        return

    try:
        # Create the main data folder
        os.makedirs(base_folder, exist_ok=True)

        # Create filename based on source (clean the source name for valid filename)
        safe_source_name = re.sub(
            r'[<>:"/\\|?*]', "_", source
        )  # Replace invalid filename chars
        safe_source_name = safe_source_name.strip(".")  # Remove leading/trailing dots
        filename = os.path.join(base_folder, f"{safe_source_name}.json")

        existing_articles = []
        if os.path.exists(filename):
            try:
                with open(filename, "r", encoding="utf-8") as f:
                    existing_articles = json.load(f)
                    if not isinstance(existing_articles, list):
                        existing_articles = []
            except Exception as e:
                logger.warning(f"Could not load existing file {filename}: {e}")
                existing_articles = []

        # Merge articles (avoid duplicates by URL)
        existing_urls = {
            article.get("url")
            for article in existing_articles
            if isinstance(article, dict)
        }
        new_articles = [
            article for article in articles if article.get("url") not in existing_urls
        ]

        if new_articles:
            all_articles = existing_articles + new_articles

            # Sort articles by scraped_at date (newest first)
            all_articles.sort(key=lambda x: x.get("scraped_at", ""), reverse=True)

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(all_articles, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ Saved {len(new_articles)} new articles to {filename}")

            # Create a summary file for the source
            summary_file = os.path.join(base_folder, f"{safe_source_name}_summary.txt")
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(f"Summary for {source}\n")
                f.write("=" * 50 + "\n")
                f.write(f"Total articles: {len(all_articles)}\n")
                f.write(f"Last updated: {datetime.now().isoformat()}\n\n")
                f.write("Recent articles:\n")
                f.write("-" * 30 + "\n")
                for i, article in enumerate(all_articles[:10], 1):  # Show latest 10
                    f.write(f"{i:2d}. {article.get('title', 'Untitled')[:80]}\n")
                    f.write(f"    {article.get('scraped_at', 'Unknown date')}\n")
                    f.write(f"    {article.get('word_count', 0)} words\n\n")

        else:
            logger.info(f"No new articles to save for {source}")

    except Exception as e:
        logger.error(f"Error saving articles for {source}: {e}")


def infer_source_name(url: str) -> str:
    """Enhanced source name inference with better news website recognition"""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace("www.", "")

        # Enhanced mapping for Indian and international news sites
        domain_mapping = {
            # Major Indian news sites
            "economictimes.indiatimes.com": "Economic_Times",
            "timesofindia.indiatimes.com": "Times_of_India",
            "hindustantimes.com": "Hindustan_Times",
            "thehindu.com": "The_Hindu",
            "indianexpress.com": "Indian_Express",
            "livemint.com": "LiveMint",
            "business-standard.com": "Business_Standard",
            "moneycontrol.com": "MoneyControl",
            "ndtv.com": "NDTV",
            "news18.com": "News18",
            "zeenews.india.com": "Zee_News",
            "indiatoday.in": "India_Today",
            "firstpost.com": "Firstpost",
            "theprint.in": "The_Print",
            "thewire.in": "The_Wire",
            "outlookindia.com": "Outlook_India",
            "financialexpress.com": "Financial_Express",
            "deccanherald.com": "Deccan_Herald",
            "tribuneindia.com": "Tribune_India",
            "scroll.in": "Scroll_In",
            "news.abplive.com": "ABP_Live",
            "aajtak.intoday.in": "Aaj_Tak",
            "republicworld.com": "Republic_World",
            "timesnownews.com": "Times_Now",
            # International news sites
            "reuters.com": "Reuters",
            "bloomberg.com": "Bloomberg",
            "cnn.com": "CNN",
            "bbc.com": "BBC",
            "bbc.co.uk": "BBC",
            "wsj.com": "Wall_Street_Journal",
            "ft.com": "Financial_Times",
            "prnewswire.com": "PR_Newswire",
            "ap.org": "Associated_Press",
            "apnews.com": "Associated_Press",
            "nytimes.com": "New_York_Times",
            "washingtonpost.com": "Washington_Post",
            "theguardian.com": "The_Guardian",
            "cnbc.com": "CNBC",
            "marketwatch.com": "MarketWatch",
            "forbes.com": "Forbes",
            "techcrunch.com": "TechCrunch",
            "venturebeat.com": "VentureBeat",
        }

        if domain in domain_mapping:
            return domain_mapping[domain]

        # Try to extract main domain name for unknown sites
        domain_parts = domain.split(".")
        if len(domain_parts) >= 2:
            # Take the main domain name (e.g., 'example' from 'news.example.com')
            main_domain = (
                domain_parts[-2] if domain_parts[-2] != "co" else domain_parts[-3]
            )
            # Clean and format
            clean_name = re.sub(r"[^a-zA-Z0-9]", "_", main_domain)
            return clean_name.title()

        # Fallback to generic processing
        domain_clean = domain.split(".")[0]
        return re.sub(r"[^a-zA-Z0-9]", "_", domain_clean).title()

    except Exception as e:
        logger.debug(f"Error inferring source name from {url}: {e}")
        return "Unknown_Source"


def create_master_index(base_folder: str):
    """Create a master index of all scraped articles"""
    try:
        master_index = {
            "created_at": datetime.now().isoformat(),
            "total_sources": 0,
            "total_articles": 0,
            "sources": {},
        }

        if not os.path.exists(base_folder):
            return

        # Scan all JSON files in the data folder
        for filename in os.listdir(base_folder):
            if filename.endswith(".json") and not filename.startswith("master_index"):
                filepath = os.path.join(base_folder, filename)

                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        articles = json.load(f)

                    if isinstance(articles, list) and articles:
                        source_name = filename.replace(".json", "")
                        article_count = len(articles)

                        # Get latest article date
                        latest_date = max(
                            article.get("scraped_at", "")
                            for article in articles
                            if article.get("scraped_at")
                        )

                        # Calculate average word count
                        total_words = sum(
                            article.get("word_count", 0) for article in articles
                        )
                        avg_words = (
                            total_words // article_count if article_count > 0 else 0
                        )

                        master_index["sources"][source_name] = {
                            "article_count": article_count,
                            "latest_scrape": latest_date,
                            "avg_word_count": avg_words,
                            "filename": filename,
                        }

                        master_index["total_articles"] += article_count
                        master_index["total_sources"] += 1

                except Exception as e:
                    logger.warning(f"Error processing {filename} for master index: {e}")

        # Save master index
        index_file = os.path.join(base_folder, "master_index.json")
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(master_index, f, indent=2, ensure_ascii=False)

        logger.info(
            f"✓ Created master index with {master_index['total_sources']} sources and {master_index['total_articles']} articles"
        )

    except Exception as e:
        logger.error(f"Error creating master index: {e}")


def main():
    """Main execution function"""
    print("=" * 70)
    print("ENHANCED NEWS SCRAPER - DATA FOLDER ORGANIZATION")
    print("=" * 70)

    logger.info("Starting enhanced news scraping with data folder organization...")

    # Load URLs
    try:
        with open("search_results.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and "results" in data:
            urls = [
                item["url"]
                for item in data["results"]
                if isinstance(item, dict) and "url" in item
            ]
        elif isinstance(data, list):
            urls = [
                item["url"] for item in data if isinstance(item, dict) and "url" in item
            ]
        else:
            logger.error("Invalid format in search_results.json")
            return

    except FileNotFoundError:
        logger.error("search_results.json not found!")
        return
    except Exception as e:
        logger.error(f"Error loading search_results.json: {e}")
        return

    if not urls:
        logger.error("No valid URLs found in search_results.json")
        return

    logger.info(f"Loaded {len(urls)} URLs to process")
    print(f"Processing {len(urls)} URLs...")
    print(f"Output folder: {OUTPUT_FOLDER}/")
    print("-" * 70)

    # Process URLs
    results = {}
    successful_scrapes = 0

    for i, url in enumerate(urls, 1):
        print(f"\n[{i:3d}/{len(urls)}] Processing: {url[:80]}...")

        source = infer_source_name(url)
        article = scrape_article(url, source)

        if article:
            if source not in results:
                results[source] = []
            results[source].append(article)
            successful_scrapes += 1
            print(f"         ✓ Success: {article['title'][:60]}...")
            print(f"         → Will save to: {OUTPUT_FOLDER}/{source}.json")
        else:
            print(f"         ✗ Failed to extract content")

        # Respectful delay
        time.sleep(random.uniform(*REQUEST_DELAY))

    # Save results by website
    print("\n" + "-" * 70)
    print("SAVING RESULTS BY WEBSITE...")

    total_articles = 0
    for source, articles in results.items():
        save_to_json_by_website(articles, source, OUTPUT_FOLDER)
        total_articles += len(articles)

    # Create master index
    if results:
        create_master_index(OUTPUT_FOLDER)
    else:
        logger.error("No articles scraped. Cannot create master index.")
        print("No articles scraped. Master index not created.")
    print(
        f"\n✓ Successfully scraped {successful_scrapes} articles from {len(results)} sources."
    )
    print(f"Total articles saved: {total_articles}")
    print(f"Master index created in: {OUTPUT_FOLDER}/master_index.json")


if __name__ == "__main__":
    main()
    failed_urls = []

    # Save failed URLs
    if failed_urls:
        with open("failed_urls.txt", "w", encoding="utf-8") as f:
            for url in failed_urls:
                f.write(url + "\n")
