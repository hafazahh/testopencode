#!/usr/bin/env python3
"""Test script for TestOpenCode enhancement."""
import sys
import os
import re

# Add project to path
sys.path.insert(0, '/home/choirulhaq/GoogleDrive/AhliPemrograman/testopencode')

from app import app, init_db, CATEGORIES


def get_csrf_token(client, url):
    """GET a page and extract the CSRF token from the hidden input."""
    resp = client.get(url)
    match = re.search(r'name="csrf_token"\s+value="([^"]+)"', resp.data.decode())
    return match.group(1) if match else None

def test_init_db():
    """Test database initialization."""
    print("=== Testing DB Init ===")
    init_db()
    print("DB initialized OK")
    
    # Check tables exist
    from app import get_db, DATABASE
    import sqlite3
    db = sqlite3.connect(DATABASE)
    
    # Check items table has category column
    cursor = db.execute("PRAGMA table_info(items)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Items columns: {columns}")
    assert 'category' in columns, "category column missing from items!"
    print("✓ category column exists in items")
    
    # Check pelanggan table exists
    cursor = db.execute("PRAGMA table_info(pelanggan)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"Pelanggan columns: {columns}")
    expected = ['id', 'nama', 'email', 'telepon', 'alamat', 'created_at']
    for col in expected:
        assert col in columns, f"{col} missing from pelanggan!"
    print("✓ pelanggan table has all required columns")
    
    db.close()
    return True

def test_categories():
    """Test category source of truth (DB-backed) and deprecated constant."""
    print("\n=== Testing Categories ===")
    print(f"Deprecated constant: {CATEGORIES}")
    assert 'Elektronik' in CATEGORIES
    assert 'Makanan' in CATEGORIES
    assert 'Pakaian' in CATEGORIES
    assert 'Lainnya' in CATEGORIES
    # Real source of truth: the kategori table
    import sqlite3
    from app import DATABASE
    db = sqlite3.connect(DATABASE)
    names = [r[0] for r in db.execute('SELECT nama FROM kategori')]
    db.close()
    for cat in ['Elektronik', 'Makanan', 'Pakaian', 'Lainnya']:
        assert cat in names, f"{cat} missing from kategori table"
    print(f"✓ Categories present in DB: {names}")
    return True

def test_routes():
    """Test all routes are registered."""
    print("\n=== Testing Routes ===")
    with app.test_client() as client:
        # Test item routes
        resp = client.get('/')
        assert resp.status_code == 200, f"GET / failed: {resp.status_code}"
        print("✓ GET / (item list)")
        
        resp = client.get('/create')
        assert resp.status_code == 200, f"GET /create failed: {resp.status_code}"
        print("✓ GET /create (item create form)")
        
        # Test pelanggan routes
        resp = client.get('/pelanggan')
        assert resp.status_code == 200, f"GET /pelanggan failed: {resp.status_code}"
        print("✓ GET /pelanggan (pelanggan list)")
        
        resp = client.get('/pelanggan/create')
        assert resp.status_code == 200, f"GET /pelanggan/create failed: {resp.status_code}"
        print("✓ GET /pelanggan/create (pelanggan create form)")
    return True

def test_item_crud():
    """Test item CRUD operations."""
    print("\n=== Testing Item CRUD ===")
    with app.test_client() as client:
        # Create
        csrf = get_csrf_token(client, '/create')
        resp = client.post('/create', data={
            'nama': 'Test Item',
            'harga_pokok': '10000',
            'harga_jual': '15000',
            'category': 'Elektronik',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert resp.status_code == 200, f"Create item failed: {resp.status_code}"
        print("✓ Create item")
        
        # Read (list)
        resp = client.get('/')
        assert b'Test Item' in resp.data, "Item not found in list"
        assert b'Elektronik' in resp.data, "Category not found in list"
        print("✓ Read item (list)")
        
        # Read (detail) - get item id from DB
        import sqlite3
        db = sqlite3.connect('/home/choirulhaq/GoogleDrive/AhliPemrograman/testopencode/database.db')
        item = db.execute("SELECT id FROM items WHERE nama = 'Test Item'").fetchone()
        db.close()
        item_id = item[0]
        
        resp = client.get(f'/item/{item_id}')
        assert resp.status_code == 200, f"View item failed: {resp.status_code}"
        assert b'Test Item' in resp.data
        assert b'Elektronik' in resp.data
        print("✓ Read item (detail)")
        
        # Update
        csrf = get_csrf_token(client, f'/item/{item_id}/edit')
        resp = client.post(f'/item/{item_id}/edit', data={
            'nama': 'Test Item Updated',
            'harga_pokok': '12000',
            'harga_jual': '18000',
            'category': 'Makanan',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert resp.status_code == 200, f"Update item failed: {resp.status_code}"
        print("✓ Update item")
        
        # Delete
        csrf = get_csrf_token(client, f'/item/{item_id}')
        resp = client.post(f'/item/{item_id}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        assert resp.status_code == 200, f"Delete item failed: {resp.status_code}"
        print("✓ Delete item")
    return True

def test_pelanggan_crud():
    """Test pelanggan CRUD operations."""
    print("\n=== Testing Pelanggan CRUD ===")
    with app.test_client() as client:
        # Create
        csrf = get_csrf_token(client, '/pelanggan/create')
        resp = client.post('/pelanggan/create', data={
            'nama': 'Budi Santoso',
            'email': 'budi@example.com',
            'telepon': '081234567890',
            'alamat': 'Jl. Merdeka No. 1',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert resp.status_code == 200, f"Create pelanggan failed: {resp.status_code}"
        print("✓ Create pelanggan")
        
        # Read (list)
        resp = client.get('/pelanggan')
        assert b'Budi Santoso' in resp.data, "Pelanggan not found in list"
        print("✓ Read pelanggan (list)")
        
        # Read (detail)
        import sqlite3
        db = sqlite3.connect('/home/choirulhaq/GoogleDrive/AhliPemrograman/testopencode/database.db')
        p = db.execute("SELECT id FROM pelanggan WHERE nama = 'Budi Santoso'").fetchone()
        db.close()
        p_id = p[0]
        
        resp = client.get(f'/pelanggan/{p_id}')
        assert resp.status_code == 200, f"View pelanggan failed: {resp.status_code}"
        assert b'Budi Santoso' in resp.data
        assert b'budi@example.com' in resp.data
        print("✓ Read pelanggan (detail)")
        
        # Update
        csrf = get_csrf_token(client, f'/pelanggan/{p_id}/edit')
        resp = client.post(f'/pelanggan/{p_id}/edit', data={
            'nama': 'Budi Santoso Updated',
            'email': 'budi.updated@example.com',
            'telepon': '081234567891',
            'alamat': 'Jl. Merdeka No. 2',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert resp.status_code == 200, f"Update pelanggan failed: {resp.status_code}"
        print("✓ Update pelanggan")
        
        # Delete
        csrf = get_csrf_token(client, f'/pelanggan/{p_id}')
        resp = client.post(f'/pelanggan/{p_id}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        assert resp.status_code == 200, f"Delete pelanggan failed: {resp.status_code}"
        print("✓ Delete pelanggan")
    return True

def test_validation():
    """Test form validation."""
    print("\n=== Testing Validation ===")
    with app.test_client() as client:
        # Item: missing nama
        csrf = get_csrf_token(client, '/create')
        resp = client.post('/create', data={
            'nama': '',
            'harga_pokok': '10000',
            'harga_jual': '15000',
            'category': 'Elektronik',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Nama item wajib diisi' in resp.data
        print("✓ Item validation: nama required")
        
        # Item: invalid category
        csrf = get_csrf_token(client, '/create')
        resp = client.post('/create', data={
            'nama': 'Test',
            'harga_pokok': '10000',
            'harga_jual': '15000',
            'category': 'InvalidCategory',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Kategori tidak valid' in resp.data
        print("✓ Item validation: invalid category")
        
        # Pelanggan: missing nama
        csrf = get_csrf_token(client, '/pelanggan/create')
        resp = client.post('/pelanggan/create', data={
            'nama': '',
            'email': 'test@example.com',
            'telepon': '081234567890',
            'alamat': 'Test',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Nama pelanggan wajib diisi' in resp.data
        print("✓ Pelanggan validation: nama required")
        
        # Pelanggan: invalid email
        csrf = get_csrf_token(client, '/pelanggan/create')
        resp = client.post('/pelanggan/create', data={
            'nama': 'Test',
            'email': 'invalid-email',
            'telepon': '081234567890',
            'alamat': 'Test',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Format email tidak valid' in resp.data
        print("✓ Pelanggan validation: invalid email")
        
        # Pelanggan: invalid telepon
        csrf = get_csrf_token(client, '/pelanggan/create')
        resp = client.post('/pelanggan/create', data={
            'nama': 'Test',
            'email': 'test@example.com',
            'telepon': 'abc123',
            'alamat': 'Test',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Nomor telepon hanya boleh angka' in resp.data
        print("✓ Pelanggan validation: invalid telepon")
    return True

def test_navigation():
    """Test navigation menu."""
    print("\n=== Testing Navigation ===")
    with app.test_client() as client:
        resp = client.get('/')
        assert b'Data Pelanggan' in resp.data, "Data Pelanggan menu not found"
        assert b'/pelanggan' in resp.data, "Pelanggan link not found"
        assert b'Data Kategori' in resp.data, "Data Kategori menu not found"
        assert b'/kategori' in resp.data, "Kategori link not found"
        print("✓ Navigation: Data Pelanggan + Data Kategori menus present")
    return True


def test_kategori_table():
    """Test kategori table schema and seeding."""
    print("\n=== Testing Kategori Table ===")
    import sqlite3
    from app import DATABASE
    db = sqlite3.connect(DATABASE)
    cols = [r[1] for r in db.execute('PRAGMA table_info(kategori)')]
    print(f"Kategori columns: {cols}")
    for col in ['id', 'nama', 'deskripsi', 'created_at']:
        assert col in cols, f"{col} missing from kategori!"
    print("✓ kategori table has all required columns")

    rows = [r[0] for r in db.execute('SELECT nama FROM kategori')]
    db.close()
    for seed in ['Elektronik', 'Makanan', 'Pakaian', 'Lainnya']:
        assert seed in rows, f"Seed '{seed}' missing!"
    print(f"✓ kategori pre-seeded: {rows}")
    return True


def test_kategori_routes():
    """Test kategori routes are registered and reachable."""
    print("\n=== Testing Kategori Routes ===")
    with app.test_client() as client:
        resp = client.get('/kategori')
        assert resp.status_code == 200, f"GET /kategori failed: {resp.status_code}"
        print("✓ GET /kategori (kategori list)")

        resp = client.get('/kategori/create')
        assert resp.status_code == 200, f"GET /kategori/create failed: {resp.status_code}"
        print("✓ GET /kategori/create (kategori create form)")
    return True


def test_kategori_crud():
    """Test kategori CRUD operations."""
    print("\n=== Testing Kategori CRUD ===")
    import sqlite3
    from app import DATABASE
    with app.test_client() as client:
        # Create
        csrf = get_csrf_token(client, '/kategori/create')
        resp = client.post('/kategori/create', data={
            'nama': 'Test Kategori',
            'deskripsi': 'Deskripsi test',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Kategori berhasil ditambahkan' in resp.data, "Create kategori failed"
        print("✓ Create kategori")

        # Read (list)
        resp = client.get('/kategori')
        assert b'Test Kategori' in resp.data, "Kategori not found in list"
        print("✓ Read kategori (list)")

        db = sqlite3.connect(DATABASE)
        kid = db.execute("SELECT id FROM kategori WHERE nama = 'Test Kategori'").fetchone()[0]
        db.close()

        # Read (detail)
        resp = client.get(f'/kategori/{kid}')
        assert resp.status_code == 200, f"View kategori failed: {resp.status_code}"
        assert b'Test Kategori' in resp.data
        print("✓ Read kategori (detail)")

        # Update
        csrf = get_csrf_token(client, f'/kategori/{kid}/edit')
        resp = client.post(f'/kategori/{kid}/edit', data={
            'nama': 'Test Kategori Updated',
            'deskripsi': 'Deskripsi updated',
            'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Kategori berhasil diperbarui' in resp.data, "Update kategori failed"
        assert b'Test Kategori Updated' in client.get('/kategori').data
        print("✓ Update kategori")

        # Delete
        csrf = get_csrf_token(client, f'/kategori/{kid}')
        resp = client.post(f'/kategori/{kid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        assert b'Kategori berhasil dihapus' in resp.data, "Delete kategori failed"
        print("✓ Delete kategori")
    return True


def test_kategori_duplicate():
    """Test case-insensitive duplicate name rejection."""
    print("\n=== Testing Kategori Duplicate ===")
    import sqlite3
    from app import DATABASE
    with app.test_client() as client:
        csrf = get_csrf_token(client, '/kategori/create')
        resp = client.post('/kategori/create', data={
            'nama': 'elektronik',  # lowercase of seeded 'Elektronik'
            'csrf_token': csrf
        }, follow_redirects=True)
        assert b'sudah ada' in resp.data, "Duplicate not rejected"
        db = sqlite3.connect(DATABASE)
        n = db.execute("SELECT COUNT(*) FROM kategori WHERE LOWER(nama) = 'elektronik'").fetchone()[0]
        db.close()
        assert n == 1, f"Duplicate inserted (count={n})"
        print("✓ Duplicate kategori (case-insensitive) rejected")
    return True


def test_kategori_delete_protection():
    """Test delete is blocked when items reference the kategori."""
    print("\n=== Testing Kategori Delete Protection ===")
    import sqlite3
    from app import DATABASE
    with app.test_client() as client:
        # Create kategori + item referencing it
        csrf = get_csrf_token(client, '/kategori/create')
        client.post('/kategori/create', data={'nama': 'Protect Test', 'csrf_token': csrf}, follow_redirects=True)
        db = sqlite3.connect(DATABASE)
        kid = db.execute("SELECT id FROM kategori WHERE nama = 'Protect Test'").fetchone()[0]
        db.close()

        csrf = get_csrf_token(client, '/create')
        client.post('/create', data={
            'nama': 'Protected Item', 'harga_pokok': '1000', 'harga_jual': '2000',
            'category': 'Protect Test', 'csrf_token': csrf
        }, follow_redirects=True)
        db = sqlite3.connect(DATABASE)
        iid = db.execute("SELECT id FROM items WHERE nama = 'Protected Item'").fetchone()[0]
        db.close()

        # Attempt delete -> blocked
        csrf = get_csrf_token(client, f'/kategori/{kid}')
        resp = client.post(f'/kategori/{kid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        assert 'tidak dapat dihapus'.encode() in resp.data, "Delete was not blocked"
        db = sqlite3.connect(DATABASE)
        still = db.execute("SELECT COUNT(*) FROM kategori WHERE id = ?", (kid,)).fetchone()[0]
        db.close()
        assert still == 1, "Kategori was deleted despite items referencing it"
        print("✓ Delete blocked while items reference kategori")

        # Cleanup: remove item then delete kategori
        csrf = get_csrf_token(client, f'/item/{iid}')
        client.post(f'/item/{iid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        csrf = get_csrf_token(client, f'/kategori/{kid}')
        resp = client.post(f'/kategori/{kid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        assert b'Kategori berhasil dihapus' in resp.data, "Delete after unreference failed"
        print("✓ Delete succeeds once no items reference kategori")
    return True


def test_kategori_rename_cascade():
    """Test renaming a kategori cascades to items.category."""
    print("\n=== Testing Kategori Rename Cascade ===")
    import sqlite3
    from app import DATABASE
    with app.test_client() as client:
        csrf = get_csrf_token(client, '/kategori/create')
        client.post('/kategori/create', data={'nama': 'Cascade Test', 'csrf_token': csrf}, follow_redirects=True)
        db = sqlite3.connect(DATABASE)
        kid = db.execute("SELECT id FROM kategori WHERE nama = 'Cascade Test'").fetchone()[0]
        db.close()

        csrf = get_csrf_token(client, '/create')
        client.post('/create', data={
            'nama': 'Cascade Item', 'harga_pokok': '1000', 'harga_jual': '2000',
            'category': 'Cascade Test', 'csrf_token': csrf
        }, follow_redirects=True)
        db = sqlite3.connect(DATABASE)
        iid = db.execute("SELECT id FROM items WHERE nama = 'Cascade Item'").fetchone()[0]
        db.close()

        csrf = get_csrf_token(client, f'/kategori/{kid}/edit')
        resp = client.post(f'/kategori/{kid}/edit', data={
            'nama': 'Cascade Renamed', 'deskripsi': '', 'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Kategori berhasil diperbarui' in resp.data
        db = sqlite3.connect(DATABASE)
        cat = db.execute("SELECT category FROM items WHERE id = ?", (iid,)).fetchone()[0]
        db.close()
        assert cat == 'Cascade Renamed', f"Rename not cascaded (got {cat})"
        print("✓ Rename cascaded to items.category")

        # Cleanup
        csrf = get_csrf_token(client, f'/item/{iid}')
        client.post(f'/item/{iid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        csrf = get_csrf_token(client, f'/kategori/{kid}')
        client.post(f'/kategori/{kid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
    return True


def test_kategori_edit_error_path():
    """Test edit_kategori error path re-renders with preserved values."""
    print("\n=== Testing Kategori Edit Error Path ===")
    import sqlite3
    from app import DATABASE
    with app.test_client() as client:
        csrf = get_csrf_token(client, '/kategori/create')
        client.post('/kategori/create', data={'nama': 'ErrPath Test', 'csrf_token': csrf}, follow_redirects=True)
        db = sqlite3.connect(DATABASE)
        kid = db.execute("SELECT id FROM kategori WHERE nama = 'ErrPath Test'").fetchone()[0]
        db.close()

        # Empty nama -> error, form re-renders
        csrf = get_csrf_token(client, f'/kategori/{kid}/edit')
        resp = client.post(f'/kategori/{kid}/edit', data={
            'nama': '', 'deskripsi': 'keep me', 'csrf_token': csrf
        }, follow_redirects=True)
        assert 'wajib diisi'.encode() in resp.data, "Validation error not shown"
        assert b'keep me' in resp.data, "Submitted deskripsi not preserved"
        print("✓ Edit error path re-renders with preserved values")

        # Cleanup
        csrf = get_csrf_token(client, f'/kategori/{kid}')
        client.post(f'/kategori/{kid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
    return True


def test_item_form_dynamic_category():
    """Test item forms render categories from DB, not a hardcoded list."""
    print("\n=== Testing Item Form Dynamic Categories ===")
    with app.test_client() as client:
        csrf = get_csrf_token(client, '/kategori/create')
        client.post('/kategori/create', data={'nama': 'Dynamic Test', 'csrf_token': csrf}, follow_redirects=True)

        resp = client.get('/create')
        assert b'Dynamic Test' in resp.data, "New kategori not shown in item create form"
        print("✓ Item create form shows DB categories")

        # Item can be saved with the new kategori
        csrf = get_csrf_token(client, '/create')
        resp = client.post('/create', data={
            'nama': 'Dynamic Item', 'harga_pokok': '1000', 'harga_jual': '2000',
            'category': 'Dynamic Test', 'csrf_token': csrf
        }, follow_redirects=True)
        assert b'Item berhasil ditambahkan' in resp.data, "Item with dynamic kategori failed"
        print("✓ Item saved with DB kategori")

        import sqlite3
        from app import DATABASE
        db = sqlite3.connect(DATABASE)
        iid = db.execute("SELECT id FROM items WHERE nama = 'Dynamic Item'").fetchone()[0]
        kid = db.execute("SELECT id FROM kategori WHERE nama = 'Dynamic Test'").fetchone()[0]
        db.close()

        # Cleanup
        csrf = get_csrf_token(client, f'/item/{iid}')
        client.post(f'/item/{iid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
        csrf = get_csrf_token(client, f'/kategori/{kid}')
        client.post(f'/kategori/{kid}/delete', data={'csrf_token': csrf}, follow_redirects=True)
    return True


def test_kategori_csrf():
    """Test CSRF protection on kategori forms."""
    print("\n=== Testing Kategori CSRF Protection ===")
    with app.test_client() as client:
        resp = client.post('/kategori/create', data={'nama': 'NoCSRF'}, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Akses ditolak' in resp.data, "Expected 'Akses ditolak' for missing CSRF"
        print("✓ POST /kategori/create without CSRF token rejected")
    return True


def test_kategori_404():
    """Test missing kategori redirects with an Indonesian flash."""
    print("\n=== Testing Kategori 404 ===")
    with app.test_client() as client:
        resp = client.get('/kategori/999999', follow_redirects=True)
        assert resp.status_code == 200
        assert b'Kategori tidak ditemukan' in resp.data, "404 flash missing"
        print("✓ Missing kategori -> flash 'Kategori tidak ditemukan!'")
    return True


def test_item_price_validation_regression():
    """Regression: non-numeric/negative/NaN/Inf prices must not 500."""
    print("\n=== Testing Item Price Validation Regression ===")
    import sqlite3
    from app import DATABASE
    with app.test_client() as client:
        # Non-numeric price -> clean error, NOT internal error
        csrf = get_csrf_token(client, '/create')
        resp = client.post('/create', data={
            'nama': 'Bad Price', 'harga_pokok': 'abc', 'harga_jual': '2000',
            'category': 'Elektronik', 'csrf_token': csrf
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'harus berupa angka' in resp.data, "Non-numeric price not rejected cleanly"
        assert b'kesalahan internal' not in resp.data, "500 handler triggered (TypeError)"
        print("✓ Non-numeric price rejected without 500")

        # Negative price
        csrf = get_csrf_token(client, '/create')
        resp = client.post('/create', data={
            'nama': 'Neg Price', 'harga_pokok': '-5', 'harga_jual': '2000',
            'category': 'Elektronik', 'csrf_token': csrf
        }, follow_redirects=True)
        assert b'tidak boleh negatif' in resp.data, "Negative price not rejected"
        print("✓ Negative price rejected")

        # Infinite price -> rejected and not stored
        csrf = get_csrf_token(client, '/create')
        resp = client.post('/create', data={
            'nama': 'Inf Price', 'harga_pokok': '1e999', 'harga_jual': '2000',
            'category': 'Elektronik', 'csrf_token': csrf
        }, follow_redirects=True)
        assert b'kesalahan internal' not in resp.data, "Inf price triggered 500"
        db = sqlite3.connect(DATABASE)
        cnt = db.execute("SELECT COUNT(*) FROM items WHERE nama = 'Inf Price'").fetchone()[0]
        db.close()
        assert cnt == 0, "Infinite price was stored"
        print("✓ Infinite price rejected and not stored")
    return True


def test_csrf_protection():
    """Test that POST requests without CSRF token are rejected."""
    print("\n=== Testing CSRF Protection ===")
    with app.test_client() as client:
        # POST without CSRF token should be rejected (403 -> redirect with error)
        resp = client.post('/create', data={
            'nama': 'Test',
            'harga_pokok': '10000',
            'harga_jual': '15000',
            'category': 'Elektronik'
        }, follow_redirects=True)
        assert resp.status_code == 200, f"Expected 200 (redirect), got {resp.status_code}"
        assert b'Akses ditolak' in resp.data, "Expected 'Akses ditolak' error message"
        print("✓ POST without CSRF token rejected")
        
        # POST with wrong CSRF token should be rejected
        resp = client.post('/create', data={
            'nama': 'Test',
            'harga_pokok': '10000',
            'harga_jual': '15000',
            'category': 'Elektronik',
            'csrf_token': 'wrong-token'
        }, follow_redirects=True)
        assert resp.status_code == 200, f"Expected 200 (redirect), got {resp.status_code}"
        assert b'Akses ditolak' in resp.data, "Expected 'Akses ditolak' error message"
        print("✓ POST with wrong CSRF token rejected")
    return True


def test_migration_default_category():
    """Test that existing items get default category on migration."""
    print("\n=== Testing Migration Default Category ===")
    import sqlite3
    db = sqlite3.connect('/home/choirulhaq/GoogleDrive/AhliPemrograman/testopencode/database.db')
    # Check no items have NULL or empty category
    cursor = db.execute("SELECT COUNT(*) FROM items WHERE category IS NULL OR category = ''")
    count = cursor.fetchone()[0]
    db.close()
    assert count == 0, f"Found {count} items with NULL or empty category"
    print("✓ All items have valid category (no NULL/empty)")
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("TestOpenCode Enhancement - Test Suite")
    print("=" * 50)
    
    tests = [
        test_init_db,
        test_categories,
        test_routes,
        test_item_crud,
        test_pelanggan_crud,
        test_validation,
        test_navigation,
        test_kategori_table,
        test_kategori_routes,
        test_kategori_crud,
        test_kategori_duplicate,
        test_kategori_delete_protection,
        test_kategori_rename_cascade,
        test_kategori_edit_error_path,
        test_item_form_dynamic_category,
        test_kategori_csrf,
        test_kategori_404,
        test_item_price_validation_regression,
        test_csrf_protection,
        test_migration_default_category,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    sys.exit(0 if failed == 0 else 1)
