import sqlite3
import os
import re
import math
import json
import secrets
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, g, abort, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# DEPRECATED: kept for backward compat; source of truth is the kategori table
CATEGORIES = ['Elektronik', 'Makanan', 'Pakaian', 'Lainnya']


def get_db():
    """Get database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE, timeout=30, check_same_thread=False)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA busy_timeout=30000")
    return g.db


def close_db(exception=None):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database with schema."""
    db = sqlite3.connect(DATABASE, timeout=30)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA busy_timeout=30000")
    db.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            harga_pokok REAL NOT NULL,
            harga_jual REAL NOT NULL,
            margin REAL GENERATED ALWAYS AS (harga_jual - harga_pokok) STORED,
            category TEXT NOT NULL DEFAULT 'Lainnya',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Migration: add category column if not exists
    try:
        db.execute("ALTER TABLE items ADD COLUMN category TEXT NOT NULL DEFAULT 'Lainnya'")
    except Exception:
        pass  # Column already exists
    # Ensure existing rows have a valid category (not NULL or empty)
    db.execute("UPDATE items SET category = 'Lainnya' WHERE category IS NULL OR category = ''")
    db.execute('''
        CREATE TABLE IF NOT EXISTS pelanggan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL,
            email TEXT,
            telepon TEXT,
            alamat TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS kategori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL UNIQUE,
            deskripsi TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Seed kategori only if the table is empty
    count = db.execute('SELECT COUNT(*) FROM kategori').fetchone()[0]
    if count == 0:
        db.executemany(
            'INSERT OR IGNORE INTO kategori (nama, deskripsi) VALUES (?, ?)',
            [
                ('Elektronik', 'Barang elektronik dan gadget'),
                ('Makanan', 'Makanan dan minuman'),
                ('Pakaian', 'Pakaian dan aksesoris'),
                ('Lainnya', 'Kategori lainnya'),
            ]
        )
    db.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama TEXT NOT NULL UNIQUE,
            deskripsi TEXT,
            permissions TEXT NOT NULL DEFAULT '{}',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        )
    ''')
    # Seed admin role with full permissions
    full_perms = json.dumps({
        'items': ['view', 'create', 'edit', 'delete'],
        'kategori': ['view', 'create', 'edit', 'delete'],
        'pelanggan': ['view', 'create', 'edit', 'delete'],
        'users': ['view', 'create', 'edit', 'delete'],
        'roles': ['view', 'create', 'edit', 'delete'],
    })
    db.execute(
        'INSERT OR IGNORE INTO roles (nama, deskripsi, permissions) VALUES (?, ?, ?)',
        ('admin', 'Full access to all menus', full_perms)
    )
    # Seed admin user (admin/admin123)
    admin_role = db.execute("SELECT id FROM roles WHERE nama = 'admin'").fetchone()
    if admin_role:
        existing_user = db.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
        if not existing_user:
            db.execute(
                'INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)',
                ('admin', generate_password_hash('admin123'), admin_role['id'])
            )
    db.commit()
    db.close()


def get_categories():
    """Return all kategori rows ordered by nama."""
    db = get_db()
    return db.execute('SELECT * FROM kategori ORDER BY nama ASC').fetchall()


def get_category_names():
    """Return set of valid kategori names."""
    return {row['nama'] for row in get_categories()}


def count_items_in_category(nama):
    """Count items referencing a kategori name."""
    db = get_db()
    return db.execute('SELECT COUNT(*) FROM items WHERE category = ?', (nama,)).fetchone()[0]


@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)


# ==================== CSRF PROTECTION ====================

def generate_csrf_token():
    """Generate a CSRF token and store it in the session."""
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


@app.before_request
def csrf_protect():
    """Validate CSRF token on POST requests."""
    if request.method == 'POST':
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        session_token = session.get('csrf_token')
        if not token or not session_token or not secrets.compare_digest(token, session_token):
            abort(403)


@app.context_processor
def inject_csrf_token():
    """Make CSRF token available to all templates."""
    return {'csrf_token': generate_csrf_token()}


# ==================== AUTH ====================

def get_user_by_username(username):
    """Get user row by username."""
    db = get_db()
    return db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()


def get_user_by_id(user_id):
    """Get user row by id."""
    db = get_db()
    return db.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()


def get_role_by_id(role_id):
    """Get role row by id."""
    db = get_db()
    return db.execute('SELECT * FROM roles WHERE id = ?', (role_id,)).fetchone()


def get_user_permissions(user_id):
    """Get permissions dict for a user via their role."""
    db = get_db()
    row = db.execute(
        'SELECT r.permissions FROM users u JOIN roles r ON u.role_id = r.id WHERE u.id = ?',
        (user_id,)
    ).fetchone()
    if row and row['permissions']:
        return json.loads(row['permissions'])
    return {}


def login_required(f):
    """Decorator: require logged-in user."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Silakan login terlebih dahulu!', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def has_permission(menu, action):
    """Decorator factory: require specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Silakan login terlebih dahulu!', 'error')
                return redirect(url_for('login'))
            perms = get_user_permissions(session['user_id'])
            menu_perms = perms.get(menu, [])
            if action not in menu_perms:
                flash('Akses ditolak! Anda tidak memiliki izin.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@app.context_processor
def inject_user():
    """Make current_user available in all templates."""
    if 'user_id' in session:
        user = get_user_by_id(session['user_id'])
        if user:
            role = get_role_by_id(user['role_id'])
            perms = get_user_permissions(session['user_id'])
            return {'current_user': user, 'current_role': role, 'user_perms': perms}
    return {'current_user': None, 'current_role': None, 'user_perms': {}}


@app.route('/reset-db')
def reset_db_route():
    """Debug route: delete DB file, re-init, report result."""
    import os
    # Close any open connections
    close_db()
    # Delete DB files
    for suffix in ['', '-wal', '-shm', '-journal']:
        path = DATABASE + suffix
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                return f"ERROR removing {path}: {e}"
    # Re-init
    try:
        init_db()
        db = sqlite3.connect(DATABASE)
        tables = [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        users = db.execute('SELECT id, username, role_id FROM users').fetchall() if 'users' in tables else []
        roles = db.execute('SELECT id, nama FROM roles').fetchall() if 'roles' in tables else []
        db.close()
        return f"OK. Tables: {tables}. Users: {users}. Roles: {roles}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


@app.route('/init-db')
def init_db_route():
    """Debug route: manually trigger init_db and report result."""
    try:
        init_db()
        db = sqlite3.connect(DATABASE)
        tables = [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        users = db.execute('SELECT id, username, role_id FROM users').fetchall() if 'users' in tables else []
        roles = db.execute('SELECT id, nama FROM roles').fetchall() if 'roles' in tables else []
        db.close()
        return f"OK. Tables: {tables}. Users: {users}. Roles: {roles}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = get_user_by_username(username)
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            flash(f'Selamat datang, {username}!', 'success')
            return redirect(url_for('index'))
        flash('Username atau password salah!', 'error')
    return render_template('login.html')


@app.route('/logout', methods=['POST'])
def logout():
    """Logout and clear session."""
    session.clear()
    flash('Anda telah logout.', 'success')
    return redirect(url_for('login'))


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    flash('Halaman tidak ditemukan!', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors with traceback for debugging."""
    import traceback
    return f"<pre>{traceback.format_exc()}</pre>", 500


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    flash('Akses ditolak!', 'error')
    return redirect(url_for('index'))


# ==================== ITEM ROUTES ====================

@app.route('/')
@has_permission('items', 'view')
def index():
    """Display all items."""
    db = get_db()
    items = db.execute('SELECT * FROM items ORDER BY id DESC').fetchall()
    return render_template('index.html', items=items)


@app.route('/item/<int:id>')
@has_permission('items', 'view')
def view_item(id):
    """View single item details."""
    db = get_db()
    item = db.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()
    if item is None:
        flash('Item tidak ditemukan!', 'error')
        return redirect(url_for('index'))
    return render_template('view.html', item=item)


@app.route('/create', methods=['GET', 'POST'])
@has_permission('items', 'create')
def create_item():
    """Create new item."""
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        harga_pokok = request.form.get('harga_pokok', '').strip()
        harga_jual = request.form.get('harga_jual', '').strip()
        category = request.form.get('category', '').strip()

        # Validation
        errors = []
        if not nama:
            errors.append('Nama item wajib diisi!')
        if not harga_pokok:
            errors.append('Harga pokok wajib diisi!')
        if not harga_jual:
            errors.append('Harga jual wajib diisi!')
        if not category:
            errors.append('Kategori wajib dipilih!')
        elif category not in get_category_names():
            errors.append('Kategori tidak valid!')

        hp = hj = None
        try:
            hp = float(harga_pokok)
            hj = float(harga_jual)
            if not math.isfinite(hp) or not math.isfinite(hj):
                errors.append('Harga harus berupa angka yang valid!')
                hp = hj = None
        except ValueError:
            errors.append('Harga harus berupa angka!')

        if hp is not None and hj is not None and (hp < 0 or hj < 0):
            errors.append('Harga tidak boleh negatif!')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('create.html', nama=nama, harga_pokok=harga_pokok, harga_jual=harga_jual, category=category, categories=get_categories())

        db = get_db()
        db.execute(
            'INSERT INTO items (nama, harga_pokok, harga_jual, category) VALUES (?, ?, ?, ?)',
            (nama, hp, hj, category)
        )
        db.commit()
        flash('Item berhasil ditambahkan!', 'success')
        return redirect(url_for('index'))

    return render_template('create.html', categories=get_categories())


@app.route('/item/<int:id>/edit', methods=['GET', 'POST'])
@has_permission('items', 'edit')
def edit_item(id):
    """Edit existing item."""
    db = get_db()
    item = db.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()

    if item is None:
        flash('Item tidak ditemukan!', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        harga_pokok = request.form.get('harga_pokok', '').strip()
        harga_jual = request.form.get('harga_jual', '').strip()
        category = request.form.get('category', '').strip()

        # Validation
        errors = []
        if not nama:
            errors.append('Nama item wajib diisi!')
        if not harga_pokok:
            errors.append('Harga pokok wajib diisi!')
        if not harga_jual:
            errors.append('Harga jual wajib diisi!')
        if not category:
            errors.append('Kategori wajib dipilih!')
        elif category not in get_category_names():
            errors.append('Kategori tidak valid!')

        hp = hj = None
        try:
            hp = float(harga_pokok)
            hj = float(harga_jual)
            if not math.isfinite(hp) or not math.isfinite(hj):
                errors.append('Harga harus berupa angka yang valid!')
                hp = hj = None
        except ValueError:
            errors.append('Harga harus berupa angka!')

        if hp is not None and hj is not None and (hp < 0 or hj < 0):
            errors.append('Harga tidak boleh negatif!')

        if errors:
            for error in errors:
                flash(error, 'error')
            # Preserve submitted values (keep row fields like created_at)
            item = dict(item)
            item['nama'] = nama
            item['harga_pokok'] = harga_pokok
            item['harga_jual'] = harga_jual
            item['category'] = category
            return render_template('edit.html', item=item, categories=get_categories())

        db.execute(
            'UPDATE items SET nama = ?, harga_pokok = ?, harga_jual = ?, category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
            (nama, hp, hj, category, id)
        )
        db.commit()
        flash('Item berhasil diperbarui!', 'success')
        return redirect(url_for('index'))

    return render_template('edit.html', item=item, categories=get_categories())


@app.route('/item/<int:id>/delete', methods=['POST'])
@has_permission('items', 'delete')
def delete_item(id):
    """Delete item."""
    db = get_db()
    item = db.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()

    if item is None:
        flash('Item tidak ditemukan!', 'error')
        return redirect(url_for('index'))

    db.execute('DELETE FROM items WHERE id = ?', (id,))
    db.commit()
    flash('Item berhasil dihapus!', 'success')
    return redirect(url_for('index'))


# ==================== PELANGGAN ROUTES ====================

@app.route('/pelanggan')
@has_permission('pelanggan', 'view')
def pelanggan_index():
    """Display all pelanggan."""
    db = get_db()
    pelanggan = db.execute('SELECT * FROM pelanggan ORDER BY id DESC').fetchall()
    return render_template('pelanggan/index.html', pelanggan=pelanggan)


@app.route('/pelanggan/<int:id>')
@has_permission('pelanggan', 'view')
def view_pelanggan(id):
    """View single pelanggan details."""
    db = get_db()
    pelanggan = db.execute('SELECT * FROM pelanggan WHERE id = ?', (id,)).fetchone()
    if pelanggan is None:
        flash('Pelanggan tidak ditemukan!', 'error')
        return redirect(url_for('pelanggan_index'))
    return render_template('pelanggan/view.html', pelanggan=pelanggan)


@app.route('/pelanggan/create', methods=['GET', 'POST'])
@has_permission('pelanggan', 'create')
def create_pelanggan():
    """Create new pelanggan."""
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        email = request.form.get('email', '').strip()
        telepon = request.form.get('telepon', '').strip()
        alamat = request.form.get('alamat', '').strip()

        # Validation
        errors = []
        if not nama:
            errors.append('Nama pelanggan wajib diisi!')

        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Format email tidak valid!')

        if telepon and not re.match(r'^[0-9+\-\s]+$', telepon):
            errors.append('Nomor telepon hanya boleh angka, +, -, dan spasi!')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('pelanggan/create.html', nama=nama, email=email, telepon=telepon, alamat=alamat)

        db = get_db()
        db.execute(
            'INSERT INTO pelanggan (nama, email, telepon, alamat) VALUES (?, ?, ?, ?)',
            (nama, email, telepon, alamat)
        )
        db.commit()
        flash('Pelanggan berhasil ditambahkan!', 'success')
        return redirect(url_for('pelanggan_index'))

    return render_template('pelanggan/create.html')


@app.route('/pelanggan/<int:id>/edit', methods=['GET', 'POST'])
@has_permission('pelanggan', 'edit')
def edit_pelanggan(id):
    """Edit existing pelanggan."""
    db = get_db()
    pelanggan = db.execute('SELECT * FROM pelanggan WHERE id = ?', (id,)).fetchone()

    if pelanggan is None:
        flash('Pelanggan tidak ditemukan!', 'error')
        return redirect(url_for('pelanggan_index'))

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        email = request.form.get('email', '').strip()
        telepon = request.form.get('telepon', '').strip()
        alamat = request.form.get('alamat', '').strip()

        # Validation
        errors = []
        if not nama:
            errors.append('Nama pelanggan wajib diisi!')

        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            errors.append('Format email tidak valid!')

        if telepon and not re.match(r'^[0-9+\-\s]+$', telepon):
            errors.append('Nomor telepon hanya boleh angka, +, -, dan spasi!')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('pelanggan/edit.html', pelanggan=pelanggan)

        db.execute(
            'UPDATE pelanggan SET nama = ?, email = ?, telepon = ?, alamat = ? WHERE id = ?',
            (nama, email, telepon, alamat, id)
        )
        db.commit()
        flash('Pelanggan berhasil diperbarui!', 'success')
        return redirect(url_for('pelanggan_index'))

    return render_template('pelanggan/edit.html', pelanggan=pelanggan)


@app.route('/pelanggan/<int:id>/delete', methods=['POST'])
@has_permission('pelanggan', 'delete')
def delete_pelanggan(id):
    """Delete pelanggan."""
    db = get_db()
    pelanggan = db.execute('SELECT * FROM pelanggan WHERE id = ?', (id,)).fetchone()

    if pelanggan is None:
        flash('Pelanggan tidak ditemukan!', 'error')
        return redirect(url_for('pelanggan_index'))

    db.execute('DELETE FROM pelanggan WHERE id = ?', (id,))
    db.commit()
    flash('Pelanggan berhasil dihapus!', 'success')
    return redirect(url_for('pelanggan_index'))


# ==================== KATEGORI ROUTES ====================

@app.route('/kategori')
@has_permission('kategori', 'view')
def kategori_index():
    """Display all kategori."""
    db = get_db()
    kategori = db.execute(
        'SELECT k.*, (SELECT COUNT(*) FROM items i WHERE i.category = k.nama) AS item_count '
        'FROM kategori k ORDER BY k.nama ASC'
    ).fetchall()
    return render_template('kategori/index.html', kategori=kategori)


@app.route('/kategori/<int:id>')
@has_permission('kategori', 'view')
def view_kategori(id):
    """View single kategori details."""
    db = get_db()
    kategori = db.execute('SELECT * FROM kategori WHERE id = ?', (id,)).fetchone()
    if kategori is None:
        flash('Kategori tidak ditemukan!', 'error')
        return redirect(url_for('kategori_index'))
    item_count = count_items_in_category(kategori['nama'])
    return render_template('kategori/view.html', kategori=kategori, item_count=item_count)


@app.route('/kategori/create', methods=['GET', 'POST'])
@has_permission('kategori', 'create')
def create_kategori():
    """Create new kategori."""
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()

        # Validation
        errors = []
        if not nama:
            errors.append('Nama kategori wajib diisi!')
        elif len(nama) > 100:
            errors.append('Nama kategori maksimal 100 karakter!')
        elif len(deskripsi) > 500:
            errors.append('Deskripsi maksimal 500 karakter!')
        else:
            db = get_db()
            existing = db.execute(
                'SELECT id FROM kategori WHERE LOWER(nama) = LOWER(?)', (nama,)
            ).fetchone()
            if existing:
                errors.append(f"Kategori '{nama}' sudah ada!")

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('kategori/create.html', nama=nama, deskripsi=deskripsi)

        db = get_db()
        try:
            db.execute(
                'INSERT INTO kategori (nama, deskripsi) VALUES (?, ?)',
                (nama, deskripsi)
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            flash(f"Kategori '{nama}' sudah ada!", 'error')
            return render_template('kategori/create.html', nama=nama, deskripsi=deskripsi)
        flash('Kategori berhasil ditambahkan!', 'success')
        return redirect(url_for('kategori_index'))

    return render_template('kategori/create.html')


@app.route('/kategori/<int:id>/edit', methods=['GET', 'POST'])
@has_permission('kategori', 'edit')
def edit_kategori(id):
    """Edit existing kategori."""
    db = get_db()
    kategori = db.execute('SELECT * FROM kategori WHERE id = ?', (id,)).fetchone()

    if kategori is None:
        flash('Kategori tidak ditemukan!', 'error')
        return redirect(url_for('kategori_index'))

    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()

        # Validation
        errors = []
        if not nama:
            errors.append('Nama kategori wajib diisi!')
        elif len(nama) > 100:
            errors.append('Nama kategori maksimal 100 karakter!')
        elif len(deskripsi) > 500:
            errors.append('Deskripsi maksimal 500 karakter!')
        else:
            existing = db.execute(
                'SELECT id FROM kategori WHERE LOWER(nama) = LOWER(?) AND id != ?',
                (nama, id)
            ).fetchone()
            if existing:
                errors.append(f"Kategori '{nama}' sudah ada!")

        if errors:
            for error in errors:
                flash(error, 'error')
            # Preserve submitted values while keeping all row fields (incl. created_at)
            kategori = dict(db.execute('SELECT * FROM kategori WHERE id = ?', (id,)).fetchone())
            kategori['nama'] = nama
            kategori['deskripsi'] = deskripsi
            return render_template('kategori/edit.html', kategori=kategori)

        old_nama = kategori['nama']
        try:
            db.execute(
                'UPDATE kategori SET nama = ?, deskripsi = ? WHERE id = ?',
                (nama, deskripsi, id)
            )
            if nama != old_nama:
                db.execute('UPDATE items SET category = ? WHERE category = ?', (nama, old_nama))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            flash(f"Kategori '{nama}' sudah ada!", 'error')
            kategori = dict(db.execute('SELECT * FROM kategori WHERE id = ?', (id,)).fetchone())
            kategori['nama'] = nama
            kategori['deskripsi'] = deskripsi
            return render_template('kategori/edit.html', kategori=kategori)
        flash('Kategori berhasil diperbarui!', 'success')
        return redirect(url_for('kategori_index'))

    return render_template('kategori/edit.html', kategori=kategori)


@app.route('/kategori/<int:id>/delete', methods=['POST'])
@has_permission('kategori', 'delete')
def delete_kategori(id):
    """Delete kategori (blocked when still referenced by items)."""
    db = get_db()
    kategori = db.execute('SELECT * FROM kategori WHERE id = ?', (id,)).fetchone()

    if kategori is None:
        flash('Kategori tidak ditemukan!', 'error')
        return redirect(url_for('kategori_index'))

    n = count_items_in_category(kategori['nama'])
    if n > 0:
        flash(f'Kategori tidak dapat dihapus! Masih ada {n} item yang menggunakan kategori ini.', 'error')
        return redirect(url_for('kategori_index'))

    # Atomic guard against TOCTOU: only delete when no item references it.
    cur = db.execute(
        'DELETE FROM kategori WHERE id = ? AND NOT EXISTS '
        '(SELECT 1 FROM items WHERE category = ?)',
        (id, kategori['nama'])
    )
    db.commit()
    if cur.rowcount == 0:
        flash('Kategori tidak dapat dihapus! Masih ada item yang menggunakan kategori ini.', 'error')
        return redirect(url_for('kategori_index'))
    flash('Kategori berhasil dihapus!', 'success')
    return redirect(url_for('kategori_index'))


# ==================== USER MANAGEMENT ====================

@app.route('/users')
@has_permission('users', 'view')
def users_index():
    """Display all users."""
    db = get_db()
    users = db.execute(
        'SELECT u.*, r.nama as role_nama FROM users u JOIN roles r ON u.role_id = r.id ORDER BY u.id DESC'
    ).fetchall()
    return render_template('users/index.html', users=users)


@app.route('/users/create', methods=['GET', 'POST'])
@has_permission('users', 'create')
def create_user():
    """Create new user."""
    db = get_db()
    roles = db.execute('SELECT * FROM roles ORDER BY nama ASC').fetchall()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role_id = request.form.get('role_id', '').strip()
        errors = []
        if not username:
            errors.append('Username wajib diisi!')
        elif len(username) < 3:
            errors.append('Username minimal 3 karakter!')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username hanya boleh huruf, angka, dan underscore!')
        if not password:
            errors.append('Password wajib diisi!')
        elif len(password) < 6:
            errors.append('Password minimal 6 karakter!')
        if not role_id:
            errors.append('Role wajib dipilih!')
        else:
            role = db.execute('SELECT id FROM roles WHERE id = ?', (int(role_id),)).fetchone()
            if not role:
                errors.append('Role tidak valid!')
        if not errors:
            existing = db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if existing:
                errors.append(f"Username '{username}' sudah digunakan!")
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('users/create.html', roles=roles, username=username, role_id=role_id)
        db.execute(
            'INSERT INTO users (username, password_hash, role_id) VALUES (?, ?, ?)',
            (username, generate_password_hash(password), int(role_id))
        )
        db.commit()
        flash('User berhasil ditambahkan!', 'success')
        return redirect(url_for('users_index'))
    return render_template('users/create.html', roles=roles)


@app.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@has_permission('users', 'edit')
def edit_user(id):
    """Edit existing user."""
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if user is None:
        flash('User tidak ditemukan!', 'error')
        return redirect(url_for('users_index'))
    roles = db.execute('SELECT * FROM roles ORDER BY nama ASC').fetchall()
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        role_id = request.form.get('role_id', '').strip()
        errors = []
        if not username:
            errors.append('Username wajib diisi!')
        elif len(username) < 3:
            errors.append('Username minimal 3 karakter!')
        elif not re.match(r'^[a-zA-Z0-9_]+$', username):
            errors.append('Username hanya boleh huruf, angka, dan underscore!')
        if password and len(password) < 6:
            errors.append('Password minimal 6 karakter!')
        if not role_id:
            errors.append('Role wajib dipilih!')
        else:
            role = db.execute('SELECT id FROM roles WHERE id = ?', (int(role_id),)).fetchone()
            if not role:
                errors.append('Role tidak valid!')
        if not errors:
            existing = db.execute('SELECT id FROM users WHERE username = ? AND id != ?', (username, id)).fetchone()
            if existing:
                errors.append(f"Username '{username}' sudah digunakan!")
        if errors:
            for error in errors:
                flash(error, 'error')
            user = dict(user)
            user['username'] = username
            user['role_id'] = role_id
            return render_template('users/edit.html', user=user, roles=roles)
        if password:
            db.execute(
                'UPDATE users SET username = ?, password_hash = ?, role_id = ? WHERE id = ?',
                (username, generate_password_hash(password), int(role_id), id)
            )
        else:
            db.execute(
                'UPDATE users SET username = ?, role_id = ? WHERE id = ?',
                (username, int(role_id), id)
            )
        db.commit()
        flash('User berhasil diperbarui!', 'success')
        return redirect(url_for('users_index'))
    return render_template('users/edit.html', user=user, roles=roles)


@app.route('/users/<int:id>/delete', methods=['POST'])
@has_permission('users', 'delete')
def delete_user(id):
    """Delete user (prevent self-delete)."""
    if id == session.get('user_id'):
        flash('Anda tidak dapat menghapus akun sendiri!', 'error')
        return redirect(url_for('users_index'))
    db = get_db()
    user = db.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
    if user is None:
        flash('User tidak ditemukan!', 'error')
        return redirect(url_for('users_index'))
    db.execute('DELETE FROM users WHERE id = ?', (id,))
    db.commit()
    flash('User berhasil dihapus!', 'success')
    return redirect(url_for('users_index'))


# ==================== ROLE MANAGEMENT ====================

@app.route('/roles')
@has_permission('roles', 'view')
def roles_index():
    """Display all roles."""
    db = get_db()
    roles = db.execute(
        'SELECT r.*, (SELECT COUNT(*) FROM users u WHERE u.role_id = r.id) AS user_count '
        'FROM roles r ORDER BY r.nama ASC'
    ).fetchall()
    return render_template('roles/index.html', roles=roles)


@app.route('/roles/create', methods=['GET', 'POST'])
@has_permission('roles', 'create')
def create_role():
    """Create new role."""
    menus = ['items', 'kategori', 'pelanggan', 'users', 'roles']
    actions = ['view', 'create', 'edit', 'delete']
    db = get_db()
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()
        permissions = {}
        for menu in menus:
            permissions[menu] = request.form.getlist(f'perm_{menu}')
        errors = []
        if not nama:
            errors.append('Nama role wajib diisi!')
        elif len(nama) > 50:
            errors.append('Nama role maksimal 50 karakter!')
        else:
            existing = db.execute('SELECT id FROM roles WHERE LOWER(nama) = LOWER(?)', (nama,)).fetchone()
            if existing:
                errors.append(f"Role '{nama}' sudah ada!")
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('roles/create.html', menus=menus, actions=actions, nama=nama, deskripsi=deskripsi, permissions=permissions)
        db = get_db()
        try:
            db.execute(
                'INSERT INTO roles (nama, deskripsi, permissions) VALUES (?, ?, ?)',
                (nama, deskripsi, json.dumps(permissions))
            )
            db.commit()
        except Exception:
            db.rollback()
            flash(f"Role '{nama}' sudah ada!", 'error')
            return render_template('roles/create.html', menus=menus, actions=actions, nama=nama, deskripsi=deskripsi, permissions=permissions)
        flash('Role berhasil ditambahkan!', 'success')
        return redirect(url_for('roles_index'))
    return render_template('roles/create.html', menus=menus, actions=actions, permissions={})


@app.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@has_permission('roles', 'edit')
def edit_role(id):
    """Edit existing role."""
    db = get_db()
    role = db.execute('SELECT * FROM roles WHERE id = ?', (id,)).fetchone()
    if role is None:
        flash('Role tidak ditemukan!', 'error')
        return redirect(url_for('roles_index'))
    menus = ['items', 'kategori', 'pelanggan', 'users', 'roles']
    actions = ['view', 'create', 'edit', 'delete']
    current_perms = json.loads(role['permissions']) if role['permissions'] else {}
    if request.method == 'POST':
        nama = request.form.get('nama', '').strip()
        deskripsi = request.form.get('deskripsi', '').strip()
        permissions = {}
        for menu in menus:
            permissions[menu] = request.form.getlist(f'perm_{menu}')
        errors = []
        if not nama:
            errors.append('Nama role wajib diisi!')
        elif len(nama) > 50:
            errors.append('Nama role maksimal 50 karakter!')
        else:
            existing = db.execute('SELECT id FROM roles WHERE LOWER(nama) = LOWER(?) AND id != ?', (nama, id)).fetchone()
            if existing:
                errors.append(f"Role '{nama}' sudah ada!")
        if errors:
            for error in errors:
                flash(error, 'error')
            role = dict(role)
            role['nama'] = nama
            role['deskripsi'] = deskripsi
            return render_template('roles/edit.html', role=role, menus=menus, actions=actions, permissions=permissions)
        try:
            db.execute(
                'UPDATE roles SET nama = ?, deskripsi = ?, permissions = ? WHERE id = ?',
                (nama, deskripsi, json.dumps(permissions), id)
            )
            db.commit()
        except Exception:
            db.rollback()
            flash(f"Role '{nama}' sudah ada!", 'error')
            role = dict(role)
            role['nama'] = nama
            role['deskripsi'] = deskripsi
            return render_template('roles/edit.html', role=role, menus=menus, actions=actions, permissions=permissions)
        flash('Role berhasil diperbarui!', 'success')
        return redirect(url_for('roles_index'))
    return render_template('roles/edit.html', role=role, menus=menus, actions=actions, permissions=current_perms)


@app.route('/roles/<int:id>/delete', methods=['POST'])
@has_permission('roles', 'delete')
def delete_role(id):
    """Delete role (prevent if users assigned)."""
    db = get_db()
    role = db.execute('SELECT * FROM roles WHERE id = ?', (id,)).fetchone()
    if role is None:
        flash('Role tidak ditemukan!', 'error')
        return redirect(url_for('roles_index'))
    user_count = db.execute('SELECT COUNT(*) FROM users WHERE role_id = ?', (id,)).fetchone()[0]
    if user_count > 0:
        flash(f'Role tidak dapat dihapus! Masih ada {user_count} user yang menggunakan role ini.', 'error')
        return redirect(url_for('roles_index'))
    db.execute('DELETE FROM roles WHERE id = ?', (id,))
    db.commit()
    flash('Role berhasil dihapus!', 'success')
    return redirect(url_for('roles_index'))


# ==================== TEMPLATE FILTERS ====================

@app.template_filter('format_rupiah')
def format_rupiah(value):
    """Format number as Indonesian Rupiah."""
    if value is None:
        return 'Rp 0'
    return f'Rp {value:,.0f}'.replace(',', '.')


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true', host='0.0.0.0', port=port)
else:
    # Ensure schema exists when served by flask run / gunicorn / waitress
    try:
        init_db()
    except Exception:
        pass
