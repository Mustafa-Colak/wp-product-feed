# Varsayılan yapılandırma ayarları
DEFAULT_CONFIG = {
    "verify_ssl": True,
    "max_pages": 10,
    "default_category_id": 9,
    "request_timeout": 10,
    "request_delay": 1,  # Saniye cinsinden siteler arası bekleme süresi
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Ürün seçicileri için varsayılan CSS seçiciler
PRODUCT_SELECTORS = {
    "product_containers": [
        '.product', '.product-item', '.item', '.product-container', 
        '.product-box', '.product-card', '.product-wrapper', 
        'div[itemtype*="Product"]', 'li.product', '.prod-card',
        '.grid-product', '.product-grid-item', '.product-list-item'
    ],
    "titles": [
        'h1.product-name', 'h1.product-title', 'h1.title', 
        'h2.product-name', 'h2.product-title', 'h2.title',
        '.product-name', '.product-title', '.item-title',
        'a.product-name', 'a.product-title', 'a.item-title',
        'meta[property="og:title"]'
    ],
    "prices": [
        '.price', '.product-price', '.item-price', 
        'span.price', 'div.price', 'p.price',
        '.regular-price', '.special-price', '.current-price',
        'meta[property="product:price:amount"]'
    ],
    "images": [
        'img.product-image', 'img.product-img', 'img.item-image',
        'img#image', 'img.main-image', '.product-image img',
        'meta[property="og:image"]'
    ],
    "links": [
        'a.product-link', 'a.item-link', 'a.product-name',
        'a.product-title', 'a.item-title', 'a[href*="product"]'
    ],
    "descriptions": [
        '.product-description', '.description', '.product-details',
        '.product-info', '.product-text', '.item-description',
        'div[itemprop="description"]', 'meta[property="og:description"]'
    ],
    "next_page": [
        'a.next', 'a[rel="next"]', 'a:-soup-contains("Next")', 
        'a:-soup-contains("Sonraki")', 'a.pagination-next',
        '.pagination a:-soup-contains("»")', '.pagination a:-soup-contains(">")',
        'a[aria-label="Next"]', '.next a', '#next'
    ]
}

# SSL doğrulaması yapılmayacak domainler
SSL_DISABLED_DOMAINS = [
    'henex.cn',
    'localhost',
    '127.0.0.1'
]

# Site özel seçicileri
SITE_SPECIFIC_SELECTORS = {}