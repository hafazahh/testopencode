# Progress: CRUD Item Application

> **STATUS TERKINI (2026-10-08):** Fase 1-4b SELESAI. Menunggu user test dari
> `~/GoogleDrive/AhliPemrograman/testopencodev2/`. **BELUM ADA COMMIT GIT** —
> commit hanya setelah user bilang "ok". Lanjut Fase 5 (RBAC), 6 (seed), 7 (deploy).
> Detail lengkap: lihat bagian **"Session Handoff (2026-10-08)"** di bawah.

## Status: COMPLETE

### Completed
- [x] Task plan dibuat
- [x] Findings dibuat
- [x] Progress file dibuat
- [x] Struktur folder dibuat (templates/, static/)
- [x] requirements.txt
- [x] app.py (main application)
- [x] templates/base.html
- [x] templates/index.html
- [x] templates/create.html
- [x] templates/edit.html
- [x] templates/view.html
- [x] static/style.css

### Pending
- [ ] Testing aplikasi (user action)
- [ ] Verifikasi CRUD operations (user action)
- [ ] Verifikasi kalkulasi margin (user action)

## Notes
- Menggunakan SQLite GENERATED ALWAYS AS untuk margin (auto-calc)
- Flask akan auto-create database.db saat pertama dijalankan
- Semua file disimpan di folder testopencode/

## Cara Menjalankan
```bash
pip install -r requirements.txt
python app.py
```
Lalu buka browser di http://localhost:5000

## Session Handoff (2026-10-07)

### Project: testopencode — Sistem Inventory + Transaksi

**Fase 1-3 selesai diimplementasikan:**
- Fase 1: Skema DB + kartu stok (7 tabel baru, 53 field, 14 constraint, 16 index)
- Fase 2: Supplier CRUD + Pembelian (stok masuk) — 9 route, 7 template
- Fase 3: Penjualan (stok keluar) + validasi stok — 4 route, 3 template

**Total kode:** app.py 2107 baris, 33 template, 11 tabel

**Test status:**
- Fase 2: 20/21 passed (curl test) — 1 "failure" = test expectation salah
- Fase 3: 30/30 passed (Flask test client)

**Known issues:**
1. ~~**Tombol "+ Tambah Item" di pembelian/create.html tidak berfungsi**~~ → ✅ **SELESAI** (2026-10-07). Root cause: CSP `script-src 'self'` blokir semua inline JS. Fix: JS eksternal + `addEventListener`. Terverifikasi Chromium lokal.
1b. ~~**Konfirmasi hapus (`onsubmit="return confirm"`) mati di 14 template**~~ → ✅ **SELESAI**. Ganti ke `data-confirm` + `static/confirm.js`.
2. **CSRF 403 di browser** — session cookie lama, workaround: clear cookies/incognito
3. **Port 5000 terbuka ke internet** — ada serangan brute force, perlu firewall

## Session Handoff (2026-10-07, lanjutan) — Fix CSP

### Yang diubah

**File baru (4):**
```
static/margin.js       preview margin (item create + edit)
static/pembelian.js    baris dinamis pembelian
static/penjualan.js    baris dinamis penjualan + info stok
static/confirm.js      konfirmasi hapus (data-confirm)
```

**Template diubah (14):**
- `create.html`, `edit.html` → `<script src=".../margin.js">`
- `pembelian/create.html` → JSON block `#items-data` + `pembelian.js`
- `penjualan/create.html` → JSON block `#items-data` + `penjualan.js`
- `base.html` → muat `confirm.js`
- 10 template index/view → `onsubmit=` jadi `data-confirm=`

**app.py** — hanya komentar CSP diperbarui, header TIDAK diubah.

### Aturan baru (WAJIB dipatuhi)

Jangan pernah tambah inline `<script>` atau atribut `onclick=` / `onchange=` /
`oninput=` / `onsubmit=` ke template. CSP `script-src 'self'` memblokirnya
**tanpa error server-side** — gejalanya cuma fitur diam-diam mati.

Pola benar:
- Logika → file di `static/`, muat lewat `<script src="{{ url_for('static', filename='x.js') }}">`
- Data dari server → `<script type="application/json" id="...">` + `JSON.parse`
- Handler → `addEventListener`
- Konfirmasi → `data-confirm="pesan"` di form

### Verifikasi (Chromium lokal, CSP asli)

| Uji | Hasil |
|---|---|
| Pembelian: baris awal otomatis | 1 baris |
| Pembelian: klik + Tambah Item 2× | 3 baris |
| Pembelian: harga auto-isi saat pilih item | 10000 |
| Pembelian: subtotal / total | Rp 30.000 / Rp 30.000 |
| Pembelian: tombol Hapus | 2 baris, total Rp 0 |
| Penjualan: 2 klik | 3 baris |
| Penjualan: info stok + saran harga | stok 100, harga 12000 |
| Margin create (jual > pokok) | Rp 5.000, margin-positive |
| Margin edit (jual < pokok) | Rp -2.000, margin-negative |
| Konfirmasi hapus: user klik Cancel | submit diblokir ✅ |
| Konfirmasi hapus: user klik OK | submit lanjut ✅ |
| `verify_security.py` | ALL CHECKS PASSED |
| `test_fase3.py` | 31 ✅, 6 ❌ — sama seperti baseline (nol regresi) |

6 ❌ di `test_fase3.py` sudah ada sebelum perubahan: data stok drift (test
hardcode angka 7/3/10/5, database sekarang 130/65) + nav link penjualan
(Fase 5 belum dikerjakan).

### Catatan lingkungan

Port `5060` diblokir Chromium (`ERR_UNSAFE_PORT` — SIP). Pakai `5070`.


**Next steps:**
1. ~~Debug tombol tambah item di pembelian~~ ✅ selesai
2. **⏸️ MENUNGGU USER TEST** — test di laptop dari `~/GoogleDrive/AhliPemrograman/testopencodev2/`
3. Fase 4: Kartu stok + laporan
4. Fase 5: RBAC untuk menu baru + navigasi
5. Fase 6: Seed data awal
6. Fase 7: Test atomicity + deploy

---

## Session Handoff (2026-10-07, sesi terakhir) — Copy ke Drive untuk test user

### Status sesi

**Berhenti di sini.** User akan shutdown host, lalu test di laptop dari Google Drive.
**BELUM ADA COMMIT GIT** — sesuai aturan: commit hanya setelah user bilang "ok".

### Yang dikerjakan sesi ini

1. Cek issue #1 (tombol "+ Tambah Item" mati) pakai Chromium lokal → root cause CSP ditemukan
2. Fix diterapkan: 4 file JS eksternal + 14 template dibersihkan dari inline JS/`on*`
3. Verifikasi di Chromium lokal dengan CSP asli → semua fungsi jalan
4. Copy snapshot ke Google Drive untuk test user

### Copy ke Drive — SELESAI ✅

**Sumber:** `/home/choirulhaq/venvProject/testopencode/`
**Tujuan:** `~/GoogleDrive/AhliPemrograman/testopencodev2/`

| Item | Hasil |
|---|---|
| Jumlah file | 65 sumber = 65 tujuan |
| Daftar relatif | `diff` kosong → **IDENTIK** |
| `app.py` checksum | `d0ca14b168c298c3de54a25c0845e0e0` (sama) |
| 4 file JS baru | checksum cocok semua |
| Marker fix di tujuan | `pembelian.js`, `application/json`, `margin.js`, `confirm.js`, `data-confirm` — ada |
| Sisa `on*=` di tujuan | 0 |
| `.git` / `__pycache__` di tujuan | sudah dibuang (sisa salinan lama) |

**Exclude saat copy:** `.git/` (snapshot bukan repo), `__pycache__/`, `*.pyc`.
**Include:** `.planning/` (berisi analisis root cause CSP).

**Catatan tooling:** `rsync` tidak terinstall di host ini. Copy pakai script Python
(`shutil.copy2`). **Jangan baca file dari mount Drive** — FUSE rclone, file uncached
butuh ~51 s. Script copy sengaja tidak pernah membaca destinasi, hanya menulis.

### Yang perlu user test di laptop

```bash
cd ~/testopencodev2
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Buka `http://localhost:5000`, login `admin` / `admin123`.

Checklist:
1. Pembelian → Tambah Pembelian → klik **+ Tambah Item** → baris nambah?
2. Pilih item di dropdown → harga beli terisi otomatis?
3. Isi qty → subtotal + total ikut update?
4. Klik **Hapus** di baris → baris hilang, total reset?
5. Penjualan → sama, plus kolom stok terisi?
6. Item → Tambah/Edit → preview margin jalan?
7. Klik **Hapus** di daftar item → dialog konfirmasi muncul?

### Kalau user bilang "ok" setelah test

1. Commit + push di `/home/choirulhaq/venvProject/testopencode/` (git masih lokal, belum ada commit sesi ini)
2. Git `post-commit` hook akan sync ke Drive otomatis
3. Lanjut Fase 4 (kartu stok + laporan)

### Kalau user lapor masih ada bug

Debug di `/home/choirulhaq/venvProject/testopencode/` (BUKAN di Drive).
Reproduce di Chromium lokal: render halaman via Flask test client, serve ulang
dengan header CSP asli di port 5070 (5060 diblokir Chromium — `ERR_UNSAFE_PORT`).

### State akhir host

- Tidak ada proses background tertinggal (Flask dev server + harness test sudah dimatikan)
- Tidak ada proses browser sandbox tertinggal
- Working tree `/home/choirulhaq/venvProject/testopencode/` punya perubahan belum di-commit:
  `app.py` (komentar), 14 template, 4 file JS baru di `static/`, + `.planning/` untracked

---

## Session Handoff (2026-10-08) — Fase 4 + 4b + copy ke Drive

### Status sesi

**Fase 4 (Kartu Stok + Laporan) dan Fase 4b (Login Page Enhancement) SELESAI.**
Snapshot sudah dicopy ke Google Drive untuk test user.
**BELUM ADA COMMIT GIT** — sesuai aturan, commit hanya setelah user bilang "ok".

### Yang dikerjakan

1. **Fase 4b — Login page**: info card di atas form login
   - Judul "Sistem Manajemen Inventory & Transaksi" + deskripsi singkat
   - Grid 2x2 fitur: Master Data, Transaksi, Laporan, Multi-User
   - CSS baru: `.login-info-card`, `.feature-grid`, `.feature-item` (+ responsive)
2. **Fase 4 — Kartu Stok** (`/stok/kartu`): dropdown item, summary stok + HPP rata-rata,
   tabel mutasi dengan badge Masuk/Keluar + saldo berjalan
3. **Fase 4 — Laporan Penjualan** (`/laporan/penjualan`): filter tanggal, 4 summary card,
   tabel detail dengan margin per baris
4. **Fase 4 — Laporan Stok** (`/laporan/stok`): 4 summary card, tabel stok + status
   badge Aman/Menipis/Habis
5. **RBAC**: permission `stok: [view]` dan `laporan: [view]` ditambah ke role admin
6. **Nav**: link "Kartu Stok", "Laporan Penjualan", "Laporan Stok" di `base.html`

### File

**Baru (5):**
```
templates/stok/kartu.html
templates/laporan/penjualan.html
templates/laporan/stok.html
static/kartu-stok.js          auto-submit dropdown kartu stok
test_fase4.py                 test suite baru, 15 assertion
```

**Diubah (5):**
```
app.py                  +3 route, +2 permission, blok FASE 4
templates/base.html     +3 nav link, +{% block scripts %}
templates/login.html    +info card
static/style.css        +login card, +badge, +summary-card
.planning/stok-transaksi/task_plan.md   fase 4 & 4b complete
```

### Verifikasi (bukan self-report)

| Uji | Hasil |
|---|---|
| `test_fase4.py` | **15/15 passed** |
| `test_fase2.py` | 18 ✅, 0 ❌ |
| `test_fase3.py` | 31 ✅, 5 ❌ — turun dari baseline 6 ❌ (nol regresi) |
| `verify_security.py` | **ALL CHECKS PASSED** |
| Live curl: 5 route | 200 semua (login 302) |
| CSP masih aktif | `script-src 'self'` utuh, tidak dilonggarkan |
| `static/kartu-stok.js` | 200 `text/javascript` |
| Inline `on*=` di templates | **0** |
| Inline `<script>` tanpa src | **0** |
| Kontras WCAG (9 pasangan) | semua PASS AA, terendah `badge-warning` 4.96:1 |

5 ❌ di `test_fase3.py` sudah ada sebelum sesi ini: test hardcode stok 7/3/10/5,
database sekarang 117/58 (data drift). Bukan regresi.

### Copy ke Drive — SELESAI

**Sumber:** `/home/choirulhaq/venvProject/testopencode/`
**Tujuan:** `~/GoogleDrive/AhliPemrograman/testopencodev2/`

| Item | Hasil |
|---|---|
| Jumlah file | 69 sumber = 69 tujuan (+ `database.db`) |
| Checksum 8 file kunci | semua IDENTIK |
| `database.db` | 151552 B, md5 `6588df6f49afcef225b0abcfa9187ff2`, IDENTIK |
| File hanya di tujuan | hanya `database.db` (disengaja) |
| File hanya di sumber | tidak ada |
| WAL checkpoint | sudah di-TRUNCATE sebelum copy |

**Exclude saat copy:** `.git/`, `__pycache__/`, `*.pyc`, `database.db*` (lalu
`database.db` disalin terpisah setelah checkpoint WAL).
**Catatan tooling:** `rsync` tidak terinstall. Copy pakai script Python
(`shutil.copy2`). Script tidak pernah membaca mount Drive untuk enumerasi —
hanya menulis, lalu verifikasi checksum pada file yang sudah ada di cache.

### Yang perlu user test

```bash
cd ~/testopencodev2
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Buka `http://localhost:5000`, login `admin` / `admin123`.

Checklist:
1. **Halaman login** — info card muncul di atas form? 4 fitur tampil rapi?
2. **Nav** — "Kartu Stok", "Laporan Penjualan", "Laporan Stok" muncul?
3. **Kartu Stok** — pilih item di dropdown → klik Tampilkan → mutasi + saldo berjalan?
4. **Kartu Stok** — badge Masuk (hijau) / Keluar (merah) benar?
5. **Laporan Penjualan** — summary card terisi? filter tanggal jalan?
6. **Laporan Stok** — status badge Aman/Menipis/Habis benar?
7. Fitur Fase 1-3 masih jalan (pembelian, penjualan, CRUD)?

### Kalau user bilang "ok"

1. Commit + push di `/home/choirulhaq/venvProject/testopencode/`
2. Git `post-commit` hook sync ke Drive otomatis
3. Lanjut Fase 5 (RBAC role kasir/gudang), Fase 6 (seed data), Fase 7 (deploy)

### State akhir host

- Tidak ada proses background tertinggal — Flask dev server sudah dimatikan,
  port 5070 dan 5000 tidak ada listener
- Working tree punya perubahan belum di-commit (lihat daftar file di atas)

---

## Session Handoff (2026-10-08, Fase 5) — RBAC

### Status sesi

**Fase 5 (RBAC untuk menu baru + navigasi) SELESAI.**

### Yang dikerjakan

1. **Fix `full_perms` admin** — tambah `'stok': ['view']` (sudah ada sebelumnya)
2. **Fix menus list** di `create_role` dan `edit_role` — tambah `'stok'` dan `'laporan'`
3. **Seed role `kasir`** — akses: items(view), kategori(view), pelanggan(view+create+edit), supplier(view), pembelian(view), penjualan(view+create+delete), stok(view), laporan(view). TIDAK punya akses: users, roles
4. **Seed role `gudang`** — akses: items(view+create+edit), kategori(view+create+edit), pelanggan(view), supplier(view+create+edit+delete), pembelian(view+create+delete), penjualan(view only), stok(view), laporan(view). TIDAK punya akses: users, roles
5. **Test `test_fase5.py`** — 8/8 passed

### Verifikasi

| Uji | Hasil |
|---|---|
| `test_fase5.py` | **8/8 passed** |
| `test_fase2.py` | 18 ✅, 0 ❌ |
| `test_fase3.py` | 31 ✅, 5 ❌ (data drift, bukan regresi) |
| `test_fase4.py` | 15 ✅, 0 ❌ |
| `verify_security.py` | **ALL CHECKS PASSED** |

### Next steps

1. **Fase 6** — Seed data awal (idempotent)
2. **Fase 7** — Test atomicity + deploy + verifikasi

---

## Session Handoff (2026-10-08, Fase 6) — Seed Data

### Status sesi

**Fase 6 (Seed data awal) SELESAI.**

### Yang dikerjakan

1. **Sync stok_akhir** dari stok_mutasi — 7 item
2. **Tambah 5 pembelian** untuk item yang belum punya stok (item 3-7)
3. **Buat 3 transaksi penjualan** contoh (PJ-2026-0001 s/d 0003)
4. **Cleanup user test** — hapus test_kasir dan test_gudang
5. **Test `test_fase6.py`** — 10/10 passed

### Data akhir

| Tabel | Jumlah |
|---|---|
| items | 24 |
| kategori | 4 |
| pelanggan | 15 |
| supplier | 15 |
| roles | 3 (admin, kasir, gudang) |
| users | 1 (admin) |
| pembelian | 19 |
| penjualan | 3 |
| stok_mutasi | 36 |
| stok_akhir | 7 |

### Verifikasi

| Uji | Hasil |
|---|---|
| `test_fase6.py` | **10/10 passed** |
| `test_fase2.py` | 18 ✅, 0 ❌ |
| `test_fase3.py` | 31 ✅, 5 ❌ (data drift) |
| `test_fase4.py` | 15 ✅, 0 ❌ |
| `test_fase5.py` | 8 ✅, 0 ❌ |
| `verify_security.py` | **ALL CHECKS PASSED** |

### Next steps

1. **Fase 7** — Test atomicity + deploy + verifikasi

---

## ⏭️ RESUME DI SINI (sesi baru, 2026-10-08)

### 5 pertanyaan reboot — jawaban

| Pertanyaan | Jawaban |
|---|---|
| Di mana saya? | Fase 1-4b selesai. Menunggu user test dari Drive. |
| Mau ke mana? | Fase 5 → 6 → 7 |
| Tujuannya? | testopencode jadi sistem inventory + transaksi siap portofolio freelance |
| Apa yang dipelajari? | CSP `script-src 'self'` memblokir inline JS/`on*` TANPA error server-side |
| Apa yang sudah dikerjakan? | Lihat Session Handoff 2026-10-08 di atas |

### Aturan yang WAJIB dipatuhi (jangan dilanggar)

1. **JANGAN commit/push git** sebelum user bilang "ok". Working tree sekarang
   punya banyak perubahan belum di-commit — itu disengaja.
2. **JANGAN tambah inline `<script>` atau atribut `on*=`** (`onclick`, `onchange`,
   `oninput`, `onsubmit`) ke template. CSP memblokirnya **tanpa error server-side** —
   gejalanya cuma fitur diam-diam mati. Pakai file di `static/` + `addEventListener`,
   atau `data-confirm` untuk konfirmasi hapus.
3. **JANGAN longgarkan security headers.** `verify_security.py` harus tetap ALL PASSED.
4. **JANGAN kerjakan project di mount Drive.** Kerja di
   `/home/choirulhaq/venvProject/testopencode/`, copy ke Drive hanya untuk test user.
5. **JANGAN baca file dari mount Drive** — FUSE rclone, file uncached ~51 detik.
6. **Port 5060 diblokir Chromium** (`ERR_UNSAFE_PORT`). Pakai 5070.
7. **Tulis script ke file**, jangan `python3 -c` (diblokir RTK/Tirith).

### Langkah pertama di sesi baru

```bash
cd /home/choirulhaq/venvProject/testopencode
read_file progress.md        # baca bagian "Session Handoff (2026-10-08)"
read_file .planning/stok-transaksi/task_plan.md
git status --short           # pastikan perubahan belum di-commit
```

Lalu tanya user: **sudah test dari Drive? ada bug? atau lanjut Fase 5?**

### Fase 5 — RBAC untuk menu baru (belum dikerjakan)

Saat ini hanya role `admin` yang ada, dengan permission `stok: [view]` dan
`laporan: [view]`. Fase 5 perlu:
- Tambah role contoh: `kasir` (penjualan view+create, stok view, laporan view),
  `gudang` (supplier+pembelian view+create, stok view)
- Pastikan nav `base.html` menyembunyikan link yang tidak diizinkan
- Test: login sebagai non-admin, cek menu yang muncul

### Fase 6 — Seed data awal (belum dikerjakan)

Role, kategori, item, pelanggan, user — idempotent (`INSERT OR IGNORE`).
`database.db` sekarang sudah berisi: 22 item, 4 kategori, 14 pelanggan,
13 supplier, 12 pembelian, 24 mutasi stok, 1 user (admin), 1 role (admin).

### Fase 7 — Test atomicity + deploy + verifikasi (belum dikerjakan)

- Test transaksi gagal-di-tengah → rollback bersih
- Test validasi stok negatif
- Deploy ke Render + Cloudflare (`crud.choirulhaq.com` sudah live untuk versi lama)
- **HANYA setelah user bilang "ok"**

### File test yang ada (jalankan untuk verifikasi)

| File | Fungsi | Baseline |
|---|---|---|
| `test_fase2.py` | Supplier + Pembelian | 18 ✅, 0 ❌ |
| `test_fase3.py` | Penjualan | 31 ✅, 5 ❌ (drift data, bukan regresi) |
| `test_fase4.py` | Kartu stok + laporan + login | **15 ✅, 0 ❌** |
| `verify_security.py` | Headers, cookie, CSRF, RBAC | ALL CHECKS PASSED |

Catatan: `test_fase3.py` hardcode angka stok lama (7/3/10/5), database sekarang
117/58. Kalau mau bersih, perbaiki assertion-nya jadi relatif (delta, bukan absolut).

### Kalau user lapor bug

Debug di `/home/choirulhaq/venvProject/testopencode/` (BUKAN di Drive).
Reproduce di Chromium lokal: render halaman via Flask test client, serve ulang
dengan header CSP asli di port 5070.



