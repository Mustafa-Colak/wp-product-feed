import tkinter as tk
from tkinter import ttk, simpledialog
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
        
        # Resim önbelleği
        self.photo = None
        
        self.create_widgets()
    
    def create_widgets(self):
        # Ana çerçeve
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Üst kısım - Başlık ve resim
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=10)
        
        # Ürün başlığı
        title_label = ttk.Label(top_frame, text=self.product["title"], font=("Arial", 16, "bold"), wraplength=700)
        title_label.pack(pady=10)
        
        # Orta kısım - Resim ve bilgiler yan yana
        middle_frame = ttk.Frame(main_frame)
        middle_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Sol taraf - Resim
        left_frame = ttk.Frame(middle_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Ürün resmi
        if self.product["image_url"]:
            try:
                response = requests.get(self.product["image_url"], verify=self.verify_ssl)
                if response.status_code == 200:
                    img_data = BytesIO(response.content)
                    img = Image.open(img_data)
                    
                    # Resmi yeniden boyutlandır
                    max_size = (300, 300)
                    img.thumbnail(max_size, Image.LANCZOS)
                    
                    self.photo = ImageTk.PhotoImage(img)
                    img_label = ttk.Label(left_frame, image=self.photo)
                    img_label.pack(pady=10)
                    
                    # Resim URL'si
                    url_label = ttk.Label(left_frame, text="Resim URL:", font=("Arial", 10, "bold"))
                    url_label.pack(anchor=tk.W, pady=(10, 0))
                    
                    url_entry = ttk.Entry(left_frame, width=40)
                    url_entry.insert(0, self.product["image_url"])
                    url_entry.pack(fill=tk.X, pady=5)
                    
                    # Resmi değiştir düğmesi
                    ttk.Button(left_frame, text="Resmi Değiştir", 
                              command=lambda: self.change_image()).pack(pady=5)
            except Exception as e:
                ttk.Label(left_frame, text=f"Resim yüklenemedi: {e}", wraplength=300).pack(pady=10)
        else:
            ttk.Label(left_frame, text="Resim bulunamadı").pack(pady=10)
            
            # Resim URL'si ekle
            url_label = ttk.Label(left_frame, text="Resim URL:", font=("Arial", 10, "bold"))
            url_label.pack(anchor=tk.W, pady=(10, 0))
            
            self.image_url_entry = ttk.Entry(left_frame, width=40)
            self.image_url_entry.pack(fill=tk.X, pady=5)
            
            # Resim ekle düğmesi
            ttk.Button(left_frame, text="Resim Ekle", 
                      command=lambda: self.add_image()).pack(pady=5)
        
        # Sağ taraf - Ürün bilgileri
        right_frame = ttk.Frame(middle_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Başlık düzenleme
        title_frame = ttk.Frame(right_frame)
        title_frame.pack(fill=tk.X, pady=5)
        ttk.Label(title_frame, text="Başlık: ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.title_entry = ttk.Entry(title_frame, width=70)
        self.title_entry.insert(0, self.product["title"])
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Fiyat düzenleme
        price_frame = ttk.Frame(right_frame)
        price_frame.pack(fill=tk.X, pady=5)
        ttk.Label(price_frame, text="Fiyat: ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.price_entry = ttk.Entry(price_frame, width=20)
        self.price_entry.insert(0, self.product["price"])
        self.price_entry.pack(side=tk.LEFT)
        
        # URL
        url_frame = ttk.Frame(right_frame)
        url_frame.pack(fill=tk.X, pady=5)
        ttk.Label(url_frame, text="URL: ", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        url_entry = ttk.Entry(url_frame, width=70)
        url_entry.insert(0, self.product["product_url"])
        url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Açıklama
        ttk.Label(right_frame, text="Açıklama:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=5)
        self.desc_text = tk.Text(right_frame, wrap=tk.WORD, height=10)
        self.desc_text.insert(tk.END, self.product["description"])
        self.desc_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Alt kısım - Düğmeler
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Değişiklikleri Kaydet", command=self.save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Kapat", command=self.window.destroy).pack(side=tk.LEFT, padx=5)
    
    def change_image(self):
        """Ürün resmini değiştir."""
        new_url = simpledialog.askstring("Resim URL", "Yeni resim URL'sini girin:", parent=self.window)
        if new_url:
            self.product["image_url"] = new_url
            # Pencereyi yeniden oluştur
            self.window.destroy()
            self.__init__(self.parent, self.product, self.verify_ssl, self.on_save)
    
    def add_image(self):
        """Ürüne resim ekle."""
        new_url = self.image_url_entry.get()
        if new_url:
            self.product["image_url"] = new_url
            # Pencereyi yeniden oluştur
            self.window.destroy()
            self.__init__(self.parent, self.product, self.verify_ssl, self.on_save)
    
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