from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import requests
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
    
    def get_page(self, url):
        """Belirtilen URL'den sayfa içeriğini alır."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, verify=self.verify_ssl, timeout=10)
            if response.status_code == 200:
                return response.text
            else:
                print(f"Hata: {url} adresinden veri alınamadı. Durum kodu: {response.status_code}")
                return None
        except Exception as e:
            print(f"İstek hatası ({url}): {e}")
            return None
    
    def is_category_url(self, url):
        """URL'nin bir kategori sayfası olup olmadığını kontrol eder."""
        category_keywords = [
            'category', 'categories', 'catalog', 'collection', 
            'department', 'products', 'urunler', 'kategori', 
            'shop', 'magaza', 'store'
        ]
        
        url_lower = url.lower()
        # URL'de kategori anahtar kelimeleri var mı kontrol et
        return any(keyword in url_lower for keyword in category_keywords)
    
    def extract_category_name(self, soup, url):
        """Sayfa içeriğinden kategori adını çıkarır."""
        # Başlık elementlerini kontrol et
        for selector in ['h1', 'h2', '.page-title', '.category-title', '.title']:
            element = soup.select_one(selector)
            if element and element.text.strip():
                return element.text.strip()
        
        # URL'den kategori adını çıkarmaya çalış
        path = urlparse(url).path
        parts = [p for p in path.split('/') if p]
        if parts:
            # Son parçayı al ve tire/alt çizgileri boşluklarla değiştir
            return parts[-1].replace('-', ' ').replace('_', ' ').title()
        
        return "Bilinmeyen Kategori"
    
    def count_products(self, soup):
        """Sayfadaki ürün sayısını tahmin eder."""
        # Ürün olabilecek elementleri bul
        product_selectors = [
            '.product', '.item', '[class*=product]', '[class*=item]',
            'a[href*=product]', 'a[href*=item]', 'a[href*=urun]',
            '.card', '.box', '.thumbnail'
        ]
        
        for selector in product_selectors:
            elements = soup.select(selector)
            if elements:
                return len(elements)
        
        # Resim içeren linkler de ürün olabilir
        product_links = []
        for a in soup.find_all('a', href=True):
            if a.find('img'):
                product_links.append(a)
        
        if product_links:
            return len(product_links)
        
        return 0
    
    def find_subcategories(self, soup, base_url):
        """Sayfadaki alt kategori linklerini bulur."""
        subcategories = []
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Sadece aynı domain'deki linkleri kontrol et
            if self.domain not in full_url or full_url == base_url:
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
        
        urls_to_visit = [(start_url, 0)]  # (url, depth)
        total_urls = 1
        processed_urls = 0
        
        self.update_progress(f"Site analizi başlatılıyor: {start_url}", 0, total_urls)
        
        while urls_to_visit:
            current_url, depth = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
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
            
            # Kategori bilgilerini kaydet
            self.categories[current_url] = {
                'name': category_name,
                'product_count': product_count,
                'subcategories': []
            }
            
            # Derinlik sınırına ulaşmadıysak alt kategorileri bul
            if depth < max_depth:
                subcategories = self.find_subcategories(soup, current_url)
                
                for subcat_url in subcategories:
                    if subcat_url not in self.visited_urls and subcat_url not in [u for u, _ in urls_to_visit]:
                        urls_to_visit.append((subcat_url, depth + 1))
                        self.categories[current_url]['subcategories'].append(subcat_url)
                
                # Toplam URL sayısını güncelle
                total_urls = len(urls_to_visit) + processed_urls
                self.update_progress(f"Analiz ediliyor... {processed_urls}/{total_urls}", processed_urls, total_urls)
            
            time.sleep(self.request_delay)
        
        self.update_progress(f"Site analizi tamamlandı. {len(self.categories)} kategori bulundu.", total_urls, total_urls)
        return self.categories
    
    def get_category_tree(self):
        """Kategori ağacını metin formatında döndürür."""
        if not self.categories:
            return "Henüz site analizi yapılmadı."
        
        result = "Kategori Yapısı:\n"
        result += "===============\n\n"
        
        # Ana kategorileri bul (hiçbir kategorinin alt kategorisi olmayan URL'ler)
        all_subcats = set()
        for cat_info in self.categories.values():
            all_subcats.update(cat_info['subcategories'])
        
        root_categories = [url for url in self.categories if url not in all_subcats]
        
        def add_category(url, indent=0):
            nonlocal result
            if url not in self.categories:
                return
                
            cat_info = self.categories[url]
            result += f"{'  ' * indent}• {cat_info['name']} ({cat_info['product_count']} ürün) - {url}\n"
            
            for subcat in cat_info['subcategories']:
                add_category(subcat, indent + 1)
        
        # Her bir ana kategoriden başlayarak ağacı oluştur
        for root_cat in root_categories:
            add_category(root_cat)
        
        # Toplam istatistikleri ekle
        total_products = sum(cat['product_count'] for cat in self.categories.values())
        result += f"\nToplam {len(self.categories)} kategori ve yaklaşık {total_products} ürün bulundu."
        
        return result