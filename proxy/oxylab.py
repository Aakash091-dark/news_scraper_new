import requests
import os
import dotenv
import logging
from datetime import datetime
import pytz
from urllib.parse import urlparse

# Load environment variables
dotenv.load_dotenv()

# Timezone
india_tz = pytz.timezone('Asia/Kolkata')

# Set up error logger
error_logger = logging.getLogger('error_logger')
error_logger.setLevel(logging.ERROR)
error_handler = logging.FileHandler('proxy_content_errors.log')
error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
error_handler.setFormatter(error_formatter)
error_logger.addHandler(error_handler)

# Set up proxy activity logger
proxy_logger = logging.getLogger('proxy_logger')
proxy_logger.setLevel(logging.INFO)
proxy_handler = logging.FileHandler('proxy.log')
proxy_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
proxy_handler.setFormatter(proxy_formatter)
proxy_logger.addHandler(proxy_handler)

# Folder for HTML logs
html_log_dir = "html_logs"
os.makedirs(html_log_dir, exist_ok=True)

def sanitize_filename(url):
    parsed = urlparse(url)
    domain = parsed.netloc.replace(":", "_")
    path = parsed.path.replace("/", "_").strip("_")
    if not path:
        path = "index"
    return f"{domain}_{path}.html"

def write_html_log(url, content):
    timestamp = datetime.now(india_tz).strftime('%Y-%m-%d %H:%M:%S %Z%z')
    filename = sanitize_filename(url)
    file_path = os.path.join(html_log_dir, filename)

    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(f"\n<!-- {timestamp} -->\n")
        f.write(content.decode('utf-8', errors='replace'))
        f.write("\n<!-- End of log entry -->\n\n")

def proxy_content(url):
    # USERNAME = os.getenv("user")
    # PASSWORD = os.getenv("pass")

    # proxies = {
    #     'http': f'http://{USERNAME}:{PASSWORD}@unblock.oxylabs.io:60000',
    #     'https': f'https://{USERNAME}:{PASSWORD}@unblock.oxylabs.io:60000',
    # }

    try:
        proxy_logger.info(f"Sending request to {url}")
        response = requests.get(url=url)
        response.raise_for_status()
        proxy_logger.info(f"Received response with status code {response.status_code} for {url}")

        if response.status_code != 200:
            response = requests.get(url=url)

        write_html_log(url, response.content)
        return response.content

    except requests.exceptions.RequestException as e:
        error_logger.error(f"Error fetching URL {url}: {e}")
        proxy_logger.error(f"Failed to fetch {url} - {e}")
        return None
