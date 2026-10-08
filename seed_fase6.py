"""Seed data Fase 6 — idempotent.
1. Sync stok_akhir dari stok_mutasi (semua item)
2. Tambah pembelian untuk item yang belum punya stok (minimal 5 item)
3. Buat 3 transaksi penjualan contoh (jika belum ada)
4. Hapus user test_kasir/test_gudang (bukan user produksi)
"""
import sqlite3
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, get_db, init_db
from werkzeug.security import generate_password_hash

def seed_stok_akhir(db):
    """Sync stok_akhir dari stok_mutasi untuk semua item."""
    rows = db.execute('''
        SELECT item_id,
               SUM(CASE WHEN jenis_mutasi = 'IN' THEN qty ELSE -qty END) as total_qty
        FROM stok_mutasi
        GROUP BY item_id
    ''').fetchall()
    
    for row in rows:
        item_id = row['item_id']
        total_qty = row['total_qty'] or 0
        
        avg = db.execute('''
            SELECT AVG(harga) as avg_harga
            FROM stok_mutasi
            WHERE item_id = ? AND jenis_mutasi = 'IN' AND qty > 0
        ''', (item_id,)).fetchone()
        avg_harga = avg['avg_harga'] if avg and avg['avg_harga'] else 0
        
        db.execute('''
            INSERT INTO stok_akhir (item_id, qty_akhir, harga_pokok_rata, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(item_id) DO UPDATE SET
                qty_akhir = excluded.qty_akhir,
                harga_pokok_rata = excluded.harga_pokok_rata,
                updated_at = CURRENT_TIMESTAMP
        ''', (item_id, total_qty, avg_harga))
    
    db.commit()
    print(f"  ✅ stok_akhir di-sync: {len(rows)} item")

def seed_pembelian_tambahan(db):
    """Tambah pembelian untuk item yang belum punya stok."""
    # Cari item yang belum punya mutasi stok
    items_tanpa_stok = db.execute('''
        SELECT i.id, i.nama, i.harga_pokok
        FROM items i
        LEFT JOIN stok_mutasi sm ON sm.item_id = i.id
        WHERE sm.id IS NULL
        LIMIT 5
    ''').fetchall()
    
    if not items_tanpa_stok:
        print("  ⚠️ semua item sudah punya stok, skip")
        return
    
    # Ambil supplier
    supplier = db.execute('SELECT id FROM supplier LIMIT 1').fetchone()
    if not supplier:
        print("  ⚠️ tidak ada supplier, skip")
        return
    
    # Ambil user admin
    admin = db.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin:
        print("  ⚠️ user admin tidak ditemukan, skip")
        return
    
    today = date.today()
    
    # Cari nomor pembelian terakhir
    last_pb = db.execute("SELECT nomor_transaksi FROM pembelian ORDER BY nomor_transaksi DESC LIMIT 1").fetchone()
    pb_num = 1
    if last_pb and last_pb['nomor_transaksi']:
        try:
            pb_num = int(last_pb['nomor_transaksi'].split('-')[-1]) + 1
        except:
            pb_num = 1
    
    for i, item in enumerate(items_tanpa_stok):
        tanggal = today - timedelta(days=i+1)
        nomor = f"PB-2026-{pb_num:04d}"
        pb_num += 1
        qty = 20 + i * 5
        harga_beli = item['harga_pokok'] if item['harga_pokok'] > 0 else 5000
        subtotal = qty * harga_beli
        
        # Insert pembelian
        db.execute('''
            INSERT INTO pembelian (supplier_id, nomor_transaksi, tanggal, catatan, total, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (supplier['id'], nomor, tanggal, f"Pembelian awal {item['nama']}", subtotal, admin['id']))
        
        pembelian_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Insert pembelian_detail
        db.execute('''
            INSERT INTO pembelian_detail (pembelian_id, item_id, qty, harga_beli, subtotal)
            VALUES (?, ?, ?, ?, ?)
        ''', (pembelian_id, item['id'], qty, harga_beli, subtotal))
        
        # Insert stok_mutasi IN
        db.execute('''
            INSERT INTO stok_mutasi (item_id, jenis_mutasi, qty, harga, saldo_berjalan,
                                     referensi_tipe, referensi_id, nomor_referensi, tanggal, created_by)
            VALUES (?, 'IN', ?, ?, ?, 'pembelian', ?, ?, ?, ?)
        ''', (item['id'], qty, harga_beli, qty, pembelian_id, nomor, tanggal, admin['id']))
        
        # Insert stok_akhir
        db.execute('''
            INSERT INTO stok_akhir (item_id, qty_akhir, harga_pokok_rata, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(item_id) DO UPDATE SET
                qty_akhir = excluded.qty_akhir,
                harga_pokok_rata = excluded.harga_pokok_rata,
                updated_at = CURRENT_TIMESTAMP
        ''', (item['id'], qty, harga_beli))
    
    db.commit()
    print(f"  ✅ {len(items_tanpa_stok)} pembelian tambahan dibuat")

def seed_penjualan(db):
    """Buat 3 transaksi penjualan contoh jika belum ada."""
    existing = db.execute('SELECT COUNT(*) FROM penjualan').fetchone()[0]
    if existing > 0:
        print(f"  ⚠️ penjualan sudah ada ({existing}), skip")
        return
    
    # Ambil item dengan stok cukup
    items = db.execute('''
        SELECT sa.item_id, i.nama, sa.qty_akhir, sa.harga_pokok_rata
        FROM stok_akhir sa
        JOIN items i ON i.id = sa.item_id
        WHERE sa.qty_akhir >= 10
        ORDER BY sa.qty_akhir DESC
        LIMIT 5
    ''').fetchall()
    
    if len(items) < 3:
        print(f"  ⚠️ hanya {len(items)} item dengan stok >= 10, buat {len(items)} penjualan")
    
    if not items:
        print("  ⚠️ tidak ada item dengan stok, skip")
        return
    
    # Ambil pelanggan
    pelanggan = db.execute('SELECT id, nama FROM pelanggan LIMIT 3').fetchall()
    if not pelanggan:
        print("  ⚠️ tidak ada pelanggan, skip")
        return
    
    # Ambil user admin
    admin = db.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not admin:
        print("  ⚠️ user admin tidak ditemukan, skip")
        return
    
    today = date.today()
    num_trans = min(3, len(items))
    
    for i in range(num_trans):
        item = items[i]
        pel = pelanggan[i % len(pelanggan)]
        tanggal = today - timedelta(days=i)
        nomor = f"PJ-2026-{i+1:04d}"
        
        # Harga jual = pokok + 20% margin
        harga_jual = int(item['harga_pokok_rata'] * 1.2) if item['harga_pokok_rata'] > 0 else 10000
        qty = min(5, int(item['qty_akhir'] / 2))
        if qty < 1:
            qty = 1
        subtotal = qty * harga_jual
        
        # Insert penjualan
        db.execute('''
            INSERT INTO penjualan (pelanggan_id, nomor_transaksi, tanggal, catatan, total, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (pel['id'], nomor, tanggal, f"Penjualan contoh {i+1}", subtotal, admin['id']))
        
        penjualan_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        
        # Insert penjualan_detail
        db.execute('''
            INSERT INTO penjualan_detail (penjualan_id, item_id, qty, harga_jual, harga_pokok, subtotal)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (penjualan_id, item['item_id'], qty, harga_jual, item['harga_pokok_rata'], subtotal))
        
        # Kurangi stok_akhir
        db.execute('''
            UPDATE stok_akhir SET qty_akhir = qty_akhir - ?, updated_at = CURRENT_TIMESTAMP
            WHERE item_id = ?
        ''', (qty, item['item_id']))
        
        # Hitung saldo_berjalan
        saldo = db.execute('''
            SELECT COALESCE(SUM(CASE WHEN jenis_mutasi = 'IN' THEN qty ELSE -qty END), 0) as saldo
            FROM stok_mutasi WHERE item_id = ?
        ''', (item['item_id'],)).fetchone()['saldo']
        saldo_baru = saldo - qty
        
        # Insert stok_mutasi OUT
        db.execute('''
            INSERT INTO stok_mutasi (item_id, jenis_mutasi, qty, harga, saldo_berjalan,
                                     referensi_tipe, referensi_id, nomor_referensi, tanggal, created_by)
            VALUES (?, 'OUT', ?, ?, ?, 'penjualan', ?, ?, ?, ?)
        ''', (item['item_id'], qty, item['harga_pokok_rata'], saldo_baru,
              penjualan_id, nomor, tanggal, admin['id']))
    
    db.commit()
    print(f"  ✅ {num_trans} transaksi penjualan dibuat")

def cleanup_test_users(db):
    """Hapus user test_kasir dan test_gudang."""
    db.execute("DELETE FROM users WHERE username IN ('test_kasir', 'test_gudang')")
    db.commit()
    print("  ✅ user test_kasir dan test_gudang dihapus")

if __name__ == '__main__':
    print("=== Seed Fase 6 ===")
    with app.app_context():
        init_db()
        db = get_db()
        
        print("1. Sync stok_akhir...")
        seed_stok_akhir(db)
        
        print("2. Seed pembelian tambahan...")
        seed_pembelian_tambahan(db)
        
        print("3. Seed penjualan...")
        seed_penjualan(db)
        
        print("4. Cleanup test users...")
        cleanup_test_users(db)
        
        # Verifikasi
        print("\n=== Verifikasi ===")
        for t in ['items', 'kategori', 'pelanggan', 'supplier', 'roles', 'users', 'pembelian', 'penjualan', 'stok_mutasi', 'stok_akhir']:
            c = db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
            print(f"  {t}: {c}")
        
        print("\n=== Seed Fase 6 selesai ===")
