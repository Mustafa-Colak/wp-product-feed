# WordPress Ürün Aktarma Aracı

Bu araç, başka web sitelerinden ürünleri çekip WordPress sitenize aktarmanızı sağlar.

## Özellikler

- Web sitelerinden otomatik ürün tarama
- Ürünleri listeden seçme imkanı
- Seçilen ürünleri WordPress/WooCommerce'e aktarma
- Ürün bilgilerini ve görsellerini otomatik aktarma

## Kurulum

### Gereksinimler

- Python 3.6 veya üzeri

### Adımlar

1. Bu repo'yu bilgisayarınıza indirin:
git clone cd wordpress-urun-aktarma

2. Kurulum betiğini çalıştırın:
python setup.py

3. Bu işlem otomatik olarak:
- Sanal ortam oluşturur
- Gerekli paketleri yükler

## Kullanım

1. Uygulamayı başlatın:

**Windows:**
venv\Scripts\python product_scraper.py

**macOS/Linux:**
venv/bin/python product_scraper.py

2. Açılan arayüzde:
- Taranacak web sitesinin URL'sini girin
- "Ürünleri Tara" düğmesine tıklayın
- Bulunan ürünler listede görüntülenecektir
- İstediğiniz ürünleri seçin
- WordPress bilgilerinizi girin
- "Seçili Ürünleri Yükle" düğmesine tıklayın

## Özelleştirme

Farklı web siteleri için ürün çekme mantığını özelleştirmeniz gerekebilir. Bunun için `ProductScraper` sınıfındaki `extract_product_data` ve `get_product_description` fonksiyonlarını hedef web sitesinin yapısına göre düzenleyin.

## Notlar

- WordPress sitenizde REST API ve WooCommerce API'nin etkin olması gerekir
- Bazı web siteleri scraping işlemlerini engelleyebilir
- Her zaman hedef web sitesinin kullanım koşullarını kontrol edin