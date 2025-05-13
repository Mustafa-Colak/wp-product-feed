import requests
import re
from urllib.parse import urlparse
from config import DEFAULT_CONFIG, SSL_DISABLED_DOMAINS

class WordPressUploader:
    def __init__(self, wp_url, username, password):
        self.wp_url = wp_url.rstrip('/')
        self.username = username
        self.password = password
        self.api_url = f"{self.wp_url}/wp-json/wp/v2"
        self.verify_ssl = DEFAULT_CONFIG["verify_ssl"]
        self.progress_callback = None
        
        # WordPress sitesi için SSL doğrulamasını kontrol et
        domain = urlparse(wp_url).netloc
        for disabled_domain in SSL_DISABLED_DOMAINS:
            if disabled_domain in domain:
                self.verify_ssl = False
                break
    
    def set_progress_callback(self, callback):
        """İlerleme durumunu bildirmek için callback fonksiyonu ayarlar."""
        self.progress_callback = callback
    
    def update_progress(self, message):
        """İlerleme durumunu günceller."""
        if self.progress_callback:
            self.progress_callback(message)
        else:
            print(message)
    
    def upload_product(self, product, category_id=9):
        """Ürünü WordPress'e yükler."""
        # WooCommerce API kullanılacak
        wc_api_url = f"{self.wp_url}/wp-json/wc/v3/products"
        
        # Temel kimlik doğrulama
        auth = (self.username, self.password)
        
        # Fiyatı temizle ve sayısal formata dönüştür
        price = product["price"]
        if price:
            # Fiyattan para birimi sembollerini ve boşlukları temizle
            price = re.sub(r'[^\d.,]', '', price)
            # Virgülü noktaya çevir (gerekirse)
            price = price.replace(',', '.')
        else:
            price = "0"
        
        # Ürün verilerini hazırla
        product_data = {
            "name": product["title"] or "Ürün Adı Bulunamadı",
            "type": "simple",
            "regular_price": price,
            "description": product["description"] or "",
            "short_description": (product["description"] or "")[:100] + "..." if len(product["description"] or "") > 100 else (product["description"] or ""),
            "categories": [
                {
                    "id": int(category_id)
                }
            ],
            "images": []
        }
        
        # Eğer ürün resmi varsa, önce resmi yükle
        if product["image_url"]:
            self.update_progress(f"Resim yükleniyor: {product['image_url']}")
            image_id = self.upload_image(product["image_url"], product["title"])
            if image_id:
                product_data["images"].append({"id": image_id})
        
        # Ürünü WooCommerce'e ekle
        self.update_progress(f"Ürün yükleniyor: {product['title']}")
        try:
            response = requests.post(
                wc_api_url, 
                json=product_data, 
                auth=auth,
                verify=self.verify_ssl
            )
            
            if response.status_code in [200, 201]:
                self.update_progress(f"Ürün başarıyla yüklendi: {product['title']}")
                return response.json()
            else:
                self.update_progress(f"Ürün yüklenirken hata: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.update_progress(f"Ürün yüklenirken hata: {e}")
            return None
    
    def upload_image(self, image_url, title):
        """Ürün resmini WordPress'e yükler ve medya ID'sini döndürür."""
        try:
            # Resmi indir
            image_response = requests.get(image_url, verify=self.verify_ssl)
            if image_response.status_code != 200:
                return None
                
            # Resim dosyasının adını oluştur
            image_name = f"{title.lower().replace(' ', '-')[:50]}.jpg" if title else "product-image.jpg"
            
            # WordPress Media API'sine yükle
            media_endpoint = f"{self.api_url}/media"
            
            headers = {
                'Content-Disposition': f'attachment; filename="{image_name}"',
                'Content-Type': 'image/jpeg',
            }
            
            auth = (self.username, self.password)
            
            upload_response = requests.post(
                media_endpoint,
                auth=auth,
                headers=headers,
                data=image_response.content,
                verify=self.verify_ssl
            )
            
            if upload_response.status_code in [200, 201]:
                return upload_response.json()['id']
            else:
                print(f"Resim yüklenirken hata: {upload_response.status_code} - {upload_response.text}")
                return None
                
        except Exception as e:
            print(f"Resim yüklenirken hata: {e}")
            return None