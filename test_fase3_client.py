#!/usr/bin/env python3
"""Test Fase 3 pakai Flask test client (bypass CSRF + permission issue)"""
import sys, os
sys.path.insert(0, "/home/choirulhaq/venvProject/testopencode")
os.chdir("/home/choirulhaq/venvProject/testopencode")

from app import app, init_db
import sqlite3, json

init_db()

# Update role admin dengan permission penjualan
db = sqlite3.connect("database.db")
perms = {
    "items": ["view", "create", "edit", "delete"],
    "kategori": ["view", "create", "edit", "delete"],
    "pelanggan": ["view", "create", "edit", "delete"],
    "users": ["view", "create", "edit", "delete"],
    "roles": ["view", "create", "edit", "delete"],
    "supplier": ["view", "create", "edit", "delete"],
    "pembelian": ["view", "create", "delete"],
    "penjualan": ["view", "create", "delete"],
}
db.execute("UPDATE roles SET permissions=? WHERE nama=?", (json.dumps(perms), "admin"))
db.commit()
db.close()

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False
client = app.test_client()

results = []
def check(name, condition, detail=""):
    status = "✅" if condition else "❌"
    results.append((name, condition))
    print(f"  {status} {name}" + (f" — {detail}" if detail else ""))

print("=" * 60)
print("FASE 3 TEST (Flask test client)")
print("=" * 60)

# Clean DB
db = sqlite3.connect("database.db")
for t in ["stok_mutasi", "stok_akhir", "penjualan_detail", "penjualan", "pembelian_detail", "pembelian", "supplier"]:
    db.execute(f"DELETE FROM {t}")
db.commit()
db.close()

# Login
print("\n[1] LOGIN")
r = client.post("/login", data={"username": "admin", "password": "admin123"})
check("Login", r.status_code == 302)

# Setup supplier
print("\n[2] SETUP: Supplier")
r = client.post("/supplier/create", data={"nama": "CV Test", "kontak": "Budi", "alamat": "Jl Test"})
check("Create supplier", r.status_code == 302)

# Setup pelanggan
print("\n[3] SETUP: Pelanggan")
r = client.post("/pelanggan/create", data={"nama": "Pak Andi", "email": "a@t.com", "telepon": "081234", "alamat": "Jl"})
check("Create pelanggan", r.status_code == 302)

# Setup pembelian
print("\n[4] SETUP: Pembelian (stok masuk)")
r = client.post("/pembelian/create", data={
    "supplier_id": "1", "tanggal": "2026-10-07", "catatan": "Stok awal",
    "item_id[]": ["1", "2"], "qty[]": ["100", "50"], "harga_beli[]": ["50000", "30000"]
})
check("Create pembelian", r.status_code == 302)

db = sqlite3.connect("database.db")
db.row_factory = sqlite3.Row
stok = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir item1=100", len(stok) >= 1 and stok[0]['qty_akhir'] == 100.0)
check("stok_akhir item2=50", len(stok) >= 2 and stok[1]['qty_akhir'] == 50.0)

# Penjualan list
print("\n[5] PENJUALAN LIST")
r = client.get("/penjualan")
check("/penjualan OK", r.status_code == 200)

# Create penjualan (2 items)
print("\n[6] CREATE PENJUALAN (2 items)")
r = client.post("/penjualan/create", data={
    "pelanggan_id": "1", "tanggal": "2026-10-07", "catatan": "",
    "item_id[]": ["1", "2"], "qty[]": ["30", "20"], "harga_jual[]": ["60000", "35000"]
})
check("Create penjualan", r.status_code == 302, f"status={r.status_code}")

# Verify DB
print("\n[7] VERIFY DB")
stok = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir item1=70", stok[0]['qty_akhir'] == 70.0, f"qty={stok[0]['qty_akhir']}")
check("stok_akhir item2=30", stok[1]['qty_akhir'] == 30.0, f"qty={stok[1]['qty_akhir']}")

mutasi = db.execute("SELECT * FROM stok_mutasi WHERE jenis_mutasi='OUT'").fetchall()
check("stok_mutasi OUT: 2 row", len(mutasi) == 2, f"count={len(mutasi)}")
for m in mutasi:
    print(f"    item={m['item_id']}, OUT, qty={m['qty']}, saldo={m['saldo_berjalan']}")

penj = db.execute("SELECT * FROM penjualan").fetchall()
check("penjualan 1 row", len(penj) == 1)
if penj:
    print(f"    nomor={penj[0]['nomor_transaksi']}, total={penj[0]['total']}")
    check("Nomor PJ-2026-0001", penj[0]['nomor_transaksi'] == "PJ-2026-0001")

detail = db.execute("SELECT * FROM penjualan_detail").fetchall()
check("penjualan_detail 2 row", len(detail) == 2)
for d in detail:
    print(f"    item={d['item_id']}, qty={d['qty']}, harga_jual={d['harga_jual']}, harga_pokok={d['harga_pokok']}")
    check(f"HPP snapshot item {d['item_id']}", d['harga_pokok'] > 0)

# Validate stok: jual melebihi stok
print("\n[8] VALIDASI STOK: jual melebihi stok")
r = client.post("/penjualan/create", data={
    "pelanggan_id": "1", "tanggal": "2026-10-07", "catatan": "",
    "item_id[]": ["1"], "qty[]": ["999"], "harga_jual[]": ["60000"]
})
check("Stok tidak cukup ditolak", "tidak cukup" in r.data.decode().lower())

# Delete penjualan (rollback)
print("\n[9] DELETE PENJUALAN")
r = client.post("/penjualan/1/delete")
check("Delete penjualan", r.status_code == 302)

stok = db.execute("SELECT * FROM stok_akhir").fetchall()
check("stok_akhir item1=100 (rollback)", stok[0]['qty_akhir'] == 100.0)
check("stok_akhir item2=50 (rollback)", stok[1]['qty_akhir'] == 50.0)

mutasi = db.execute("SELECT COUNT(*) FROM stok_mutasi WHERE jenis_mutasi='OUT'").fetchone()[0]
check("stok_mutasi OUT kosong", mutasi == 0)

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
