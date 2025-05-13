import tkinter as tk
from tkinter import ttk
import requests
from PIL import Image, ImageTk
from io import BytesIO

class ProductPreviewWindow:
    def __init__(self, parent, product, verify_ssl=True, on_save=None):
        self.parent = parent
        self.product = product
        self.verify_ssl = verify_ssl
        self.on_save = on_save
        
        self.window = tk.Toplevel(parent)
        self.window.title("Ürün Önizleme")
        self.window.geometry("800x600")
        
        self.create_widgets()
        
    def create_widgets(self):
        # Ana çerçeve
        frame = ttk.Frame(self.window, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Ürün başlığı
        ttk.Label(frame, text=self.product["title"], font=("Arial", 16, "bold")).pack(pady=10)
        
        # Ürün resmi
        if self.product["image_url"]:
            try:
                response = requests.get(self.product["image_url"], verify=self.verify_ssl)
                if response.status_code == 200:
                    img_data = BytesIO(response.content)
                    img = Image.open(img_data)
                    
                    # Resmi yeniden boyutlandır
                    max_size = (400, 400)
                    img.thumbnail(max_size, Image.LANCZOS)
                    
                    photo = ImageTk.PhotoImage(img)
                    img_label = ttk.Label(frame, image=photo)
                    img_label.image = photo  # Referansı sakla
                    img_label.pack(pady=10)
            except Exception as e:
                ttk.Label(frame, text=f"Resim yüklenemedi: {e}").pack(pady=10)
        
        # Başlık düzenleme
        title_frame = ttk.Frame(frame)
        title_frame.pack(fill=tk.X, pady=5)
        ttk.Label(title_frame, text="Başlık: ").pack(side=tk.LEFT)
        self.title_entry = ttk.Entry(title_frame, width=70)
        self.title_entry.insert(0, self.product["title"])
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Fiyat düzenleme
        price_frame = ttk.Frame(frame)
        price_frame.pack(fill=tk.X, pady=5)
        ttk.Label(price_frame, text="Fiyat: ").pack(side=tk.LEFT)
        self.price_entry = ttk.Entry(price_frame, width=20)
        self.price_entry.insert(0, self.product["price"])
        self.price_entry.pack(side=tk.LEFT)
        
        # URL
        url_frame = ttk.Frame(frame)
        url_frame.pack(fill=tk.X, pady=5)
        ttk.Label(url_frame, text="URL: ").pack(side=tk.LEFT)
        url_entry = ttk.Entry(url_frame, width=70)
        url_entry.insert(0, self.product["product_url"])
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Açıklama
        ttk.Label(frame, text="Açıklama:", font=("Arial", 12)).pack(anchor=tk.W, pady=5)
        self.desc_text = tk.Text(frame, wrap=tk.WORD, height=10)
        self.desc_text.insert(tk.END, self.product["description"])
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Düğmeler
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Değişiklikleri Kaydet", command=self.save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kapat", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def save_changes(self):
        """Değişiklikleri kaydeder ve pencereyi kapatır."""
        # Ürün bilgilerini güncelle
        self.product["title"] = self.title_entry.get()
        self.product["price"] = self.price_entry.get()
        self.product["description"] = self.desc_text.get("1.0", tk.END).strip()
        
        # Callback fonksiyonu çağır
        if self.on_save:
            self.on_save(self.product)
            
        self.window.destroy()