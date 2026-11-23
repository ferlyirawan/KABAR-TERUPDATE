"""Membaca RSS dari beberapa situs lalu menyimpan hasilnya ke docs/news.json."""
import json, re, time, calendar
from concurrent.futures import ThreadPoolExecutor
import feedparser, requests

# Tambah/ubah sumber di sini. Buka URL RSS di browser dulu untuk memastikan masih aktif.
FEEDS=
    {"sumber": "Detik",         "kategori": "Berita",    "url": "https://news.detik.com/berita/rss"},
    {"sumber": "Detik",         "kategori": "Ekonomi",   "url": "https://finance.detik.com/rss"},
    {"sumber": "Kontan",        "kategori": "Ekonomi",   "url": "https://rss.kontan.co.id/news/keuangan"},
    {"sumber": "Kontan",        "kategori": "Berita",    "url": "https://rss.kontan.co.id/news/nasional"},
    {"sumber": "Suara",         "kategori": "Berita",    "url": "https://www.suara.com/rss/news"},
    {"sumber": "Suara",         "kategori": "Ekonomi",   "url": "https://www.suara.com/rss/bisnis"},
    {"sumber": "Liputan6",      "kategori": "Berita",    "url": "https://feed.liputan6.com/rss/news"},
    {"sumber": "Tempo",         "kategori": "Berita",    "url": "http://rss.tempo.co/nasional"},
    {"sumber": "Tempo",         "kategori": "Ekonomi",   "url": "http://rss.tempo.co/bisnis"},
    {"sumber": "CNN Indonesia", "kategori": "Berita",    "url": "https://www.cnnindonesia.com/nasional/rss"},
    {"sumber": "CNN Indonesia", "kategori": "Ekonomi",   "url": "https://www.cnnindonesia.com/ekonomi/rss"},
    {"sumber": "CNN Indonesia", "kategori": "Teknologi", "url": "https://www.cnnindonesia.com/teknologi/rss"},
    {"sumber": "CNBC Indonesia","kategori": "Berita",    "url": "https://www.cnbcindonesia.com/news/rss"},
    {"sumber": "CNBC Indonesia","kategori": "Ekonomi",   "url": "https://www.cnbcindonesia.com/market/rss/"},
    {"sumber": "Republika",     "kategori": "Berita",    "url": "https://www.republika.co.id/rss/nasional/"},
    {"sumber": "Republika",     "kategori": "Ekonomi",   "url": "https://www.republika.co.id/rss/ekonomi/"},
    {"sumber": "Media Indonesia","kategori": "Berita",   "url": "https://mediaindonesia.com/feed"},
    {"sumber": "JawaPos",       "kategori": "Berita",    "url": "https://www.jawapos.com/nasional/rss"},
    {"sumber": "JawaPos",       "kategori": "Ekonomi",   "url": "https://www.jawapos.com/ekonomi/rss"},
    {"sumber": "Kumparan",      "kategori": "Berita",    "url": "https://lapi.kumparan.com/v2.0/rss/"},
    {"sumber": "VICE",          "kategori": "Berita",    "url": "https://www.vice.com/id_id/rss"},
    {"sumber": "Coconuts",      "kategori": "Berita",    "url": "http://coconuts.co/jakarta/feed/"},
]
PER_FEED = 8
MAKS_TOTAL = 250
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
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump({"diperbarui": int(time.time()), "berita": semua[:MAKS_TOTAL]}, f, ensure_ascii=False)
    print("Tersimpan:", min(len(semua), MAKS_TOTAL), "berita")


if __name__ == "__main__":
    main()
