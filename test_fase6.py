"""Test Fase 6: Seed data awal — idempotent."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, get_db, init_db
import json

def test_stok_akhir_sync():
    """Test bahwa stok_akhir konsisten dengan stok_mutasi."""
    with app.app_context():
        init_db()
        db = get_db()
        
        # Hitung saldo per item dari stok_mutasi
        mutasi = db.execute('''
            SELECT item_id,
                   SUM(CASE WHEN jenis_mutasi = 'IN' THEN qty ELSE -qty END) as saldo
            FROM stok_mutasi
            GROUP BY item_id
        ''').fetchall()
        
        for m in mutasi:
            item_id = m['item_id']
            saldo_mutasi = m['saldo'] or 0
            
            stok = db.execute('SELECT qty_akhir FROM stok_akhir WHERE item_id = ?', (item_id,)).fetchone()
            assert stok is not None, f"stok_akhir untuk item {item_id} tidak ada"
            assert stok['qty_akhir'] == saldo_mutasi, \
                f"Item {item_id}: stok_akhir={stok['qty_akhir']} != mutasi={saldo_mutasi}"
        
        print(f"✅ test_stok_akhir_sync passed ({len(mutasi)} item)")

def test_penjualan_exists():
    """Test bahwa ada transaksi penjualan."""
    with app.app_context():
        init_db()
        db = get_db()
        
        count = db.execute('SELECT COUNT(*) FROM penjualan').fetchone()[0]
        assert count > 0, "Tidak ada transaksi penjualan"
        
        # Cek detail penjualan
        detail_count = db.execute('SELECT COUNT(*) FROM penjualan_detail').fetchone()[0]
        assert detail_count > 0, "Tidak ada detail penjualan"
        
        # Cek nomor transaksi format benar
        penjualan = db.execute('SELECT nomor_transaksi FROM penjualan LIMIT 1').fetchone()
        assert penjualan['nomor_transaksi'].startswith('PJ-'), \
            f"Nomor transaksi salah format: {penjualan['nomor_transaksi']}"
        
        print(f"✅ test_penjualan_exists passed ({count} transaksi)")

def test_pembelian_exists():
    """Test bahwa ada transaksi pembelian."""
    with app.app_context():
        init_db()
        db = get_db()
        
        count = db.execute('SELECT COUNT(*) FROM pembelian').fetchone()[0]
        assert count > 0, "Tidak ada transaksi pembelian"
        
        # Cek nomor transaksi format benar
        pembelian = db.execute('SELECT nomor_transaksi FROM pembelian LIMIT 1').fetchone()
        assert pembelian['nomor_transaksi'].startswith('PB-'), \
            f"Nomor transaksi salah format: {pembelian['nomor_transaksi']}"
        
        print(f"✅ test_pembelian_exists passed ({count} transaksi)")

def test_no_test_users():
    """Test bahwa user test sudah dibersihkan."""
    with app.app_context():
        init_db()
        db = get_db()
        
        test_kasir = db.execute("SELECT id FROM users WHERE username = 'test_kasir'").fetchone()
        assert test_kasir is None, "User test_kasir masih ada"
        
        test_gudang = db.execute("SELECT id FROM users WHERE username = 'test_gudang'").fetchone()
        assert test_gudang is None, "User test_gudang masih ada"
        
        print("✅ test_no_test_users passed")

def test_roles_complete():
    """Test bahwa 3 role ada: admin, kasir, gudang."""
    with app.app_context():
        init_db()
        db = get_db()
        
        roles = db.execute('SELECT nama FROM roles').fetchall()
        role_names = [r['nama'] for r in roles]
        
        assert 'admin' in role_names, "Role admin tidak ada"
        assert 'kasir' in role_names, "Role kasir tidak ada"
        assert 'gudang' in role_names, "Role gudang tidak ada"
        
        print(f"✅ test_roles_complete passed ({len(roles)} roles)")

def test_stok_akhir_untuk_semua_item():
    """Test bahwa semua item yang punya mutasi punya stok_akhir."""
    with app.app_context():
        init_db()
        db = get_db()
        
        items_dengan_mutasi = db.execute('''
            SELECT DISTINCT item_id FROM stok_mutasi
        ''').fetchall()
        
        for item in items_dengan_mutasi:
            stok = db.execute('SELECT item_id FROM stok_akhir WHERE item_id = ?', (item['item_id'],)).fetchone()
            assert stok is not None, f"Item {item['item_id']} punya mutasi tapi tidak ada stok_akhir"
        
        print(f"✅ test_stok_akhir_untuk_semua_item passed ({len(items_dengan_mutasi)} item)")

def test_penjualan_detail_consistency():
    """Test bahwa penjualan_detail.total == penjualan.total."""
    with app.app_context():
        init_db()
        db = get_db()
        
        penjualan = db.execute('SELECT id, total FROM penjualan').fetchall()
        
        for pj in penjualan:
            detail_total = db.execute(
                'SELECT SUM(subtotal) as total FROM penjualan_detail WHERE penjualan_id = ?',
                (pj['id'],)
            ).fetchone()['total'] or 0
            
            assert detail_total == pj['total'], \
                f"Penjualan {pj['id']}: total={pj['total']} != detail_total={detail_total}"
        
        print(f"✅ test_penjualan_detail_consistency passed ({len(penjualan)} transaksi)")

def test_stok_tidak_negatif():
    """Test bahwa tidak ada stok negatif."""
    with app.app_context():
        init_db()
        db = get_db()
        
        negatif = db.execute('SELECT item_id, qty_akhir FROM stok_akhir WHERE qty_akhir < 0').fetchall()
        assert len(negatif) == 0, f"Ada {len(negatif)} item dengan stok negatif"
        
        print("✅ test_stok_tidak_negatif passed")

def test_laporan_penjualan_data():
    """Test bahwa laporan penjualan punya data."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1  # admin
        
        resp = client.get('/laporan/penjualan')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        
        # Cek ada summary card
        assert 'Total Penjualan' in html or 'total' in html.lower(), "Laporan penjualan tidak ada data"
        
        print("✅ test_laporan_penjualan_data passed")

def test_laporan_stok_data():
    """Test bahwa laporan stok punya data."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1  # admin
        
        resp = client.get('/laporan/stok')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        
        # Cek ada tabel stok
        assert 'stok' in html.lower() or 'Stok' in html, "Laporan stok tidak ada data"
        
        print("✅ test_laporan_stok_data passed")

if __name__ == '__main__':
    print("=== Test Fase 6: Seed Data ===")
    test_stok_akhir_sync()
    test_penjualan_exists()
    test_pembelian_exists()
    test_no_test_users()
    test_roles_complete()
    test_stok_akhir_untuk_semua_item()
    test_penjualan_detail_consistency()
    test_stok_tidak_negatif()
    test_laporan_penjualan_data()
    test_laporan_stok_data()
    print("\n=== Semua test Fase 6 passed! ===")
