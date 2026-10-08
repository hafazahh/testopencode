#!/usr/bin/env python3
"""Test login + access penjualan via Flask test client"""
import sys, os, json, re
sys.path.insert(0, "/home/choirulhaq/venvProject/testopencode")
os.chdir("/home/choirulhaq/venvProject/testopencode")

from app import app, init_db
init_db()

app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False  # Bypass CSRF for testing
client = app.test_client()

print("=== LOGIN ===")
r = client.post("/login", data={"username": "admin", "password": "admin123"})
print(f"Status: {r.status_code}")

print("\n=== /penjualan ===")
r = client.get("/penjualan")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ /penjualan accessible")
elif r.status_code == 302:
    print(f"Redirect to: {r.headers.get('Location')}")
elif r.status_code == 403:
    print("❌ 403 Forbidden - permission issue")
else:
    print(f"Unexpected: {r.status_code}")

print("\n=== /supplier ===")
r = client.get("/supplier")
print(f"Status: {r.status_code}")
if r.status_code == 200:
    print("✅ /supplier accessible")
