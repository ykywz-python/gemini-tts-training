# gemini-2.5-flash-preview-tts
implementasi penggunakan model gemini-2.5-flash-preview-tts, model ini digunakan untuk membuat tulisan menjadi suara, atau istilah inggrisnya text to speech

## Penjelajahan
- basic, cara penggunaan biasa
- rotation, merotasi api key
- chunk, memisah kata
- main, mengoptimalkan limitasi rpd (request per day), perbaikan chunk menjadi jumlah kata, penambahan delay menghindari rpm (request per minute), menggabungkan audio ketika terjadi chunking

## Penggunaan
- install uv `powershell -c "irm https://astral.sh/uv/install.ps1 | more"`
- jalankan uv: `uv sync`
- buat file: api-keys.txt
- taruh api keynya didalam api-keys.txt, pisah dengan baris baru untuk merotasinya [dapatkan api key disini](https://aistudio.google.com/app/api-keys)
- taruh `ffmpeg.exe` kedalam folder pastikan sejajar dengan file `main.py`
- jalankan program: `uv run main.py`


## 📊 Limitasi API Key Gratis

| Satuan Limitasi | Singkatan | Batas (Free Tier) | Deskripsi |
| :--- | :--- | :--- | :--- |
| **Requests Per Minute** | RPM | 3 | Jumlah maksimum permintaan (panggilan API) yang dapat Anda lakukan per menit. |
| **Tokens Per Minute** | TPM | 10.000 | Jumlah maksimum token teks input yang dapat Anda kirim per menit. |
| **Requests Per Day** | RPD | 15 | Jumlah maksimum permintaan (panggilan API) yang dapat Anda lakukan dalam satu hari (24 jam). |

## Model yang tersedia
[lihat daftar lengkap model](https://ai.google.dev/gemini-api/docs/speech-generation?hl=id#voices)

```
voices = [
    # Suara dari daftar Anda sebelumnya
    {'name': 'Zephyr', 'style': 'Wanita - Jelas & Bersemangat (Iklan, E-Learning)'},
    {'name': 'Puck', 'style': 'Pria - Ceria & Riang (Dongeng Anak, Vlog)'},
    {'name': 'Charon', 'style': 'Pria - Berwibawa & Informatif (Berita, Dokumenter)'},
    {'name': 'Kore', 'style': 'Wanita - Tegas & Profesional (Presentasi, Pengumuman)'},
    {'name': 'Fenrir', 'style': 'Pria - Penuh Semangat (Iklan Enerjik, Video Hype)'},
    {'name': 'Leda', 'style': 'Wanita - Muda & Enerjik (Podcast Remaja, Iklan)'},
    {'name': 'Orus', 'style': 'Pria - Tegas & Dalam (Narasi Dramatis, Trailer Film)'},
    {'name': 'Aoede', 'style': 'Wanita - Ringan & Ramah (Podcast Kasual, Narasi Santai)'},
    
    # Kategori Wanita/Female:
    {'name': 'Callirrhoe', 'style': 'Wanita - Santai & Mengalir (Narasi E-book, Panduan)'},
    {'name': 'Autonoe', 'style': 'Wanita - Cerdas & Jelas (Konten Edukasi, Tutorial)'},
    {'name': 'Despina', 'style': 'Wanita - Halus & Menenangkan (Layanan Pelanggan, Meditasi)'},
    {'name': 'Erinome', 'style': 'Wanita - Jernih & Terstruktur (Presentasi Teknis, Berita)'},
    {'name': 'Gacrux', 'style': 'Wanita - Dewasa & Berwibawa (Pengumuman Resmi, Dokumenter)'},
    {'name': 'Laomedeia', 'style': 'Wanita - Penuh Semangat & Cepat (Review Produk, Podcast)'},
    {'name': 'Pulcherrima', 'style': 'Wanita - Antusias & Menonjol (Iklan, Konten Populer)'},
    {'name': 'Achernar', 'style': 'Wanita - Lembut & Tenang (Asisten Pribadi, Suara Latar)'},
    {'name': 'Schedar', 'style': 'Wanita - Netral & Stabil (Narasi Umum, Instruksi)'},
    {'name': 'Sulafat', 'style': 'Wanita - Hangat & Meyakinkan (Konsultasi, Penjualan)'},
    {'name': 'Vindemiatrix', 'style': 'Wanita - Lemah Lembut & Anggun (Narasi Fiksi, Iklan Mewah)'},
    
    # Kategori Pria/Male:
    {'name': 'Enceladus', 'style': 'Pria - Bergetar & Emosional (Narasi Dramatis, Podcast Karakter)'},
    {'name': 'Iapetus', 'style': 'Pria - Jernih & Lugas (Instruksi Teknis, Berita Bisnis)'},
    {'name': 'Umbriel', 'style': 'Pria - Mudah Diterima & Kasual (Vlog, Panduan Santai)'},
    {'name': 'Algieba', 'style': 'Pria - Halus & Berkarisma (Narasi Film, Audio Drama)'},
    {'name': 'Algenib', 'style': 'Pria - Berat & Bertekstur (Trailer, Suara Karakter)'},
    {'name': 'Rasalgethi', 'style': 'Pria - Menginformasikan & Berstruktur (Laporan, Berita Formal)'},
    {'name': 'Achird', 'style': 'Pria - Ramah & Bersahabat (Sapaan, Pesan Otomatis)'},
    {'name': 'Alnilam', 'style': 'Pria - Tegas & Mendalam (Pidato, Komentar Olahraga)'},
    {'name': 'Zubenelgenubi', 'style': 'Pria - Santai & Tidak Formal (Obrolan, Narasi Ringan)'},
    {'name': 'Sadachbia', 'style': 'Pria - Penuh Semangat & Energik (Iklan, Promosi)'},
    {'name': 'Sadaltager', 'style': 'Pria - Berpengetahuan & Otoritatif (Lektor, Kursus Online)'},
]
```

## 🎙️ Suara Wanita (Female Voices) 👩

| Name | Style |
| :--- | :--- |
| Zephyr | Jelas & Bersemangat (Iklan, E-Learning) |
| Kore | Tegas & Profesional (Presentasi, Pengumuman) |
| Leda | Muda & Enerjik (Podcast Remaja, Iklan) |
| Aoede | Ringan & Ramah (Podcast Kasual, Narasi Santai) |
| Callirrhoe | Santai & Mengalir (Narasi E-book, Panduan) |
| Autonoe | Cerdas & Jelas (Konten Edukasi, Tutorial) |
| Despina | Halus & Menenangkan (Layanan Pelanggan, Meditasi) |
| Erinome | Jernih & Terstruktur (Presentasi Teknis, Berita) |
| Gacrux | Dewasa & Berwibawa (Pengumuman Resmi, Dokumenter) |
| Laomedeia | Penuh Semangat & Cepat (Review Produk, Podcast) |
| Pulcherrima | Antusias & Menonjol (Iklan, Konten Populer) |
| Achernar | Lembut & Tenang (Asisten Pribadi, Suara Latar) |
| Schedar | Netral & Stabil (Narasi Umum, Instruksi) |
| Sulafat | Hangat & Meyakinkan (Konsultasi, Penjualan) |
| Vindemiatrix | Lemah Lembut & Anggun (Narasi Fiksi, Iklan Mewah) |

---

## 🎙️ Suara Pria (Male Voices) 👨

| Name | Style |
| :--- | :--- |
| Puck | Ceria & Riang (Dongeng Anak, Vlog) |
| Charon | Berwibawa & Informatif (Berita, Dokumenter) |
| Fenrir | Penuh Semangat (Iklan Enerjik, Video Hype) |
| Orus | Tegas & Dalam (Narasi Dramatis, Trailer Film) |
| Enceladus | Bergetar & Emosional (Narasi Dramatis, Podcast Karakter) |
| Iapetus | Jernih & Lugas (Instruksi Teknis, Berita Bisnis) |
| Umbriel | Mudah Diterima & Kasual (Vlog, Panduan Santai) |
| Algieba | Halus & Berkarisma (Narasi Film, Audio Drama) |
| Algenib | Berat & Bertekstur (Trailer, Suara Karakter) |
| Rasalgethi | Menginformasikan & Berstruktur (Laporan, Berita Formal) |
| Achird | Ramah & Bersahabat (Sapaan, Pesan Otomatis) |
| Alnilam | Tegas & Mendalam (Pidato, Komentar Olahraga) |
| Zubenelgenubi | Santai & Tidak Formal (Obrolan, Narasi Ringan) |
| Sadachbia | Penuh Semangat & Energik (Iklan, Promosi) |
| Sadaltager | Berpengetahuan & Otoritatif (Lektor, Kursus Online) |

# 🎤 FORMAT UMUM MENGONTROL GAYA UCAPAN (SPEECH STYLE)

Anda dapat memulai chunk teks Anda dengan tag di bawah ini. Pastikan untuk menjaga konsistensi format.

Say in a `<style-modifier> <emotion-or-tone> <speech-rate> <pitch-modifier> <volume-modifier>`:
"Teks yang ingin diucapkan dengan gaya tersebut"

---

## CONTOH PENGGUNAAN PADA CHUNK TEKS

# 1. Rap Cepat dan Energik
Say with a fast, energetic rap style:
"Lihat, ini ritme, dari nol kini kita naik level.
Kode bersinar terang, Gemini Flash kini jadi bekal."

# 2. Narasi Misterius dan Berbisik
Say in a hushed, mysterious tone:
"Di sebuah kota tua yang diselimuti kabut, tinggallah seorang penjaga mercusuar bernama Elara."

# 3. Teriakan Panik (Gaya Vokal Dramatis)
Say with a loud, desperate yell:
"Siapa di sana? teriak Elara, suaranya terdengar kecil dan putus asa di tengah hiruk pikuk badai."

# 4. Suara Dingin dan Ethereal
Say with a cold, ethereal whisper:
"Pulang," bisik anak itu. "Mereka sedang menunggu."

---

## CATATAN PENTING

* Model TTS akan berusaha mencocokkan gaya yang Anda berikan.
* Anda dapat menggunakan tag gaya **di awal setiap chunk** untuk memastikan gaya tetap konsisten, terutama setelah pemecahan otomatis berdasarkan batas karakter.