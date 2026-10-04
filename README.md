# CRUD Item - Panduan Menjalankan di Laptop

## Deskripsi
Program CRUD Item dengan harga pokok dan harga jual. Python + Flask + SQLite + HTML.

## Cara Menjalankan di Laptop (di luar host)

### 1. Copy project dari host
```bash
scp -r choirulhaq@<host-ip>:/home/choirulhaq/GoogleDrive/AhliPemrograman/testopencode ~/testopencode
```

### 2. Install Python 3.10+ (jika belum)
- **Windows:** download dari [python.org](https://python.org)
- **Mac:** `brew install python3`
- **Linux:** `sudo apt install python3 python3-venv`

### 3. Setup venv + install dependencies
```bash
cd ~/testopencode
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install flask
```

### 4. Jalankan aplikasi
```bash
python app.py
```

### 5. Buka browser
```
http://localhost:5000
```

## Catatan
- Database `database.db` auto-create saat pertama run
- Port 5000 harus bebas
- Untuk akses dari laptop lain di network yang sama, app.py sudah pakai `host='0.0.0.0'`

## Fitur
| Fitur | Deskripsi |
|-------|-----------|
| Create | Tambah item baru |
| Read | Lihat daftar + detail item |
| Update | Edit item |
| Delete | Hapus item |
| Margin Auto | `harga_jual - harga_pokok` |
| Format Rupiah | `Rp 10.000` |

## Struktur File
```
testopencode/
├── app.py
├── requirements.txt
├── database.db (auto-generated)
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── create.html
│   ├── edit.html
│   └── view.html
└── static/
    └── style.css
```
