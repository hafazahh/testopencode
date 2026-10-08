#!/usr/bin/env python3
"""Test Fase 3: Penjualan (stok keluar) + validasi stok — pakai curl via subprocess"""
import subprocess
import re
import os
import sqlite3

BASE = "http://localhost:5000"
COOKIES = "/tmp/test_fase3_cookies.txt"

results = []

def check(name, condition, detail=""):
    status = "✅" if condition else "❌"
    results.append((name, condition))
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

def curl(method, path, data=None, follow=False):
    cmd = ["curl", "-s", "-c", COOKIES, "-b", COOKIES, "-w", "\n%{http_code}", "-X", method]
    if follow:
        cmd.append("-L")
    if data:
        for k, v in data.items():
            cmd.extend(["-d", f"{k}={v}"])
    cmd.append(f"{BASE}{path}")
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    lines = r.stdout.rsplit("\n", 1)
    body = lines[0] if len(lines) > 1 else ""
    status = int(lines[-1]) if lines[-1].isdigit() else 0
    return status, body

def get_csrf(path):
    _, body = curl("GET", path)
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', body)
    return m.group(1) if m else None

# Clean up
if os.path.exists(COOKIES):
    os.remove(COOKIES)

# Reset DB
db = sqlite3.connect("/home/choirulhaq/venvProject/testopencode/database.db")
for table in ["stok_mutasi", "stok_akhir", "penjualan_detail", "penjualan", "pembelian_detail", "pembelian", "supplier"]:
    db.execute(f"DELETE FROM {table}")
db.execute("DELETE FROM sqlite_sequence WHERE name IN ('supplier', 'pembelian', 'pembelian_detail', 'penjualan', 'penjualan_detail', 'stok_mutasi', 'stok_akhir')")
db.commit()
db.close()

print("=" * 60)
print("FASE 3 TEST: Penjualan + Validasi Stok (curl)")
print("=" * 60)

# 1. LOGIN
print("\n[1] LOGIN")
csrf = get_csrf("/login")
status, _ = curl("POST", "/login", {
    "csrf_token": csrf,
    "username": "admin",
    "password": "admin123"
})
check("Login berhasil", status == 302, f"status={status}")

# 2. SETUP: Create supplier
print("\n[2] SETUP: Supplier")
csrf = get_csrf("/supplier/create")
status, _ = curl("POST", "/supplier/create", {
    "csrf_token": csrf,
    "nama": "CV Test Supplier",
    "kontak": "Budi",
    "alamat": "Jl. Test"
})
check("Create supplier", status == 302)

# 3. SETUP: Create pelanggan
print("\n[3] SETUP: Pelanggan")
csrf = get_csrf("/pelanggan/create")
status, _ = curl("POST", "/pelanggan/create", {
    "csrf_token": csrf,
    "nama": "Pak Andi",
    "email": "andi@test.com",
    "telepon": "08123456789",
    "alamat": "Jl. Pelanggan"
})
check("Create pelanggan", status == 302)

# 4. SETUP: Create pembelian (stok masuk)
print("\n[4] SETUP: Pembelian (stok masuk)")
csrf = get_csrf("/pembelian/create")
cmd = ["curl", "-s", "-c", COOKIES, "-b", COOKIES, "-w", "\n%{http_code}", "-X", "POST",
       "-d", f"csrf_token={csrf}",
       "-d", "supplier_id=1",
       "-d", "tanggal=2026-10-07",
       "-d", "catatan=Stok awal",
       "-d", "item_id[]=1",
       "-d", "qty[]=100",
       "-d", "harga_beli[]=50000",
       "-d", "item_id[]=2",
       "-d", "qty[]=50",
       "-d", "harga_beli[]=30000",
       f"{BASE}/pembelian/create"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
lines = r.stdout.rsplit("\n", 1)
status = int(lines[-1]) if lines[-1].isdigit() else 0
check("Create pembelian", status == 302, f"status={status}")

# Verify stok_akhir
db = sqlite3.connect("/home/choirulhaq/venvProject/testopencode/database.db")
db.row_factory = sqlite3.Row
stok = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir: item1=100", len(stok) >= 1 and stok[0]['qty_akhir'] == 100.0)
check("stok_akhir: item2=50", len(stok) >= 2 and stok[1]['qty_akhir'] == 50.0)

# 5. PENJUALAN LIST
print("\n[5] PENJUALAN LIST")
status, body = curl("GET", "/penjualan")
check("/penjualan OK", status == 200)

# 6. CREATE PENJUALAN (2 items)
print("\n[6] CREATE PENJUALAN (2 items)")
csrf = get_csrf("/penjualan/create")
cmd = ["curl", "-s", "-c", COOKIES, "-b", COOKIES, "-w", "\n%{http_code}", "-X", "POST",
       "-d", f"csrf_token={csrf}",
       "-d", "pelanggan_id=1",
       "-d", "tanggal=2026-10-07",
       "-d", "catatan=",
       "-d", "item_id[]=1",
       "-d", "qty[]=30",
       "-d", "harga_jual[]=60000",
       "-d", "item_id[]=2",
       "-d", "qty[]=20",
       "-d", "harga_jual[]=35000",
       f"{BASE}/penjualan/create"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
lines = r.stdout.rsplit("\n", 1)
status = int(lines[-1]) if lines[-1].isdigit() else 0
check("Create penjualan", status == 302, f"status={status}")

# 7. VERIFY DB
print("\n[7] VERIFY DB")
stok_akhir = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir: item1=70", len(stok_akhir) >= 1 and stok_akhir[0]['qty_akhir'] == 70.0, f"qty={stok_akhir[0]['qty_akhir']}")
check("stok_akhir: item2=30", len(stok_akhir) >= 2 and stok_akhir[1]['qty_akhir'] == 30.0, f"qty={stok_akhir[1]['qty_akhir']}")

mutasi = db.execute("SELECT * FROM stok_mutasi WHERE jenis_mutasi='OUT'").fetchall()
check("stok_mutasi OUT: 2 row", len(mutasi) == 2, f"count={len(mutasi)}")
for row in mutasi:
    print(f"    item={row['item_id']}, OUT, qty={row['qty']}, saldo={row['saldo_berjalan']}")

penjualan = db.execute("SELECT * FROM penjualan").fetchall()
check("penjualan: 1 row", len(penjualan) == 1)
if penjualan:
    print(f"    nomor={penjualan[0]['nomor_transaksi']}, total={penjualan[0]['total']}")
    check("Nomor PJ-2026-0001", penjualan[0]['nomor_transaksi'] == "PJ-2026-0001")

detail = db.execute("SELECT * FROM penjualan_detail").fetchall()
check("penjualan_detail: 2 row", len(detail) == 2)
for row in detail:
    print(f"    item={row['item_id']}, qty={row['qty']}, harga_jual={row['harga_jual']}, harga_pokok={row['harga_pokok']}")
    check(f"HPP snapshot item {row['item_id']}", row['harga_pokok'] > 0)

# 8. VALIDASI STOK: coba jual melebihi stok
print("\n[8] VALIDASI STOK: jual melebihi stok")
csrf = get_csrf("/penjualan/create")
cmd = ["curl", "-s", "-c", COOKIES, "-b", COOKIES, "-w", "\n%{http_code}", "-X", "POST",
       "-d", f"csrf_token={csrf}",
       "-d", "pelanggan_id=1",
       "-d", "tanggal=2026-10-07",
       "-d", "catatan=",
       "-d", "item_id[]=1",
       "-d", "qty[]=999",
       "-d", "harga_jual[]=60000",
       f"{BASE}/penjualan/create"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
lines = r.stdout.rsplit("\n", 1)
status = int(lines[-1]) if lines[-1].isdigit() else 0
body = lines[0] if len(lines) > 1 else ""
check("Stok tidak cukup ditolak", status == 200 and "tidak cukup" in body.lower(), f"status={status}")

# 9. DELETE PENJUALAN (rollback stok)
print("\n[9] DELETE PENJUALAN (rollback stok)")
csrf = get_csrf("/penjualan/1")
status, _ = curl("POST", "/penjualan/1/delete", {"csrf_token": csrf})
check("Delete penjualan", status == 302)

stok_akhir_after = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir: item1=100 (rollback)", len(stok_akhir_after) >= 1 and stok_akhir_after[0]['qty_akhir'] == 100.0, f"qty={stok_akhir_after[0]['qty_akhir']}")
check("stok_akhir: item2=50 (rollback)", len(stok_akhir_after) >= 2 and stok_akhir_after[1]['qty_akhir'] == 50.0, f"qty={stok_akhir_after[1]['qty_akhir']}")

mutasi_after = db.execute("SELECT COUNT(*) FROM stok_mutasi WHERE jenis_mutasi='OUT'").fetchone()[0]
check("stok_mutasi OUT kosong", mutasi_after == 0, f"count={mutasi_after}")

# 10. NAVIGATION
print("\n[10] NAVIGATION")
status, body = curl("GET", "/")
check("Penjualan nav link", "Penjualan" in body)

# 11. SECURITY HEADERS
print("\n[11] SECURITY HEADERS")
cmd = ["curl", "-s", "-c", COOKIES, "-b", COOKIES, "-D", "-", "-o", "/dev/null", f"{BASE}/login"]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
headers = r.stdout
check("CSP header", "Content-Security-Policy" in headers)
check("X-Frame-Options", "X-Frame-Options: DENY" in headers)
check("X-Content-Type-Options", "X-Content-Type-Options: nosniff" in headers)

db.close()

# Summary
print("\n" + "=" * 60)
passed = sum(1 for _, c in results if c)
total = len(results)
print(f"RESULT: {passed}/{total} passed")
if passed == total:
    print("✅ ALL TESTS PASSED")
else:
    print(f"❌ {total - passed} tests failed")
print("=" * 60)
