from PIL import Image, ImageTk
from io import BytesIO
import requests
import tkinter as tk
from tkinter import ttk
import threading

def load_image_from_url(url, size=(100, 100), verify_ssl=True):
    """URL'den resim yükler ve belirtilen boyuta getirir."""
    try:
        response = requests.get(url, verify=verify_ssl, timeout=5)
        if response.status_code == 200:
            img_data = BytesIO(response.content)
            img = Image.open(img_data)
            img.thumbnail(size, Image.LANCZOS)
            return ImageTk.PhotoImage(img)
    except Exception as e:
        print(f"Resim yüklenirken hata: {e}")
    return None

def create_scrollable_frame(parent):
    """Kaydırılabilir bir çerçeve oluşturur."""
    # Ana çerçeve
    container = ttk.Frame(parent)
    container.pack(fill=tk.BOTH, expand=True)
    
    # Canvas
    canvas = tk.Canvas(container)
    scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    return scrollable_frame

def run_with_progress(root, func, args=(), kwargs={}, on_complete=None):
    """İşlevi ayrı bir thread'de çalıştırır ve ilerleme gösterir."""
    progress_window = tk.Toplevel(root)
    progress_window.title("İşlem Sürüyor")
    progress_window.geometry("300x100")
    progress_window.transient(root)
    progress_window.grab_set()
    
    ttk.Label(progress_window, text="İşlem devam ediyor...").pack(pady=10)
    
    progress = ttk.Progressbar(progress_window, mode="indeterminate")
    progress.pack(fill=tk.X, padx=20, pady=10)
    progress.start()
    
    def thread_func():
        result = func(*args, **kwargs)
        progress_window.destroy()
        if on_complete:
            on_complete(result)
    
    threading.Thread(target=thread_func, daemon=True).start()