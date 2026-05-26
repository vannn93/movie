from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import json
import time
import re
import os

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    return webdriver.Chrome(options=chrome_options)

def extract_year_from_text(text):
    """Extract tahun dari text apapun"""
    match = re.search(r'\b(19[0-9]{2}|20[0-9]{2})\b', str(text))
    return match.group(0) if match else None

def get_movie_info_from_detail_page(imdb_id):
    """Ambil info lengkap dari halaman detail film"""
    url = f"https://www.imdb.com/title/{imdb_id}/"
    driver = None
    
    try:
        driver = get_driver()
        driver.get(url)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Title
        title = "Unknown"
        title_selectors = [
            'h1[data-testid="hero-title-block__title"]',
            'h1',
            'title'
        ]
        for selector in title_selectors:
            elem = soup.select_one(selector)
            if elem:
                title = elem.text.strip().replace(' - IMDb', '')
                if title and title != 'IMDb':
                    break
        
        # Year (PASTI DAPET)
        year = "N/A"
        year_selectors = [
            ('a[href*="releaseinfo"]', 'text'),
            ('span[data-testid="hero-title-block__metadata"] span', 'text'),
            ('div[data-testid="hero-title-block__metadata"] span', 'text'),
            ('span[class*="TitleBlock"] span', 'text'),
            ('ul[data-testid="hero-title-block__metadata"] li', 'text')
        ]
        
        for selector, attr in year_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                extracted = extract_year_from_text(text)
                if extracted:
                    year = extracted
                    break
            if year != "N/A":
                break
        
        if year == "N/A":
            all_text = soup.get_text()
            extracted = extract_year_from_text(all_text)
            if extracted:
                year = extracted
        
        # Rating
        rating = "N/A"
        rating_selectors = [
            'div[data-testid="hero-rating-bar__aggregate-rating"] span',
            'span[class*="Rating"] span'
        ]
        for selector in rating_selectors:
            elem = soup.select_one(selector)
            if elem:
                rating_text = elem.text.strip()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = rating_match.group(0)
                    break
        
        # Description
        description = "No description available"
        desc_selectors = [
            'span[data-testid="plot-xl"]',
            'div[data-testid="plot"] span'
        ]
        for selector in desc_selectors:
            elem = soup.select_one(selector)
            if elem:
                desc_text = elem.text.strip()
                if desc_text and len(desc_text) > 20:
                    description = desc_text
                    break
        
        # Image
        image = ""
        image_elem = soup.select_one('meta[property="og:image"]')
        if image_elem and image_elem.get('content'):
            image = image_elem['content']
        
        return {
            'id': imdb_id,
            'title': title,
            'year': year,
            'rating_imdb': rating,
            'description': description,
            'image': image,
            'url': url
        }, None
        
    except Exception as e:
        return None, str(e)
    finally:
        if driver:
            driver.quit()

def scrape_imdb_top250():
    """Scrape IMDb Top 250 dan tampilkan di terminal"""
    
    print("\n" + "="*80)
    print("🎬 IMDb TOP 250 MOVIES - SCRAPER")
    print("="*80)
    
    driver = None
    all_movies = []
    
    try:
        driver = get_driver()
        print("\n📡 Mengakses IMDb Top 250...")
        driver.get('https://www.imdb.com/chart/top/')
        time.sleep(3)
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        movie_items = soup.select('li.ipc-metadata-list-summary-item')
        
        total_movies = len(movie_items)
        print(f"📋 Menemukan {total_movies} film di Top 250")
        print("-"*80)
        
        for idx, item in enumerate(movie_items[:25], 1):
            print(f"\n[{idx}/25] 🔍 Mengambil data...")
            
            link_elem = item.select_one('a')
            if not link_elem:
                continue
            
            href = link_elem.get('href', '')
            imdb_id_match = re.search(r'tt\d+', href)
            
            if imdb_id_match:
                imdb_id = imdb_id_match.group()
                movie_info, error = get_movie_info_from_detail_page(imdb_id)
                
                if movie_info:
                    print(f"   ✅ {movie_info['title']}")
                    print(f"   📅 Tahun: {movie_info['year']}")
                    print(f"   ⭐ IMDb Rating: {movie_info['rating_imdb']}/10")
                    print(f"   📝 Deskripsi: {movie_info['description'][:100]}..." if len(movie_info['description']) > 100 else f"   📝 Deskripsi: {movie_info['description']}")
                    print(f"   🔗 URL: {movie_info['url']}")
                    all_movies.append(movie_info)
                else:
                    print(f"   ❌ Gagal: {error}")
            
            time.sleep(1)
        
        return all_movies
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return []
    finally:
        if driver:
            driver.quit()

def save_to_json(movies, filename="imdb_top_movies.json"):
    """Simpan data ke file JSON"""
    if not movies:
        print("\n⚠️ Tidak ada data untuk disimpan!")
        return False
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(movies, f, ensure_ascii=False, indent=2)
        
        file_size = os.path.getsize(filename)
        print(f"\n💾 Data berhasil disimpan ke: {filename}")
        print(f"📦 Ukuran file: {file_size} bytes")
        print(f"🎬 Jumlah film: {len(movies)}")
        return True
    except Exception as e:
        print(f"❌ Gagal menyimpan file: {e}")
        return False

def load_from_json(filename="imdb_top_movies.json"):
    """Load data dari file JSON"""
    if not os.path.exists(filename):
        print(f"\n⚠️ File {filename} tidak ditemukan!")
        return None
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            movies = json.load(f)
        print(f"\n✅ Load {len(movies)} film dari {filename}")
        return movies
    except Exception as e:
        print(f"❌ Gagal load file: {e}")
        return None

def display_movies(movies):
    """Tampilkan film di terminal dengan rapi"""
    if not movies:
        print("\n📭 Tidak ada data untuk ditampilkan!")
        return
    
    print("\n" + "="*80)
    print(f"🎬 DAFTAR FILM ({len(movies)} film)")
    print("="*80)
    
    for idx, movie in enumerate(movies, 1):
        print(f"\n{idx}. 🎥 {movie.get('title', 'Unknown')}")
        print(f"   🆔 ID: {movie.get('id', 'N/A')}")
        print(f"   📅 Tahun: {movie.get('year', 'N/A')}")
        print(f"   ⭐ Rating IMDb: {movie.get('rating_imdb', 'N/A')}/10")
        print(f"   📝 Deskripsi: {movie.get('description', '-')[:150]}..." if len(movie.get('description', '')) > 150 else f"   📝 Deskripsi: {movie.get('description', '-')}")
        print(f"   🔗 URL: {movie.get('url', 'N/A')}")
        print("-"*80)

def display_movies_table(movies):
    """Tampilkan film dalam format tabel di terminal"""
    if not movies:
        print("\n📭 Tidak ada data untuk ditampilkan!")
        return
    
    print("\n" + "="*100)
    print(f"{'NO':<4} {'TAHUN':<6} {'JUDUL':<45} {'RATING':<8}")
    print("="*100)
    
    for idx, movie in enumerate(movies, 1):
        year = movie.get('year', 'N/A')
        title = movie.get('title', 'Unknown')[:42]
        rating = movie.get('rating_imdb', 'N/A')
        print(f"{idx:<4} {year:<6} {title:<45} {rating:<8}")
    
    print("="*100)

def main():
    print("\n" + "="*80)
    print("🎬 MOVIE SCRAPER - IMDb Top 250")
    print("="*80)
    
    while True:
        print("\n📌 MENU:")
        print("   1. 🔥 START SCRAPING (Scrape & Tampilkan di Terminal)")
        print("   2. 💾 SCRAPE & SAVE (Scrape & Simpan ke JSON)")
        print("   3. 📂 LOAD JSON (Tampilkan data dari file JSON)")
        print("   4. 📋 TAMPILKAN TABEL (Format tabel di terminal)")
        print("   5. 🚪 Keluar")
        
        choice = input("\n👉 Pilih menu (1-5): ").strip()
        
        if choice == '1':
            movies = scrape_imdb_top250()
            if movies:
                display_movies(movies)
            else:
                print("\n❌ Gagal scraping data!")
                
        elif choice == '2':
            movies = scrape_imdb_top250()
            if movies:
                save_to_json(movies)
                print("\n✅ Scraping dan penyimpanan selesai!")
            else:
                print("\n❌ Gagal scraping data!")
                
        elif choice == '3':
            filename = input("📁 Nama file JSON (default: imdb_top_movies.json): ").strip()
            if not filename:
                filename = "imdb_top_movies.json"
            
            movies = load_from_json(filename)
            if movies:
                display_movies(movies)
                
        elif choice == '4':
            filename = input("📁 Nama file JSON (default: imdb_top_movies.json): ").strip()
            if not filename:
                filename = "imdb_top_movies.json"
            
            movies = load_from_json(filename)
            if movies:
                display_movies_table(movies)
                
        elif choice == '5':
            print("\n👋 Sampai jumpa!")
            break
            
        else:
            print("\n❌ Pilihan tidak valid!")

if __name__ == '__main__':
    main()