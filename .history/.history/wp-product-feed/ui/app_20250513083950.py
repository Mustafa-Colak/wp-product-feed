import tkinter as tk
from tkinter import ttk, messagebox
import threading
from scrapers.product_scraper import ProductScraper
from uploaders.wordpress_uploader import WordPressUploader
from ui.product_preview import ProductPreviewWindow
from config import DEFAULT_CONFIG

class ProductScraperApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Ürün Aktarma Aracı")
        self.root.geometry("1200x800")
        
        self.scraper = ProductScraper()
        self.uploader = None
        
        # İlerleme bilgisi için değişkenler
        self.progress_var = tk.DoubleVar()
        self.progress_text = tk.StringVar()
        self.progress_text.set("Hazır")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Ana çerçeve
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Üst kısım - URL girişi ve tarama düğmesi
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(top_frame, text="Taranacak URL:").pack(side=tk.LEFT, padx=5)
        self.url_entry = ttk.Entry(top_frame, width=50)
        self.url_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Label(top_frame, text="Maks. Sayfa:").pack(side=tk.LEFT, padx=5)
        self.max_pages_entry = ttk.Entry(top_frame, width=5)
        self.max_pages_entry.insert(0, str(DEFAULT_CONFIG["max_pages"]))
        self.max_pages_entry.pack(side=tk.LEFT, padx=5)
        
        # SSL doğrulama seçeneği
        self.verify_ssl_var = tk.BooleanVar(value=DEFAULT_CONFIG["verify_ssl"])
        self.verify_ssl_check = ttk.Checkbutton(
            top_frame, 
            text="SSL Doğrula", 
            variable=self.verify_ssl_var,
            command=self.toggle_ssl_verification
        )
        self.verify_ssl_check.pack(side=tk.LEFT, padx=5)
        
        self.scan_button = ttk.Button(top_frame, text="Ürünleri Tara", command=self.start_scanning)
        self.scan_button.pack(side=tk.LEFT, padx=5)
        
        # İlerleme çubuğu
        progress_frame = ttk.Frame(main_frame)
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            orient=tk.HORIZONTAL, 
            length=100, 
            mode='determinate',
            variable=self.progress_var
        )
        self.progress_bar.pack(fill=tk.X, side=tk.TOP, padx=5, pady=5)
        
        ttk.Label(progress_frame, textvariable=self.progress_text).pack(side=tk.LEFT, padx=5)
        
        # Orta kısım - Ürün listesi
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Treeview oluştur
        self.tree = ttk.Treeview(middle_frame, columns=("title", "price", "url"), show="headings")
        self.tree.heading("title", text="Ürün Adı")
        self.tree.heading("price", text="Fiyat")
        self.tree.heading("url", text="URL")
        
        self.tree.column("title", width=400)
        self.tree.column("price", width=100)
        self.tree.column("url", width=500)
        
        # Çift tıklama olayını ekle
        self.tree.bind("<Double-1>", self.on_item_double_click)
        
        # Scrollbar ekle
        scrollbar = ttk.Scrollbar(middle_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Alt kısım - WordPress bilgileri ve yükleme düğmesi
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(bottom_frame, text="WordPress URL:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.wp_url_entry = ttk.Entry(bottom_frame, width=30)
        self.wp_url_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(bottom_frame, text="Kullanıcı Adı:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.username_entry = ttk.Entry(bottom_frame, width=30)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(bottom_frame, text="Şifre:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.password_entry = ttk.Entry(bottom_frame, width=30, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Kategori seçimi
        ttk.Label(bottom_frame, text="Kategori ID:").grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        self.category_entry = ttk.Entry(bottom_frame, width=10)
        self.category_entry.insert(0, str(DEFAULT_CONFIG["default_category_id"]))
        self.category_entry.grid(row=3, column=1, padx=5, pady=5, sticky=tk.W)
        
        # WordPress SSL doğrulama seçeneği
        self.wp_verify_ssl_var = tk.BooleanVar(value=DEFAULT_CONFIG["verify_ssl"])
        self.wp_verify_ssl_check = ttk.Checkbutton(
            bottom_frame, 
            text="WordPress SSL Doğrula", 
            variable=self.wp_verify_ssl_var
        )
        self.wp_verify_ssl_check.grid(row=4, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # Düğmeler
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=5)
        
        self.select_all_button = ttk.Button(button_frame, text="Tümünü Seç", command=self.select_all_products)
        self.select_all_button.pack(side=tk.LEFT, padx=5)
        
        self.deselect_all_button = ttk.Button(button_frame, text="Seçimi Kaldır", command=self.deselect_all_products)
        self.deselect_all_button.pack(side=tk.LEFT, padx=5)
        
        self.upload_button = ttk.Button(button_frame, text="Seçili Ürünleri Yükle", command=self.start_uploading)
        self.upload_button.pack(side=tk.LEFT, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Ürünleri Kaydet", command=self.save_products)
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        self.load_button = ttk.Button(button_frame, text="Ürünleri Yükle", command=self.load_products)
        self.load_button.pack(side=tk.LEFT, padx=5)
        
        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def toggle_ssl_verification(self):
        """SSL doğrulama seçeneğini değiştirir."""
        self.scraper.verify_ssl = self.verify_ssl_var.get()
    
    def update_progress(self, message, current=0, total=0):
        """İlerleme durumunu günceller."""
        self.progress_text.set(message)
        if total > 0:
            self.progress_var.set((current / total) * 100)
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def on_item_double_click(self, event):
        """Ürün listesinde bir öğeye çift tıklandığında ürün önizlemesini gösterir."""
        selected = self.tree.selection()
        if not selected:
            return
            
        item = selected[0]
        index = int(item)
        product = self.scraper.products[index]
        self.show_product_preview(product, index)
    
    def show_product_preview(self, product, index):
        """Ürün önizleme penceresini gösterir."""
        def on_save(updated_product):
            # Ürünü güncelle
            self.scraper.products[index] = updated_product
            
            # Treeview'i güncelle
            self.tree.item(str(index), values=(
                updated_product["title"],
                updated_product["price"],
                updated_product["product_url"]
            ))
        
        # Ürün önizleme penceresini oluştur
        ProductPreviewWindow(
            self.root, 
            product, 
            verify_ssl=self.scraper.verify_ssl,
            on_save=on_save
        )
        
    def start_scanning(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Hata", "Lütfen bir URL girin.")
            return
            
        try:
            max_pages = int(self.max_pages_entry.get())
        except ValueError:
            max_pages = DEFAULT_CONFIG["max_pages"]
            
        # SSL doğrulama ayarını güncelle
        self.scraper.verify_ssl = self.verify_ssl_var.get()
            
        self.status_var.set("Ürünler taranıyor...")
        self.scan_button.config(state=tk.DISABLED)
        
        # İlerleme çubuğunu sıfırla
        self.progress_var.set(0)
        self.progress_text.set("Tarama hazırlanıyor...")
        
        # Treeview'i temizle
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # İlerleme callback'ini ayarla
        self.scraper.set_progress_callback(self.update_progress)
        
        # Tarama işlemini ayrı bir thread'de başlat
        threading.Thread(target=self.scan_products, args=(url, max_pages), daemon=True).start()
    
    def scan_products(self, url, max_pages):
        try:
            products = self.scraper.scrape_products(url, max_pages)
            
            # UI güncellemelerini ana thread'de yap
            self.root.after(0, self.update_product_list, products)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Hata", f"Tarama sırasında hata oluştu: {e}"))
            self.root.after(0, lambda: self.status_var.set("Hata oluştu"))
            
        finally:
            self.root.after(0, lambda: self.scan_button.config(state=tk.NORMAL))
    
    def update_product_list(self, products):
        for i, product in enumerate(products):
            self.tree.insert("", tk.END, iid=i, values=(
                product["title"],
                product["price"],
                product["product_url"]
            ))
            
        self.status_var.set(f"{len(products)} ürün bulundu.")
        self.progress_text.set(f"Tarama tamamlandı. {len(products)} ürün bulundu.")
        self.progress_var.set(100)
    
    def select_all_products(self):
        for item in self.tree.get_children():
            self.tree.selection_add(item)
    
    def deselect_all_products(self):
        for item in self.tree.get_children():
            self.tree.selection_remove(item)
    
    def save_products(self):
        if not self.scraper.products:
            messagebox.showinfo("Bilgi", "Kaydedilecek ürün bulunamadı.")
            return
            
        self.scraper.save_products_to_json()
        messagebox.showinfo("Başarılı", "Ürünler products.json dosyasına kaydedildi.")
    
    def load_products(self):
        self.scraper.load_products_from_json()
        
        # Treeview'i temizle
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Ürünleri listele
        self.update_product_list(self.scraper.products)
    
    def start_uploading(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showinfo("Bilgi", "Lütfen yüklenecek ürünleri seçin.")
            return
            
        wp_url = self.wp_url_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not all([wp_url, username, password]):
            messagebox.showerror("Hata", "Lütfen WordPress bilgilerini girin.")
            return
            
        try:
            category_id = int(self.category_entry.get())
        except ValueError:
            category_id = DEFAULT_CONFIG["default_category_id"]
            
        self.uploader = WordPressUploader(wp_url, username, password)
        self.uploader.verify_ssl = self.wp_verify_ssl_var.get()
        self.uploader.set_progress_callback(lambda msg: self.update_progress(msg))
        
        self.status_var.set("Ürünler yükleniyor...")
        self.upload_button.config(state=tk.DISABLED)
        
        # İlerleme çubuğunu sıfırla
        self.progress_var.set(0)
        self.progress_text.set("Yükleme hazırlanıyor...")
        
        # Yükleme işlemini ayrı bir thread'de başlat
        threading.Thread(target=self.upload_products, args=(selected_items, category_id), daemon=True).start()
    
    def upload_products(self, selected_items, category_id):
        success_count = 0
        error_count = 0
        total = len(selected_items)
        
        for i, item in enumerate(selected_items):
            try:
                index = int(item)
                product = self.scraper.products[index]
                
                # UI'ı güncelle
                self.update_progress(f"Yükleniyor: {product['title']} ({i+1}/{total})", i+1, total)
                
                result = self.uploader.upload_product(product, category_id)
                if result:
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                print(f"Ürün yüklenirken hata: {e}")
                error_count += 1
        
        # İşlem tamamlandığında UI'ı güncelle
        final_message = f"Yükleme tamamlandı. Başarılı: {success_count}, Hata: {error_count}"
        self.root.after(0, lambda: self.update_progress(final_message, total, total))
        self.root.after(0, lambda: self.upload_button.config(state=tk.NORMAL))
        self.root.after(0, lambda: messagebox.showinfo("Tamamlandı", final_message))