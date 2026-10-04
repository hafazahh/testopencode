# Task Plan: CRUD Item dengan Harga Pokok dan Harga Jual

## Objective
Membuat aplikasi web CRUD (Create, Read, Update, Delete) untuk mengelola item dengan harga pokok dan harga jual, menggunakan Python + Flask + SQLite.

## Requirements
1. Python + Flask
2. SQLite database (SQL tanpa server)
3. HTML template untuk tampilan
4. CRUD item: nama, harga_pokok, harga_jual
5. Hitung margin otomatis (harga_jual - harga_pokok)
6. Gunakan planning-with-files: task_plan.md, findings.md, progress.md
7. Simpan semua file di folder ini

## Tasks

### Phase 1: Planning & Setup
- [x] Buat task_plan.md
- [x] Buat findings.md
- [x] Buat progress.md
- [x] Buat requirements.txt
- [x] Buat struktur folder (templates/, static/)

### Phase 2: Database & Backend
- [ ] Buat database schema (SQLite)
- [ ] Buat app.py dengan Flask routes
- [ ] Implementasi CRUD operations
- [ ] Implementasi kalkulasi margin otomatis

### Phase 3: Frontend
- [ ] Buat base.html (template utama)
- [ ] Buat index.html (daftar item)
- [ ] Buat create.html (tambah item)
- [ ] Buat edit.html (edit item)
- [ ] Buat view.html (detail item)
- [ ] Buat style.css (styling)

### Phase 4: Testing
- [ ] Install dependencies
- [ ] Jalankan aplikasi
- [ ] Test semua operasi CRUD
- [ ] Verifikasi kalkulasi margin

## Project Structure
```
testopencode/
├── app.py
├── requirements.txt
├── database.db (auto-generated)
├── task_plan.md
├── findings.md
├── progress.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── create.html
│   ├── edit.html
│   └── view.html
└── static/
    └── style.css
```

## Database Schema
```sql
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    harga_pokok REAL NOT NULL,
    harga_jual REAL NOT NULL,
    margin REAL GENERATED ALWAYS AS (harga_jual - harga_pokok) STORED,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Daftar semua item |
| GET | /item/<id> | Detail item |
| GET | /create | Form tambah item |
| POST | /create | Proses tambah item |
| GET | /item/<id>/edit | Form edit item |
| POST | /item/<id>/edit | Proses edit item |
| POST | /item/<id>/delete | Hapus item |
