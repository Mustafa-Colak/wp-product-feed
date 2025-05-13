from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
from config import PRODUCT_SELECTORS, SITE_SPECIFIC_SELECTORS

class ProductScraper(BaseScraper):
    """Ürün bilgilerini çekmek için özelleştirilmiş scraper."""
    
    def __init__(self):
        super().__init__()
        self.products = []
        self.product_selectors = PRODUCT_SELECTORS
        self.progress_callback = None
        
        # İstatistik değişkenleri
        self.stats = {
            "total_pages_scanned": 0,
            "total_products_found": 0,
            "unique_products": 0,
            "duplicate_products": 0,
            "pages_with_products": 0,
            "pages_without_products": 0,
            "products_per_page": {},
            "scan_duration": 0
        }
        
        # Ürün URL'lerini takip etmek için set
        self.product_urls = set()
        
    def set_progress_callback(self, callback):
        """İlerleme durumunu bildirmek için callback fonksiyonu ayarlar."""
        self.progress_callback = callback
        
    def update_progress(self, message, current=0, total=0):
        """İlerleme durumunu günceller."""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        else:
            print(message)
    
    def get_site_specific_selectors(self):
        """Site için özel seçicileri döndürür."""
        if self.domain in SITE_SPECIFIC_SELECTORS:
            # Varsayılan seçiciler ile site özel seçicileri birleştir
            selectors = self.product_selectors.copy()
            
            # Her bir seçici türü için site özel seçicileri ekle
            for selector_type, selector_list in SITE_SPECIFIC_SELECTORS[self.domain].items():
                if selector_type in selectors and selector_list:
                    # Site özel seçicileri listenin başına ekle (öncelik ver)
                    selectors[selector_type] = selector_list + selectors[selector_type]
                elif selector_list:
                    selectors[selector_type] = selector_list
            
            return selectors
        
        return self.product_selectors
    
    def analyze_page_structure(self, soup):
        """Sayfa yapısını analiz ederek ürün elementlerini tespit eder."""
        # Site özel seçicileri al
        selectors = self.get_site_specific_selectors()
        
        # Önce seçicileri kullanarak ürünleri bulmaya çalış
        products = self.find_elements_by_selectors(soup, selectors["product_containers"])
        
        if products:
            return products
        
        # Eğer bulunamazsa, sayfadaki tüm <a> etiketlerini kontrol et
        links = soup.find_all('a', href=True)
        product_links = []
        
        for link in links:
            href = link['href'].lower()
            # Ürün bağlantısı olabilecek linkleri filtrele
            if 'product' in href or 'item' in href or 'detail' in href:
                product_links.append(link)
                
        if product_links:
            return product_links
            
        # Son çare: Sayfadaki tüm resimleri içeren div'leri kontrol et
        img_divs = []
        for img in soup.find_all('img'):
            if img.parent and img.parent.name == 'div':
                img_divs.append(img.parent)
                
        return img_divs
    
    def extract_product_info(self, element, page_url):
        """Verilen elementten ürün bilgilerini çıkarır."""
        # Site özel seçicileri al
        selectors = self.get_site_specific_selectors()
        
        # Element içinde başlık ara
        title_element = self.find_element_by_selectors(element, selectors["titles"])
        title = title_element.get_text().strip() if hasattr(title_element, 'get_text') else str(title_element) if title_element else ''
        
        # Element içinde fiyat ara
        price_element = self.find_element_by_selectors(element, selectors["prices"])
        price = price_element.get_text().strip() if hasattr(price_element, 'get_text') else str(price_element) if price_element else ''
        
        # Element içinde resim ara
        image = self.find_element_by_selectors(element, selectors["images"], 'src')
        image_url = urljoin(page_url, image) if image else ''
        
        # Ürün URL'sini bul
        link = element.find('a', href=True) if element.name != 'a' else element
        product_url = urljoin(page_url, link['href']) if link and 'href' in link.attrs else ''
        
        return {
            "title": title,
            "price": price,
            "image_url": image_url,
            "product_url": product_url,
            "description": "",
            "selected": False
        }
    
    def get_product_details(self, product_url):
        """Ürün sayfasından detaylı bilgileri çeker."""
        if not product_url or product_url in self.visited_urls:
            return {}
            
        self.visited_urls.add(product_url)
        
        html = self.get_page(product_url)
        if not html:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # Site özel seçicileri al
        selectors = self.get_site_specific_selectors()
        
        # Başlık
        title = self.find_element_by_selectors(soup, selectors["titles"])
        title = title.get_text().strip() if hasattr(title, 'get_text') else str(title) if title else ''
        
        # Fiyat
        price = self.find_element_by_selectors(soup, selectors["prices"])
        price = price.get_text().strip() if hasattr(price, 'get_text') else str(price) if price else ''
        
        # Resim
        image = self.find_element_by_selectors(soup, selectors["images"], 'src')
        image_url = urljoin(product_url, image) if image else ''
        
        # Açıklama
        description = self.find_element_by_selectors(soup, selectors["descriptions"])
        description = description.get_text().strip() if hasattr(description, 'get_text') else str(description) if description else ''
        
        return {
            "title": title,
            "price": price,
            "image_url": image_url,
            "description": description
        }
    
    def scrape_products(self, start_url, max_pages=10):
        """Belirtilen URL'den başlayarak ürünleri kazır."""
        start_time = time.time()
        self.extract_domain(start_url)
        self.products = []
        self.visited_urls = set()
        self.product_urls = set()
        
        # İstatistikleri sıfırla
        self.stats = {
            "total_pages_scanned": 0,
            "total_products_found": 0,
            "unique_products": 0,
            "duplicate_products": 0,
            "pages_with_products": 0,
            "pages_without_products": 0,
            "products_per_page": {},
            "scan_duration": 0
        }
        
        urls_to_visit = [start_url]
        page_count = 0
        total_pages = min(max_pages, len(urls_to_visit))
        
        self.update_progress(f"Taramaya başlanıyor: {start_url}", 0, total_pages)
        
        # Site özel seçicileri al
        selectors = self.get_site_specific_selectors()
        
        while urls_to_visit and page_count < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.update_progress(f"Sayfa taranıyor: {current_url}", page_count + 1, total_pages)
            self.visited_urls.add(current_url)
            self.stats["total_pages_scanned"] += 1
            
            html = self.get_page(current_url)
            if not html:
                self.stats["pages_without_products"] += 1
                continue
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Sayfa yapısını analiz et
            product_elements = self.analyze_page_structure(soup)
            
            page_product_count = 0
            
            self.update_progress(f"Sayfada {len(product_elements)} ürün elementi bulundu", page_count + 1, total_pages)
            
            for i, element in enumerate(product_elements):
                try:
                    product_data = self.extract_product_info(element, current_url)
                    
                    # Ürün URL'si zaten var mı kontrol et
                    if product_data["product_url"] in self.product_urls:
                        self.stats["duplicate_products"] += 1
                        continue
                    
                    if product_data["product_url"]:
                        self.product_urls.add(product_data["product_url"])
                    
                    if product_data["product_url"] and product_data["product_url"] not in self.visited_urls:
                        # Ürün detay sayfasından daha fazla bilgi al
                        self.update_progress(f"Ürün detayları alınıyor: {product_data['title'] or 'Ürün'} ({i+1}/{len(product_elements)})", page_count + 1, total_pages)
                        details = self.get_product_details(product_data["product_url"])
                        
                        # Detay sayfasından gelen bilgileri birleştir
                        if details:
                            if not product_data["title"] and details.get("title"):
                                product_data["title"] = details["title"]
                                
                            if not product_data["price"] and details.get("price"):
                                product_data["price"] = details["price"]
                                
                            if not product_data["image_url"] and details.get("image_url"):
                                product_data["image_url"] = details["image_url"]
                                
                            if details.get("description"):
                                product_data["description"] = details["description"]
                    
                    # Ürün başlığı veya URL'si varsa listeye ekle
                    if product_data["title"] or product_data["product_url"]:
                        self.products.append(product_data)
                        self.stats["total_products_found"] += 1
                        page_product_count += 1
                        
                except Exception as e:
                    print(f"Ürün çıkarılırken hata: {e}")
            
            # Sayfa ürün istatistiklerini güncelle
            if page_product_count > 0:
                self.stats["pages_with_products"] += 1
                self.stats["products_per_page"][current_url] = page_product_count
            else:
                self.stats["pages_without_products"] += 1
            
            # Sonraki sayfa linkini bul
            next_page = None
            next_element = self.find_element_by_selectors(soup, selectors["next_page"])
            
            if next_element and hasattr(next_element, 'get') and next_element.get('href'):
                next_page = urljoin(current_url, next_element['href'])
            
            if next_page and next_page not in self.visited_urls and page_count < max_pages - 1:
                urls_to_visit.append(next_page)
            
            # Kategori sayfalarını bul (sadece ilk sayfada)
            if page_count == 0:
                category_keywords = ['category', 'categories', 'catalog', 'collection', 'department', 'products']
                links = soup.find_all('a', href=True)
                
                for link in links:
                    href = link['href'].lower()
                    
                    # Sadece aynı domain'deki kategori linklerini takip et
                    full_url = urljoin(current_url, href)
                    if self.domain in full_url and full_url not in self.visited_urls and full_url not in urls_to_visit:
                        if any(keyword in href for keyword in category_keywords):
                            urls_to_visit.append(full_url)
            
            # Toplam sayfa sayısını güncelle
            total_pages = min(max_pages, len(urls_to_visit) + page_count + 1)
            
            page_count += 1
            time.sleep(self.request_delay)  # Siteyi çok hızlı taramaktan kaçınmak için bekleme
        
        # İstatistikleri tamamla
        self.stats["unique_products"] = len(self.products)
        self.stats["scan_duration"] = round(time.time() - start_time, 2)
        
        self.update_progress(f"Tarama tamamlandı. Toplam {len(self.products)} benzersiz ürün bulundu.", max_pages, max_pages)
        return self.products
    
    def get_stats_summary(self):
        """İstatistik özetini döndürür."""
        summary = f"""
Tarama İstatistikleri:
---------------------
Taranan Toplam Sayfa: {self.stats['total_pages_scanned']}
Bulunan Toplam Ürün: {self.stats['total_products_found']}
Benzersiz Ürün Sayısı: {self.stats['unique_products']}
Mükerrer Ürün Sayısı: {self.stats['duplicate_products']}
Ürün İçeren Sayfa Sayısı: {self.stats['pages_with_products']}
Ürün İçermeyen Sayfa Sayısı: {self.stats['pages_without_products']}
Tarama Süresi: {self.stats['scan_duration']} saniye

Sayfa Başına Ürün Sayıları:
"""
        # En çok ürün içeren 5 sayfayı göster
        sorted_pages = sorted(self.stats['products_per_page'].items(), key=lambda x: x[1], reverse=True)
        for i, (url, count) in enumerate(sorted_pages[:5]):
            summary += f"  {url}: {count} ürün\n"
            
        if len(sorted_pages) > 5:
            summary += f"  ... ve {len(sorted_pages) - 5} sayfa daha\n"
            
        return summary
            
    def save_products_to_json(self, filename="products.json"):
        """Bulunan ürünleri JSON dosyasına kaydeder."""
        self.save_to_json(self.products, filename)
    
    def load_products_from_json(self, filename="products.json"):
        """JSON dosyasından ürünleri yükler."""
        data = self.load_from_json(filename)
        if data:
            self.products = data
        return self.products