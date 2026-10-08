# Findings: Transaksi Penjualan + Pengadaan Stok

**Project:** `/home/choirulhaq/venvProject/testopencode/`

---

## Audit Project Sekarang

```
app.py        : 1.221 baris
test_enhancement.py : 672 baris
verify_security.py  : 148 baris
templates     : 23 file HTML
Route         : 27
Tabel         : 5
```

### Tabel yang ada

| Tabel | Kolom kunci |
|---|---|
| `items` | id, nama, harga_pokok, harga_jual, **margin (GENERATED)**, category |
| `pelanggan` | id, nama, email, telepon, alamat |
| `kategori` | id, nama (UNIQUE), deskripsi |
| `roles` | id, nama (UNIQUE), deskripsi, **permissions (JSON)** |
| `users` | id, username (UNIQUE), password_hash, password_plain, role_id |

### Route yang ada (27)

```
login, logout, 404/500/403 handlers
items      : index, view, create, edit, delete
pelanggan  : index, view, create, edit, delete
kategori   : index, view, create, edit, delete
users      : index, view, create, edit, delete
roles      : index, view, create, edit, delete
```

### Pola RBAC

```python
# Permission disimpan sebagai JSON di tabel roles
'items': ['view', 'create', 'edit', 'delete'],
'kategori': ['view', 'create', 'edit', 'delete'],
'pelanggan': ['view', 'create', 'edit', 'delete'],
'users': ['view', 'create', 'edit', 'delete'],
'roles': ['view', 'create', 'edit', 'delete'],

# Dipakai sebagai decorator
@has_permission('items', 'view')
def index(): ...
```

**Menu baru harus mengikuti pola ini** — tambah key di `full_perms` saat seed,
lalu decorator di route.

### Seed yang sudah ada

- `kategori` — di-seed kalau tabel kosong
- `roles` — role `admin` dengan `full_perms`
- `users` — user `admin` (password `admin123`)

**Seed sekarang belum lengkap** untuk demo: tidak ada item, pelanggan, supplier.

---

## Desain Kartu Stok (bagian paling menentukan)

### ❌ Cara salah

```sql
ALTER TABLE items ADD COLUMN stok INTEGER DEFAULT 0;
-- lalu UPDATE items SET stok = stok - 5 WHERE id = 1;
```

**Kenapa salah:**
- Tidak ada jejak **kenapa** stok berubah
- Selisih tidak bisa dilacak — mustahil audit
- Stok bisa negatif tanpa terdeteksi
- Tidak bisa menjawab "stok ini dari pembelian mana?"

### ✅ Cara benar — ledger

```sql
CREATE TABLE stok_mutasi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    tanggal TEXT NOT NULL,           -- ISO8601
    jenis TEXT NOT NULL,             -- 'masuk' | 'keluar'
    qty REAL NOT NULL,               -- selalu positif; arah dari 'jenis'
    harga_satuan REAL,               -- harga beli (masuk) / HPP snapshot (keluar)
    ref_tipe TEXT,                   -- 'pembelian' | 'penjualan' | 'awal'
    ref_id INTEGER,                  -- id di tabel pembelian/penjualan
    saldo_setelah REAL,              -- saldo berjalan (memudahkan laporan)
    keterangan TEXT,
    created_at TEXT NOT NULL
);
```

**Prinsip:** stok adalah **turunan**, bukan kolom yang di-`UPDATE`.
Saldo = jumlah mutasi. Setiap perubahan = baris baru. Tidak ada `UPDATE` pada stok.

**Keuntungan:**
- Audit lengkap — bisa jawab "kenapa stok 7?"
- Koreksi = mutasi baru (penyesuaian), bukan menimpa sejarah
- Cocok untuk pola akuntansi (yang dicari klien)

---

## HPP Moving Average

### Rumus

```
Saat PEMBELIAN:
  total_nilai_lama = qty_lama × hpp_lama
  total_nilai_baru = total_nilai_lama + (qty_beli × harga_beli)
  qty_baru         = qty_lama + qty_beli
  hpp_baru         = total_nilai_baru / qty_baru

Saat PENJUALAN:
  HPP di-snapshot ke baris penjualan_detail (hpp_saat_jual)
  hpp master TIDAK berubah
```

### Kenapa snapshot HPP di baris penjualan

Kalau HPP diambil dari master saat mencetak laporan lama, **laporan lama berubah**
setiap kali ada pembelian baru. Itu salah — laporan historis harus tetap.

**Contoh:**
```
1 Jan  beli 10 @ 5.000  → hpp = 5.000
5 Jan  jual 4 @ 8.000   → snapshot hpp = 5.000, laba = 4×(8.000-5.000) = 12.000
10 Jan beli 10 @ 7.000  → hpp = (6×5.000 + 10×7.000)/16 = 6.250

Laporan 5 Jan harus tetap laba 12.000, bukan 4×(8.000-6.250) = 7.000
```

**Ini yang membedakan sistem serius dari sistem asal jalan.**

---

## Struktur Tabel Baru

```sql
supplier (
    id, nama, kontak, telepon, email, alamat, created_at
)

pembelian (
    id, nomor (UNIQUE), tanggal, supplier_id,
    total, keterangan, created_at
)

pembelian_detail (
    id, pembelian_id, item_id, qty, harga_satuan, subtotal
)

penjualan (
    id, nomor (UNIQUE), tanggal, pelanggan_id,
    total, keterangan, created_at
)

penjualan_detail (
    id, penjualan_id, item_id, qty, harga_satuan,
    hpp_saat_jual,      -- ← SNAPSHOT, kunci laporan historis
    subtotal
)

stok_mutasi (
    id, item_id, tanggal, jenis, qty, harga_satuan,
    ref_tipe, ref_id, saldo_setelah, keterangan, created_at
)
```

**Kolom baru di `items`:** `hpp_average REAL DEFAULT 0`

---

## Atomicity — Risiko Tertinggi

Satu penjualan menyentuh 3 tabel:
```
INSERT penjualan          (header)
INSERT penjualan_detail   (baris)
INSERT stok_mutasi        (keluar) — 1 baris per item
UPDATE items.hpp_average  (tidak berubah saat jual, tapi saat beli berubah)
```

Kalau gagal di tengah → stok kacau, tidak bisa dilacak.

**Solusi:** `BEGIN IMMEDIATE` ... `COMMIT` / `ROLLBACK`.
`IMMEDIATE` (bukan `DEFERRED`) supaya lock diambil sejak awal — mencegah
race condition dua kasir menjual item terakhir bersamaan.

**Test yang harus dibuat:** paksa error di tengah transaksi → verifikasi tidak
ada baris yang tersisa di ketiga tabel.

---

## Nomor Transaksi Otomatis

```
PJ-2026-0001   penjualan
PB-2026-0001   pembelian
```

Cara: `SELECT MAX(nomor) WHERE nomor LIKE 'PJ-2026-%'` lalu increment.
Harus di dalam transaksi yang sama supaya tidak bentrok.

---

## Verifikasi yang Harus Dilakukan

| Aspek | Cara |
|---|---|
| Stok berkurang saat jual | Bandingkan saldo kartu stok sebelum/sesudah |
| Tidak bisa jual > stok | Test jual 999 unit → harus ditolak |
| Atomicity | Paksa error di tengah → cek 3 tabel bersih |
| HPP average | Hitung manual vs hasil sistem |
| HPP snapshot | Jual, lalu beli lagi, cek laporan lama tidak berubah |
| RBAC | User tanpa permission → 403 |
| Security tidak turun | `verify_security.py` |
| Test lama tetap lolos | `test_enhancement.py` |

---

## Catatan Alur Kerja

**Development di host dulu. JANGAN commit ke git sampai user selesai test.**

Alasan: user ingin memverifikasi sendiri sebelum masuk ke repo live
(`crud.choirulhaq.com` auto-deploy dari GitHub).

**Implikasi:** git post-commit hook (backup ke Drive) tidak akan jalan selama
belum ada commit — itu memang yang diinginkan.

---

## Issue #1 — Tombol "+ Tambah Item" tidak berfungsi (ROOT CAUSE, 2026-10-07)

### Gejala

Klik `+ Tambah Item` di `/pembelian/create` → tidak ada baris yang muncul.
Sama di `/penjualan/create`. Preview margin di `/create` dan `/item/<id>/edit`
juga mati.

### Root cause

`CSP` di `app.py` baris 41–52:

```
script-src 'self';
```

Tanpa `'nonce-...'` dan tanpa `'unsafe-inline'`. Akibatnya **setiap inline
`<script>` diblokir browser** — termasuk blok `<script>` di 4 template:

| Template | Blok inline | Isi |
|---|---|---|
| `create.html` | 1 | preview margin |
| `edit.html` | 1 | preview margin |
| `pembelian/create.html` | 1 | `addDetailRow`, subtotal, total |
| `penjualan/create.html` | 1 | `addDetailRow`, stok info, subtotal |

Ini **bukan** bug JavaScript. Kode JS-nya benar. Bukti: setelah blok inline
di-`eval()` manual (jalur yang melewati CSP), `typeof addDetailRow === 'function'`
dan tombol langsung berfungsi — 2 klik = 2 baris.

Komentar di `app.py` baris 37–38 menyatakan "this app uses NO inline JS" —
pernyataan itu **salah** dan itulah asal bug.

### Bukti pengukuran (Chromium lokal, CSP asli dikirim ulang)

| Halaman | Inline script | Global JS terdefinisi | Baris tabel |
|---|---|---|---|
| `/create` | 1 | tidak ada | — |
| `/item/1/edit` | 1 | tidak ada | — |
| `/pembelian/create` | 1 | tidak ada | 0 |
| `/penjualan/create` | 1 | tidak ada | 0 |

Klik `+ Tambah Item` 2× pada `/pembelian/create` → tetap 0 baris.

### Probe CSP (halaman uji, CSP sendiri)

| Bentuk | Hasil |
|---|---|
| `<script>` inline biasa | ❌ diblokir |
| `<script nonce="X">` + CSP punya nonce X | ✅ jalan |
| `<script type="application/json">` | ✅ terbaca (tidak dieksekusi) |
| `onclick=` atribut di HTML | ❌ diblokir (tanpa `'unsafe-inline'`) |
| `onclick=` atribut dibuat via JS | ❌ diblokir |
| `addEventListener` via JS | ✅ jalan |

**Kesimpulan penting:** nonce saja **tidak cukup**. Atribut `onclick=`,
`onchange=`, `oninput=` di dalam baris dinamis tetap diblokir tanpa
`'unsafe-inline'` — dan menambah `'unsafe-inline'` akan menurunkan grade
security A+ dan membuat `verify_security.py` GAGAL (cek baris 38).

### Fix yang terverifikasi (belum diterapkan)

1. Pindahkan JS ke file eksternal di `static/` — `script-src 'self'` mengizinkan.
2. Data item dari Jinja → `<script type="application/json" id="items-data">`
   (tidak dieksekusi, jadi CSP tidak menyentuh), lalu `JSON.parse` di file JS.
3. Ganti semua `onclick=` / `onchange=` / `oninput=` dengan `addEventListener`.
4. `verify_security.py` tetap lolos — CSP tidak diubah sama sekali.

Hasil uji sandbox dengan CSP asli:

```
BEFORE   : rows=1 (baris awal otomatis), addDetailRow=function
2 klik   : rows=3
isi form : harga terisi otomatis 10000, subtotal "Rp 30.000", total "Rp 30.000"
hapus    : rows=2, total "Rp 0"
margin   : "Rp 5.000", class margin-positive
```

Semua fungsi kembali normal tanpa melonggarkan CSP.

### File terdampak

```
templates/create.html            → static/margin.js
templates/edit.html              → static/margin.js
templates/pembelian/create.html  → static/pembelian.js
templates/penjualan/create.html  → static/penjualan.js
```

