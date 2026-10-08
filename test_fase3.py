#!/usr/bin/env python3
"""Test script for Fase 3: Penjualan using Flask test client"""
import sys
import os
import re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_db

# Initialize database
init_db()

# Create test client
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

def get_csrf(response):
    """Extract CSRF token from response."""
    for line in response.data.decode().split('\n'):
        if 'name="csrf_token"' in line:
            match = re.search(r'value="([^"]+)"', line)
            if match:
                return match.group(1)
    return None

def test(name, condition, detail=""):
    status = "✅" if condition else "❌"
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    return condition

print("=" * 60)
print("FASE 3 TEST: Penjualan")
print("=" * 60)

# 1. Login
print("\n[1] LOGIN")
response = client.get('/login')
csrf_token = get_csrf(response)
response = client.post('/login', data={
    'csrf_token': csrf_token,
    'username': 'admin',
    'password': 'admin123'
})
test("Login berhasil", response.status_code == 302 and '/login' not in response.location, f"status={response.status_code}")

# 2. Setup: Create pelanggan
print("\n[2] SETUP: PELANGGAN")
response = client.get('/pelanggan/create')
csrf_token = get_csrf(response)
response = client.post('/pelanggan/create', data={
    'csrf_token': csrf_token,
    'nama': 'Pelanggan Test',
    'email': 'test@example.com',
    'telepon': '08123456789',
    'alamat': 'Jl. Test'
})
test("Create pelanggan", response.status_code == 302, f"status={response.status_code}")

# Get pelanggan ID from DB
from app import get_db
with app.app_context():
    db = get_db()
    row = db.execute("SELECT id FROM pelanggan WHERE nama = 'Pelanggan Test'").fetchone()
    pelanggan_id = str(row['id']) if row else None
test("Pelanggan ID found", pelanggan_id is not None, f"id={pelanggan_id}")

# 3. Setup: Create items
print("\n[3] SETUP: ITEMS")
response = client.get('/create')
csrf_token = get_csrf(response)
response = client.post('/create', data={
    'csrf_token': csrf_token,
    'nama': 'Item Test A',
    'harga_pokok': '10000',
    'harga_jual': '15000',
    'category': 'Lainnya'
})
test("Create item A", response.status_code == 302, f"status={response.status_code}")

response = client.get('/create')
csrf_token = get_csrf(response)
response = client.post('/create', data={
    'csrf_token': csrf_token,
    'nama': 'Item Test B',
    'harga_pokok': '20000',
    'harga_jual': '30000',
    'category': 'Lainnya'
})
test("Create item B", response.status_code == 302, f"status={response.status_code}")

# 4. Setup: Create supplier + pembelian (to add stock)
print("\n[4] SETUP: SUPPLIER + PEMBELIAN")
response = client.get('/supplier/create')
csrf_token = get_csrf(response)
response = client.post('/supplier/create', data={
    'csrf_token': csrf_token,
    'nama': 'Supplier Test',
    'kontak': 'Budi',
    'alamat': 'Jl. Supplier'
})
test("Create supplier", response.status_code == 302, f"status={response.status_code}")

# Get supplier ID from DB
with app.app_context():
    db = get_db()
    row = db.execute("SELECT id FROM supplier WHERE nama = 'Supplier Test'").fetchone()
    supplier_id = str(row['id']) if row else None
test("Supplier ID found", supplier_id is not None, f"id={supplier_id}")

# Create pembelian to add stock
response = client.get('/pembelian/create')
csrf_token = get_csrf(response)
response = client.post('/pembelian/create', data={
    'csrf_token': csrf_token,
    'supplier_id': supplier_id,
    'tanggal': '2026-10-07',
    'catatan': 'Pembelian test',
    'item_id[]': ['1', '2'],
    'qty[]': ['10', '5'],
    'harga_beli[]': ['10000', '20000']
})
test("Create pembelian", response.status_code == 302, f"status={response.status_code}")

# 5. Penjualan Index
print("\n[5] PENJUALAN INDEX")
response = client.get('/penjualan')
test("Penjualan page loads", response.status_code == 200, f"status={response.status_code}")
test("Penjualan nav link", b'Penjualan' in response.data)

# 6. Create Penjualan
print("\n[6] CREATE PENJUALAN")
response = client.get('/penjualan/create')
csrf_token = get_csrf(response)
response = client.post('/penjualan/create', data={
    'csrf_token': csrf_token,
    'pelanggan_id': pelanggan_id,
    'tanggal': '2026-10-07',
    'catatan': 'Penjualan test',
    'item_id[]': ['1', '2'],
    'qty[]': ['3', '2'],
    'harga_jual[]': ['15000', '30000']
})
test("Create penjualan", response.status_code == 302 and '/penjualan/' in response.location, f"status={response.status_code}, location={response.location}")

# Check nomor transaksi
response = client.get('/penjualan')
test("Nomor transaksi PJ-2026-0001", b'PJ-2026-0001' in response.data)

# 7. View Penjualan Detail
print("\n[7] VIEW PENJUALAN DETAIL")
# Get penjualan ID from DB
with app.app_context():
    db = get_db()
    row = db.execute("SELECT id FROM penjualan WHERE nomor_transaksi = 'PJ-2026-0001'").fetchone()
    penjualan_id = str(row['id']) if row else None
test("Penjualan ID found", penjualan_id is not None, f"id={penjualan_id}")

response = client.get(f'/penjualan/{penjualan_id}')
test("View penjualan detail", response.status_code == 200 and b'Penjualan test' in response.data, f"status={response.status_code}")
test("Detail shows item A", b'Item Test A' in response.data)
test("Detail shows item B", b'Item Test B' in response.data)
test("HPP snapshot", b'10,000' in response.data or b'20,000' in response.data)

# 8. Check stok_akhir
print("\n[8] CHECK STOK AKHIR")
from app import get_db
with app.app_context():
    db = get_db()
    stok_a = db.execute("SELECT qty_akhir FROM stok_akhir WHERE item_id = 1").fetchone()
    stok_b = db.execute("SELECT qty_akhir FROM stok_akhir WHERE item_id = 2").fetchone()
    test("Stok item A berkurang", stok_a and stok_a['qty_akhir'] == 7, f"stok={stok_a['qty_akhir'] if stok_a else 'N/A'}")
    test("Stok item B berkurang", stok_b and stok_b['qty_akhir'] == 3, f"stok={stok_b['qty_akhir'] if stok_b else 'N/A'}")

# 9. Check stok_mutasi
print("\n[9] CHECK STOK MUTASI")
with app.app_context():
    db = get_db()
    mutasi = db.execute("SELECT * FROM stok_mutasi WHERE referensi_tipe = 'penjualan' AND referensi_id = ?", (penjualan_id,)).fetchall()
    test("2 mutasi OUT", len(mutasi) == 2, f"count={len(mutasi)}")
    test("Mutasi OUT type", all(m['jenis_mutasi'] == 'OUT' for m in mutasi))

# 10. Check penjualan_detail
print("\n[10] CHECK PENJUALAN DETAIL")
with app.app_context():
    db = get_db()
    details = db.execute("SELECT * FROM penjualan_detail WHERE penjualan_id = ?", (penjualan_id,)).fetchall()
    test("2 detail rows", len(details) == 2, f"count={len(details)}")
    test("HPP snapshot in detail", all(d['harga_pokok'] > 0 for d in details))

# 11. Delete Penjualan (rollback stok)
print("\n[11] DELETE PENJUALAN (ROLLBACK STOK)")
response = client.get(f'/penjualan/{penjualan_id}')
csrf_token = get_csrf(response)
response = client.post(f'/penjualan/{penjualan_id}/delete', data={
    'csrf_token': csrf_token
})
test("Delete penjualan", response.status_code == 302 and '/penjualan' in response.location, f"status={response.status_code}")

# Verify stok restored
with app.app_context():
    db = get_db()
    stok_a = db.execute("SELECT qty_akhir FROM stok_akhir WHERE item_id = 1").fetchone()
    stok_b = db.execute("SELECT qty_akhir FROM stok_akhir WHERE item_id = 2").fetchone()
    test("Stok item A restored", stok_a and stok_a['qty_akhir'] == 10, f"stok={stok_a['qty_akhir'] if stok_a else 'N/A'}")
    test("Stok item B restored", stok_b and stok_b['qty_akhir'] == 5, f"stok={stok_b['qty_akhir'] if stok_b else 'N/A'}")

# Verify mutasi deleted
with app.app_context():
    db = get_db()
    mutasi = db.execute("SELECT * FROM stok_mutasi WHERE referensi_tipe = 'penjualan' AND referensi_id = ?", (penjualan_id,)).fetchall()
    test("Mutasi deleted", len(mutasi) == 0, f"count={len(mutasi)}")

# 12. Validation Tests
print("\n[12] VALIDATION TESTS")

# Empty pelanggan
response = client.get('/penjualan/create')
csrf_token = get_csrf(response)
response = client.post('/penjualan/create', data={
    'csrf_token': csrf_token,
    'pelanggan_id': '',
    'tanggal': '2026-10-07',
    'catatan': '',
    'item_id[]': ['1'],
    'qty[]': ['1'],
    'harga_jual[]': ['10000']
})
test("Empty pelanggan rejected", b'wajib' in response.data.lower())

# Empty tanggal
response = client.get('/penjualan/create')
csrf_token = get_csrf(response)
response = client.post('/penjualan/create', data={
    'csrf_token': csrf_token,
    'pelanggan_id': pelanggan_id,
    'tanggal': '',
    'catatan': '',
    'item_id[]': ['1'],
    'qty[]': ['1'],
    'harga_jual[]': ['10000']
})
test("Empty tanggal rejected", b'wajib' in response.data.lower())

# Negative qty
response = client.get('/penjualan/create')
csrf_token = get_csrf(response)
response = client.post('/penjualan/create', data={
    'csrf_token': csrf_token,
    'pelanggan_id': pelanggan_id,
    'tanggal': '2026-10-07',
    'catatan': '',
    'item_id[]': ['1'],
    'qty[]': ['-5'],
    'harga_jual[]': ['10000']
})
test("Negative qty rejected", b'lebih dari 0' in response.data)

# Negative harga
response = client.get('/penjualan/create')
csrf_token = get_csrf(response)
response = client.post('/penjualan/create', data={
    'csrf_token': csrf_token,
    'pelanggan_id': pelanggan_id,
    'tanggal': '2026-10-07',
    'catatan': '',
    'item_id[]': ['1'],
    'qty[]': ['5'],
    'harga_jual[]': ['-10000']
})
test("Negative harga rejected", b'negatif' in response.data)

# Stok tidak cukup
response = client.get('/penjualan/create')
csrf_token = get_csrf(response)
response = client.post('/penjualan/create', data={
    'csrf_token': csrf_token,
    'pelanggan_id': pelanggan_id,
    'tanggal': '2026-10-07',
    'catatan': '',
    'item_id[]': ['1'],
    'qty[]': ['9999'],
    'harga_jual[]': ['10000']
})
test("Stok tidak cukup rejected", b'tidak cukup' in response.data.lower() or b'Stok' in response.data)

# 13. Navigation
print("\n[13] NAVIGATION")
response = client.get('/')
test("Penjualan nav link", b'Penjualan' in response.data)

# 14. Security Headers
print("\n[14] SECURITY HEADERS")
response = client.get('/login')
test("CSP header", 'Content-Security-Policy' in response.headers)
test("X-Frame-Options", response.headers.get('X-Frame-Options') == 'DENY')
test("X-Content-Type-Options", response.headers.get('X-Content-Type-Options') == 'nosniff')

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
