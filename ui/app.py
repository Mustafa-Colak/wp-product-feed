import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import os
import json
from PIL import Image, ImageTk
from io import BytesIO
import requests
import webbrowser

from scrapers.product_scraper import ProductScraper
from scrapers.site_analyzer import SiteAnalyzer
from scrapers.selector_builder import SelectorBuilder
from uploaders.wordpress_uploader import WordPressUploader
from ui.product_preview import ProductPreviewWindow
from ui.utils import run_with_progress, load_image_from_url

class ProductScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ürün Kazıyıcı")
        self.root.geometry("1200x800")
        
        # Ürün kazıyıcı ve yükleyici nesneleri
        self.scraper = ProductScraper()
        self.site_analyzer = SiteAnalyzer()
        self.selector_builder = SelectorBuilder()
        self.uploader = None
        
        # Ürün listesi
        self.products = []
        
        # SSL doğrulama ayarı
        self.verify_ssl = tk.BooleanVar(value=True)
        
        # Kategori ağacı
        self.category_tree = {}
        
        # Arayüz elemanlarını oluştur
        self.create_widgets()
        
        # İlerleme durumu için callback fonksiyonları ayarla
        self.scraper.set_progress_callback(self.update_progress)
        self.site_analyzer.set_progress_callback(self.update_progress)
        self.selector_builder.set_progress_callback(self.update_progress)
    
    def create_widgets(self):
        # Ana çerçeve
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Üst kısım - Ayarlar ve kontroller
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=10)
        
        # URL girişi
        ttk.Label(top_frame, text="URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.url_entry = ttk.Entry(top_frame, width=50)
        self.url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Sayfa sayısı
        ttk.Label(top_frame, text="Maks. Sayfa:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.max_pages_entry = ttk.Spinbox(top_frame, from_=1, to=100, width=5)
        self.max_pages_entry.set(10)
        self.max_pages_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # SSL doğrulama
        self.ssl_check = ttk.Checkbutton(top_frame, text="SSL Doğrulama", variable=self.verify_ssl, command=self.toggle_ssl_verification)
        self.ssl_check.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        
        # Tarama düğmesi
        self.scan_button = ttk.Button(top_frame, text="Ürünleri Tara", command=self.start_scanning)
        self.scan_button.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        
        # Site analiz düğmesi
        self.analyze_button = ttk.Button(top_frame, text="Siteyi Analiz Et", command=self.start_site_analysis)
        self.analyze_button.grid(row=0, column=6, padx=5, pady=5, sticky=tk.W)
        
        # Seçici oluşturma düğmesi
        self.selector_button = ttk.Button(top_frame, text="Seçici Oluştur", command=self.start_selector_builder)
        self.selector_button.grid(row=0, column=7, padx=5, pady=5, sticky=tk.W)
        
        # Orta kısım - Ürün listesi ve detayları
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Ürün listesi
        list_frame = ttk.Frame(middle_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Ürün listesi başlığı
        ttk.Label(list_frame, text="Ürün Listesi", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        
        # Ürün listesi araç çubuğu
        list_toolbar = ttk.Frame(list_frame)
        list_toolbar.pack(fill=tk.X, pady=5)
        
        ttk.Button(list_toolbar, text="Tümünü Seç", command=self.select_all_products).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_toolbar, text="Seçimi Kaldır", command=self.deselect_all_products).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_toolbar, text="Kaydet", command=self.save_products).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_toolbar, text="Yükle", command=self.load_products).pack(side=tk.LEFT, padx=2)
        ttk.Button(list_toolbar, text="İstatistikler", command=self.show_stats).pack(side=tk.LEFT, padx=2)
        
        # Ürün listesi tablosu
        table_frame = ttk.Frame(list_frame)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(table_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        columns = ("selected", "title", "price", "image")
        self.product_table = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.product_table.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar bağlantısı
        scrollbar.config(command=self.product_table.yview)
        self.product_table.config(yscrollcommand=scrollbar.set)
        
        # Sütun başlıkları
        self.product_table.heading("selected", text="Seç")
        self.product_table.heading("title", text="Başlık")
        self.product_table.heading("price", text="Fiyat")
        self.product_table.heading("image", text="Resim")
        
        # Sütun genişlikleri
        self.product_table.column("selected", width=50, anchor=tk.CENTER)
        self.product_table.column("title", width=300)
        self.product_table.column("price", width=100)
        self.product_table.column("image", width=100, anchor=tk.CENTER)
        
        # Çift tıklama olayı
        self.product_table.bind("<Double-1>", self.on_item_double_click)
        
        # Alt kısım - İlerleme durumu
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        # İlerleme çubuğu
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(bottom_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Durum etiketi
        self.status_label = ttk.Label(bottom_frame, text="Hazır")
        self.status_label.pack(fill=tk.X, padx=5)
        
        # WordPress yükleme çerçevesi
        upload_frame = ttk.LabelFrame(main_frame, text="WordPress Yükleme", padding="10")
        upload_frame.pack(fill=tk.X, pady=10)
        
        # WordPress URL
        ttk.Label(upload_frame, text="WordPress URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.wp_url_entry = ttk.Entry(upload_frame, width=40)
        self.wp_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Kullanıcı adı
        ttk.Label(upload_frame, text="Kullanıcı Adı:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.wp_username_entry = ttk.Entry(upload_frame, width=20)
        self.wp_username_entry.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Şifre
        ttk.Label(upload_frame, text="Şifre:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.wp_password_entry = ttk.Entry(upload_frame, width=20, show="*")
        self.wp_password_entry.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W+tk.E)
        
        # Kategori ID
        ttk.Label(upload_frame, text="Kategori ID:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.category_id_entry = ttk.Entry(upload_frame, width=10)
        self.category_id_entry.insert(0, "9")  # Varsayılan kategori ID
        self.category_id_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Yükleme düğmesi
        self.upload_button = ttk.Button(upload_frame, text="Seçili Ürünleri Yükle", command=self.start_uploading)
        self.upload_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
    
    def toggle_ssl_verification(self):
        """SSL doğrulama ayarını değiştirir."""
        self.scraper.verify_ssl = self.verify_ssl.get()
        self.site_analyzer.verify_ssl = self.verify_ssl.get()
        self.selector_builder.verify_ssl = self.verify_ssl.get()
    
    def start_scanning(self):
        """Ürün tarama işlemini başlatır."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Hata", "Lütfen bir URL girin.")
            return
        
        try:
            max_pages = int(self.max_pages_entry.get())
        except ValueError:
            max_pages = 10
        
        # Tarama işlemini başlat
        run_with_progress(
            self.root,
            self.scan_products,
            args=(url, max_pages),
            on_complete=lambda result: self.update_product_list(result)
        )
    
    def start_site_analysis(self):
        """Site analiz işlemini başlatır."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Hata", "Lütfen bir URL girin.")
            return
        
        # Analiz işlemini başlat
        run_with_progress(
            self.root,
            self.analyze_site,
            args=(url,),
            on_complete=lambda result: self.show_category_tree()
        )
    
    def start_selector_builder(self):
        """Seçici oluşturma işlemini başlatır."""
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Hata", "Lütfen bir URL girin.")
            return
        
        # Seçici oluşturma işlemini başlat
        run_with_progress(
            self.root,
            self.build_selectors,
            args=(url,),
            on_complete=lambda result: self.update_progress("Seçici oluşturma tamamlandı.") if result else None
        )
    
    def build_selectors(self, url):
        """Seçici oluşturma işlemini gerçekleştirir."""
        return self.selector_builder.load_page_preview(url)
    
    def scan_products(self, url, max_pages):
        """Ürün tarama işlemini gerçekleştirir."""
        return self.scraper.scrape_products(url, max_pages)
    
    def analyze_site(self, url):
        """Site analiz işlemini gerçekleştirir."""
        self.category_tree = self.site_analyzer.analyze_site(url)
        return self.category_tree
    
    def show_category_tree(self):
        """Kategori ağacını gösterir."""
        if not self.category_tree:
            messagebox.showinfo("Bilgi", "Kategori ağacı bulunamadı.")
            return
        
        # Kategori ağacı penceresini oluştur
        tree_window = tk.Toplevel(self.root)
        tree_window.title("Kategori Ağacı")
        tree_window.geometry("600x400")
        
        # Ağaç görünümü
        tree_frame = ttk.Frame(tree_window, padding="10")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Treeview
        category_tree = ttk.Treeview(tree_frame, show="tree")
        category_tree.pack(fill=tk.BOTH, expand=True)
        
        # Scrollbar bağlantısı
        scrollbar.config(command=category_tree.yview)
        category_tree.config(yscrollcommand=scrollbar.set)
        
        # Kategori ağacını doldur
        def add_category_to_tree(parent_id, category_data, level=0):
            for url, data in category_data.items():
                if isinstance(data, dict) and "name" in data:
                    # Kategori adını ve ürün sayısını göster
                    item_text = f"{data['name']} ({data.get('product_count', 0)} ürün)"
                    item_id = category_tree.insert(parent_id, "end", text=item_text)
                    
                    # Alt kategorileri ekle
                    if "subcategories" in data and data["subcategories"]:
                        add_category_to_tree(item_id, data["subcategories"], level + 1)
        
        # Kök kategoriyi ekle
        root_id = category_tree.insert("", "end", text="Kategoriler")
        add_category_to_tree(root_id, self.category_tree)
        
        # Kategori ağacını genişlet
        category_tree.item(root_id, open=True)
        
        # Düğmeler
        button_frame = ttk.Frame(tree_window, padding="10")
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="JSON Olarak Kaydet", 
                  command=self.save_categories_to_json).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(button_frame, text="Kapat", 
                  command=tree_window.destroy).pack(side=tk.RIGHT, padx=5)
    
    def save_categories_to_json(self):
        """Kategori ağacını JSON dosyasına kaydeder."""
        if not self.category_tree:
            messagebox.showinfo("Bilgi", "Kaydedilecek kategori ağacı bulunamadı.")
            return
        
        filename = f"{self.site_analyzer.domain}_categories.json"
        self.site_analyzer.export_to_json(filename)
        messagebox.showinfo("Bilgi", f"Kategori ağacı {filename} dosyasına kaydedildi.")
    
    def update_product_list(self, products):
        """Ürün listesini günceller."""
        self.products = products
        
        # Tabloyu temizle
        for item in self.product_table.get_children():
            self.product_table.delete(item)
        
        # Ürünleri tabloya ekle
        for i, product in enumerate(products):
            selected = "✓" if product.get("selected", False) else ""
            title = product.get("title", "")
            price = product.get("price", "")
            
            self.product_table.insert("", "end", values=(selected, title, price, "Resim"), iid=i)
    
    def load_product_image(self, image_url, size=(50, 50)):
        """Ürün resmini yükler."""
        try:
            return load_image_from_url(image_url, size, self.verify_ssl.get())
        except Exception as e:
            print(f"Resim yüklenemedi: {e}")
            return None
    
    def on_item_double_click(self, event):
        """Ürün tablosunda bir öğeye çift tıklandığında ürün önizleme penceresini açar."""
        selection = self.product_table.selection()
        if selection:
            index = int(selection[0])
            if 0 <= index < len(self.products):
                self.show_product_preview(self.products[index], index)
    
    def show_product_preview(self, product, index):
        """Ürün önizleme penceresini gösterir."""
        def on_save(updated_product):
            self.products[index] = updated_product
            self.update_product_list(self.products)
        
        ProductPreviewWindow(self.root, product, self.verify_ssl.get(), on_save)
    
    def select_all_products(self):
        """Tüm ürünleri seçer."""
        for i, product in enumerate(self.products):
            product["selected"] = True
            self.product_table.item(i, values=("✓", product.get("title", ""), product.get("price", ""), "Resim"))
    
    def deselect_all_products(self):
        """Tüm ürünlerin seçimini kaldırır."""
        for i, product in enumerate(self.products):
            product["selected"] = False
            self.product_table.item(i, values=("", product.get("title", ""), product.get("price", ""), "Resim"))
    
    def save_products(self):
        """Ürünleri JSON dosyasına kaydeder."""
        if not self.products:
            messagebox.showinfo("Bilgi", "Kaydedilecek ürün bulunamadı.")
            return
        
        self.scraper.save_products_to_json()
        messagebox.showinfo("Bilgi", "Ürünler products.json dosyasına kaydedildi.")
    
    def load_products(self):
        """JSON dosyasından ürünleri yükler."""
        products = self.scraper.load_products_from_json()
        if products:
            self.update_product_list(products)
            messagebox.showinfo("Bilgi", f"{len(products)} ürün yüklendi.")
    
    def show_stats(self):
        """Tarama istatistiklerini gösterir."""
        stats_summary = self.scraper.get_stats_summary()
        
        # İstatistik penceresini oluştur
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Tarama İstatistikleri")
        stats_window.geometry("600x400")
        
        # İstatistik metni
        text_widget = tk.Text(stats_window, wrap=tk.WORD, padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, stats_summary)
        text_widget.config(state=tk.DISABLED)
        
        # Kapat düğmesi
        ttk.Button(stats_window, text="Kapat", command=stats_window.destroy).pack(pady=10)
    
    def start_uploading(self):
        """WordPress'e ürün yükleme işlemini başlatır."""
        # WordPress bilgilerini kontrol et
        wp_url = self.wp_url_entry.get().strip()
        username = self.wp_username_entry.get().strip()
        password = self.wp_password_entry.get().strip()
        
        if not wp_url or not username or not password:
            messagebox.showerror("Hata", "Lütfen WordPress bilgilerini eksiksiz girin.")
            return
        
        # Seçili ürünleri bul
        selected_items = [product for product in self.products if product.get("selected", False)]
        
        if not selected_items:
            messagebox.showerror("Hata", "Lütfen yüklenecek ürünleri seçin.")
            return
        
        # Kategori ID'yi al
        try:
            category_id = int(self.category_id_entry.get())
        except ValueError:
            category_id = 9  # Varsayılan kategori ID
        
        # Yükleme işlemini başlat
        self.uploader = WordPressUploader(wp_url, username, password)
        self.uploader.set_progress_callback(self.update_progress)
        
        run_with_progress(
            self.root,
            self.upload_products,
            args=(selected_items, category_id),
            on_complete=lambda result: messagebox.showinfo("Bilgi", f"{len(result)} ürün başarıyla yüklendi.")
        )
    
    def upload_products(self, selected_items, category_id):
        """Seçili ürünleri WordPress'e yükler."""
        uploaded = []
        
        for i, product in enumerate(selected_items):
            try:
                self.update_progress(f"Ürün yükleniyor: {product.get('title', 'Ürün')} ({i+1}/{len(selected_items)})", i+1, len(selected_items))
                result = self.uploader.upload_product(product, category_id)
                if result:
                    uploaded.append(result)
            except Exception as e:
                print(f"Ürün yüklenirken hata: {e}")
        
        return uploaded
    
    def update_progress(self, message, current=0, total=0):
        """İlerleme durumunu günceller."""
        self.status_label.config(text=message)
        
        if total > 0:
            progress = (current / total) * 100
            self.progress_var.set(progress)
        else:
            self.progress_var.set(0)
            
        self.root.update_idletasks()