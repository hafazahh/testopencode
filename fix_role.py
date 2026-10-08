import sqlite3, json

db = sqlite3.connect("/home/choirulhaq/venvProject/testopencode/database.db")

perms = {
    "items": ["view", "create", "edit", "delete"],
    "kategori": ["view", "create", "edit", "delete"],
    "pelanggan": ["view", "create", "edit", "delete"],
    "users": ["view", "create", "edit", "delete"],
    "roles": ["view", "create", "edit", "delete"],
    "supplier": ["view", "create", "edit", "delete"],
    "pembelian": ["view", "create", "delete"],
    "penjualan": ["view", "create", "delete"]
}

db.execute("UPDATE roles SET permissions=? WHERE nama=?", (json.dumps(perms), "admin"))
db.commit()

row = db.execute("SELECT permissions FROM roles WHERE nama=?", ("admin",)).fetchone()
p = json.loads(row[0])
print(f"penjualan permission: {p.get('penjualan')}")
print("Role admin updated OK")
db.close()
