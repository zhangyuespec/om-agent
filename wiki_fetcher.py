import requests
from typing import List, Dict
import logging
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import socket

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WikiDataFetcher:
    def __init__(self, wiki_domain: str, wiki_username: str, wiki_password: str):
        self.wiki_domain = wiki_domain
        self.wiki_username = wiki_username
        self.wiki_password = wiki_password
        self.session = requests.Session()
        self.session.auth = (self.wiki_username, self.wiki_password)
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
        try:
            ip = socket.gethostbyname(self.wiki_domain)
            logger.info(f"Resolved {self.wiki_domain} to IP: {ip}")
        except socket.gaierror as e:
            logger.error(f"Failed to resolve {self.wiki_domain}: {str(e)}")
        
    def fetch_page_and_children(self, page_id: str) -> List[Dict]:
        """Fetch a page and its children from the wiki."""
        documents = []
        
        # Fetch the main page
        main_page = self._fetch_page(page_id)
        if main_page:
            documents.append(main_page)
        else:
            logger.warning(f"Main page {page_id} is empty or failed to fetch, but continuing to fetch child pages.")
        
        # Fetch child pages
        child_pages = self._fetch_child_pages(page_id)
        if child_pages:
            documents.extend(child_pages)
        else:
            logger.warning(f"No child pages found for page {page_id}.")
        
        return documents
        
    def _fetch_page(self, page_id: str) -> Dict:
        """Fetch a single page from the wiki."""
        url = f"{self.wiki_domain}/rest/api/content/{page_id}"
        params = {
            "expand": "body.storage,body.view"  # 同时获取 storage 和 view 格式的内容
        }
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 优先使用 storage 格式的内容，如果没有则使用 view 格式
            content = data.get('body', {}).get('storage', {}).get('value') or \
                     data.get('body', {}).get('view', {}).get('value')
            
            if not content:
                logger.error(f"No content found for page {page_id}")
                return None
            
            return {
                "title": data['title'],
                "content": self._clean_content(content)
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch page {page_id}: {str(e)}")
            return None
        
    def _fetch_child_pages(self, page_id: str) -> List[Dict]:
        """Fetch child pages of a given page."""
        url = f"{self.wiki_domain}/rest/api/content/search"
        params = {
            "cql": f"parent={page_id}",
            "expand": "body.storage,body.view"
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            child_pages = []
            for item in response.json()['results']:
                content = item.get('body', {}).get('storage', {}).get('value') or \
                         item.get('body', {}).get('view', {}).get('value')
                
                if content:
                    child_pages.append({
                        'title': item['title'],
                        'content': self._clean_content(content)
                    })
            
            return child_pages
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch child pages: {str(e)}")
            return []

    def _clean_content(self, html_content: str) -> str:
        """Extract clean text from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        # Get text and clean up whitespace
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
        
    def _fetch_single_page(self, page_id: str) -> Dict:
        """Fetch a single page by its ID"""
        url = f"{self.wiki_domain}/rest/api/content/{page_id}"
        params = {
            "expand": "body.storage"
        }
        
        logger.info(f"Fetching single page: {url}")
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to fetch page {page_id}: {response.status_code}")
            raise Exception(f"Failed to fetch page {page_id}: {response.status_code}\nResponse: {response.text}")
            
        item = response.json()
        logger.info(f"Successfully fetched page: {item['title']}")
        return {
            'title': item['title'],
            'content': self._clean_content(item['body']['storage']['value'])
        }
        
    def _fetch_child_pages(self, page_id: str) -> List[Dict]:
        """Fetch all child pages of a given page"""
        url = f"{self.wiki_domain}/rest/api/content/search"
        params = {
            "cql": f"parent={page_id}",
            "expand": "body.storage"
        }
        
        logger.info(f"Fetching child pages for parent_id: {page_id}")
        response = self.session.get(url, params=params)
        if response.status_code != 200:
            logger.error(f"Failed to fetch child pages: {response.status_code}")
            raise Exception(f"Failed to fetch child pages: {response.status_code}\nResponse: {response.text}")
            
        contents = []
        for item in response.json()['results']:
            logger.info(f"Found child page: {item['title']}")
            contents.append({
                'title': item['title'],
                'content': self._clean_content(item['body']['storage']['value'])
            })
        return contents 