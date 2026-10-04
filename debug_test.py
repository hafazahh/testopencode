#!/usr/bin/env python3
"""Debug script for item detail test."""
import sys
sys.path.insert(0, '/home/choirulhaq/GoogleDrive/AhliPemrograman/testopencode')

from app import app, init_db
import sqlite3

init_db()

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
    db = sqlite3.connect('/home/choirulhaq/GoogleDrive/AhliPemrograman/testopencode/database.db')
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
