"""Test Fase 5: RBAC untuk menu baru (stok, laporan) + seed role kasir/gudang."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, get_db, init_db
import json

def test_seed_roles():
    """Test bahwa role kasir dan gudang sudah di-seed."""
    with app.app_context():
        init_db()
        db = get_db()
        
        # Cek role kasir
        kasir = db.execute("SELECT * FROM roles WHERE nama = 'kasir'").fetchone()
        assert kasir is not None, "Role kasir tidak ditemukan"
        kasir_perms = json.loads(kasir['permissions'])
        assert 'penjualan' in kasir_perms, "Kasir harus punya akses penjualan"
        assert 'view' in kasir_perms['penjualan'], "Kasir harus bisa view penjualan"
        assert 'create' in kasir_perms['penjualan'], "Kasir harus bisa create penjualan"
        assert 'laporan' in kasir_perms, "Kasir harus punya akses laporan"
        assert 'stok' in kasir_perms, "Kasir harus punya akses stok"
        assert 'items' in kasir_perms, "Kasir harus punya akses items"
        assert 'users' not in kasir_perms, "Kasir TIDAK boleh punya akses users"
        assert 'roles' not in kasir_perms, "Kasir TIDAK boleh punya akses roles"
        
        # Cek role gudang
        gudang = db.execute("SELECT * FROM roles WHERE nama = 'gudang'").fetchone()
        assert gudang is not None, "Role gudang tidak ditemukan"
        gudang_perms = json.loads(gudang['permissions'])
        assert 'supplier' in gudang_perms, "Gudang harus punya akses supplier"
        assert 'pembelian' in gudang_perms, "Gudang harus punya akses pembelian"
        assert 'stok' in gudang_perms, "Gudang harus punya akses stok"
        assert 'items' in gudang_perms, "Gudang harus punya akses items"
        assert 'penjualan' in gudang_perms, "Gudang harus punya akses penjualan (view only)"
        assert 'view' in gudang_perms['penjualan'], "Gudang harus bisa view penjualan"
        assert 'create' not in gudang_perms['penjualan'], "Gudang TIDAK boleh create penjualan"
        assert 'users' not in gudang_perms, "Gudang TIDAK boleh punya akses users"
        assert 'roles' not in gudang_perms, "Gudang TIDAK boleh punya akses roles"
        
        print("✅ test_seed_roles passed")

def test_admin_full_perms():
    """Test bahwa admin punya akses penuh termasuk stok dan laporan."""
    with app.app_context():
        init_db()
        db = get_db()
        
        admin = db.execute("SELECT * FROM roles WHERE nama = 'admin'").fetchone()
        assert admin is not None, "Role admin tidak ditemukan"
        admin_perms = json.loads(admin['permissions'])
        
        assert 'stok' in admin_perms, "Admin harus punya akses stok"
        assert 'view' in admin_perms['stok'], "Admin harus bisa view stok"
        assert 'laporan' in admin_perms, "Admin harus punya akses laporan"
        assert 'view' in admin_perms['laporan'], "Admin harus bisa view laporan"
        
        print("✅ test_admin_full_perms passed")

def test_nav_visibility():
    """Test bahwa nav base.html menyembunyikan link berdasarkan permission."""
    with app.test_client() as client:
        # Login sebagai admin
        with client.session_transaction() as sess:
            sess['user_id'] = 1  # admin
        
        resp = client.get('/')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        
        # Admin harus melihat semua link
        assert 'Kartu Stok' in html, "Admin harus melihat link Kartu Stok"
        assert 'Laporan Penjualan' in html, "Admin harus melihat link Laporan Penjualan"
        assert 'Laporan Stok' in html, "Admin harus melihat link Laporan Stok"
        assert 'Pembelian' in html, "Admin harus melihat link Pembelian"
        assert 'Penjualan' in html, "Admin harus melihat link Penjualan"
        
        print("✅ test_nav_visibility (admin) passed")

def test_kasir_nav_visibility():
    """Test bahwa kasir tidak melihat link yang tidak diizinkan."""
    with app.app_context():
        init_db()
        db = get_db()
        kasir_role = db.execute("SELECT id FROM roles WHERE nama = 'kasir'").fetchone()
        if not kasir_role:
            print("⚠️ test_kasir_nav_visibility skipped: role kasir tidak ada")
            return
        
        # Buat user kasir temporary
        from werkzeug.security import generate_password_hash
        db.execute(
            'INSERT OR IGNORE INTO users (username, password_hash, password_plain, role_id) VALUES (?, ?, ?, ?)',
            ('test_kasir', generate_password_hash('test123'), 'test123', kasir_role['id'])
        )
        db.commit()
        kasir_user = db.execute("SELECT id FROM users WHERE username = 'test_kasir'").fetchone()
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = kasir_user['id']
        
        resp = client.get('/')
        assert resp.status_code == 200
        html = resp.data.decode('utf-8')
        
        # Kasir TIDAK boleh melihat link ini
        assert 'Data User' not in html, "Kasir TIDAK boleh melihat link Data User"
        assert 'Data Role' not in html, "Kasir TIDAK boleh melihat link Data Role"
        
        # Kasir boleh melihat link ini
        assert 'Penjualan' in html, "Kasir harus melihat link Penjualan"
        assert 'Kartu Stok' in html, "Kasir harus melihat link Kartu Stok"
        assert 'Laporan Penjualan' in html, "Kasir harus melihat link Laporan Penjualan"
        
        print("✅ test_kasir_nav_visibility passed")

def test_kasir_cannot_access_users():
    """Test bahwa kasir tidak bisa akses halaman users."""
    with app.app_context():
        init_db()
        db = get_db()
        kasir_user = db.execute("SELECT id FROM users WHERE username = 'test_kasir'").fetchone()
        if not kasir_user:
            print("⚠️ test_kasir_cannot_access_users skipped: user kasir tidak ada")
            return
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = kasir_user['id']
        
        resp = client.get('/users')
        # Harus redirect (302) karena tidak punya permission
        assert resp.status_code == 302, f"Kasir harus ditolak akses /users, dapat {resp.status_code}"
        
        print("✅ test_kasir_cannot_access_users passed")

def test_gudang_cannot_create_penjualan():
    """Test bahwa gudang tidak bisa create penjualan."""
    with app.app_context():
        init_db()
        db = get_db()
        gudang_role = db.execute("SELECT id FROM roles WHERE nama = 'gudang'").fetchone()
        if not gudang_role:
            print("⚠️ test_gudang_cannot_create_penjualan skipped: role gudang tidak ada")
            return
        
        from werkzeug.security import generate_password_hash
        db.execute(
            'INSERT OR IGNORE INTO users (username, password_hash, password_plain, role_id) VALUES (?, ?, ?, ?)',
            ('test_gudang', generate_password_hash('test123'), 'test123', gudang_role['id'])
        )
        db.commit()
        gudang_user = db.execute("SELECT id FROM users WHERE username = 'test_gudang'").fetchone()
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = gudang_user['id']
        
        resp = client.get('/penjualan/create')
        assert resp.status_code == 302, f"Gudang harus ditolak akses /penjualan/create, dapat {resp.status_code}"
        
        print("✅ test_gudang_cannot_create_penjualan passed")

def test_stok_route_requires_permission():
    """Test bahwa /stok/kartu butuh permission stok:view."""
    with app.test_client() as client:
        # Tanpa login
        resp = client.get('/stok/kartu')
        assert resp.status_code == 302, "Harus redirect ke login"
        
        print("✅ test_stok_route_requires_permission passed")

def test_laporan_route_requires_permission():
    """Test bahwa /laporan/penjualan butuh permission laporan:view."""
    with app.test_client() as client:
        # Tanpa login
        resp = client.get('/laporan/penjualan')
        assert resp.status_code == 302, "Harus redirect ke login"
        
        print("✅ test_laporan_route_requires_permission passed")

if __name__ == '__main__':
    print("=== Test Fase 5: RBAC ===")
    test_seed_roles()
    test_admin_full_perms()
    test_nav_visibility()
    test_kasir_nav_visibility()
    test_kasir_cannot_access_users()
    test_gudang_cannot_create_penjualan()
    test_stok_route_requires_permission()
    test_laporan_route_requires_permission()
    print("\n=== Semua test Fase 5 passed! ===")
