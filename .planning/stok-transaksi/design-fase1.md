# Desain Fase 1: Skema DB + Kartu Stok

**Project:** `/home/choirulhaq/venvProject/testopencode/`
**Status:** Draft untuk review user
**Tanggal:** 2026-10-07

---

## 1. Diagram Relasi Antar Tabel

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│    supplier     │     │     pembelian       │     │  pembelian_detail   │
├─────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ id (PK)         │◄────│ id (PK)             │◄────│ id (PK)             │
│ nama            │     │ supplier_id (FK)    │     │ pembelian_id (FK)   │
│ kontak          │     │ nomor_transaksi     │     │ item_id (FK)        │
│ alamat          │     │ tanggal             │     │ qty                 │
│ created_at      │     │ catatan             │     │ harga_beli           │
│                 │     │ created_by (FK)     │     │ subtotal            │
└─────────────────┘     │ created_at          │     │ created_at          │
                        └─────────────────────┘     └─────────────────────┘
                                                        │
                                                        │ item_id
                                                        ▼
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│    pelanggan    │     │     penjualan       │     │  penjualan_detail   │
├─────────────────┤     ├─────────────────────┤     ├─────────────────────┤
│ id (PK)         │◄────│ id (PK)             │◄────│ id (PK)             │
│ nama            │     │ pelanggan_id (FK)   │     │ penjualan_id (FK)   │
│ email           │     │ nomor_transaksi     │     │ item_id (FK)        │
│ telepon         │     │ tanggal             │     │ qty                 │
│ alamat          │     │ catatan             │     │ harga_jual           │
│ created_at      │     │ created_by (FK)     │     │ harga_pokok (snap)  │
└─────────────────┘     │ created_at          │     │ subtotal            │
                        └─────────────────────┘     └─────────────────────┘
                                                        │
                                                        │ item_id
                                                        ▼
                        ┌─────────────────────────────────────────────┐
                        │              stok_mutasi                     │
                        ├─────────────────────────────────────────────┤
                        │ id (PK)                                     │
                        │ item_id (FK)                                │
                        │ jenis_mutasi ('IN' | 'OUT')                 │
                        │ qty                                         │
                        │ harga                                       │
                        │ saldo_berjalan                              │
                        │ referensi_tipe ('pembelian'|'penjualan')   │
                        │ referensi_id                                │
                        │ nomor_referensi                             │
                        │ tanggal                                     │
                        │ created_by (FK)                             │
                        │ created_at                                  │
                        └─────────────────────────────────────────────┘
```

---

## 2. DDL SQL Lengkap

### 2.1 Tabel `supplier`

```sql
CREATE TABLE IF NOT EXISTS supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    kontak TEXT,
    alamat TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_supplier_nama ON supplier(nama);
```

### 2.2 Tabel `pembelian` (Header)

```sql
CREATE TABLE IF NOT EXISTS pembelian (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    nomor_transaksi TEXT NOT NULL UNIQUE,
    tanggal DATE NOT NULL DEFAULT CURRENT_DATE,
    catatan TEXT,
    total REAL NOT NULL DEFAULT 0,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_pembelian_tanggal ON pembelian(tanggal);
CREATE INDEX idx_pembelian_supplier ON pembelian(supplier_id);
CREATE INDEX idx_pembelian_nomor ON pembelian(nomor_transaksi);
```

### 2.3 Tabel `pembelian_detail` (Baris)

```sql
CREATE TABLE IF NOT EXISTS pembelian_detail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pembelian_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    qty REAL NOT NULL CHECK(qty > 0),
    harga_beli REAL NOT NULL CHECK(harga_beli >= 0),
    subtotal REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pembelian_id) REFERENCES pembelian(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE RESTRICT
);

CREATE INDEX idx_pembelian_detail_pembelian ON pembelian_detail(pembelian_id);
CREATE INDEX idx_pembelian_detail_item ON pembelian_detail(item_id);
```

### 2.4 Tabel `penjualan` (Header)

```sql
CREATE TABLE IF NOT EXISTS penjualan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pelanggan_id INTEGER NOT NULL,
    nomor_transaksi TEXT NOT NULL UNIQUE,
    tanggal DATE NOT NULL DEFAULT CURRENT_DATE,
    catatan TEXT,
    total REAL NOT NULL DEFAULT 0,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pelanggan_id) REFERENCES pelanggan(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_penjualan_tanggal ON penjualan(tanggal);
CREATE INDEX idx_penjualan_pelanggan ON penjualan(pelanggan_id);
CREATE INDEX idx_penjualan_nomor ON penjualan(nomor_transaksi);
```

### 2.5 Tabel `penjualan_detail` (Baris)

```sql
CREATE TABLE IF NOT EXISTS penjualan_detail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    penjualan_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    qty REAL NOT NULL CHECK(qty > 0),
    harga_jual REAL NOT NULL CHECK(harga_jual >= 0),
    harga_pokok REAL NOT NULL CHECK(harga_pokok >= 0),
    subtotal REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (penjualan_id) REFERENCES penjualan(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE RESTRICT
);

CREATE INDEX idx_penjualan_detail_penjualan ON penjualan_detail(penjualan_id);
CREATE INDEX idx_penjualan_detail_item ON penjualan_detail(item_id);
```

### 2.6 Tabel `stok_mutasi` (Kartu Stok / Ledger)

```sql
CREATE TABLE IF NOT EXISTS stok_mutasi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    jenis_mutasi TEXT NOT NULL CHECK(jenis_mutasi IN ('IN', 'OUT')),
    qty REAL NOT NULL,
    harga REAL NOT NULL,
    saldo_berjalan REAL NOT NULL,
    referensi_tipe TEXT NOT NULL CHECK(referensi_tipe IN ('pembelian', 'penjualan')),
    referensi_id INTEGER NOT NULL,
    nomor_referensi TEXT NOT NULL,
    tanggal DATE NOT NULL DEFAULT CURRENT_DATE,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);

CREATE INDEX idx_stok_mutasi_item ON stok_mutasi(item_id);
CREATE INDEX idx_stok_mutasi_tanggal ON stok_mutasi(tanggal);
CREATE INDEX idx_stok_mutasi_referensi ON stok_mutasi(referensi_tipe, referensi_id);
CREATE INDEX idx_stok_mutasi_nomor ON stok_mutasi(nomor_referensi);
```

### 2.7 Tabel `stok_akhir` (Cache Saldo Terakhir — Optional)

```sql
CREATE TABLE IF NOT EXISTS stok_akhir (
    item_id INTEGER PRIMARY KEY,
    qty_akhir REAL NOT NULL DEFAULT 0,
    harga_pokok_rata REAL NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);

CREATE INDEX idx_stok_akhir_item ON stok_akhir(item_id);
```

---

## 3. Logika Kartu Stok (`stok_mutasi`)

### 3.1 Konsep

`stok_mutasi` adalah **ledger append-only** yang mencatat setiap perubahan stok. Tabel ini menjadi **sumber kebenaran** untuk:
- Saldo stok saat ini
- Riwayat mutasi per item
- Audit trail

### 3.2 Struktur Data

| Field | Tipe | Keterangan |
|-------|------|------------|
| `id` | INTEGER PK | Auto-increment |
| `item_id` | INTEGER FK | Item yang dimutasi |
| `jenis_mutasi` | TEXT | `IN` (pembelian) atau `OUT` (penjualan) |
| `qty` | REAL | Jumlah mutasi (selalu positif) |
| `harga` | REAL | Harga per unit saat transaksi |
| `saldo_berjalan` | REAL | Saldo stok setelah mutasi ini |
| `referensi_tipe` | TEXT | `pembelian` atau `penjualan` |
| `referensi_id` | INTEGER | ID di tabel header |
| `nomor_referensi` | TEXT | Nomor transaksi (PB-2026-0001) |
| `tanggal` | DATE | Tanggal transaksi |
| `created_by` | INTEGER FK | User yang membuat |
| `created_at` | TIMESTAMP | Waktu pencatatan |

### 3.3 Cara Hitung Saldo Berjalan

```python
def hitung_saldo_berjalan(item_id, jenis_mutasi, qty):
    """
    Hitung saldo berjalan untuk kartu stok.
    
    Args:
        item_id: ID item
        jenis_mutasi: 'IN' atau 'OUT'
        qty: jumlah mutasi (selalu positif)
    
    Returns:
        saldo_berjalan: saldo setelah mutasi ini
    """
    # Ambil saldo terakhir dari stok_mutasi
    saldo_terakhir = db.execute(
        "SELECT saldo_berjalan FROM stok_mutasi "
        "WHERE item_id = ? ORDER BY id DESC LIMIT 1",
        (item_id,)
    ).fetchone()
    
    saldo_sebelumnya = saldo_terakhir['saldo_berjalan'] if saldo_terakhir else 0
    
    if jenis_mutasi == 'IN':
        saldo_berjalan = saldo_sebelumnya + qty
    else:  # OUT
        saldo_berjalan = saldo_sebelumnya - qty
    
    return saldo_berjalan
```

### 3.4 Contoh Data Kartu Stok

| id | item_id | jenis | qty | harga | saldo_berjalan | referensi | nomor |
|----|---------|-------|-----|-------|----------------|-----------|-------|
| 1 | 1 | IN | 100 | 50000 | 100 | pembelian | PB-2026-0001 |
| 2 | 1 | OUT | 20 | 50000 | 80 | penjualan | PJ-2026-0001 |
| 3 | 1 | IN | 50 | 55000 | 130 | pembelian | PB-2026-0002 |
| 4 | 1 | OUT | 30 | 55000 | 100 | penjualan | PJ-2026-0002 |

---

## 4. Strategi HPP Moving Average

### 4.1 Formula

```
HPP_baru = (Saldo_lama × HPP_lama + Qty_beli × Harga_beli) / (Saldo_lama + Qty_beli)
```

### 4.2 Kapan Dihitung Ulang

HPP dihitung ulang **setiap ada pembelian** (stok masuk). Perhitungan ini:
1. Ambil saldo stok dan HPP saat ini dari `stok_akhir`
2. Hitung HPP baru dengan formula moving average
3. Update `stok_akhir` dengan nilai baru

### 4.3 Cara Snapshot di `penjualan_detail`

Saat penjualan dibuat:
1. Ambil HPP saat ini dari `stok_akhir`
2. Simpan HPP ini di kolom `harga_pokok` di `penjualan_detail`
3. HPP ini **tidak berubah** meski ada pembelian setelahnya

### 4.4 Contoh Perhitungan

```
Keadaan awal: Saldo = 100, HPP = 50.000

Pembelian 1: Qty = 50, Harga = 55.000
HPP_baru = (100 × 50.000 + 50 × 55.000) / (100 + 50)
         = (5.000.000 + 2.750.000) / 150
         = 7.750.000 / 150
         = 51.667

Penjualan 1: Qty = 30
- HPP snapshot = 51.667 (dari stok_akhir)
- Saldo berkurang menjadi 120
- HPP tetap 51.667 (tidak berubah karena penjualan)

Pembelian 2: Qty = 100, Harga = 60.000
HPP_baru = (120 × 51.667 + 100 × 60.000) / (120 + 100)
         = (6.200.040 + 6.000.000) / 220
         = 12.200.040 / 220
         = 55.455
```

### 4.5 Pseudocode Implementasi

```python
def hitung_hpp_moving_average(item_id, qty_beli, harga_beli):
    """
    Hitung HPP moving average setelah pembelian.
    """
    # Ambil data stok akhir
    stok_akhir = db.execute(
        "SELECT qty_akhir, harga_pokok_rata FROM stok_akhir WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    
    if stok_akhir is None:
        # Item belum ada di stok_akhir, inisialisasi
        qty_akhir_lama = 0
        hpp_lama = 0
    else:
        qty_akhir_lama = stok_akhir['qty_akhir']
        hpp_lama = stok_akhir['harga_pokok_rata']
    
    # Hitung HPP baru
    if qty_akhir_lama + qty_beli == 0:
        hpp_baru = 0
    else:
        hpp_baru = ((qty_akhir_lama * hpp_lama) + (qty_beli * harga_beli)) / (qty_akhir_lama + qty_beli)
    
    return hpp_baru

def update_stok_akhir_setelah_pembelian(item_id, qty_beli, harga_beli):
    """
    Update stok_akhir setelah pembelian.
    """
    hpp_baru = hitung_hpp_moving_average(item_id, qty_beli, harga_beli)
    
    # Ambil qty akhir saat ini
    stok_akhir = db.execute(
        "SELECT qty_akhir FROM stok_akhir WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    
    qty_akhir_lama = stok_akhir['qty_akhir'] if stok_akhir else 0
    qty_akhir_baru = qty_akhir_lama + qty_beli
    
    # Upsert stok_akhir
    db.execute('''
        INSERT INTO stok_akhir (item_id, qty_akhir, harga_pokok_rata, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(item_id) DO UPDATE SET
            qty_akhir = excluded.qty_akhir,
            harga_pokok_rata = excluded.harga_pokok_rata,
            updated_at = CURRENT_TIMESTAMP
    ''', (item_id, qty_akhir_baru, hpp_baru))
```

---

## 5. Validasi Stok Negatif

### 5.1 Level Validasi

Validasi dilakukan di **dua level**:

| Level | Cara | Tujuan |
|-------|------|--------|
| **Database** | `CHECK(qty > 0)` di detail, `CHECK(saldo_berjalan >= 0)` di stok_mutasi | Last line of defense |
| **Aplikasi** | Validasi sebelum INSERT, pesan error jelas | User experience |

### 5.2 Validasi di Level Aplikasi

```python
def validasi_stok_cukup(item_id, qty_diminta):
    """
    Cek apakah stok cukup untuk penjualan.
    
    Returns:
        (bool, str): (cukup, pesan_error)
    """
    # Ambil saldo terakhir dari stok_mutasi
    saldo = db.execute(
        "SELECT saldo_berjalan FROM stok_mutasi "
        "WHERE item_id = ? ORDER BY id DESC LIMIT 1",
        (item_id,)
    ).fetchone()
    
    saldo_akhir = saldo['saldo_berjalan'] if saldo else 0
    
    if saldo_akhir < qty_diminta:
        return False, f"Stok tidak cukup. Tersedia: {saldo_akhir}, Diminta: {qty_diminta}"
    
    return True, ""
```

### 5.3 Validasi di Level Database

```sql
-- Constraint di stok_mutasi
CHECK(saldo_berjalan >= 0)

-- Atau trigger untuk validasi tambahan
CREATE TRIGGER IF NOT EXISTS trg_validasi_stok_negatif
BEFORE INSERT ON stok_mutasi
BEGIN
    SELECT CASE
        WHEN NEW.saldo_berjalan < 0 THEN
            RAISE(ABORT, 'Stok tidak boleh negatif')
    END;
END;
```

### 5.4 Alur Validasi di Aplikasi

```
1. User input penjualan
2. Untuk setiap item:
   a. Ambil saldo terakhir dari stok_mutasi
   b. Cek saldo >= qty_diminta
   c. Jika tidak cukup → tampilkan error, batalkan transaksi
3. Jika semua valid → lanjut ke proses INSERT
```

---

## 6. Atomicity Strategy

### 6.1 Konsep

Semua transaksi (pembelian/penjualan) harus **atomic**:
- Semua operasi berhasil → COMMIT
- Ada yang gagal → ROLLBACK (tidak ada perubahan setengah jadi)

### 6.2 Implementasi dengan SQLite

```python
import sqlite3

def buat_pembelian_atomic(data_pembelian, detail_pembelian, user_id):
    """
    Buat transaksi pembelian secara atomic.
    """
    db = get_db()
    
    try:
        # BEGIN IMMEDIATE — kunci database sejak awal
        db.execute("BEGIN IMMEDIATE")
        
        # 1. Insert header pembelian
        nomor = generate_nomor_transaksi('PB')
        cursor = db.execute('''
            INSERT INTO pembelian (supplier_id, nomor_transaksi, tanggal, catatan, total, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data_pembelian['supplier_id'], nomor, data_pembelian['tanggal'],
              data_pembelian['catatan'], data_pembelian['total'], user_id))
        
        pembelian_id = cursor.lastrowid
        
        # 2. Insert detail pembelian
        for detail in detail_pembelian:
            db.execute('''
                INSERT INTO pembelian_detail (pembelian_id, item_id, qty, harga_beli, subtotal)
                VALUES (?, ?, ?, ?, ?)
            ''', (pembelian_id, detail['item_id'], detail['qty'],
                  detail['harga_beli'], detail['subtotal']))
            
            # 3. Hitung HPP moving average
            hpp_baru = hitung_hpp_moving_average(detail['item_id'], detail['qty'], detail['harga_beli'])
            
            # 4. Update stok_akhir
            update_stok_akhir_setelah_pembelian(detail['item_id'], detail['qty'], detail['harga_beli'])
            
            # 5. Insert ke stok_mutasi
            saldo_berjalan = hitung_saldo_berjalan(detail['item_id'], 'IN', detail['qty'])
            db.execute('''
                INSERT INTO stok_mutasi (item_id, jenis_mutasi, qty, harga, saldo_berjalan,
                                         referensi_tipe, referensi_id, nomor_referensi, tanggal, created_by)
                VALUES (?, 'IN', ?, ?, ?, 'pembelian', ?, ?, ?, ?)
            ''', (detail['item_id'], detail['qty'], detail['harga_beli'], saldo_berjalan,
                  pembelian_id, nomor, data_pembelian['tanggal'], user_id))
        
        # Semua berhasil → COMMIT
        db.commit()
        return True, nomor
        
    except Exception as e:
        # Ada yang gagal → ROLLBACK
        db.rollback()
        return False, str(e)
```

### 6.3 Pola yang Digunakan

| Pola | Keterangan |
|------|------------|
| `BEGIN IMMEDIATE` | Kunci database sejak awal transaksi |
| `try/except` | Tangkap semua error |
| `db.commit()` | Simpan jika semua berhasil |
| `db.rollback()` | Batalkan jika ada error |
| `ON DELETE RESTRICT` | Cegah delete yang merusak integritas |
| `ON DELETE CASCADE` | Hapus detail jika header dihapus |

### 6.4 Savepoint untuk Transaksi Kompleks

Jika ada transaksi yang sangat kompleks (misal: retur penjualan), bisa pakai savepoint:

```python
def buat_retur_penjualan_atomic(retur_data):
    db = get_db()
    
    try:
        db.execute("BEGIN IMMEDIATE")
        
        # Savepoint untuk retur
        db.execute("SAVEPOINT retur_penjualan")
        
        # Proses retur...
        
        db.execute("RELEASE retur_penjualan")
        db.commit()
        
    except Exception as e:
        db.execute("ROLLBACK TO retur_penjualan")
        db.execute("RELEASE retur_penjualan")
        db.rollback()
        raise
```

---

## 7. Nomor Transaksi Otomatis

### 7.1 Format

- Pembelian: `PB-YYYY-NNNN` (contoh: `PB-2026-0001`)
- Penjualan: `PJ-YYYY-NNNN` (contoh: `PJ-2026-0001`)

### 7.2 Implementasi

```python
def generate_nomor_transaksi(prefix):
    """
    Generate nomor transaksi otomatis.
    
    Args:
        prefix: 'PB' atau 'PJ'
    
    Returns:
        nomor_transaksi: string seperti 'PB-2026-0001'
    """
    from datetime import datetime
    
    tahun = datetime.now().year
    pattern = f"{prefix}-{tahun}-%"
    
    # Ambil nomor terakhir
    terakhir = db.execute(
        "SELECT nomor_transaksi FROM pembelian WHERE nomor_transaksi LIKE ? ORDER BY nomor_transaksi DESC LIMIT 1",
        (pattern,)
    ).fetchone()
    
    if terakhir:
        # Extract nomor urut terakhir
        nomor_urut = int(terakhir['nomor_transaksi'].split('-')[-1]) + 1
    else:
        nomor_urut = 1
    
    return f"{prefix}-{tahun}-{nomor_urut:04d}"
```

---

## 8. Estimasi Kompleksitas per Tabel

| Tabel | Jumlah Field | Constraint | Index | Kompleksitas |
|-------|--------------|------------|-------|--------------|
| `supplier` | 6 | 1 FK | 1 | Rendah |
| `pembelian` | 8 | 2 FK, 1 UNIQUE | 3 | Sedang |
| `pembelian_detail` | 7 | 2 FK, 2 CHECK | 2 | Sedang |
| `penjualan` | 8 | 2 FK, 1 UNIQUE | 3 | Sedang |
| `penjualan_detail` | 8 | 2 FK, 3 CHECK | 2 | Sedang |
| `stok_mutasi` | 12 | 2 FK, 2 CHECK | 4 | Tinggi |
| `stok_akhir` | 4 | 1 FK | 1 | Rendah |

**Total:** 7 tabel baru, 53 field, 14 constraint, 16 index

---

## 9. Ringkasan Aturan Bisnis

| Aturan | Implementasi |
|--------|--------------|
| Stok berkurang saat penjualan | `stok_mutasi` dengan `jenis_mutasi = 'OUT'` |
| Stok bertambah saat pembelian | `stok_mutasi` dengan `jenis_mutasi = 'IN'` |
| Tidak bisa jual melebihi stok | Validasi aplikasi + `CHECK(saldo_berjalan >= 0)` |
| Atomicity | `BEGIN IMMEDIATE` + `try/except` + `commit/rollback` |
| HPP moving average | Dihitung ulang tiap pembelian, disimpan di `stok_akhir` |
| HPP snapshot | Disimpan di `penjualan_detail.harga_pokok` |
| Nomor transaksi otomatis | `generate_nomor_transaksi()` dengan format `PREFIX-YYYY-NNNN` |

---

## 10. Langkah Selanjutnya (Fase 2+)

1. **Fase 2:** Implementasi supplier + pembelian
2. **Fase 3:** Implementasi penjualan + validasi stok
3. **Fase 4:** Implementasi kartu stok + laporan
4. **Fase 5:** RBAC untuk menu baru
5. **Fase 6:** Seed data awal
6. **Fase 7:** Test atomicity + deploy

---

**Catatan:** Desain ini belum diimplementasikan. User perlu review sebelum lanjut ke Fase 2.
