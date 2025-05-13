import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json
import os
from config import DEFAULT_CONFIG, SSL_DISABLED_DOMAINS

class BaseScraper:
    """Temel web scraper sınıfı."""
    
    def __init__(self):
        self.visited_urls = set()
        self.base_url = ""
        self.domain = ""
        self.verify_ssl = DEFAULT_CONFIG["verify_ssl"]
        self.user_agent = DEFAULT_CONFIG["user_agent"]
        self.request_timeout = DEFAULT_CONFIG["request_timeout"]
        self.request_delay = DEFAULT_CONFIG["request_delay"]
        
    def extract_domain(self, url):
        """URL'den domain adını çıkarır."""
        parsed_url = urlparse(url)
        self.domain = parsed_url.netloc
        self.base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # SSL doğrulamasını kontrol et
        for domain in SSL_DISABLED_DOMAINS:
            if domain in self.domain:
                self.verify_ssl = False
                break
        
    def get_page(self, url):
        """Belirtilen URL'den sayfa içeriğini alır."""
        try:
            response = requests.get(
                url, 
                headers={"User-Agent": self.user_agent},
                verify=self.verify_ssl,
                timeout=self.request_timeout
            )
            
            if response.status_code != 200:
                print(f"Hata: {response.status_code} - {url}")
                return None
                
            return response.text
            
        except Exception as e:
            print(f"Sayfa alınırken hata: {e} - {url}")
            return None
    
    def find_element_by_selectors(self, soup, selectors, attr=None):
        """Verilen seçiciler listesini kullanarak bir element bulmaya çalışır."""
        for selector in selectors:
            try:
                # CSS seçici mi yoksa meta etiketi mi kontrol et
                if selector.startswith('meta['):
                    element = soup.select_one(selector)
                    if element and attr and attr in element.attrs:
                        return element[attr]
                    elif element and 'content' in element.attrs:
                        return element['content']
                else:
                    elements = soup.select(selector)
                    if elements:
                        if attr and attr in elements[0].attrs:
                            return elements[0][attr]
                        return elements[0]
            except Exception:
                continue
        return None
    
    def find_elements_by_selectors(self, soup, selectors):
        """Verilen seçiciler listesini kullanarak elementler bulmaya çalışır."""
        for selector in selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    return elements
            except Exception:
                continue
        return []
    
    def save_to_json(self, data, filename):
        """Verileri JSON dosyasına kaydeder."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Veriler {filename} dosyasına kaydedildi.")
    
    def load_from_json(self, filename):
        """JSON dosyasından verileri yükler."""
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"Veriler {filename} dosyasından yüklendi.")
            return data
        else:
            print(f"{filename} dosyası bulunamadı.")
            return None