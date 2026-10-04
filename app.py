import sqlite3
import os
import re
import math
import secrets
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, g, abort, session

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database.db')

# DEPRECATED: kept for backward compat; source of truth is the kategori table
CATEGORIES = ['Elektronik', 'Makanan', 'Pakaian', 'Lainnya']


def get_db():
    """Get database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception=None):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database with schema."""
    db = sqlite3.connect(DATABASE)
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


# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    flash('Halaman tidak ditemukan!', 'error')
    return redirect(url_for('index'))


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    flash('Terjadi kesalahan internal!', 'error')
    return redirect(url_for('index'))


@app.errorhandler(403)
def forbidden(error):
    """Handle 403 errors."""
    flash('Akses ditolak!', 'error')
    return redirect(url_for('index'))


# ==================== ITEM ROUTES ====================

@app.route('/')
def index():
    """Display all items."""
    db = get_db()
    items = db.execute('SELECT * FROM items ORDER BY id DESC').fetchall()
    return render_template('index.html', items=items)


@app.route('/item/<int:id>')
def view_item(id):
    """View single item details."""
    db = get_db()
    item = db.execute('SELECT * FROM items WHERE id = ?', (id,)).fetchone()
    if item is None:
        flash('Item tidak ditemukan!', 'error')
        return redirect(url_for('index'))
    return render_template('view.html', item=item)


@app.route('/create', methods=['GET', 'POST'])
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
def pelanggan_index():
    """Display all pelanggan."""
    db = get_db()
    pelanggan = db.execute('SELECT * FROM pelanggan ORDER BY id DESC').fetchall()
    return render_template('pelanggan/index.html', pelanggan=pelanggan)


@app.route('/pelanggan/<int:id>')
def view_pelanggan(id):
    """View single pelanggan details."""
    db = get_db()
    pelanggan = db.execute('SELECT * FROM pelanggan WHERE id = ?', (id,)).fetchone()
    if pelanggan is None:
        flash('Pelanggan tidak ditemukan!', 'error')
        return redirect(url_for('pelanggan_index'))
    return render_template('pelanggan/view.html', pelanggan=pelanggan)


@app.route('/pelanggan/create', methods=['GET', 'POST'])
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
def kategori_index():
    """Display all kategori."""
    db = get_db()
    kategori = db.execute(
        'SELECT k.*, (SELECT COUNT(*) FROM items i WHERE i.category = k.nama) AS item_count '
        'FROM kategori k ORDER BY k.nama ASC'
    ).fetchall()
    return render_template('kategori/index.html', kategori=kategori)


@app.route('/kategori/<int:id>')
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
