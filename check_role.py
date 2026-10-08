#!/usr/bin/env python3
import sqlite3, json

db = sqlite3.connect("/home/choirulhaq/venvProject/testopencode/database.db")
db.row_factory = sqlite3.Row

# Check admin user
user = db.execute("SELECT * FROM users WHERE username=?", ("admin",)).fetchone()
print(f"User: id={user['id']}, username={user['username']}, role_id={user['role_id']}")

# Check admin role + perms
role = db.execute("SELECT * FROM roles WHERE id=?", (user["role_id"],)).fetchone()
perms = json.loads(role["permissions"]) if role["permissions"] else {}
print(f"Role: {role['nama']}, permissions keys: {list(perms.keys())}")
print(f"penjualan perms: {perms.get('penjualan', 'NOT FOUND')}")
print(f"supplier perms: {perms.get('supplier', 'NOT FOUND')}")
print(f"pembelian perms: {perms.get('pembelian', 'NOT FOUND')}")

db.close()
