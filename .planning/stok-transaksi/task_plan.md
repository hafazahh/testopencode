# Task Plan: Transaksi Penjualan + Pengadaan Stok (Opsi B)

**Project:** `/home/choirulhaq/venvProject/testopencode/` (tambahan ke CRUD yang sudah live)
**Live:** `crud.choirulhaq.com` (Render + Cloudflare, grade A+)
**Status:** Fase 4 in_progress

---

## Tujuan

Ubah `testopencode` dari CRUD master data menjadi **sistem inventory + transaksi**:
pengadaan barang (stok masuk), penjualan (stok keluar), dan kartu stok sebagai
sumber kebenaran. HPP pakai **moving average**.

**Kenapa:** portofolio freelance. Klien membayar untuk sistem kasir/stok, bukan
website profil. Atomicity + ledger + HPP membedakan programmer pemula dari yang
bisa dipercaya pegang data uang.

---

## Keputusan User

| # | Keputusan |
|---|---|
| 1 | **Opsi B** — penjualan + pembelian + kartu stok (bukan pemakaian stok/FIFO) |
| 2 | **HPP moving average** (bukan FIFO) |
| 3 | **Tambahan ke testopencode**, bukan project baru |
| 4 | Data lama tidak signifikikan (demo) — boleh reset |
| 5 | Perlu **inisialisasi data awal**: role, kategori, item, pelanggan, user |
| 6 | **Login page**: tambah label keterangan fungsi aplikasi dengan style UIX |

---

## Fase

| # | Fase | Status | Estimasi |
|---|---|---|---|
| 1 | **Desain skema DB + kartu stok** | ✅ complete | 2026-10-07 |
| 2 | Supplier + Pembelian (stok masuk) | ✅ complete | 2026-10-07 |
| 3 | Penjualan (stok keluar) + validasi | ✅ complete | 2026-10-07 |
| 3b | **Fix CSP: tombol "+ Tambah Item" + konfirmasi hapus** | ✅ complete | 2026-10-07 |
| 4 | Kartu stok + laporan | ✅ complete | 2026-10-08 |
| 4b | **Login page: label keterangan fungsi aplikasi** | ✅ complete | 2026-10-08 |
| 5 | RBAC untuk menu baru + navigasi | pending | kecil |
| 6 | Seed data awal | pending | kecil |
| 7 | Test atomicity + deploy + verifikasi | pending | sedang |

**Status sesi ini (2026-10-08):** Fase 4 + 4b selesai. 15/15 test passed, 0 regression.

---

## Fase 4: Kartu Stok + Laporan — Detail

### 4.1 Kartu Stok (`/stok/kartu`)
- Tabel: `stok_mutasi` sudah ada (Fase 1)
- Route baru: `GET /stok/kartu` — pilih item, lihat semua mutasi
- Tampilkan: tanggal, nomor_referensi, jenis (IN/OUT), qty, saldo_berjalan
- Template: `templates/stok/kartu.html`
- RBAC: `@has_permission('stok', 'view')`

### 4.2 Laporan Penjualan (`/laporan/penjualan`)
- Route baru: `GET /laporan/penjualan`
- Tampilkan: semua penjualan + detail (join penjualan_detail + items)
- Filter: date range (optional)
- Summary: total penjualan, total item terjual, total margin
- Template: `templates/laporan/penjualan.html`
- RBAC: `@has_permission('laporan', 'view')`

### 4.3 Laporan Stok (`/laporan/stok`)
- Route baru: `GET /laporan/stok`
- Tampilkan: semua item + stok_akhir (qty_akhir, harga_pokok_rata)
- Highlight: item dengan stok menipis (qty < 10)
- Template: `templates/laporan/stok.html`
- RBAC: `@has_permission('laporan', 'view')`

### 4.4 Navigasi baru
- Tambah link di `base.html`: "Kartu Stok", "Laporan Penjualan", "Laporan Stok"
- Atau grouping dropdown

---

## Fase 4b: Login Page Enhancement

### Yang ditambah
- **Info card** di atas form login: "Sistem Manajemen Inventory & Transaksi"
- **Deskripsi singkat**: "Kelola stok barang, pembelian, penjualan, dan laporan dalam satu sistem."
- **Fitur list** (icon + text):
  - CRUD Master Data (Item, Kategori, Pelanggan, Supplier)
  - Pembelian & Penjualan dengan validasi stok
  - Kartu Stok & Laporan real-time
  - Multi-user dengan Role-Based Access Control
- **Style**: modern, clean, sesuai UIX standard
  - Card dengan shadow, rounded corners
  - Icon pakai emoji atau SVG inline
  - Color scheme sesuai existing (purple/blue gradient)
  - Responsive

### File diubah
- `templates/login.html` — tambah info card
- `static/style.css` — tambah class `.login-info-card`, `.feature-list`, dll

---

## Yang Sudah Ada (jangan diubah)

```
Route        : 27 (5 menu CRUD + login/logout)
app.py       : 2.107 baris
Templates    : 33 file
Tabel        : 11 — items, pelanggan, kategori, roles, users, supplier, pembelian, pembelian_detail, penjualan, penjualan_detail, stok_mutasi, stok_akhir
Pola RBAC    : @has_permission('menu', 'action')
Navigasi     : templates/base.html — 5 link
Security     : A+ (CSP, HSTS, cookie flags, rate limit, CSRF)
```

**Pertahankan:** pola `@has_permission`, CSRF, security headers, struktur template.

---

## Acceptance Criteria

- [ ] Stok berkurang otomatis saat penjualan, bertambah saat pembelian
- [ ] Tidak bisa jual melebihi stok tersedia (validasi + pesan jelas)
- [ ] Semua transaksi **atomic** — gagal di tengah = tidak ada perubahan
- [ ] Kartu stok menampilkan semua mutasi + saldo berjalan
- [ ] HPP average dihitung ulang tiap pembelian
- [ ] HPP di-snapshot di baris penjualan (laporan lama tidak berubah)
- [ ] Nomor transaksi otomatis (`PJ-2026-0001`, `PB-2026-0001`)
- [ ] RBAC bekerja untuk 4 menu baru
- [ ] Security grade tetap A+
- [ ] Seed data awal lengkap dan idempotent
- [ ] Semua test lama masih lolos
- [ ] **Login page**: info card dengan deskripsi fungsi aplikasi + fitur list
- [ ] **Kartu stok**: tampilkan semua mutasi per item dengan saldo berjalan
- [ ] **Laporan penjualan**: tampilkan semua penjualan + summary
- [ ] **Laporan stok**: tampilkan stok akhir + highlight stok menipis

---

## Error Log

| Error | Percobaan | Resolusi |
|---|---|---|
| Tombol "+ Tambah Item" di pembelian/create.html tidak berfungsi | 1 | ✅ **SELESAI** — root cause CSP `script-src 'self'` blokir inline JS. Fix: 4 file JS eksternal di `static/` + `addEventListener` + data JSON block. Terverifikasi di Chromium lokal, CSP tidak dilonggarkan. |
| `onsubmit="return confirm(...)"` mati di 14 template | 1 | ✅ **SELESAI** — CSP juga blokir atribut `on*`. Ganti ke `data-confirm` + `static/confirm.js` (`addEventListener`). |
| CSRF 403 di browser (iPad & laptop) | 1 | ⚠️ Workaround: clear cookies/incognito |
| Login CSRF 403 di Flask test client | 1 | ⚠️ Workaround: WTF_CSRF_ENABLED=False |
| Port 5000 terbuka ke internet — serangan brute force | 1 | ❌ OPEN — perlu firewall |

---

## Catatan Risiko

| Risiko | Dampak | Mitigasi |
|---|---|---|
| **Atomicity salah** | Stok kacau, tidak bisa dilacak | `BEGIN IMMEDIATE` + rollback; test gagal-di-tengah |
| **Skema kartu stok salah** | Semua fase ikut salah | Fase 1 ditahan sampai desain disetujui |
| **Stok negatif** | Data tidak masuk akal | Validasi sebelum commit + constraint |
| **Migrasi DB live** | Data hilang | Data demo, boleh reset — tapi `/reset-db` tidak boleh ikut ke produksi |
| **Regresi security** | Grade A+ turun | `verify_security.py` dijalankan tiap fase |
