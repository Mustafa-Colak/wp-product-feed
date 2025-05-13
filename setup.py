"""
Bu script, gerekli klasörleri ve dosyaları oluşturur.
"""

import os
import sys

def create_directory(directory):
    """Dizin yoksa oluşturur."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Dizin oluşturuldu: {directory}")
    else:
        print(f"Dizin zaten var: {directory}")

def create_init_file(directory):
    """Dizinde __init__.py dosyası oluşturur."""
    init_file = os.path.join(directory, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, 'w', encoding='utf-8') as f:
            f.write(f"# Bu dosya {os.path.basename(directory)} paketini tanımlar\n")
        print(f"__init__.py dosyası oluşturuldu: {init_file}")
    else:
        print(f"__init__.py dosyası zaten var: {init_file}")

def setup_project():
    """Proje yapısını oluşturur."""
    # Ana dizinler
    directories = ["scrapers", "uploaders", "ui"]
    
    for directory in directories:
        create_directory(directory)
        create_init_file(directory)
    
    print("\nProje yapısı başarıyla oluşturuldu.")
    print("Şimdi dosyaları ilgili konumlara yerleştirin.")
if __name__ == "__main__":
    setup_project()
