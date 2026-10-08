#!/usr/bin/env python3
"""Test Fase 4 — Kartu Stok + Laporan + Login Page."""
import os
import re
import sys
import tempfile

# Use temp DB
TMP_DB = os.path.join(tempfile.mkdtemp(), 'test.db')
os.environ['DATABASE'] = TMP_DB

# Import app
sys.path.insert(0, '/home/choirulhaq/venvProject/testopencode')
import app as m

# Override DATABASE
m.DATABASE = TMP_DB

import sqlite3
with m.app.app_context():
    m.init_db()

# Seed test data via direct connection (same file the app uses)
db = sqlite3.connect(TMP_DB)
db.execute("INSERT INTO items (nama, harga_pokok, harga_jual, category) VALUES ('Test Item', 10000, 15000, 'Elektronik')")
db.execute("INSERT INTO stok_akhir (item_id, qty_akhir, harga_pokok_rata) VALUES (1, 50, 10000)")
db.execute("INSERT INTO stok_mutasi (item_id, jenis_mutasi, qty, harga, saldo_berjalan, referensi_tipe, referensi_id, nomor_referensi, created_by) VALUES (1, 'IN', 50, 10000, 50, 'pembelian', 1, 'PB-2026-0001', 1)")
db.commit()
db.close()

# Test client
c = m.app.test_client()

# Login
r = c.get('/login')
assert r.status_code == 200, f"Login page: {r.status_code}"

# Check login page has info card
html = r.get_data(as_text=True)
checks = [
    ('Login info card', 'login-info-card' in html),
    ('App title', 'Sistem Manajemen Inventory' in html),
    ('Description', 'Kelola stok barang' in html),
    ('Feature: Master Data', 'Master Data' in html),
    ('Feature: Transaksi', 'Transaksi' in html),
    ('Feature: Laporan', 'Laporan' in html),
    ('Feature: Multi-User', 'Multi-User' in html),
]

# Get CSRF token
csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', html)
assert csrf_match, "CSRF token not found"
csrf_token = csrf_match.group(1)

# Login
r = c.post('/login', data={
    'username': 'admin',
    'password': 'admin123',
    'csrf_token': csrf_token
}, follow_redirects=False)
assert r.status_code == 302, f"Login failed: {r.status_code}"

# Test new routes
routes = [
    ('/stok/kartu', 'Kartu Stok'),
    ('/laporan/penjualan', 'Laporan Penjualan'),
    ('/laporan/stok', 'Laporan Stok'),
]

for route, expected_text in routes:
    r = c.get(route)
    assert r.status_code == 200, f"{route}: {r.status_code}"
    html = r.get_data(as_text=True)
    checks.append((f'{route} content', expected_text in html))

# Test kartu stok with item_id
r = c.get('/stok/kartu?item_id=1')
assert r.status_code == 200, f"/stok/kartu?item_id=1: {r.status_code}"
html = r.get_data(as_text=True)
checks.append(('Kartu stok detail', 'Stok Akhir' in html))

# Test laporan penjualan with date filter
r = c.get('/laporan/penjualan?start_date=2026-01-01&end_date=2026-12-31')
assert r.status_code == 200, f"Laporan penjualan filter: {r.status_code}"
html = r.get_data(as_text=True)
checks.append(('Laporan penjualan filter', 'Total Transaksi' in html))

# Test laporan stok
r = c.get('/laporan/stok')
assert r.status_code == 200, f"Laporan stok: {r.status_code}"
html = r.get_data(as_text=True)
checks.append(('Laporan stok content', 'Total Item' in html))

# Test nav links in base.html
r = c.get('/')
html = r.get_data(as_text=True)
checks.append(('Nav: Kartu Stok', 'Kartu Stok' in html))
checks.append(('Nav: Laporan', 'Laporan' in html))

# Print results
print("=" * 60)
print("FASE 4 TEST RESULTS")
print("=" * 60)
passed = 0
failed = 0
for name, result in checks:
    status = "✅" if result else "❌"
    print(f"  {status} {name}")
    if result:
        passed += 1
    else:
        failed += 1

print("=" * 60)
print(f"Total: {passed} passed, {failed} failed")
print("=" * 60)

if failed > 0:
    sys.exit(1)
