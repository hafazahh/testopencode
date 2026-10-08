"""Test Fase 7: Atomicity + validasi stok negatif."""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_db

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['SESSION_COOKIE_SECURE'] = False

init_db()
client = app.test_client()

def get_csrf(response):
    """Extract CSRF token from response."""
    for line in response.data.decode().split('\n'):
        if 'name="csrf_token"' in line:
            match = re.search(r'value="([^"]+)"', line)
            if match:
                return match.group(1)
    return None

def login():
    """Login sebagai admin."""
    resp = client.get('/login')
    csrf = get_csrf(resp)
    resp = client.post('/login', data={
        'csrf_token': csrf,
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    return resp

def test(name, condition, detail=""):
    status = "✅" if condition else "❌"
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    return condition

print("=" * 60)
print("FASE 7 TEST: Atomicity + Validasi Stok")
print("=" * 60)

# Login
print("\n[1] LOGIN")
resp = login()
test("Login berhasil", resp.status_code == 200, f"status={resp.status_code}")

# Get item dengan stok cukup
from app import get_db
with app.app_context():
    db = get_db()
    item = db.execute('''
        SELECT sa.item_id, sa.qty_akhir, sa.harga_pokok_rata
        FROM stok_akhir sa
        WHERE sa.qty_akhir >= 10
        LIMIT 1
    ''').fetchone()
    pelanggan = db.execute('SELECT id FROM pelanggan LIMIT 1').fetchone()

item_id = item['item_id']
stok_awal = item['qty_akhir']
pelanggan_id = pelanggan['id']

# Test 1: Penjualan gagal (melebihi stok) → rollback
print("\n[2] ATOMICITY: Penjualan gagal → rollback")
with app.app_context():
    db = get_db()
    mutasi_awal = db.execute('SELECT COUNT(*) FROM stok_mutasi WHERE item_id = ?', (item_id,)).fetchone()[0]

resp = client.get('/penjualan/create')
csrf = get_csrf(resp)
resp = client.post('/penjualan/create', data={
    'csrf_token': csrf,
    'pelanggan_id': pelanggan_id,
    'tanggal': '2026-10-08',
    'catatan': 'Test atomicity',
    'item_id[]': [str(item_id)],
    'qty[]': ['99999'],
    'harga_jual[]': ['10000'],
}, follow_redirects=True)

with app.app_context():
    db = get_db()
    stok_akhir = db.execute('SELECT qty_akhir FROM stok_akhir WHERE item_id = ?', (item_id,)).fetchone()
    mutasi_akhir = db.execute('SELECT COUNT(*) FROM stok_mutasi WHERE item_id = ?', (item_id,)).fetchone()[0]

test("Stok tidak berubah setelah rollback", stok_akhir['qty_akhir'] == stok_awal, f"{stok_awal} → {stok_akhir['qty_akhir']}")
test("Tidak ada mutasi baru", mutasi_akhir == mutasi_awal, f"{mutasi_awal} → {mutasi_akhir}")

# Test 2: Pembelian gagal (qty negatif) → rollback
print("\n[3] ATOMICITY: Pembelian gagal → rollback")
with app.app_context():
    db = get_db()
    supplier = db.execute('SELECT id FROM supplier LIMIT 1').fetchone()
    mutasi_awal = db.execute('SELECT COUNT(*) FROM stok_mutasi WHERE item_id = ?', (item_id,)).fetchone()[0]

resp = client.get('/pembelian/create')
csrf = get_csrf(resp)
resp = client.post('/pembelian/create', data={
    'csrf_token': csrf,
    'supplier_id': supplier['id'],
    'tanggal': '2026-10-08',
    'catatan': 'Test atomicity',
    'item_id[]': [str(item_id)],
    'qty[]': ['-5'],
    'harga_beli[]': ['10000'],
}, follow_redirects=True)

with app.app_context():
    db = get_db()
    mutasi_akhir = db.execute('SELECT COUNT(*) FROM stok_mutasi WHERE item_id = ?', (item_id,)).fetchone()[0]

test("Tidak ada mutasi baru", mutasi_akhir == mutasi_awal, f"{mutasi_awal} → {mutasi_akhir}")

# Test 3: Validasi stok negatif
print("\n[4] VALIDASI: Stok tidak boleh negatif")
with app.app_context():
    db = get_db()
    stok_awal = db.execute('SELECT qty_akhir FROM stok_akhir WHERE item_id = ?', (item_id,)).fetchone()['qty_akhir']

resp = client.get('/penjualan/create')
csrf = get_csrf(resp)
resp = client.post('/penjualan/create', data={
    'csrf_token': csrf,
    'pelanggan_id': pelanggan_id,
    'tanggal': '2026-10-08',
    'catatan': 'Test overstock',
    'item_id[]': [str(item_id)],
    'qty[]': [str(int(stok_awal) + 100)],
    'harga_jual[]': ['10000'],
}, follow_redirects=True)

with app.app_context():
    db = get_db()
    stok_akhir = db.execute('SELECT qty_akhir FROM stok_akhir WHERE item_id = ?', (item_id,)).fetchone()['qty_akhir']

test("Stok tidak berubah setelah validasi gagal", stok_akhir == stok_awal, f"{stok_awal} → {stok_akhir}")

# Test 4: Penjualan normal tetap jalan
print("\n[5] NORMAL: Penjualan valid tetap jalan")
with app.app_context():
    db = get_db()
    stok_awal = db.execute('SELECT qty_akhir FROM stok_akhir WHERE item_id = ?', (item_id,)).fetchone()['qty_akhir']

resp = client.get('/penjualan/create')
csrf = get_csrf(resp)
resp = client.post('/penjualan/create', data={
    'csrf_token': csrf,
    'pelanggan_id': pelanggan_id,
    'tanggal': '2026-10-08',
    'catatan': 'Test normal',
    'item_id[]': [str(item_id)],
    'qty[]': ['1'],
    'harga_jual[]': ['10000'],
}, follow_redirects=True)

with app.app_context():
    db = get_db()
    stok_akhir = db.execute('SELECT qty_akhir FROM stok_akhir WHERE item_id = ?', (item_id,)).fetchone()['qty_akhir']

test("Stok berkurang 1", stok_akhir == stok_awal - 1, f"{stok_awal} → {stok_akhir}")

# Test 5: Pembelian normal tetap jalan
print("\n[6] NORMAL: Pembelian valid tetap jalan")
with app.app_context():
    db = get_db()
    mutasi_awal = db.execute('SELECT COUNT(*) FROM stok_mutasi WHERE item_id = ?', (item_id,)).fetchone()[0]

resp = client.get('/pembelian/create')
csrf = get_csrf(resp)
resp = client.post('/pembelian/create', data={
    'csrf_token': csrf,
    'supplier_id': supplier['id'],
    'tanggal': '2026-10-08',
    'catatan': 'Test normal',
    'item_id[]': [str(item_id)],
    'qty[]': ['5'],
    'harga_beli[]': ['10000'],
}, follow_redirects=True)

with app.app_context():
    db = get_db()
    mutasi_akhir = db.execute('SELECT COUNT(*) FROM stok_mutasi WHERE item_id = ?', (item_id,)).fetchone()[0]

test("Mutasi bertambah 1", mutasi_akhir == mutasi_awal + 1, f"{mutasi_awal} → {mutasi_akhir}")

# Test 6: Multi-item atomicity
print("\n[7] MULTI-ITEM: Satu gagal, semua rollback")
with app.app_context():
    db = get_db()
    items = db.execute('''
        SELECT sa.item_id, sa.qty_akhir
        FROM stok_akhir sa
        WHERE sa.qty_akhir >= 10
        LIMIT 2
    ''').fetchall()
    
    if len(items) >= 2:
        item1_id = items[0]['item_id']
        item2_id = items[1]['item_id']
        stok1_awal = items[0]['qty_akhir']
        stok2_awal = items[1]['qty_akhir']
        
        resp = client.get('/penjualan/create')
        csrf = get_csrf(resp)
        resp = client.post('/penjualan/create', data={
            'csrf_token': csrf,
            'pelanggan_id': pelanggan_id,
            'tanggal': '2026-10-08',
            'catatan': 'Test multi-item',
            'item_id[]': [str(item1_id), str(item2_id)],
            'qty[]': ['1', '99999'],
            'harga_jual[]': ['10000', '10000'],
        }, follow_redirects=True)
        
        stok1 = db.execute('SELECT qty_akhir FROM stok_akhir WHERE item_id = ?', (item1_id,)).fetchone()
        stok2 = db.execute('SELECT qty_akhir FROM stok_akhir WHERE item_id = ?', (item2_id,)).fetchone()
        
        test("Item 1 tidak berubah", stok1['qty_akhir'] == stok1_awal, f"{stok1_awal} → {stok1['qty_akhir']}")
        test("Item 2 tidak berubah", stok2['qty_akhir'] == stok2_awal, f"{stok2_awal} → {stok2['qty_akhir']}")
    else:
        print("  ⚠️ Skip: tidak cukup item")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
