#!/usr/bin/env python3
"""Test script for Fase 2: Supplier + Pembelian using Flask test client"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, init_db
import json

# Initialize database
init_db()

# Create test client
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

def test(name, condition, detail=""):
    status = "✅" if condition else "❌"
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))
    return condition

print("=" * 60)
print("FASE 2 TEST: Supplier + Pembelian")
print("=" * 60)

# 1. Login
print("\n[1] LOGIN")
# Get CSRF token from login page
response = client.get('/login')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/login', data={
    'csrf_token': csrf_token,
    'username': 'admin',
    'password': 'admin123'
})
test("Login berhasil", response.status_code == 302 and '/login' not in response.location, f"status={response.status_code}, location={response.location}")

# 2. Supplier CRUD
print("\n[2] SUPPLIER CRUD")

# Get CSRF token from supplier create page
response = client.get('/supplier/create')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

# Create
response = client.post('/supplier/create', data={
    'csrf_token': csrf_token,
    'nama': 'Supplier Test ABC',
    'kontak': 'Budi',
    'alamat': 'Jl. Test No. 123'
})
test("Create supplier", response.status_code == 302 and '/supplier' in response.location, f"status={response.status_code}")

# List
response = client.get('/supplier')
test("List suppliers", b'Supplier Test ABC' in response.data)

# View
response = client.get('/supplier/1')
test("View supplier", response.status_code == 200 and b'Supplier Test ABC' in response.data)

# Edit
response = client.get('/supplier/1/edit')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/supplier/1/edit', data={
    'csrf_token': csrf_token,
    'nama': 'Supplier Test ABC Updated',
    'kontak': 'Budi Santoso',
    'alamat': 'Jl. Updated No. 456'
})
test("Edit supplier", response.status_code == 302 and '/supplier' in response.location)

# Verify edit
response = client.get('/supplier/1')
test("Verify edit", b'Supplier Test ABC Updated' in response.data)

# 3. Pembelian
print("\n[3] PEMBELIAN")

# Create pembelian with 2 items
response = client.get('/pembelian/create')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/pembelian/create', data={
    'csrf_token': csrf_token,
    'supplier_id': '1',
    'tanggal': '2026-10-07',
    'catatan': 'Pembelian test',
    'item_id[]': ['1', '2'],
    'qty[]': ['10', '5'],
    'harga_beli[]': ['50000', '30000']
})
test("Create pembelian", response.status_code == 302 and '/pembelian/' in response.location, f"status={response.status_code}, location={response.location}")

# Check nomor transaksi
response = client.get('/pembelian')
test("Nomor transaksi PB-2026-0001", b'PB-2026-0001' in response.data)

# View detail
response = client.get('/pembelian/1')
test("View pembelian detail", response.status_code == 200 and b'Pembelian test' in response.data)

# 4. Delete Pembelian (rollback stok)
print("\n[4] DELETE PEMBELIAN (ROLLBACK STOK)")
response = client.get('/pembelian/1')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/pembelian/1/delete', data={
    'csrf_token': csrf_token
})
test("Delete pembelian", response.status_code == 302 and '/pembelian' in response.location)

# Verify deleted
response = client.get('/pembelian')
test("Verify deleted", b'PB-2026-0001' not in response.data)

# 5. Delete Supplier
print("\n[5] DELETE SUPPLIER")
response = client.get('/supplier/1')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/supplier/1/delete', data={
    'csrf_token': csrf_token
})
test("Delete supplier", response.status_code == 302 and '/supplier' in response.location)

# 6. Validation Tests
print("\n[6] VALIDATION TESTS")

# Empty supplier name
response = client.get('/supplier/create')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/supplier/create', data={
    'csrf_token': csrf_token,
    'nama': '',
    'kontak': '',
    'alamat': ''
})
test("Empty supplier name rejected", b'wajib diisi' in response.data)

# Empty pembelian
response = client.get('/pembelian/create')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/pembelian/create', data={
    'csrf_token': csrf_token,
    'supplier_id': '',
    'tanggal': '',
    'catatan': '',
    'item_id[]': [''],
    'qty[]': [''],
    'harga_beli[]': ['']
})
test("Empty pembelian rejected", b'wajib' in response.data.lower())

# Negative qty
response = client.get('/pembelian/create')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/pembelian/create', data={
    'csrf_token': csrf_token,
    'supplier_id': '1',
    'tanggal': '2026-10-07',
    'catatan': '',
    'item_id[]': ['1'],
    'qty[]': ['-5'],
    'harga_beli[]': ['10000']
})
test("Negative qty rejected", b'lebih dari 0' in response.data)

# Negative harga
response = client.get('/pembelian/create')
csrf_token = None
for line in response.data.decode().split('\n'):
    if 'name="csrf_token"' in line:
        import re
        match = re.search(r'value="([^"]+)"', line)
        if match:
            csrf_token = match.group(1)
            break

response = client.post('/pembelian/create', data={
    'csrf_token': csrf_token,
    'supplier_id': '1',
    'tanggal': '2026-10-07',
    'catatan': '',
    'item_id[]': ['1'],
    'qty[]': ['5'],
    'harga_beli[]': ['-10000']
})
test("Negative harga rejected", b'negatif' in response.data)

# 7. Navigation
print("\n[7] NAVIGATION")
response = client.get('/')
test("Supplier nav link", b'Data Supplier' in response.data)
test("Pembelian nav link", b'Pembelian' in response.data)

# 8. Security Headers
print("\n[8] SECURITY HEADERS")
response = client.get('/login')
test("CSP header", 'Content-Security-Policy' in response.headers)
test("X-Frame-Options", response.headers.get('X-Frame-Options') == 'DENY')
test("X-Content-Type-Options", response.headers.get('X-Content-Type-Options') == 'nosniff')

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
