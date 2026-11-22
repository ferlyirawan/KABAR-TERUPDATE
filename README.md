# Kabar Satu Layar

Agregator berita gratis di GitHub. Skrip `fetch_news.py` dijalankan GitHub Actions
tiap 30 menit, hasilnya disimpan di `docs/news.json`, dan GitHub Pages
menampilkannya lewat `docs/index.html`.

## Cara memasang
1. Buat repository baru di GitHub (Public), misalnya `kabar-satu-layar`.
2. Upload SEMUA isi folder ini, termasuk folder `.github` dan `docs`.
3. Settings > Pages > Source: "Deploy from a branch", Branch: `main`, folder: `/docs`. Simpan.
4. Tab Actions > "Perbarui berita" > Run workflow (jalan pertama kali manual).
5. Tunggu 1-2 menit, buka `https://USERNAME.github.io/kabar-satu-layar/`.

## Menambah sumber berita
Edit daftar `FEEDS` di `fetch_news.py`, lalu commit.
