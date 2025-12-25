import customtkinter as ctk
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse, unquote
import os
import re
import time
import threading
from pathlib import Path
import mimetypes
from collections import deque

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class WebsiteSourceGetter(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Website Source Getter")
        self.geometry("1200x950")
        self.minsize(1000, 700)
        
        # Variables
        self.url_var = ctk.StringVar()
        self.status_var = ctk.StringVar(value="Checking dependencies...")
        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_text_var = ctk.StringVar(value="")
        self.is_scraping = False
        self.visited_urls = set()
        self.chrome_available = False
        
        self.setup_ui()
        
        # Run startup check slightly after UI loads so the window appears first
        self.after(200, self.run_startup_checks)
        
    def run_startup_checks(self):
        """Runs the Chrome check in a thread to keep UI responsive"""
        self.log("System: Checking Chrome Driver availability... Please wait.")
        threading.Thread(target=self.check_chrome_availability, daemon=True).start()

    def check_chrome_availability(self):
        """Check if Chrome is available"""
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            # Suppress logs for the check
            options.add_experimental_option('excludeSwitches', ['enable-logging'])
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.quit()
            
            self.chrome_available = True
            self.after(0, lambda: self.update_chrome_status(True))
        except Exception as e:
            self.chrome_available = False
            self.after(0, lambda: self.update_chrome_status(False))

    def update_chrome_status(self, available):
        if available:
            self.use_selenium.configure(state="normal")
            self.use_selenium.select()
            self.chrome_status_label.configure(text="Chrome detected", text_color="#10b981")
            self.update_status("Ready")
        else:
            self.use_selenium.configure(state="disabled")
            self.chrome_status_label.configure(text="Chrome not installed", text_color="#ef4444")
            self.update_status("Ready (Requests mode only)")
        
    def setup_ui(self):
        # Main container with padding
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Header
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", pady=(0, 25))
        
        title = ctk.CTkLabel(
            header,
            text="Website Source Getter",
            font=("Segoe UI", 36, "bold")
        )
        title.pack()
        
        subtitle = ctk.CTkLabel(
            header,
            text="Made by Crypted, dont skid.",
            font=("Segoe UI", 13),
            text_color=("#666666", "#999999")
        )
        subtitle.pack(pady=(5, 0))
        
        # URL Input Card
        url_card = ctk.CTkFrame(main, fg_color=("#f8f9fa", "#1a1a1a"), corner_radius=12)
        url_card.pack(fill="x", pady=(0, 15))
        
        url_inner = ctk.CTkFrame(url_card, fg_color="transparent")
        url_inner.pack(fill="x", padx=25, pady=20)
        
        ctk.CTkLabel(
            url_inner,
            text="Target URL",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        url_entry = ctk.CTkEntry(
            url_inner,
            textvariable=self.url_var,
            placeholder_text="https://example.com",
            height=50,
            font=("Segoe UI", 14),
            border_width=2,
            corner_radius=10
        )
        url_entry.pack(fill="x")
        
        # Two-column layout
        columns = ctk.CTkFrame(main, fg_color="transparent")
        columns.pack(fill="both", expand=True)
        
        # Left column - Options
        left = ctk.CTkFrame(columns, fg_color=("#f8f9fa", "#1a1a1a"), corner_radius=12)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        
        left_inner = ctk.CTkFrame(left, fg_color="transparent")
        left_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        ctk.CTkLabel(
            left_inner,
            text="Download Options",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 15))
        
        # Crawl settings
        crawl_frame = ctk.CTkFrame(left_inner, fg_color="transparent")
        crawl_frame.pack(fill="x", pady=(0, 15))
        
        self.crawl_subpages = ctk.CTkSwitch(
            crawl_frame,
            text="Crawl multiple pages",
            font=("Segoe UI", 12),
            switch_width=50,
            switch_height=25
        )
        self.crawl_subpages.pack(anchor="w", pady=5)
        self.crawl_subpages.select()
        
        self.organize_netlify = ctk.CTkSwitch(
            crawl_frame,
            text="Organize for Netlify",
            font=("Segoe UI", 12),
            switch_width=50,
            switch_height=25
        )
        self.organize_netlify.pack(anchor="w", pady=5)
        self.organize_netlify.select()

        # Max pages
        pages_frame = ctk.CTkFrame(left_inner, fg_color="transparent")
        pages_frame.pack(fill="x", pady=(0, 20))
        
        self.max_pages_var = ctk.IntVar(value=10)
        pages_label = ctk.CTkLabel(
            pages_frame,
            text=f"Max pages: {self.max_pages_var.get()}",
            font=("Segoe UI", 11),
            text_color=("#666666", "#999999")
        )
        pages_label.pack(anchor="w", pady=(0, 5))
        
        def update_pages_label(value):
            pages_label.configure(text=f"Max pages: {int(float(value))}")
        
        ctk.CTkSlider(
            pages_frame,
            from_=1,
            to=50,
            number_of_steps=49,
            variable=self.max_pages_var,
            command=update_pages_label,
            height=18
        ).pack(fill="x")
        
        # Resource checkboxes
        resources_label = ctk.CTkLabel(
            left_inner,
            text="Resources",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        )
        resources_label.pack(fill="x", pady=(0, 10))
        
        self.download_images = ctk.CTkCheckBox(left_inner, text="Images", font=("Segoe UI", 12))
        self.download_images.pack(anchor="w", pady=4)
        self.download_images.select()
        
        self.download_videos = ctk.CTkCheckBox(left_inner, text="Videos", font=("Segoe UI", 12))
        self.download_videos.pack(anchor="w", pady=4)
        self.download_videos.select()
        
        self.download_audio = ctk.CTkCheckBox(left_inner, text="Audio", font=("Segoe UI", 12))
        self.download_audio.pack(anchor="w", pady=4)
        self.download_audio.select()
        
        self.download_css = ctk.CTkCheckBox(left_inner, text="CSS Stylesheets", font=("Segoe UI", 12))
        self.download_css.pack(anchor="w", pady=4)
        self.download_css.select()
        
        self.download_js = ctk.CTkCheckBox(left_inner, text="JavaScript", font=("Segoe UI", 12))
        self.download_js.pack(anchor="w", pady=4)
        self.download_js.select()
        
        self.download_fonts = ctk.CTkCheckBox(left_inner, text="Web Fonts", font=("Segoe UI", 12))
        self.download_fonts.pack(anchor="w", pady=4)
        self.download_fonts.select()
        
        # Selenium option with status
        selenium_frame = ctk.CTkFrame(left_inner, fg_color="transparent")
        selenium_frame.pack(fill="x", pady=(15, 0))
        
        ctk.CTkLabel(
            selenium_frame,
            text="Advanced",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        self.use_selenium = ctk.CTkCheckBox(
            selenium_frame,
            text="Use Selenium (Cloudflare bypass)",
            font=("Segoe UI", 12),
            state="disabled"
        )
        self.use_selenium.pack(anchor="w", pady=4)
        
        # Status Label placeholder (updated by startup check)
        self.chrome_status_label = ctk.CTkLabel(
            selenium_frame,
            text="Checking dependencies...",
            font=("Segoe UI", 10),
            text_color="#eab308" # Yellow warning color initially
        )
        self.chrome_status_label.pack(anchor="w", padx=(30, 0))
        
        # Right column - Progress & Log
        right = ctk.CTkFrame(columns, fg_color=("#f8f9fa", "#1a1a1a"), corner_radius=12)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))
        
        right_inner = ctk.CTkFrame(right, fg_color="transparent")
        right_inner.pack(fill="both", expand=True, padx=25, pady=20)
        
        # Progress section
        progress_header = ctk.CTkFrame(right_inner, fg_color="transparent")
        progress_header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            progress_header,
            text="Progress",
            font=("Segoe UI", 14, "bold"),
            anchor="w"
        ).pack(side="left")
        
        self.progress_label = ctk.CTkLabel(
            progress_header,
            textvariable=self.progress_text_var,
            font=("Segoe UI", 11),
            text_color=("#666666", "#999999"),
            anchor="e"
        )
        self.progress_label.pack(side="right")
        
        self.progress_bar = ctk.CTkProgressBar(
            right_inner,
            variable=self.progress_var,
            height=12,
            corner_radius=6
        )
        self.progress_bar.pack(fill="x", pady=(0, 10))
        
        self.status_label = ctk.CTkLabel(
            right_inner,
            textvariable=self.status_var,
            font=("Segoe UI", 12),
            anchor="w",
            wraplength=450
        )
        self.status_label.pack(fill="x", pady=(0, 15))
        
        # Activity log
        ctk.CTkLabel(
            right_inner,
            text="Activity Log",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))
        
        self.log_text = ctk.CTkTextbox(
            right_inner,
            font=("Consolas", 10),
            corner_radius=8,
            wrap="word"
        )
        self.log_text.pack(fill="both", expand=True)
        
        # Action buttons
        button_frame = ctk.CTkFrame(main, fg_color="transparent")
        button_frame.pack(fill="x", pady=(15, 0))
        
        self.scrape_btn = ctk.CTkButton(
            button_frame,
            text="Start Scraping",
            command=self.start_scraping,
            height=50,
            font=("Segoe UI", 15, "bold"),
            fg_color=("#10b981", "#059669"),
            hover_color=("#059669", "#047857"),
            corner_radius=10
        )
        self.scrape_btn.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="Stop",
            command=self.stop_scraping,
            height=50,
            font=("Segoe UI", 15, "bold"),
            fg_color=("#6b7280", "#4b5563"),
            hover_color=("#4b5563", "#374151"),
            corner_radius=10,
            state="disabled"
        )
        self.stop_btn.pack(side="left", fill="x", expand=True)

        # Footer / Credits
        footer_frame = ctk.CTkFrame(main, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0))
        
        credits_label = ctk.CTkLabel(
            footer_frame,
            text="made by crypted",
            font=("Segoe UI", 10),
            text_color=("#666666", "#888888")
        )
        credits_label.pack(side="right")
        
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        try:
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
        except:
            safe_msg = message.encode('ascii', 'ignore').decode('ascii')
            self.log_text.insert("end", f"[{timestamp}] {safe_msg}\n")
        self.log_text.see("end")
        
    def update_status(self, message, progress_text=""):
        try:
            self.status_var.set(message)
            if progress_text:
                self.progress_text_var.set(progress_text)
            self.log(message)
        except:
            safe_msg = message.encode('ascii', 'ignore').decode('ascii')
            self.status_var.set(safe_msg)
            self.log(safe_msg)
        
    def start_scraping(self):
        url = self.url_var.get().strip()
        if not url:
            self.update_status("Please enter a URL")
            return
            
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
        
        self.is_scraping = True
        self.visited_urls.clear()
        self.scrape_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal", fg_color=("#ef4444", "#dc2626"), hover_color=("#dc2626", "#b91c1c"))
        self.progress_var.set(0)
        self.progress_text_var.set("0%")
        self.log_text.delete("1.0", "end")
        
        thread = threading.Thread(target=self.scrape_website, args=(url,), daemon=True)
        thread.start()
        
    def stop_scraping(self):
        self.is_scraping = False
        self.update_status("Stopped by user")
        self.scrape_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled", fg_color=("#6b7280", "#4b5563"), hover_color=("#4b5563", "#374151"))
        
    def check_url_validity(self, url):
        """Check if URL is accessible before scraping"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            # Try HEAD first (faster)
            response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                return True
            
            # HEAD failed, try GET (some sites block HEAD requests)
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            return response.status_code < 400
        except:
            # If both fail, still return True to let the main scraper try
            # Better to attempt and fail than to skip valid pages
            return True
        
    def scrape_website(self, start_url):
        try:
            self.update_status(f"Initializing crawl: {start_url}")
            
            # Setup directories
            domain = urlparse(start_url).netloc.replace('www.', '')
            base_domain = '.'.join(domain.split('.')[-2:]) if domain.count('.') > 0 else domain
            output_dir = Path(f"scraped_{domain.replace('.', '_')}_{int(time.time())}")
            output_dir.mkdir(exist_ok=True)
            
            # Create structure
            (output_dir / "assets").mkdir(exist_ok=True)
            (output_dir / "assets" / "images").mkdir(exist_ok=True)
            (output_dir / "assets" / "videos").mkdir(exist_ok=True)
            (output_dir / "assets" / "audio").mkdir(exist_ok=True)
            (output_dir / "assets" / "css").mkdir(exist_ok=True)
            (output_dir / "assets" / "js").mkdir(exist_ok=True)
            (output_dir / "assets" / "fonts").mkdir(exist_ok=True)
            (output_dir / "pages").mkdir(exist_ok=True)
            
            downloaded_files = {} # Key: Original URL, Value: Path relative to ROOT (scraped_folder/)
            pages_to_visit = deque([start_url])
            pages_crawled = 0
            max_pages = self.max_pages_var.get() if self.crawl_subpages.get() else 1
            
            while pages_to_visit and pages_crawled < max_pages and self.is_scraping:
                current_url = pages_to_visit.popleft()
                
                if current_url in self.visited_urls:
                    continue
                
                if not self.check_url_validity(current_url):
                    self.log(f"Skipped (404 or unreachable): {current_url}")
                    continue
                
                self.visited_urls.add(current_url)
                pages_crawled += 1
                
                progress_pct = int((pages_crawled / max_pages) * 100)
                self.update_status(
                    f"Crawling: {current_url}",
                    f"{progress_pct}% ({pages_crawled}/{max_pages})"
                )
                self.progress_var.set(pages_crawled / max_pages)
                
                # Get page efficiently
                html = None
                if self.use_selenium.get() and self.chrome_available:
                    html = self.get_with_selenium(current_url)
                else:
                    html = self.get_with_requests(current_url)
                
                if not html:
                    self.log(f"Failed to fetch: {current_url}")
                    continue
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find more pages to crawl
                if self.crawl_subpages.get() and pages_crawled < max_pages:
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        
                        if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                            continue
                        
                        full_url = urljoin(current_url, href)
                        parsed = urlparse(full_url)
                        
                        if base_domain in parsed.netloc and full_url not in self.visited_urls:
                            skip_subdomains = ['dash', 'admin', 'api', 'reseller', 'portal', 'account', 'auth']
                            subdomain = parsed.netloc.split('.')[0] if parsed.netloc.count('.') > 1 else ''
                            
                            if subdomain.lower() in skip_subdomains:
                                continue
                            
                            if not any(ext in full_url.lower() for ext in ['.pdf', '.zip', '.jpg', '.png', '.gif']):
                                pages_to_visit.append(full_url)
                
                # Download resources (Note: Logic works recursively now because we pass downloaded_files)
                if self.download_images.get():
                    self.download_resources(soup, current_url, 'img', 'src', output_dir / "assets" / "images", downloaded_files)
                    self.download_resources(soup, current_url, 'img', 'data-src', output_dir / "assets" / "images", downloaded_files)
                
                if self.download_videos.get():
                    self.download_media(soup, current_url, ['video', 'source'], ['src', 'data-src'], output_dir / "assets" / "videos", downloaded_files, ['.mp4', '.webm', '.ogg', '.mov'])
                
                if self.download_audio.get():
                    self.download_media(soup, current_url, ['audio', 'source'], ['src'], output_dir / "assets" / "audio", downloaded_files, ['.mp3', '.wav', '.ogg', '.m4a'])
                
                if self.download_css.get():
                    self.download_resources(soup, current_url, 'link', 'href', output_dir / "assets" / "css", downloaded_files, rel='stylesheet')
                
                if self.download_js.get():
                    self.download_resources(soup, current_url, 'script', 'src', output_dir / "assets" / "js", downloaded_files)
                
                if self.download_fonts.get():
                    self.download_fonts_from_css(soup, current_url, output_dir / "assets" / "fonts", downloaded_files)
                
                # DETERMINE FILE SAVE LOCATION
                if current_url == start_url:
                    filename = "index.html"
                    file_subdir = "." # Root
                else:
                    path = urlparse(current_url).path.strip('/')
                    filename = f"pages/{path.replace('/', '_')}.html" if path else f"pages/page_{pages_crawled}.html"
                    file_subdir = "pages" # Inside pages folder
                
                # UPDATE HTML PATHS WITH RELATIVE CHECK
                html_updated = self.update_html_paths(str(soup), downloaded_files, current_url, file_subdir)
                
                filepath = output_dir / filename
                filepath.parent.mkdir(exist_ok=True, parents=True)
                
                with open(filepath, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(html_updated)
                
                self.log(f"Saved: {filename}")
            
            if self.organize_netlify.get():
                self.create_netlify_config(output_dir)
                self.log(f"Generated Netlify configuration")
            
            self.progress_var.set(1.0)
            self.progress_text_var.set("100%")
            self.update_status(f"Complete! Scraped {pages_crawled} pages -> {output_dir.absolute()}")
            
            # Auto-open folder in Windows Explorer
            try:
                import subprocess
                subprocess.Popen(f'explorer "{output_dir.absolute()}"')
                self.log(f"Opened output folder")
            except Exception as e:
                self.log(f"Could not auto-open folder: {e}")
            
        except Exception as e:
            error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            self.update_status(f"Error: {error_msg}")
            # print error for debugging
            print(f"DEBUG ERROR: {e}")
        finally:
            self.scrape_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled", fg_color=("#6b7280", "#4b5563"), hover_color=("#4b5563", "#374151"))
            self.is_scraping = False
    
    def get_with_selenium(self, url):
        try:
            options = Options()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            driver.get(url)
            time.sleep(2)
            
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, 0);")
            
            html = driver.page_source
            driver.quit()
            return html
        except Exception as e:
            return None
    
    def get_with_requests(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            return None
    
    def download_resources(self, soup, base_url, tag, attr, output_dir, downloaded_files, **kwargs):
        elements = soup.find_all(tag, **kwargs)
        
        for idx, element in enumerate(elements):
            if not self.is_scraping:
                break
            
            resource_url = element.get(attr)
            if not resource_url or resource_url.startswith('data:'):
                continue
            
            try:
                full_url = urljoin(base_url, resource_url)
                
                # If already downloaded, just ensure mapping is there
                if full_url in downloaded_files:
                    continue

                parsed = urlparse(full_url)
                filename = os.path.basename(unquote(parsed.path))
                
                if not filename or '.' not in filename:
                    ext = mimetypes.guess_extension(element.get('type', '')) or '.bin'
                    filename = f"resource_{abs(hash(full_url))}{ext}"
                
                filename = re.sub(r'[^\w\.-]', '_', filename)
                filepath = output_dir / filename
                
                if not filepath.exists():
                    response = requests.get(full_url, timeout=15)
                    response.raise_for_status()
                    
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    size_kb = len(response.content) // 1024
                    self.log(f"Downloaded: {filename} ({size_kb}KB)")
                
                # IMPORTANT: Store path relative to the ROOT scraped folder
                # e.g. assets/css/style.css
                rel_path_from_root = str(filepath.relative_to(filepath.parents[2]))
                downloaded_files[full_url] = rel_path_from_root
                downloaded_files[resource_url] = rel_path_from_root # Store original relative URL too
                
            except Exception as e:
                pass
    
    def download_media(self, soup, base_url, tags, attrs, output_dir, downloaded_files, extensions):
        for tag in tags:
            for attr in attrs:
                self.download_resources(soup, base_url, tag, attr, output_dir, downloaded_files)
    
    def download_fonts_from_css(self, soup, base_url, output_dir, downloaded_files):
        css_links = soup.find_all('link', rel='stylesheet')
        for link in css_links:
            href = link.get('href')
            if href:
                try:
                    css_url = urljoin(base_url, href)
                    response = requests.get(css_url, timeout=10)
                    css_content = response.text
                    
                    font_urls = re.findall(r'url\(["\']?([^"\'()]+\.(woff2?|ttf|otf|eot))["\']?\)', css_content)
                    for font_url, ext in font_urls:
                        if not self.is_scraping:
                            break
                        try:
                            full_font_url = urljoin(css_url, font_url)
                            
                            if full_font_url in downloaded_files:
                                continue

                            filename = os.path.basename(unquote(font_url))
                            filename = re.sub(r'[^\w\.-]', '_', filename)
                            filepath = output_dir / filename
                            
                            if not filepath.exists():
                                font_response = requests.get(full_font_url, timeout=10)
                                font_response.raise_for_status()
                                
                                with open(filepath, 'wb') as f:
                                    f.write(font_response.content)
                                self.log(f"Downloaded font: {filename}")
                            
                            rel_path_from_root = str(filepath.relative_to(filepath.parents[2]))
                            downloaded_files[full_font_url] = rel_path_from_root
                            downloaded_files[font_url] = rel_path_from_root
                        except:
                            pass
                except:
                    pass
    
    def update_html_paths(self, html, downloaded_files, base_url, html_subdir="."):
        """
        Intelligently updates paths based on where the HTML file is located.
        html_subdir: The directory the HTML file is in, relative to the root scraped folder.
                     e.g., "." for index.html, "pages" for subpages.
        """
        # Sort by length descending to prevent partial replacements
        sorted_urls = sorted(downloaded_files.keys(), key=len, reverse=True)
        
        for original_url in sorted_urls:
            root_relative_path = downloaded_files[original_url]
            
            if html_subdir == ".":
                final_path = root_relative_path.replace("\\", "/")
            else:
                # File is in pages/, asset is at assets/...
                # We need ../assets/...
                final_path = "../" + root_relative_path.replace("\\", "/")
            
            # Replace strictly
            html = html.replace(f'"{original_url}"', f'"{final_path}"')
            html = html.replace(f"'{original_url}'", f"'{final_path}'")
            
            # Handle absolute URLs that might have been constructed
            if not original_url.startswith(('http://', 'https://', '//')):
                full_url = urljoin(base_url, original_url)
                html = html.replace(f'"{full_url}"', f'"{final_path}"')
                html = html.replace(f"'{full_url}'", f"'{final_path}'")
        
        # NUCLEAR OPTION: For pages in subfolders, aggressively rewrite ALL resource paths
        if html_subdir != ".":
            # Fix assets/ references
            html = re.sub(r'(href|src|content|data-src|data-href)=(["\'])assets/', r'\1=\2../assets/', html, flags=re.IGNORECASE)
            html = re.sub(r'url\((["\']?)assets/', r'url(\1../assets/', html, flags=re.IGNORECASE)
            
            # Fix absolute paths like /css/, /js/, /images/ etc
            # Map common absolute paths to our assets structure
            html = re.sub(r'(href|src|content|data-src)=(["\'])/css/', r'\1=\2../assets/css/', html, flags=re.IGNORECASE)
            html = re.sub(r'(href|src|content|data-src)=(["\'])/js/', r'\1=\2../assets/js/', html, flags=re.IGNORECASE)
            html = re.sub(r'(href|src|content|data-src)=(["\'])/javascript/', r'\1=\2../assets/js/', html, flags=re.IGNORECASE)
            html = re.sub(r'(href|src|content|data-src)=(["\'])/images?/', r'\1=\2../assets/images/', html, flags=re.IGNORECASE)
            html = re.sub(r'(href|src|content|data-src)=(["\'])/img/', r'\1=\2../assets/images/', html, flags=re.IGNORECASE)
            html = re.sub(r'(href|src|content|data-src)=(["\'])/fonts?/', r'\1=\2../assets/fonts/', html, flags=re.IGNORECASE)
            html = re.sub(r'(href|src|content|data-src)=(["\'])/videos?/', r'\1=\2../assets/videos/', html, flags=re.IGNORECASE)
            html = re.sub(r'(href|src|content|data-src)=(["\'])/audio/', r'\1=\2../assets/audio/', html, flags=re.IGNORECASE)
            html = re.sub(r'(href|src|content|data-src)=(["\'])/media/', r'\1=\2../assets/images/', html, flags=re.IGNORECASE)
            
            # Fix CSS url() with absolute paths
            html = re.sub(r'url\((["\']?)/css/', r'url(\1../assets/css/', html, flags=re.IGNORECASE)
            html = re.sub(r'url\((["\']?)/images?/', r'url(\1../assets/images/', html, flags=re.IGNORECASE)
            html = re.sub(r'url\((["\']?)/fonts?/', r'url(\1../assets/fonts/', html, flags=re.IGNORECASE)
        
        # Clean up <base> tags which might break relative links
        html = re.sub(r'<base[^>]*>', '', html, flags=re.IGNORECASE)
        
        return html
    
    def create_netlify_config(self, output_dir):
        config = """[build]
  publish = "."
  
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
"""
        with open(output_dir / "netlify.toml", 'w', encoding='utf-8') as f:
            f.write(config)

if __name__ == "__main__":
    app = WebsiteSourceGetter()
    app.mainloop()