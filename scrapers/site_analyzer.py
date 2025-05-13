from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
import time
import requests
import re
import json
from collections import defaultdict

class SiteAnalyzer:
    """Web sitesinin yapısını analiz eden sınıf."""
    
    def __init__(self, verify_ssl=True):
        self.verify_ssl = verify_ssl
        self.visited_urls = set()
        self.categories = {}  # kategori URL'si -> {name, product_count, subcategories}
        self.domain = None
        self.progress_callback = None
        self.request_delay = 0.5  # Saniye cinsinden istekler arası bekleme süresi
        self.site_type = "unknown"  # Algılanan site türü
        self.max_retries = 3  # Başarısız istekler için yeniden deneme sayısı
        
        # Farklı site türleri için seçiciler
        self.site_patterns = {
            "woocommerce": {
                "category_selectors": [".product-category", ".products", ".woocommerce-loop-product"],
                "product_selectors": [".product", ".products li", ".woocommerce-loop-product__title"],
                "category_url_patterns": ["product-category", "shop", "products"],
                "product_url_patterns": ["product", "item", "urun"]
            },
            "shopify": {
                "category_selectors": [".collection-grid", ".collection-list", ".collection"],
                "product_selectors": [".product-card", ".product-item", ".product-grid-item"],
                "category_url_patterns": ["collections", "category", "collection"],
                "product_url_patterns": ["products", "product", "item"]
            },
            "magento": {
                "category_selectors": [".category-products", ".categories-list", ".catalog-category-view"],
                "product_selectors": [".product-item", ".product-info", ".product-name"],
                "category_url_patterns": ["category", "catalog", "categories"],
                "product_url_patterns": ["product", "item", "detail"]
            },
            "opencart": {
                "category_selectors": [".category-list", ".category-info", ".category"],
                "product_selectors": [".product-layout", ".product-thumb", ".product-grid"],
                "category_url_patterns": ["category", "categories", "cat"],
                "product_url_patterns": ["product", "products", "item"]
            },
            "prestashop": {
                "category_selectors": [".category", ".category-products", ".subcategories"],
                "product_selectors": [".product-container", ".product-miniature", ".product"],
                "category_url_patterns": ["category", "categories", "cat"],
                "product_url_patterns": ["product", "products", "item"]
            },
            "generic": {
                "category_selectors": [".category", ".categories", ".catalog", ".collection", ".department", ".products", ".items"],
                "product_selectors": [".product", ".item", ".card", ".box", ".thumbnail", ".product-item"],
                "category_url_patterns": ["category", "categories", "catalog", "collection", "department", "products", "items", "shop", "store"],
                "product_url_patterns": ["product", "item", "detail", "goods", "urun"]
            },
            "chinese": {  # Çince siteler için özel desenler
                "category_selectors": [".cate", ".category", ".cat-list", ".nav-item", ".menu-item"],
                "product_selectors": [".product", ".item", ".goods", ".pro-item", ".product-item"],
                "category_url_patterns": ["category", "cat", "list", "c=", "cid=", "id="],
                "product_url_patterns": ["product", "item", "goods", "detail", "p=", "pid=", "id="]
            }
        }
    
    def set_progress_callback(self, callback):
        """İlerleme durumunu bildirmek için callback fonksiyonu ayarlar."""
        self.progress_callback = callback
    
    def update_progress(self, message, current=0, total=0):
        """İlerleme durumunu günceller."""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        else:
            print(message)
    
    def extract_domain(self, url):
        """URL'den domain adını çıkarır."""
        parsed_url = urlparse(url)
        self.domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return self.domain
    
    def get_page(self, url, retry_count=0):
        """Belirtilen URL'den sayfa içeriğini alır."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,tr;q=0.6',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': self.domain if self.domain else url
            }
            response = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=15)
            
            if response.status_code == 200:
                return response.text
            elif response.status_code == 403 and retry_count < self.max_retries:
                # 403 Forbidden hatası - farklı bir User-Agent ile yeniden dene
                time.sleep(2)  # Biraz bekle
                return self.get_page_with_different_agent(url, retry_count + 1)
            else:
                print(f"Hata: {url} adresinden veri alınamadı. Durum kodu: {response.status_code}")
                return None
        except Exception as e:
            print(f"İstek hatası ({url}): {e}")
            if retry_count < self.max_retries:
                time.sleep(2)  # Biraz bekle
                return self.get_page(url, retry_count + 1)
            return None
    
    def get_page_with_different_agent(self, url, retry_count):
        """Farklı bir User-Agent ile sayfayı almayı dener."""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1'
        ]
        
        try:
            headers = {
                'User-Agent': user_agents[retry_count % len(user_agents)],
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Referer': self.domain if self.domain else url
            }
            response = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=15)
            
            if response.status_code == 200:
                return response.text
            else:
                print(f"Farklı User-Agent ile deneme başarısız: {response.status_code}")
                return None
        except Exception as e:
            print(f"Farklı User-Agent ile istek hatası: {e}")
            return None
    
    def detect_site_type(self, html, url):
        """Sitenin türünü tespit eder."""
        if not html:
            return "generic"
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # WooCommerce kontrolü
        if soup.select('.woocommerce') or 'woocommerce' in html.lower():
            return "woocommerce"
            
        # Shopify kontrolü
        if 'shopify' in html.lower() or soup.select('[data-shopify]'):
            return "shopify"
            
        # Magento kontrolü
        if 'magento' in html.lower() or soup.select('[data-mage-init]'):
            return "magento"
            
        # OpenCart kontrolü
        if 'opencart' in html.lower() or soup.find('footer', text=re.compile('OpenCart')):
            return "opencart"
            
        # PrestaShop kontrolü
        if 'prestashop' in html.lower() or soup.find('meta', attrs={'name': 'generator', 'content': re.compile('PrestaShop')}):
            return "prestashop"
            
        # Çince site kontrolü
        chinese_chars = re.findall(r'[\u4e00-\u9fff]+', html)
        if chinese_chars or '.cn' in url:
            return "chinese"
            
        return "generic"
    
    def is_category_url(self, url):
        """URL'nin bir kategori sayfası olup olmadığını kontrol eder."""
        url_lower = url.lower()
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Site türüne göre kategori URL desenlerini kontrol et
        patterns = self.site_patterns.get(self.site_type, self.site_patterns["generic"])["category_url_patterns"]
        
        # URL'de kategori anahtar kelimeleri var mı kontrol et
        if any(pattern in url_lower for pattern in patterns):
            return True
            
        # URL parametrelerinde kategori belirten bir şey var mı kontrol et
        if 'category' in query_params or 'cat' in query_params or 'c' in query_params:
            return True
            
        # Çince siteler için özel kontrol
        if self.site_type == "chinese":
            if 'c=' in url_lower or 'cid=' in url_lower or 'category_id=' in url_lower:
                return True
        
        return False
    
    def extract_category_name(self, soup, url):
        """Sayfa içeriğinden kategori adını çıkarır."""
        # Başlık elementlerini kontrol et
        for selector in ['h1', 'h2', '.page-title', '.category-title', '.title', '.breadcrumb', '.crumbs']:
            element = soup.select_one(selector)
            if element and element.text.strip():
                # Gereksiz boşlukları temizle
                return re.sub(r'\s+', ' ', element.text.strip())
        
        # URL parametrelerinden kategori adını çıkarmaya çalış
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        # Kategori ID'si varsa kullan
        if 'id' in query_params:
            return f"Kategori {query_params['id'][0]}"
        elif 'category_id' in query_params:
            return f"Kategori {query_params['category_id'][0]}"
        elif 'cat' in query_params:
            return f"Kategori {query_params['cat'][0]}"
        elif 'c' in query_params and query_params['c'][0] == 'category' and 'id' in query_params:
            return f"Kategori {query_params['id'][0]}"
        
        # URL'den kategori adını çıkarmaya çalış
        path = parsed_url.path
        parts = [p for p in path.split('/') if p]
        if parts:
            # Son parçayı al ve tire/alt çizgileri boşluklarla değiştir
            return parts[-1].replace('-', ' ').replace('_', ' ').title()
        
        return "Bilinmeyen Kategori"
    
    def count_products(self, soup):
        """Sayfadaki ürün sayısını tahmin eder."""
        # Site türüne göre ürün seçicilerini al
        product_selectors = self.site_patterns.get(self.site_type, self.site_patterns["generic"])["product_selectors"]
        
        # Ürün olabilecek elementleri bul
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                return len(elements)
        
        # Ürün linklerini kontrol et
        product_url_patterns = self.site_patterns.get(self.site_type, self.site_patterns["generic"])["product_url_patterns"]
        product_links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href'].lower()
            if any(pattern in href for pattern in product_url_patterns):
                product_links.append(a)
        
        if product_links:
            return len(product_links)
        
        # Resim içeren linkler de ürün olabilir
        img_links = [a for a in soup.find_all('a', href=True) if a.find('img')]
        if img_links:
            return len(img_links)
        
        return 0
    
    def find_subcategories(self, soup, base_url):
        """Sayfadaki alt kategori linklerini bulur."""
        subcategories = []
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            
            # Göreceli URL'leri mutlak URL'lere dönüştür
            if href.startswith('?'):
                href = urljoin(base_url, href)
            elif not (href.startswith('http://') or href.startswith('https://')):
                href = urljoin(self.domain, href)
                
            full_url = href
            
            # Sadece aynı domain'deki linkleri kontrol et
            if urlparse(full_url).netloc != urlparse(self.domain).netloc or full_url == base_url:
                continue
                
            # Kategori olabilecek linkleri filtrele
            if self.is_category_url(full_url) and full_url not in self.visited_urls:
                subcategories.append(full_url)
        
        return subcategories
    
    def analyze_site(self, start_url, max_depth=2):
        """Web sitesini analiz eder ve kategori yapısını çıkarır."""
        self.extract_domain(start_url)
        self.visited_urls = set()
        self.categories = {}
        
        print(f"Site analizi başlatılıyor: {start_url}")
        print(f"Domain: {self.domain}")
        
        # İlk sayfayı al ve site türünü tespit et
        html = self.get_page(start_url)
        if not html:
            self.update_progress("Site analizi başarısız oldu: Sayfa yüklenemedi.", 0, 0)
            return {}
            
        self.site_type = self.detect_site_type(html, start_url)
        print(f"Algılanan site türü: {self.site_type}")
        
        urls_to_visit = [(start_url, 0)]  # (url, depth)
        total_urls = 1
        processed_urls = 0
        
        self.update_progress(f"Site analizi başlatılıyor: {start_url} (Tür: {self.site_type})", 0, total_urls)
        
        max_urls = 50  # Maksimum işlenecek URL sayısı
        
        while urls_to_visit and processed_urls < max_urls:
            current_url, depth = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            print(f"Sayfa analiz ediliyor ({processed_urls+1}/{max_urls}): {current_url}")
            self.update_progress(f"Sayfa analiz ediliyor: {current_url}", processed_urls, total_urls)
            self.visited_urls.add(current_url)
            processed_urls += 1
            
            html = self.get_page(current_url)
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Kategori bilgilerini çıkar
            category_name = self.extract_category_name(soup, current_url)
            product_count = self.count_products(soup)
            
            print(f"Kategori: {category_name}, Ürün sayısı: {product_count}")
            
            # Kategori bilgilerini kaydet
            self.categories[current_url] = {
                'name': category_name,
                'product_count': product_count,
                'subcategories': []
            }
            
            # Derinlik sınırına ulaşmadıysak alt kategorileri bul
            if depth < max_depth:
                subcategories = self.find_subcategories(soup, current_url)
                print(f"Alt kategoriler bulundu: {len(subcategories)}")
                
                for subcat_url in subcategories:
                    if subcat_url not in self.visited_urls and subcat_url not in [u for u, _ in urls_to_visit]:
                        urls_to_visit.append((subcat_url, depth + 1))
                        self.categories[current_url]['subcategories'].append(subcat_url)
                
                # Toplam URL sayısını güncelle
                total_urls = min(len(urls_to_visit) + processed_urls, max_urls)
                self.update_progress(f"Analiz ediliyor... {processed_urls}/{total_urls}", processed_urls, total_urls)
            
            time.sleep(self.request_delay)
        
        print(f"Site analizi tamamlandı. {len(self.categories)} kategori bulundu.")
        for url, info in self.categories.items():
            print(f"Kategori: {info['name']}, Ürün sayısı: {info['product_count']}, Alt kategori sayısı: {len(info['subcategories'])}")
            
        self.update_progress(f"Site analizi tamamlandı. {len(self.categories)} kategori bulundu.", total_urls, total_urls)
        return self.categories
    
    def get_category_tree(self):
        """Kategori ağacını metin formatında döndürür."""
        if not self.categories:
            return "Henüz site analizi yapılmadı veya hiç kategori bulunamadı."
        
        result = "Kategori Yapısı:\n"
        result += "===============\n\n"
        result += f"Site Türü: {self.site_type}\n"
        result += f"Domain: {self.domain}\n\n"
        
        # Ana kategorileri bul (hiçbir kategorinin alt kategorisi olmayan URL'ler)
        all_subcats = set()
        for cat_info in self.categories.values():
            all_subcats.update(cat_info['subcategories'])
        
        root_categories = [url for url in self.categories if url not in all_subcats]
        
        if not root_categories and self.categories:
            # Ana kategori bulunamadıysa ilk kategoriyi kök olarak al
            root_categories = [list(self.categories.keys())[0]]
        
        def add_category(url, indent=0, visited=None):
            if visited is None:
                visited = set()
                
            nonlocal result
            if url not in self.categories or url in visited:
                return
                
            visited.add(url)
            cat_info = self.categories[url]
            result += f"{'  ' * indent}• {cat_info['name']} ({cat_info['product_count']} ürün)\n"
            result += f"{'  ' * (indent+1)}URL: {url}\n"
            
            for subcat in cat_info['subcategories']:
                if subcat not in visited:
                    add_category(subcat, indent + 1, visited)
        
        # Her bir ana kategoriden başlayarak ağacı oluştur
        for root_cat in root_categories:
            add_category(root_cat)
        
        # Toplam istatistikleri ekle
        total_products = sum(cat['product_count'] for cat in self.categories.values())
        result += f"\nToplam {len(self.categories)} kategori ve yaklaşık {total_products} ürün bulundu."
        
        return result
    
    def export_to_json(self, filename="site_structure.json"):
        """Site yapısını JSON formatında dışa aktarır."""
        if not self.categories:
            return False
            
        data = {
            "site_type": self.site_type,
            "domain": self.domain,
            "categories": self.categories,
            "stats": {
                "total_categories": len(self.categories),
                "total_products": sum(cat['product_count'] for cat in self.categories.values())
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"JSON dışa aktarma hatası: {e}")
            return False