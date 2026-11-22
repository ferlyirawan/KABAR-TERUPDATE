"""Membaca RSS dari beberapa situs lalu menyimpan hasilnya ke docs/news.json."""
import json, re, time, calendar
from concurrent.futures import ThreadPoolExecutor
import feedparser, requests

# Tambah/ubah sumber di sini. Buka URL RSS di browser dulu untuk memastikan masih aktif.
FEEDS = [
    {"sumber": "Antara",       "kategori": "Politik",   "url": "https://www.antaranews.com/rss/politik.xml"},
    {"sumber": "Antara",       "kategori": "Ekonomi",   "url": "https://www.antaranews.com/rss/ekonomi.xml"},
    {"sumber": "Antara",       "kategori": "Olahraga",  "url": "https://www.antaranews.com/rss/olahraga.xml"},
    {"sumber": "CNN Indonesia", "kategori": "Teknologi", "url": "https://www.cnnindonesia.com/teknologi/rss"},
    {"sumber": "Suara",        "kategori": "Hiburan",   "url": "https://www.suara.com/rss/entertainment"},
]
PER_FEED = 8
MAKS_TOTAL = 80
HEADERS = {"User-Agent": "Mozilla/5.0 (KabarSatuLayar)"}


def gambar_dari_entry(e):
    for key in ("media_content", "media_thumbnail"):
        for m in e.get(key, []) or []:
            if m.get("url"):
                return m["url"]
    for en in e.get("enclosures", []) or []:
        if en.get("type", "").startswith("image") and en.get("href"):
            return en["href"]
    for l in e.get("links", []) or []:
        if l.get("type", "").startswith("image") and l.get("href"):
            return l["href"]
    html = e.get("summary", "") or ""
    for c in e.get("content", []) or []:
        html += c.get("value", "")
    m = re.search(r'<img[^>]+src=["\']([^"\']+)', html)
    return m.group(1) if m else None


def og_image(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', r.text) \
            or re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', r.text)
        return m.group(1) if m else None
    except Exception:
        return None


def ambil_feed(f):
    try:
        r = requests.get(f["url"], headers=HEADERS, timeout=15)
        d = feedparser.parse(r.content)
    except Exception as ex:
        print("GAGAL", f["url"], ex)
        return []
    hasil = []
    for e in d.entries[:PER_FEED]:
        t = e.get("published_parsed") or e.get("updated_parsed")
        hasil.append({
            "judul": e.get("title", "").strip(),
            "link": e.get("link"),
            "sumber": f["sumber"],
            "kategori": f["kategori"],
            "gambar": gambar_dari_entry(e),
            "waktu": calendar.timegm(t) if t else int(time.time()),
        })
    print(f["sumber"], f["kategori"], len(hasil), "berita")
    return hasil


def main():
    with ThreadPoolExecutor(8) as ex:
        semua = [b for hasil in ex.map(ambil_feed, FEEDS) for b in hasil if b["link"]]
    kosong = [b for b in semua if not b["gambar"]]
    with ThreadPoolExecutor(8) as ex:
        for b, img in zip(kosong, ex.map(lambda b: og_image(b["link"]), kosong)):
            b["gambar"] = img
    semua.sort(key=lambda b: b["waktu"], reverse=True)
    if not semua:
        print("Tidak ada berita terambil; news.json tidak diubah.")
        return
    with open("docs/news.json", "w", encoding="utf-8") as f:
        json.dump({"diperbarui": int(time.time()), "berita": semua[:MAKS_TOTAL]}, f, ensure_ascii=False)
    print("Tersimpan:", min(len(semua), MAKS_TOTAL), "berita")


if __name__ == "__main__":
    main()
