#!/usr/bin/env python3
"""Test Fase 2: Supplier + Pembelian — pakai curl via subprocess"""
import subprocess
import re
import json
import sqlite3

BASE = "http://localhost:5000"
COOKIES = "/tmp/test_fase2_cookies.txt"

results = []

def check(name, condition, detail=""):
    status = "✅" if condition else "❌"
    results.append((name, condition))
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

def curl(method, path, data=None, follow=False):
    """Run curl and return (status_code, headers, body)"""
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
    """Get CSRF token from a page"""
    _, body = curl("GET", path)
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', body)
    return m.group(1) if m else None

import os

# Clean up cookies from previous run
if os.path.exists(COOKIES):
    os.remove(COOKIES)

# Reset DB
db = sqlite3.connect("/home/choirulhaq/venvProject/testopencode/database.db")
db.execute("DELETE FROM stok_mutasi")
db.execute("DELETE FROM stok_akhir")
db.execute("DELETE FROM pembelian_detail")
db.execute("DELETE FROM pembelian")
db.execute("DELETE FROM supplier")
db.execute("DELETE FROM sqlite_sequence WHERE name IN ('supplier', 'pembelian', 'pembelian_detail', 'stok_mutasi', 'stok_akhir')")
db.commit()
db.close()

print("=" * 60)
print("FASE 2 TEST: Supplier + Pembelian (curl)")
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

# 2. SUPPLIER LIST
print("\n[2] SUPPLIER LIST")
status, body = curl("GET", "/supplier")
check("/supplier OK", status == 200)

# 3. CREATE SUPPLIER
print("\n[3] CREATE SUPPLIER")
csrf = get_csrf("/supplier/create")
status, _ = curl("POST", "/supplier/create", {
    "csrf_token": csrf,
    "nama": "CV Maju Jaya",
    "kontak": "Pak Budi",
    "alamat": "Jl. Merdeka No. 10"
})
check("Create supplier", status == 302, f"status={status}")

# 4. SUPPLIER VIEW
print("\n[4] SUPPLIER VIEW")
status, body = curl("GET", "/supplier/1")
check("View supplier", status == 200 and "Maju Jaya" in body)

# 5. SUPPLIER EDIT
print("\n[5] SUPPLIER EDIT")
csrf = get_csrf("/supplier/1/edit")
status, _ = curl("POST", "/supplier/1/edit", {
    "csrf_token": csrf,
    "nama": "CV Maju Jaya Abadi",
    "kontak": "Pak Budi",
    "alamat": "Jl. Merdeka No. 10"
})
check("Edit supplier", status == 302)

# 6. PEMBELIAN LIST
print("\n[6] PEMBELIAN LIST")
status, body = curl("GET", "/pembelian")
check("/pembelian OK", status == 200)

# 7. CREATE PEMBELIAN (2 items in 1 request)
print("\n[7] CREATE PEMBELIAN (2 items)")
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

# 8. VERIFY DB
print("\n[8] VERIFY DB")
db = sqlite3.connect("/home/choirulhaq/venvProject/testopencode/database.db")
db.row_factory = sqlite3.Row

stok_akhir = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir ada 2 row", len(stok_akhir) == 2, f"count={len(stok_akhir)}")
for row in stok_akhir:
    print(f"    item={row['item_id']}, qty={row['qty_akhir']}, hpp={row['harga_pokok_rata']}")

mutasi = db.execute("SELECT * FROM stok_mutasi").fetchall()
check("stok_mutasi ada 2 row", len(mutasi) == 2, f"count={len(mutasi)}")
for row in mutasi:
    print(f"    item={row['item_id']}, {row['jenis_mutasi']}, qty={row['qty']}, saldo={row['saldo_berjalan']}")

pembelian = db.execute("SELECT * FROM pembelian").fetchall()
check("pembelian 1 row", len(pembelian) == 1)
if pembelian:
    print(f"    nomor={pembelian[0]['nomor_transaksi']}, total={pembelian[0]['total']}")
    check("Nomor PB-2026-0001", pembelian[0]['nomor_transaksi'] == "PB-2026-0001")

detail = db.execute("SELECT * FROM pembelian_detail").fetchall()
check("pembelian_detail 2 row", len(detail) == 2)

# 9. DELETE PEMBELIAN (rollback stok)
print("\n[9] DELETE PEMBELIAN (rollback stok)")
csrf = get_csrf("/pembelian/1")
status, _ = curl("POST", "/pembelian/1/delete", {"csrf_token": csrf})
check("Delete pembelian", status == 302)

stok_akhir_after = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir kosong setelah delete", len(stok_akhir_after) == 0, f"count={len(stok_akhir_after)}")

mutasi_after = db.execute("SELECT COUNT(*) FROM stok_mutasi").fetchone()[0]
check("stok_mutasi kosong setelah delete", mutasi_after == 0, f"count={mutasi_after}")

# 10. DELETE SUPPLIER
print("\n[10] DELETE SUPPLIER")
csrf = get_csrf("/supplier/1")
status, _ = curl("POST", "/supplier/1/delete", {"csrf_token": csrf})
check("Delete supplier", status == 302)

# 11. NAVIGATION
print("\n[11] NAVIGATION")
status, body = curl("GET", "/")
check("Supplier nav link", "Data Supplier" in body)
check("Pembelian nav link", "Pembelian" in body)

# 12. SECURITY HEADERS
print("\n[12] SECURITY HEADERS")
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
