#!/usr/bin/env python3
"""Debug script for item category test."""
import sys
sys.path.insert(0, '/home/choirulhaq/GoogleDrive/AhliPemrograman/testopencode')

from app import app, init_db, CATEGORIES, DATABASE
import sqlite3
import os

# Remove old database to start fresh
if os.path.exists(DATABASE):
    os.remove(DATABASE)
    print(f"Removed old database: {DATABASE}")

init_db()

# Check schema
db = sqlite3.connect(DATABASE)
cursor = db.execute("PRAGMA table_info(items)")
columns = cursor.fetchall()
print("Items table schema:")
for col in columns:
    print(f"  {col}")
db.close()

with app.test_client() as client:
    # Create item
    resp = client.post('/create', data={
        'nama': 'Test Item',
        'harga_pokok': '10000',
        'harga_jual': '15000',
        'category': 'Elektronik'
    }, follow_redirects=True)
    print('Create status:', resp.status_code)
    
    # Get item id
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    item = db.execute("SELECT * FROM items WHERE nama = 'Test Item'").fetchone()
    print('Item from DB:', dict(item))
    item_id = item['id']
    db.close()
    
    # View item
    resp = client.get(f'/item/{item_id}')
    print('View status:', resp.status_code)
    print('Has Test Item:', b'Test Item' in resp.data)
    print('Has Elektronik:', b'Elektronik' in resp.data)
    # Print relevant part of response
    text = resp.data.decode('utf-8')
    # Find the detail section
    idx = text.find('Detail Item')
    if idx >= 0:
        print('Detail section:', text[idx:idx+500])
    else:
        print('Detail Item not found in response')
        print('Full response:', text[:3000])
