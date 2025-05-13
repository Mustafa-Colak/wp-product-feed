import tkinter as tk
from tkinter import ttk
import webview
import os
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
from scrapers.base_scraper import BaseScraper

class SelectorBuilder(BaseScraper):
    """Web sayfasını görüntüleyip interaktif olarak seçici oluşturmayı sağlayan sınıf."""
    
    def __init__(self):
        super().__init__()
        self.selectors = {
            "product_containers": [],
            "titles": [],
            "prices": [],
            "images": [],
            "descriptions": [],
            "next_page": []
        }
        self.current_page_html = None
        self.current_url = None
        self.window = None
        self.progress_callback = None
        
    def set_progress_callback(self, callback):
        """İlerleme durumunu bildirmek için callback fonksiyonu ayarlar."""
        self.progress_callback = callback
        
    def update_progress(self, message, current=0, total=0):
        """İlerleme durumunu günceller."""
        if self.progress_callback:
            self.progress_callback(message, current, total)
        else:
            print(message)
    
    def load_page_preview(self, url):
        """Belirtilen URL'yi yükler ve önizleme penceresini açar."""
        self.current_url = url
        self.extract_domain(url)
        
        self.update_progress(f"Sayfa yükleniyor: {url}")
        
        # Sayfayı indir
        html = self.get_page(url)
        if not html:
            self.update_progress(f"Sayfa yüklenemedi: {url}")
            return False
            
        self.current_page_html = html
        
        # Geçici HTML dosyasını oluştur
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_file = os.path.join(temp_dir, "page_preview.html")
        
        # Seçici oluşturma JavaScript kodunu HTML'e ekle
        soup = BeautifulSoup(html, 'html.parser')
        
        # Seçici oluşturma için gerekli JavaScript kodunu ekle
        script_tag = soup.new_tag("script")
        script_tag.string = """
        document.addEventListener('DOMContentLoaded', function() {
            // Tüm elementlere hover ve tıklama olayları ekle
            var allElements = document.querySelectorAll('*');
            var selectedElements = {};
            var currentType = '';
            
            // Kontrol paneli oluştur
            var controlPanel = document.createElement('div');
            controlPanel.style.position = 'fixed';
            controlPanel.style.top = '10px';
            controlPanel.style.right = '10px';
            controlPanel.style.backgroundColor = 'rgba(255, 255, 255, 0.9)';
            controlPanel.style.padding = '10px';
            controlPanel.style.border = '1px solid #ccc';
            controlPanel.style.borderRadius = '5px';
            controlPanel.style.zIndex = '10000';
            controlPanel.innerHTML = `
                <h3>Seçici Oluşturucu</h3>
                <div>
                    <button id="select-product">Ürün Konteyneri</button>
                    <button id="select-title">Başlık</button>
                    <button id="select-price">Fiyat</button>
                    <button id="select-image">Resim</button>
                    <button id="select-desc">Açıklama</button>
                    <button id="select-next">Sonraki Sayfa</button>
                </div>
                <div style="margin-top: 10px;">
                    <button id="save-selectors">Seçicileri Kaydet</button>
                </div>
                <div id="selection-info" style="margin-top: 10px; max-width: 300px; word-wrap: break-word;"></div>
            `;
            document.body.appendChild(controlPanel);
            
            // Düğmelere tıklama olayları ekle
            document.getElementById('select-product').addEventListener('click', function() {
                currentType = 'product_containers';
                updateSelectionMode();
            });
            
            document.getElementById('select-title').addEventListener('click', function() {
                currentType = 'titles';
                updateSelectionMode();
            });
            
            document.getElementById('select-price').addEventListener('click', function() {
                currentType = 'prices';
                updateSelectionMode();
            });
            
            document.getElementById('select-image').addEventListener('click', function() {
                currentType = 'images';
                updateSelectionMode();
            });
            
            document.getElementById('select-desc').addEventListener('click', function() {
                currentType = 'descriptions';
                updateSelectionMode();
            });
            
            document.getElementById('select-next').addEventListener('click', function() {
                currentType = 'next_page';
                updateSelectionMode();
            });
            
            document.getElementById('save-selectors').addEventListener('click', function() {
                // Seçicileri Python'a gönder
                window.pywebview.api.save_selectors(selectedElements);
            });
            
            function updateSelectionMode() {
                // Tüm düğmeleri normal hale getir
                var buttons = controlPanel.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    buttons[i].style.backgroundColor = '';
                }
                
                // Aktif düğmeyi vurgula
                document.getElementById('select-' + currentType.replace('_containers', '').replace('_page', '')).style.backgroundColor = '#ffcc00';
                
                document.getElementById('selection-info').textContent = currentType + ' için bir element seçin';
            }
            
            function getSelector(element) {
                if (element.id) {
                    return '#' + element.id;
                }
                
                if (element.className) {
                    var classes = element.className.split(' ').filter(function(c) { return c; });
                    if (classes.length > 0) {
                        return '.' + classes.join('.');
                    }
                }
                
                var tag = element.tagName.toLowerCase();
                var siblings = [].filter.call(element.parentNode.children, function(child) {
                    return child.tagName === element.tagName;
                });
                
                if (siblings.length === 1) {
                    return getSelector(element.parentNode) + ' > ' + tag;
                }
                
                var index = [].indexOf.call(siblings, element);
                return getSelector(element.parentNode) + ' > ' + tag + ':nth-child(' + (index + 1) + ')';
            }
            
            function addHoverEffect() {
                allElements.forEach(function(el) {
                    el.addEventListener('mouseover', function(e) {
                        if (currentType) {
                            e.stopPropagation();
                            this.style.outline = '2px solid #ff0000';
                        }
                    });
                    
                    el.addEventListener('mouseout', function(e) {
                        if (currentType) {
                            e.stopPropagation();
                            this.style.outline = '';
                        }
                    });
                    
                    el.addEventListener('click', function(e) {
                        if (currentType) {
                            e.preventDefault();
                            e.stopPropagation();
                            
                            var selector = getSelector(this);
                            
                            // Seçiciyi kaydet
                            if (!selectedElements[currentType]) {
                                selectedElements[currentType] = [];
                            }
                            
                            if (!selectedElements[currentType].includes(selector)) {
                                selectedElements[currentType].push(selector);
                                
                                // Seçim bilgisini güncelle
                                var info = document.getElementById('selection-info');
                                info.textContent = currentType + ' için seçilen: ' + selector;
                                
                                // Seçilen elementi vurgula
                                this.style.outline = '2px solid #00ff00';
                                setTimeout(function() {
                                    el.style.outline = '';
                                }, 2000);
                            }
                        }
                    });
                });
            }
            
            addHoverEffect();
        });
        """
        
        # JavaScript kodunu HTML'e ekle
        soup.head.append(script_tag)
        
        # Düzenlenmiş HTML'i geçici dosyaya kaydet
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(str(soup))
            
        self.update_progress("Sayfa önizlemesi hazırlanıyor...")
        
        # WebView penceresini aç
        self.open_webview(temp_file, url)
        
        return True
    
    def open_webview(self, html_file, original_url):
        """WebView penceresini açar."""
        # WebView API'sini tanımla
        class Api:
            def __init__(self, selector_builder):
                self.selector_builder = selector_builder
                
            def save_selectors(self, selectors):
                """JavaScript'ten gelen seçicileri kaydet."""
                self.selector_builder.selectors.update(selectors)
                self.selector_builder.save_selectors_to_json()
                webview.windows[0].evaluate_js("""
                    alert('Seçiciler başarıyla kaydedildi!');
                """)
        
        # WebView penceresini aç
        api = Api(self)
        self.window = webview.create_window(
            title=f"Sayfa Önizleme - {original_url}",
            url=html_file,
            js_api=api,
            width=1200,
            height=800
        )
        webview.start()
    
    def save_selectors_to_json(self, filename=None):
        """Seçicileri JSON dosyasına kaydeder."""
        if not filename:
            filename = f"{self.domain}_selectors.json"
            
        # Seçicileri kaydet
        self.save_to_json(self.selectors, filename)
        self.update_progress(f"Seçiciler {filename} dosyasına kaydedildi.")
        
        # Seçicileri global yapılandırmaya ekle
        from config import SITE_SPECIFIC_SELECTORS
        SITE_SPECIFIC_SELECTORS[self.domain] = self.selectors
        
        # Yapılandırma dosyasını güncelle
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.py")
        with open(config_path, "r", encoding="utf-8") as f:
            config_content = f.read()
            
        # SITE_SPECIFIC_SELECTORS değişkenini güncelle
        import re
        pattern = r"SITE_SPECIFIC_SELECTORS\s*=\s*\{[^}]*\}"
        replacement = f"SITE_SPECIFIC_SELECTORS = {SITE_SPECIFIC_SELECTORS}"
        
        if "SITE_SPECIFIC_SELECTORS" in config_content:
            new_config = re.sub(pattern, replacement, config_content)
        else:
            new_config = config_content + "\n\n# Site özel seçicileri\n" + replacement
            
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(new_config)
    
    def load_selectors_from_json(self, filename=None):
        """JSON dosyasından seçicileri yükler."""
        if not filename and self.domain:
            filename = f"{self.domain}_selectors.json"
            
        data = self.load_from_json(filename)
        if data:
            self.selectors = data
        return self.selectors