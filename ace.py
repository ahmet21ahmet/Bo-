import requests
import re
import sys

# Kaynak M3U dosyasının URL'si
SOURCE_URL = "https://raw.githubusercontent.com/Icastresana/lista1/main/eventos.m3u"

# Çıktı M3U dosyasının adı
OUTPUT_FILE = "processed_list.m3u"

# Kanalların sonuna eklenecek metin
SUFFIX_TEXT = " (telegram: @playtvmedya)"

# Kategori anahtar kelimeleri (Türkçe)
# Daha fazla kategori ve anahtar kelime eklenebilir.
CATEGORIES = {
    "Fútbol": ["Fútbol", "LaLiga", "Premier", "Champions", "UEFA", "Bundesliga", "Ligue 1", "Serie A"],
    "Basketbol": ["Basket", "NBA", "EuroLeague", "Baloncesto", "ACB"],
    "Tenis": ["Tenis", "WTA", "ATP", "Open", "Grand Slam"],
    "Motor": ["F1", "MotoGP", "Formula 1", "NASCAR"],
    "Golf": ["Golf", "PGA Tour"],
}

def get_category(title):
    """Verilen başlığa göre bir kategori adı döndürür."""
    title_lower = title.lower()
    for category, keywords in CATEGORIES.items():
        for keyword in keywords:
            if keyword.lower() in title_lower:
                return category
    return "Diğer"  # Eşleşme bulunamazsa varsayılan kategori

def process_m3u():
    """M3U dosyasını indirir, işler ve yeni dosyayı kaydeder."""
    print(f"M3U dosyası indiriliyor: {SOURCE_URL}")
    try:
        response = requests.get(SOURCE_URL, timeout=10)
        response.raise_for_status()  # HTTP hatası varsa istisna fırlat
        
        # --- GÜNCELLEME 1: Kaynak kodlamayı UTF-8 olarak garanti et ---
        response.encoding = 'utf-8' 

    except requests.exceptions.RequestException as e:
        print(f"Hata: M3U dosyası indirilemedi. {e}", file=sys.stderr)
        return

    lines = response.text.splitlines()
    
    if not lines or not lines[0].startswith("#EXTM3U"):
        print("Hata: Geçerli bir M3U dosyası değil.", file=sys.stderr)
        return

    processed_lines = []
    # İlk satırı (başlık) koru
    processed_lines.append(lines[0].strip())

    # Satırları işle
    for i in range(1, len(lines)):
        line = lines[i].strip()

        if line.startswith("#EXTINF"):
            try:
                # Satırı özellikler ve başlık olarak ayır
                # rsplit(',', 1) kullanarak sondaki virgülü baz al
                parts = line.rsplit(',', 1)
                attributes = parts[0]
                title = parts[1]

                # 1. Başlığa eki ekle
                new_title = title.strip() + SUFFIX_TEXT

                # 2. Kategoriyi belirle
                category = get_category(new_title)

                # 3. 'group-title' özelliğini ekle veya güncelle
                if 'group-title=' in attributes:
                    # Mevcut 'group-title'ı bizim kategoriyle değiştir
                    attributes = re.sub(r'group-title=".*?"', f'group-title="{category}"', attributes)
                else:
                    # 'group-title' yok, #EXTINF:-1'den sonraya ekle
                    attributes = attributes.replace(
                        '#EXTINF:-1', f'#EXTINF:-1 group-title="{category}"'
                    )

                # İşlenmiş satırı listeye ekle
                processed_lines.append(f"{attributes},{new_title}")

            except IndexError:
                # Başlık veya özellik bulunamayan bozuk #EXTINF satırı
                processed_lines.append(line) # Olduğu gibi ekle
            except Exception as e:
                print(f"Satır işlenirken hata (göz ardı ediliyor): {line}\nHata: {e}", file=sys.stderr)
                processed_lines.append(line)

        elif line.startswith("http"):
            # URL satırını olduğu gibi ekle
            processed_lines.append(line)
        
        elif line.startswith("#"):
            # Diğer M3U etiketlerini (örn: #EXTVLCOPT) koru
            processed_lines.append(line)

    # İşlenmiş M3U içeriğini dosyaya yaz
    try:
        # --- GÜNCELLEME 2: Çıktı kodlamasını 'utf-8-sig' (BOM ile UTF-8) yap ---
        with open(OUTPUT_FILE, 'w', encoding='utf-8-sig') as f:
            for line in processed_lines:
                f.write(line + '\n')
        print(f"İşlem tamamlandı. Dosya kaydedildi: {OUTPUT_FILE}")
    except IOError as e:
        print(f"Hata: Dosya yazılamadı. {e}", file=sys.stderr)

if __name__ == "__main__":
    process_m3u()