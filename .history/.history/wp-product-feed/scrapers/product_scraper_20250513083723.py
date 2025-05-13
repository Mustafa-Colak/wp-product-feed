from scrapers.base_scraper import BaseScraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import time
from config import PRODUCT_SELECTORS

class ProductScraper(BaseScraper):
    """Ürün bilgilerini çekmek için özelleştirilmiş scraper."""
    
    def __init__(self):
        super().__init__()
        self.products = []
        self.product_selectors = PRODUCT_SELECTORS
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """İlerleme durumunu bildirmek için callback fonksiyonu ayarlar."""
        self.progress_callback = callback
        
    def update_progress(self, message, current=0, total=0):
        """İlerleme durumunu günceller."""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        else:
            print(message)
    
    def analyze_page_structure(self, soup):
        """Sayfa yapısını analiz ederek ürün elementlerini tespit eder."""
        # Önce varsayılan seçicileri kullanarak ürünleri bulmaya çalış
        products = self.find_elements_by_selectors(soup, self.product_selectors["product_containers"])
        
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
        # Element bir link ise ve içinde resim varsa
        if element.name == 'a' and element.find('img'):
            title = element.get_text().strip() if element.get_text().strip() else element.get('title', '')
            img = element.find('img')
            image_url = urljoin(page_url, img.get('src', '')) if img.get('src') else ''
            product_url = urljoin(page_url, element['href']) if 'href' in element.attrs else ''
            
            # Fiyat bilgisini bulmaya çalış
            price_element = element.find(class_=re.compile('price', re.I))
            price = price_element.get_text().strip() if price_element else ''
            
            return {
                "title": title,
                "price": price,
                "image_url": image_url,
                "product_url": product_url,
                "description": "",
                "selected": False
            }
            
        # Element bir div veya başka bir container ise
        else:
            # Başlık bulmaya çalış
            title_element = None
            for selector in ['h1', 'h2', 'h3', 'h4', '.title', '.name', '.product-title', '.product-name']:
                title_element = element.select_one(selector)
                if title_element:
                    break
                    
            title = title_element.get_text().strip() if title_element else ''
            
            # Başlık bulunamadıysa ve bir link varsa, linkin metnini kullan
            if not title:
                link = element.find('a')
                if link:
                    title = link.get_text().strip() or link.get('title', '')
            
            # Fiyat bulmaya çalış
            price_element = element.find(class_=re.compile('price', re.I))
            price = price_element.get_text().strip() if price_element else ''
            
            # Resim bulmaya çalış
            img = element.find('img')
            image_url = urljoin(page_url, img.get('src', '')) if img and img.get('src') else ''
            
            # Link bulmaya çalış
            link = element.find('a', href=True)
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
        
        # Başlık
        title = self.find_element_by_selectors(soup, self.product_selectors["titles"])
        title = title.get_text().strip() if hasattr(title, 'get_text') else str(title) if title else ''
        
        # Fiyat
        price = self.find_element_by_selectors(soup, self.product_selectors["prices"])
        price = price.get_text().strip() if hasattr(price, 'get_text') else str(price) if price else ''
        
        # Resim
        image = self.find_element_by_selectors(soup, self.product_selectors["images"], 'src')
        image_url = urljoin(product_url, image) if image else ''
        
        # Açıklama
        description = self.find_element_by_selectors(soup, self.product_selectors["descriptions"])
        description = description.get_text().strip() if hasattr(description, 'get_text') else str(description) if description else ''
        
        return {
            "title": title,
            "price": price,
            "image_url": image_url,
            "description": description
        }
    
    def scrape_products(self, start_url, max_pages=10):
        """Belirtilen URL'den başlayarak ürünleri kazır."""
        self.extract_domain(start_url)
        self.products = []
        self.visited_urls = set()
        
        urls_to_visit = [start_url]
        page_count = 0
        total_pages = min(max_pages, len(urls_to_visit))
        
        self.update_progress(f"Taramaya başlanıyor: {start_url}", 0, total_pages)
        
        while urls_to_visit and page_count < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in self.visited_urls:
                continue
                
            self.update_progress(f"Sayfa taranıyor: {current_url}", page_count + 1, total_pages)
            self.visited_urls.add(current_url)
            
            html = self.get_page(current_url)
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'html.parser')
            
            # Sayfa yapısını analiz et
            product_elements = self.analyze_page_structure(soup)
            
            self.update_progress(f"Sayfada {len(product_elements)} ürün elementi bulundu", page_count + 1, total_pages)
            
            for i, element in enumerate(product_elements):
                try:
                    product_data = self.extract_product_info(element, current_url)
                    
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
                        
                except Exception as e:
                    print(f"Ürün çıkarılırken hata: {e}")
            
            # Sonraki sayfa linkini bul
            next_page = None
            next_element = self.find_element_by_selectors(soup, self.product_selectors["next_page"])
            
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
        
        self.update_progress(f"Tarama tamamlandı. Toplam {len(self.products)} ürün bulundu.", max_pages, max_pages)
        return self.products
            
    def save_products_to_json(self, filename="products.json"):
        """Bulunan ürünleri JSON dosyasına kaydeder."""
        self.save_to_json(self.products, filename)
    
    def load_products_from_json(self, filename="products.json"):
        """JSON dosyasından ürünleri yükler."""
        data = self.load_from_json(filename)
        if data:
            self.products = data
        return self.products