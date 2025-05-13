import os
import sys
import subprocess
import platform

def setup_virtual_environment():
    """Sanal ortam kurulumu ve gerekli paketlerin yüklenmesi"""
    
    print("Ürün Aktarma Aracı Kurulumu Başlatılıyor...")
    
    # İşletim sistemini kontrol et
    system = platform.system().lower()
    
    # Python yolu
    python_executable = sys.executable
    
    # Sanal ortam klasör adı
    venv_dir = "venv"
    
    # Sanal ortam zaten var mı kontrol et
    if os.path.exists(venv_dir):
        print(f"'{venv_dir}' zaten mevcut. Yeniden kurmak ister misiniz? (e/h): ", end="")
        response = input().lower()
        if response == 'e':
            print(f"Mevcut '{venv_dir}' siliniyor...")
            try:
                if system == "windows":
                    os.system(f"rmdir /s /q {venv_dir}")
                else:
                    os.system(f"rm -rf {venv_dir}")
            except Exception as e:
                print(f"Hata: {e}")
                return False
        else:
            print("Mevcut sanal ortam korunuyor.")
            return True
    
    # Sanal ortam oluştur
    print(f"Sanal ortam '{venv_dir}' oluşturuluyor...")
    try:
        subprocess.check_call([python_executable, "-m", "venv", venv_dir])
    except subprocess.CalledProcessError as e:
        print(f"Sanal ortam oluşturulurken hata: {e}")
        return False
    
    # Pip'i güncelle
    print("pip güncelleniyor...")
    
    # İşletim sistemine göre aktivasyon komutu
    if system == "windows":
        pip_cmd = f"{venv_dir}\\Scripts\\pip"
        python_cmd = f"{venv_dir}\\Scripts\\python"
    else:
        pip_cmd = f"{venv_dir}/bin/pip"
        python_cmd = f"{venv_dir}/bin/python"
    
    try:
        subprocess.check_call([pip_cmd, "install", "--upgrade", "pip"])
    except subprocess.CalledProcessError as e:
        print(f"pip güncellenirken hata: {e}")
        return False
    
    # Gereksinimleri yükle
    print("Gerekli paketler yükleniyor...")
    try:
        subprocess.check_call([pip_cmd, "install", "-r", "requirements.txt"])
    except subprocess.CalledProcessError as e:
        print(f"Paketler yüklenirken hata: {e}")
        return False
    
    print("\nKurulum tamamlandı!")
    
    # Nasıl çalıştırılacağına dair bilgi ver
    print("\nUygulamayı çalıştırmak için:")
    if system == "windows":
        print(f"  {venv_dir}\\Scripts\\python product_scraper.py")
    else:
        print(f"  {venv_dir}/bin/python product_scraper.py")
    
    return True

if __name__ == "__main__":
    setup_virtual_environment()