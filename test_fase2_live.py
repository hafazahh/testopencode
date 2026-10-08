#!/usr/bin/env python3
"""Test Fase 2: Supplier + Pembelian — live server"""
import re
import requests
import sqlite3

BASE = "http://localhost:5000"
s = requests.Session()

def get_csrf(url):
    r = s.get(url)
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', r.text)
    return m.group(1) if m else None

results = []

def check(name, condition, detail=""):
    status = "✅" if condition else "❌"
    results.append((name, condition))
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("FASE 2 TEST: Supplier + Pembelian (live server)")
print("=" * 60)

# 1. LOGIN
print("\n[1] LOGIN")
csrf = get_csrf(f"{BASE}/login")
r = s.post(f"{BASE}/login", data={"username": "admin", "password": "admin123", "csrf_token": csrf})
check("Login berhasil", r.status_code == 302 and "/login" not in r.url, f"status={r.status_code}")

# 2. SUPPLIER LIST
print("\n[2] SUPPLIER LIST")
r = s.get(f"{BASE}/supplier")
check("/supplier OK", r.status_code == 200)

# 3. CREATE SUPPLIER
print("\n[3] CREATE SUPPLIER")
csrf = get_csrf(f"{BASE}/supplier/create")
r = s.post(f"{BASE}/supplier/create", data={
    "csrf_token": csrf,
    "nama": "CV Maju Jaya",
    "kontak": "Pak Budi",
    "alamat": "Jl. Merdeka No. 10"
})
check("Create supplier", r.status_code == 302, f"status={r.status_code}")

# 4. SUPPLIER VIEW
print("\n[4] SUPPLIER VIEW")
r = s.get(f"{BASE}/supplier/1")
check("View supplier", r.status_code == 200 and "Maju Jaya" in r.text)

# 5. SUPPLIER EDIT
print("\n[5] SUPPLIER EDIT")
csrf = get_csrf(f"{BASE}/supplier/1/edit")
r = s.post(f"{BASE}/supplier/1/edit", data={
    "csrf_token": csrf,
    "nama": "CV Maju Jaya Abadi",
    "kontak": "Pak Budi",
    "alamat": "Jl. Merdeka No. 10"
})
check("Edit supplier", r.status_code == 302)

# 6. PEMBELIAN LIST
print("\n[6] PEMBELIAN LIST")
r = s.get(f"{BASE}/pembelian")
check("/pembelian OK", r.status_code == 200)

# 7. CREATE PEMBELIAN (2 items)
print("\n[7] CREATE PEMBELIAN (2 items)")
csrf = get_csrf(f"{BASE}/pembelian/create")
r = s.post(f"{BASE}/pembelian/create", data={
    "csrf_token": csrf,
    "supplier_id": "1",
    "tanggal": "2026-10-07",
    "catatan": "Stok awal",
    "item_id[]": ["1", "2"],
    "qty[]": ["100", "50"],
    "harga_beli[]": ["50000", "30000"]
})
check("Create pembelian", r.status_code == 302, f"status={r.status_code}")

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
csrf = get_csrf(f"{BASE}/pembelian/1")
r = s.post(f"{BASE}/pembelian/1/delete", data={"csrf_token": csrf})
check("Delete pembelian", r.status_code == 302)

stok_akhir_after = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir kosong setelah delete", len(stok_akhir_after) == 0, f"count={len(stok_akhir_after)}")

mutasi_after = db.execute("SELECT COUNT(*) FROM stok_mutasi").fetchone()[0]
check("stok_mutasi kosong setelah delete", mutasi_after == 0, f"count={mutasi_after}")

# 10. DELETE SUPPLIER
print("\n[10] DELETE SUPPLIER")
csrf = get_csrf(f"{BASE}/supplier/1")
r = s.post(f"{BASE}/supplier/1/delete", data={"csrf_token": csrf})
check("Delete supplier", r.status_code == 302)

# 11. NAVIGATION
print("\n[11] NAVIGATION")
r = s.get(f"{BASE}/")
check("Supplier nav link", "Data Supplier" in r.text)
check("Pembelian nav link", "Pembelian" in r.text)

# 12. SECURITY HEADERS
print("\n[12] SECURITY HEADERS")
r = s.get(f"{BASE}/login")
check("CSP header", "Content-Security-Policy" in r.headers)
check("X-Frame-Options", r.headers.get("X-Frame-Options") == "DENY")
check("X-Content-Type-Options", r.headers.get("X-Content-Type-Options") == "nosniff")

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
