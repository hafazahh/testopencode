# Desain Fase 2: Supplier + Pembelian (Stok Masuk)

**Project:** `/home/choirulhaq/venvProject/testopencode/`
**Status:** Draft untuk review user
**Tanggal:** 2026-10-07
**Fase sebelumnya:** Fase 1 (Skema DB + Kartu Stok) — ✅ approved

---

## 1. Ringkasan

Fase 2 menambahkan **2 menu baru** ke sistem:
- **Supplier** — CRUD master data pemasok
- **Pembelian** — Transaksi pengadaan barang (stok masuk) dengan atomic insert

**Total route baru:** 9 route
**Total template baru:** 7 file
**Tabel baru:** 2 (supplier, pembelian + pembelian_detail)
**Tabel yang dimodifikasi:** 0 (stok_mutasi dan stok_akhir sudah dirancang di Fase 1)

---

## 2. Route Lengkap

### 2.1 Route Supplier (5 route)

| # | Route | Method | Permission | Fungsi |
|---|-------|--------|------------|--------|
| 1 | `/supplier` | GET | `supplier.view` | Daftar semua supplier |
| 2 | `/supplier/create` | GET, POST | `supplier.create` | Form tambah supplier |
| 3 | `/supplier/<int:id>` | GET | `supplier.view` | Detail supplier |
| 4 | `/supplier/<int:id>/edit` | GET, POST | `supplier.edit` | Form edit supplier |
| 5 | `/supplier/<int:id>/delete` | POST | `supplier.delete` | Hapus supplier |

### 2.2 Route Pembelian (4 route)

| # | Route | Method | Permission | Fungsi |
|---|-------|--------|------------|--------|
| 6 | `/pembelian` | GET | `pembelian.view` | Daftar semua pembelian |
| 7 | `/pembelian/create` | GET, POST | `pembelian.create` | Form tambah pembelian (multi-item) |
| 8 | `/pembelian/<int:id>` | GET | `pembelian.view` | Detail pembelian (header + detail) |
| 9 | `/pembelian/<int:id>/delete` | POST | `pembelian.delete` | Hapus pembelian (rollback stok) |

**Catatan:** Route pembelian delete akan me-rollback stot_mutasi dan stok_akhir terkait.

---

## 3. Template Lengkap

### 3.1 Struktur Template

```
templates/
├── supplier/
│   ├── index.html      — Daftar supplier (tabel + aksi)
│   ├── create.html     — Form tambah supplier
│   ├── edit.html       — Form edit supplier
│   └── view.html       — Detail supplier
├── pembelian/
│   ├── index.html      — Daftar pembelian (tabel + aksi)
│   ├── create.html     — Form pembelian multi-item (dynamic rows)
│   └── view.html       — Detail pembelian (header + detail)
```

### 3.2 Template: `supplier/index.html`

```html
{% extends "base.html" %}

{% block title %}Daftar Supplier - CRUD Item{% endblock %}

{% block content %}
<div class="list-header">
    <h2>Daftar Supplier</h2>
    {% if 'create' in user_perms.get('supplier', []) %}
    <a href="{{ url_for('create_supplier') }}" class="btn btn-primary">+ Tambah Supplier</a>
    {% endif %}
</div>

{% if suppliers %}
    <table class="data-table">
        <thead>
            <tr>
                <th scope="col">No</th>
                <th scope="col">Nama</th>
                <th scope="col">Kontak</th>
                <th scope="col">Telepon</th>
                <th scope="col">Aksi</th>
            </tr>
        </thead>
        <tbody>
            {% for s in suppliers %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ s.nama }}</td>
                <td>{{ s.kontak if s.kontak else '-' }}</td>
                <td class="actions">
                    <a href="{{ url_for('view_supplier', id=s.id) }}" class="btn btn-sm btn-view">Lihat</a>
                    {% if 'edit' in user_perms.get('supplier', []) %}
                    <a href="{{ url_for('edit_supplier', id=s.id) }}" class="btn btn-sm btn-edit">Edit</a>
                    {% endif %}
                    {% if 'delete' in user_perms.get('supplier', []) %}
                    <form action="{{ url_for('delete_supplier', id=s.id) }}" method="POST" class="inline-form" onsubmit="return confirm('Yakin ingin hapus supplier ini?');">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                        <button type="submit" class="btn btn-sm btn-delete">Hapus</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
{% else %}
    <div class="empty-state">
        <p>Belum ada supplier. <a href="{{ url_for('create_supplier') }}">Tambah supplier pertama</a></p>
    </div>
{% endif %}
{% endblock %}
```

### 3.3 Template: `supplier/create.html`

```html
{% extends "base.html" %}

{% block title %}Tambah Supplier - CRUD Item{% endblock %}

{% block content %}
<h2>Tambah Supplier Baru</h2>

<form method="POST" action="{{ url_for('create_supplier') }}" class="form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div class="form-group">
        <label for="nama">Nama Supplier</label>
        <input type="text" id="nama" name="nama" value="{{ nama if nama else '' }}" required placeholder="Masukkan nama supplier">
    </div>

    <div class="form-group">
        <label for="kontak">Kontak Person</label>
        <input type="text" id="kontak" name="kontak" value="{{ kontak if kontak else '' }}" placeholder="Masukkan nama kontak (opsional)">
    </div>

    <div class="form-group">
        <label for="alamat">Alamat</label>
        <textarea id="alamat" name="alamat" rows="3" placeholder="Masukkan alamat (opsional)">{{ alamat if alamat else '' }}</textarea>
    </div>

    <div class="form-actions">
        <button type="submit" class="btn btn-primary">Simpan</button>
        <a href="{{ url_for('supplier_index') }}" class="btn btn-secondary">Batal</a>
    </div>
</form>
{% endblock %}
```

### 3.4 Template: `supplier/edit.html`

```html
{% extends "base.html" %}

{% block title %}Edit Supplier - CRUD Item{% endblock %}

{% block content %}
<h2>Edit Supplier</h2>

<form method="POST" action="{{ url_for('edit_supplier', id=supplier.id) }}" class="form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <div class="form-group">
        <label for="nama">Nama Supplier</label>
        <input type="text" id="nama" name="nama" value="{{ supplier.nama }}" required placeholder="Masukkan nama supplier">
    </div>

    <div class="form-group">
        <label for="kontak">Kontak Person</label>
        <input type="text" id="kontak" name="kontak" value="{{ supplier.kontak if supplier.kontak else '' }}" placeholder="Masukkan nama kontak (opsional)">
    </div>

    <div class="form-group">
        <label for="alamat">Alamat</label>
        <textarea id="alamat" name="alamat" rows="3" placeholder="Masukkan alamat (opsional)">{{ supplier.alamat if supplier.alamat else '' }}</textarea>
    </div>

    <div class="form-actions">
        <button type="submit" class="btn btn-primary">Update</button>
        <a href="{{ url_for('supplier_index') }}" class="btn btn-secondary">Batal</a>
    </div>
</form>
{% endblock %}
```

### 3.5 Template: `supplier/view.html`

```html
{% extends "base.html" %}

{% block title %}{{ supplier.nama }} - CRUD Item{% endblock %}

{% block content %}
<h2>Detail Supplier</h2>

<div class="detail-card">
    <div class="detail-row">
        <span class="detail-label">ID</span>
        <span class="detail-value">{{ supplier.id }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Nama</span>
        <span class="detail-value">{{ supplier.nama }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Kontak</span>
        <span class="detail-value">{{ supplier.kontak if supplier.kontak else '-' }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Alamat</span>
        <span class="detail-value">{{ supplier.alamat if supplier.alamat else '-' }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Dibuat</span>
        <span class="detail-value">{{ supplier.created_at }}</span>
    </div>
</div>

<div class="form-actions">
    {% if 'edit' in user_perms.get('supplier', []) %}
    <a href="{{ url_for('edit_supplier', id=supplier.id) }}" class="btn btn-primary">Edit</a>
    {% endif %}
    {% if 'delete' in user_perms.get('supplier', []) %}
    <form action="{{ url_for('delete_supplier', id=supplier.id) }}" method="POST" class="inline-form" onsubmit="return confirm('Yakin ingin hapus supplier ini?');">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit" class="btn btn-delete">Hapus</button>
    </form>
    {% endif %}
    <a href="{{ url_for('supplier_index') }}" class="btn btn-secondary">Kembali</a>
</div>
{% endblock %}
```

### 3.6 Template: `pembelian/index.html`

```html
{% extends "base.html" %}

{% block title %}Daftar Pembelian - CRUD Item{% endblock %}

{% block content %}
<div class="list-header">
    <h2>Daftar Pembelian</h2>
    {% if 'create' in user_perms.get('pembelian', []) %}
    <a href="{{ url_for('create_pembelian') }}" class="btn btn-primary">+ Tambah Pembelian</a>
    {% endif %}
</div>

{% if pembelian %}
    <table class="data-table">
        <thead>
            <tr>
                <th scope="col">No</th>
                <th scope="col">No. Transaksi</th>
                <th scope="col">Tanggal</th>
                <th scope="col">Supplier</th>
                <th scope="col">Total</th>
                <th scope="col">Aksi</th>
            </tr>
        </thead>
        <tbody>
            {% for p in pembelian %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ p.nomor_transaksi }}</td>
                <td>{{ p.tanggal }}</td>
                <td>{{ p.supplier_nama }}</td>
                <td>Rp {{ "{:,.0f}".format(p.total) }}</td>
                <td class="actions">
                    <a href="{{ url_for('view_pembelian', id=p.id) }}" class="btn btn-sm btn-view">Lihat</a>
                    {% if 'delete' in user_perms.get('pembelian', []) %}
                    <form action="{{ url_for('delete_pembelian', id=p.id) }}" method="POST" class="inline-form" onsubmit="return confirm('Yakin ingin hapus pembelian ini? Stok akan di-rollback.');">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
                        <button type="submit" class="btn btn-sm btn-delete">Hapus</button>
                    </form>
                    {% endif %}
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
{% else %}
    <div class="empty-state">
        <p>Belum ada pembelian. <a href="{{ url_for('create_pembelian') }}">Tambah pembelian pertama</a></p>
    </div>
{% endif %}
{% endblock %}
```

### 3.7 Template: `pembelian/create.html`

```html
{% extends "base.html" %}

{% block title %}Tambah Pembelian - CRUD Item{% endblock %}

{% block content %}
<h2>Tambah Pembelian Baru</h2>

<form method="POST" action="{{ url_for('create_pembelian') }}" class="form" id="pembelian-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    
    <div class="form-row">
        <div class="form-group">
            <label for="supplier_id">Supplier</label>
            <select id="supplier_id" name="supplier_id" required>
                <option value="">-- Pilih Supplier --</option>
                {% for s in suppliers %}
                <option value="{{ s.id }}" {% if supplier_id == s.id %}selected{% endif %}>{{ s.nama }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="tanggal">Tanggal</label>
            <input type="date" id="tanggal" name="tanggal" value="{{ tanggal if tanggal else today }}" required>
        </div>
    </div>

    <div class="form-group">
        <label for="catatan">Catatan</label>
        <textarea id="catatan" name="catatan" rows="2" placeholder="Masukkan catatan (opsional)">{{ catatan if catatan else '' }}</textarea>
    </div>

    <h3>Detail Item</h3>
    <table class="data-table" id="detail-table">
        <thead>
            <tr>
                <th scope="col">Item</th>
                <th scope="col">Qty</th>
                <th scope="col">Harga Beli</th>
                <th scope="col">Subtotal</th>
                <th scope="col">Aksi</th>
            </tr>
        </thead>
        <tbody id="detail-rows">
            <!-- Dynamic rows will be added here -->
        </tbody>
        <tfoot>
            <tr>
                <td colspan="3" style="text-align: right;"><strong>Total:</strong></td>
                <td colspan="2"><strong id="total-display">Rp 0</strong></td>
            </tr>
        </tfoot>
    </table>

    <button type="button" class="btn btn-secondary" id="add-row-btn">+ Tambah Item</button>

    <div class="form-actions">
        <button type="submit" class="btn btn-primary">Simpan Pembelian</button>
        <a href="{{ url_for('pembelian_index') }}" class="btn btn-secondary">Batal</a>
    </div>
</form>

<script>
// Template untuk baris item
const itemOptions = `{% for item in items %}
    <option value="{{ item.id }}">{{ item.nama }}</option>
{% endfor %}`;

// Data items untuk lookup harga
const itemsData = {
    {% for item in items %}
    {{ item.id }}: { nama: "{{ item.nama }}", harga_pokok: {{ item.harga_pokok }} },
    {% endfor %}
};

let rowCount = 0;

function addDetailRow(itemId = '', qty = '', harga = '') {
    rowCount++;
    const tbody = document.getElementById('detail-rows');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            <select name="item_id[]" required onchange="updateHarga(this)">
                <option value="">-- Pilih Item --</option>
                ${itemOptions}
            </select>
        </td>
        <td>
            <input type="number" name="qty[]" value="${qty}" min="0.01" step="0.01" required placeholder="0" oninput="updateSubtotal(this)">
        </td>
        <td>
            <input type="number" name="harga_beli[]" value="${harga}" min="0" step="0.01" required placeholder="0" oninput="updateSubtotal(this)">
        </td>
        <td>
            <span class="subtotal-display">Rp 0</span>
        </td>
        <td>
            <button type="button" class="btn btn-sm btn-delete" onclick="removeRow(this)">Hapus</button>
        </td>
    `;
    tbody.appendChild(row);
    
    if (itemId) {
        row.querySelector('select[name="item_id[]"]').value = itemId;
    }
}

function removeRow(btn) {
    btn.closest('tr').remove();
    updateTotal();
}

function updateHarga(select) {
    const itemId = select.value;
    const row = select.closest('tr');
    const hargaInput = row.querySelector('input[name="harga_beli[]"]');
    if (itemId && itemsData[itemId]) {
        hargaInput.value = itemsData[itemId].harga_pokok;
    }
    updateSubtotal(hargaInput);
}

function updateSubtotal(input) {
    const row = input.closest('tr');
    const qty = parseFloat(row.querySelector('input[name="qty[]"]').value) || 0;
    const harga = parseFloat(row.querySelector('input[name="harga_beli[]"]').value) || 0;
    const subtotal = qty * harga;
    row.querySelector('.subtotal-display').textContent = 'Rp ' + subtotal.toLocaleString('id-ID');
    updateTotal();
}

function updateTotal() {
    let total = 0;
    document.querySelectorAll('#detail-rows tr').forEach(row => {
        const qty = parseFloat(row.querySelector('input[name="qty[]"]').value) || 0;
        const harga = parseFloat(row.querySelector('input[name="harga_beli[]"]').value) || 0;
        total += qty * harga;
    });
    document.getElementById('total-display').textContent = 'Rp ' + total.toLocaleString('id-ID');
}

// Tambah baris pertama saat halaman dimuat
document.addEventListener('DOMContentLoaded', function() {
    addDetailRow();
});

document.getElementById('add-row-btn').addEventListener('click', function() {
    addDetailRow();
});
</script>
{% endblock %}
```

### 3.8 Template: `pembelian/view.html`

```html
{% extends "base.html" %}

{% block title %}{{ pembelian.nomor_transaksi }} - CRUD Item{% endblock %}

{% block content %}
<h2>Detail Pembelian</h2>

<div class="detail-card">
    <div class="detail-row">
        <span class="detail-label">No. Transaksi</span>
        <span class="detail-value">{{ pembelian.nomor_transaksi }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Tanggal</span>
        <span class="detail-value">{{ pembelian.tanggal }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Supplier</span>
        <span class="detail-value">{{ pembelian.supplier_nama }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Catatan</span>
        <span class="detail-value">{{ pembelian.catatan if pembelian.catatan else '-' }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Dibuat oleh</span>
        <span class="detail-value">{{ pembelian.created_by_username }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Dibuat pada</span>
        <span class="detail-value">{{ pembelian.created_at }}</span>
    </div>
</div>

<h3>Detail Item</h3>
<table class="data-table">
    <thead>
        <tr>
            <th scope="col">No</th>
            <th scope="col">Item</th>
            <th scope="col">Qty</th>
            <th scope="col">Harga Beli</th>
            <th scope="col">Subtotal</th>
        </tr>
    </thead>
    <tbody>
        {% for d in detail %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ d.item_nama }}</td>
            <td>{{ d.qty }}</td>
            <td>Rp {{ "{:,.0f}".format(d.harga_beli) }}</td>
            <td>Rp {{ "{:,.0f}".format(d.subtotal) }}</td>
        </tr>
        {% endfor %}
    </tbody>
    <tfoot>
        <tr>
            <td colspan="4" style="text-align: right;"><strong>Total:</strong></td>
            <td><strong>Rp {{ "{:,.0f}".format(pembelian.total) }}</strong></td>
        </tr>
    </tfoot>
</table>

<div class="form-actions">
    {% if 'delete' in user_perms.get('pembelian', []) %}
    <form action="{{ url_for('delete_pembelian', id=pembelian.id) }}" method="POST" class="inline-form" onsubmit="return confirm('Yakin ingin hapus pembelian ini? Stok akan di-rollback.');">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit" class="btn btn-delete">Hapus</button>
    </form>
    {% endif %}
    <a href="{{ url_for('pembelian_index') }}" class="btn btn-secondary">Kembali</a>
</div>
{% endblock %}
```

---

## 4. Integrasi RBAC

### 4.1 Permission Structure

Permission untuk menu baru mengikuti pola yang sama dengan menu existing:

```json
{
    "supplier": ["view", "create", "edit", "delete"],
    "pembelian": ["view", "create", "delete"]
}
```

**Catatan:** Pembelian tidak punya permission `edit` karena transaksi pembelian tidak bisa diedit setelah dibuat (hanya bisa dihapus dan dibuat ulang).

### 4.2 Update Role Admin

Role `admin` di-update dengan menambahkan permission untuk menu baru:

```python
full_perms = json.dumps({
    'items': ['view', 'create', 'edit', 'delete'],
    'kategori': ['view', 'create', 'edit', 'delete'],
    'pelanggan': ['view', 'create', 'edit', 'delete'],
    'users': ['view', 'create', 'edit', 'delete'],
    'roles': ['view', 'create', 'edit', 'delete'],
    'supplier': ['view', 'create', 'edit', 'delete'],
    'pembelian': ['view', 'create', 'delete'],
})
```

### 4.3 Navigasi Sidebar

Tambahkan di `base.html`:

```html
{% if 'view' in user_perms.get('supplier', []) %}
<a href="{{ url_for('supplier_index') }}" class="btn btn-nav">Data Supplier</a>
{% endif %}
{% if 'view' in user_perms.get('pembelian', []) %}
<a href="{{ url_for('pembelian_index') }}" class="btn btn-nav">Pembelian</a>
{% endif %}
```

---

## 5. Alur Pembelian Atomic

### 5.1 Flowchart

```
User submit form pembelian
        │
        ▼
┌───────────────────────────────────┐
│ 1. Validasi form                  │
│    - supplier_id wajib           │
│    - tanggal wajib               │
│    - minimal 1 item               │
│    - qty > 0 untuk setiap item    │
│    - harga_beli >= 0              │
└───────────────────────────────────┘
        │
        ▼ (valid)
┌───────────────────────────────────┐
│ 2. BEGIN IMMEDIATE                │
│    (kunci database)               │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 3. Generate nomor transaksi       │
│    PB-YYYY-NNNN                   │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 4. INSERT header pembelian        │
│    (supplier_id, nomor, tanggal,  │
│     catatan, total, created_by)   │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 5. LOOP untuk setiap item:        │
│    a. INSERT pembelian_detail     │
│    b. Hitung HPP moving average   │
│    c. UPDATE stok_akhir           │
│    d. INSERT stok_mutasi (IN)     │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 6. COMMIT                         │
└───────────────────────────────────┘
        │
        ▼ (sukses)
   Redirect ke detail pembelian

        │
        ▼ (gagal)
┌───────────────────────────────────┐
│ 7. ROLLBACK                       │
│    (tidak ada perubahan)          │
└───────────────────────────────────┘
        │
        ▼
   Flash error, redirect ke form
```

### 5.2 Pseudocode Implementasi

```python
@app.route('/pembelian/create', methods=['GET', 'POST'])
@has_permission('pembelian', 'create')
def create_pembelian():
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id', '').strip()
        tanggal = request.form.get('tanggal', '').strip()
        catatan = request.form.get('catatan', '').strip()
        
        # Ambil array dari form
        item_ids = request.form.getlist('item_id[]')
        qtys = request.form.getlist('qty[]')
        hargas = request.form.getlist('harga_beli[]')
        
        # Validasi
        errors = []
        if not supplier_id:
            errors.append('Supplier wajib dipilih!')
        if not tanggal:
            errors.append('Tanggal wajib diisi!')
        if not item_ids or len(item_ids) == 0:
            errors.append('Minimal 1 item harus ditambahkan!')
        
        # Validasi setiap item
        valid_items = []
        for i in range(len(item_ids)):
            item_id = item_ids[i]
            qty_str = qtys[i] if i < len(qtys) else ''
            harga_str = hargas[i] if i < len(hargas) else ''
            
            if not item_id:
                continue  # Skip baros kosong
            
            try:
                qty = float(qty_str)
                harga = float(harga_str)
                if qty <= 0:
                    errors.append(f'Item {i+1}: Qty harus lebih dari 0!')
                    continue
                if harga < 0:
                    errors.append(f'Item {i+1}: Harga beli tidak boleh negatif!')
                    continue
                valid_items.append({
                    'item_id': int(item_id),
                    'qty': qty,
                    'harga_beli': harga,
                    'subtotal': qty * harga
                })
            except ValueError:
                errors.append(f'Item {i+1}: Qty dan harga harus berupa angka!')
        
        if len(valid_items) == 0 and len(errors) == 0:
            errors.append('Minimal 1 item harus ditambahkan!')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('pembelian/create.html', 
                                   suppliers=get_suppliers(),
                                   items=get_items(),
                                   supplier_id=supplier_id,
                                   tanggal=tanggal,
                                   catatan=catatan)
        
        # Hitung total
        total = sum(item['subtotal'] for item in valid_items)
        
        # Atomic insert
        db = get_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            
            # Generate nomor transaksi
            nomor = generate_nomor_transaksi('PB')
            
            # Insert header
            cursor = db.execute('''
                INSERT INTO pembelian (supplier_id, nomor_transaksi, tanggal, catatan, total, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (int(supplier_id), nomor, tanggal, catatan, total, session['user_id']))
            
            pembelian_id = cursor.lastrowid
            
            # Insert detail + update stok
            for item in valid_items:
                # Insert detail
                db.execute('''
                    INSERT INTO pembelian_detail (pembelian_id, item_id, qty, harga_beli, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                ''', (pembelian_id, item['item_id'], item['qty'], item['harga_beli'], item['subtotal']))
                
                # Update stok_akhir (moving average)
                update_stok_akhir_setelah_pembelian(item['item_id'], item['qty'], item['harga_beli'])
                
                # Insert stok_mutasi
                saldo_berjalan = hitung_saldo_berjalan(item['item_id'], 'IN', item['qty'])
                db.execute('''
                    INSERT INTO stok_mutasi (item_id, jenis_mutasi, qty, harga, saldo_berjalan,
                                             referensi_tipe, referensi_id, nomor_referensi, tanggal, created_by)
                    VALUES (?, 'IN', ?, ?, ?, 'pembelian', ?, ?, ?, ?)
                ''', (item['item_id'], item['qty'], item['harga_beli'], saldo_berjalan,
                      pembelian_id, nomor, tanggal, session['user_id']))
            
            db.commit()
            flash(f'Pembelian {nomor} berhasil dibuat!', 'success')
            return redirect(url_for('view_pembelian', id=pembelian_id))
            
        except Exception as e:
            db.rollback()
            flash(f'Gagal membuat pembelian: {str(e)}', 'error')
            return render_template('pembelian/create.html',
                                   suppliers=get_suppliers(),
                                   items=get_items(),
                                   supplier_id=supplier_id,
                                   tanggal=tanggal,
                                   catatan=catatan)
    
    # GET request
    return render_template('pembelian/create.html',
                           suppliers=get_suppliers(),
                           items=get_items(),
                           today=datetime.now().strftime('%Y-%m-%d'))
```

---

## 6. Validasi

### 6.1 Validasi Supplier

| Field | Aturan | Pesan Error |
|-------|--------|-------------|
| `nama` | Wajib diisi, max 100 karakter | "Nama supplier wajib diisi!" / "Nama supplier maksimal 100 karakter!" |
| `kontak` | Opsional, max 100 karakter | "Kontak maksimal 100 karakter!" |
| `alamat` | Opsional, max 500 karakter | "Alamat maksimal 500 karakter!" |

### 6.2 Validasi Pembelian

| Field | Aturan | Pesan Error |
|-------|--------|-------------|
| `supplier_id` | Wajib dipilih | "Supplier wajib dipilih!" |
| `tanggal` | Wajib diisi, format date | "Tanggal wajib diisi!" |
| `catatan` | Opsional, max 500 karakter | "Catatan maksimal 500 karakter!" |
| `item_id[]` | Minimal 1 item valid | "Minimal 1 item harus ditambahkan!" |
| `qty[]` | > 0, angka valid | "Qty harus lebih dari 0!" / "Qty harus berupa angka!" |
| `harga_beli[]` | >= 0, angka valid | "Harga beli tidak boleh negatif!" / "Harga beli harus berupa angka!" |

### 6.3 Validasi Delete Pembelian

Saat hapus pembelian:
1. Cek apakah pembelian ada
2. Rollback stok_akhir (kurangi stok, hitung ulang HPP)
3. Hapus stok_mutasi terkait
4. Hapus pembelian_detail (CASCADE)
5. Hapus pembelian header

**Catatan:** Ini operasi atomic yang kompleks. Alternatif lebih aman: **soft delete** (tambah kolom `deleted_at`) atau **jangan izinkan delete** jika sudah ada penjualan terkait.

---

## 7. Nomor Transaksi Otomatis

### 7.1 Format

- Pembelian: `PB-YYYY-NNNN` (contoh: `PB-2026-0001`)
- Penjualan: `PJ-YYYY-NNNN` (contoh: `PJ-2026-0001`) — untuk Fase 3

### 7.2 Implementasi

```python
def generate_nomor_transaksi(prefix):
    """
    Generate nomor transaksi otomatis.
    
    Args:
        prefix: 'PB' atau 'PJ'
    
    Returns:
        nomor_transaksi: string seperti 'PB-2026-0001'
    """
    from datetime import datetime
    
    tahun = datetime.now().year
    pattern = f"{prefix}-{tahun}-%"
    
    # Ambil nomor terakhir
    db = get_db()
    terakhir = db.execute(
        "SELECT nomor_transaksi FROM pembelian WHERE nomor_transaksi LIKE ? ORDER BY nomor_transaksi DESC LIMIT 1",
        (pattern,)
    ).fetchone()
    
    if terakhir:
        # Extract nomor urut terakhir
        nomor_urut = int(terakhir['nomor_transaksi'].split('-')[-1]) + 1
    else:
        nomor_urut = 1
    
    return f"{prefix}-{tahun}-{nomor_urut:04d}"
```

### 7.3 Concurrency Safety

Untuk menghindari race condition saat generate nomor:
- Gunakan `BEGIN IMMEDIATE` sebelum generate nomor
- Atau gunakan `SELECT ... FOR UPDATE` (tidak didukung SQLite)
- Atau buat tabel `nomor_transaksi_counter` dengan atomic increment

**Rekomendasi:** Karena `BEGIN IMMEDIATE` sudah dipakai di alur pembelian, nomor transaksi di-generate di dalam transaksi yang sama, sehingga aman dari race condition.

---

## 8. Helper Functions

### 8.1 `get_suppliers()`

```python
def get_suppliers():
    """Return all suppliers ordered by nama."""
    db = get_db()
    return db.execute('SELECT * FROM supplier ORDER BY nama ASC').fetchall()
```

### 8.2 `get_items()`

```python
def get_items():
    """Return all items ordered by nama."""
    db = get_db()
    return db.execute('SELECT * FROM items ORDER BY nama ASC').fetchall()
```

### 8.3 `hitung_saldo_berjalan(item_id, jenis_mutasi, qty)`

```python
def hitung_saldo_berjalan(item_id, jenis_mutasi, qty):
    """
    Hitung saldo berjalan untuk kartu stok.
    """
    db = get_db()
    saldo_terakhir = db.execute(
        "SELECT saldo_berjalan FROM stok_mutasi "
        "WHERE item_id = ? ORDER BY id DESC LIMIT 1",
        (item_id,)
    ).fetchone()
    
    saldo_sebelumnya = saldo_terakhir['saldo_berjalan'] if saldo_terakhir else 0
    
    if jenis_mutasi == 'IN':
        saldo_berjalan = saldo_sebelumnya + qty
    else:  # OUT
        saldo_berjalan = saldo_sebelumnya - qty
    
    return saldo_berjalan
```

### 8.4 `hitung_hpp_moving_average(item_id, qty_beli, harga_beli)`

```python
def hitung_hpp_moving_average(item_id, qty_beli, harga_beli):
    """
    Hitung HPP moving average setelah pembelian.
    """
    db = get_db()
    stok_akhir = db.execute(
        "SELECT qty_akhir, harga_pokok_rata FROM stok_akhir WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    
    if stok_akhir is None:
        qty_akhir_lama = 0
        hpp_lama = 0
    else:
        qty_akhir_lama = stok_akhir['qty_akhir']
        hpp_lama = stok_akhir['harga_pokok_rata']
    
    if qty_akhir_lama + qty_beli == 0:
        hpp_baru = 0
    else:
        hpp_baru = ((qty_akhir_lama * hpp_lama) + (qty_beli * harga_beli)) / (qty_akhir_lama + qty_beli)
    
    return hpp_baru
```

### 8.5 `update_stok_akhir_setelah_pembelian(item_id, qty_beli, harga_beli)`

```python
def update_stok_akhir_setelah_pembelian(item_id, qty_beli, harga_beli):
    """
    Update stok_akhir setelah pembelian.
    """
    db = get_db()
    hpp_baru = hitung_hpp_moving_average(item_id, qty_beli, harga_beli)
    
    stok_akhir = db.execute(
        "SELECT qty_akhir FROM stok_akhir WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    
    qty_akhir_lama = stok_akhir['qty_akhir'] if stok_akhir else 0
    qty_akhir_baru = qty_akhir_lama + qty_beli
    
    db.execute('''
        INSERT INTO stok_akhir (item_id, qty_akhir, harga_pokok_rata, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(item_id) DO UPDATE SET
            qty_akhir = excluded.qty_akhir,
            harga_pokok_rata = excluded.harga_pokok_rata,
            updated_at = CURRENT_TIMESTAMP
    ''', (item_id, qty_akhir_baru, hpp_baru))
```

---

## 9. Database Migration

### 9.1 DDL untuk Tabel Baru

```sql
-- Tabel supplier
CREATE TABLE IF NOT EXISTS supplier (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT NOT NULL,
    kontak TEXT,
    alamat TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_supplier_nama ON supplier(nama);

-- Tabel pembelian (header)
CREATE TABLE IF NOT EXISTS pembelian (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    nomor_transaksi TEXT NOT NULL UNIQUE,
    tanggal DATE NOT NULL DEFAULT CURRENT_DATE,
    catatan TEXT,
    total REAL NOT NULL DEFAULT 0,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);
CREATE INDEX idx_pembelian_tanggal ON pembelian(tanggal);
CREATE INDEX idx_pembelian_supplier ON pembelian(supplier_id);
CREATE INDEX idx_pembelian_nomor ON pembelian(nomor_transaksi);

-- Tabel pembelian_detail
CREATE TABLE IF NOT EXISTS pembelian_detail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pembelian_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    qty REAL NOT NULL CHECK(qty > 0),
    harga_beli REAL NOT NULL CHECK(harga_beli >= 0),
    subtotal REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pembelian_id) REFERENCES pembelian(id) ON DELETE CASCADE,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE RESTRICT
);
CREATE INDEX idx_pembelian_detail_pembelian ON pembelian_detail(pembelian_id);
CREATE INDEX idx_pembelian_detail_item ON pembelian_detail(item_id);

-- Tabel stok_mutasi (sudah dirancang di Fase 1)
CREATE TABLE IF NOT EXISTS stok_mutasi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    jenis_mutasi TEXT NOT NULL CHECK(jenis_mutasi IN ('IN', 'OUT')),
    qty REAL NOT NULL,
    harga REAL NOT NULL,
    saldo_berjalan REAL NOT NULL,
    referensi_tipe TEXT NOT NULL CHECK(referensi_tipe IN ('pembelian', 'penjualan')),
    referensi_id INTEGER NOT NULL,
    nomor_referensi TEXT NOT NULL,
    tanggal DATE NOT NULL DEFAULT CURRENT_DATE,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT
);
CREATE INDEX idx_stok_mutasi_item ON stok_mutasi(item_id);
CREATE INDEX idx_stok_mutasi_tanggal ON stok_mutasi(tanggal);
CREATE INDEX idx_stok_mutasi_referensi ON stok_mutasi(referensi_tipe, referensi_id);
CREATE INDEX idx_stok_mutasi_nomor ON stok_mutasi(nomor_referensi);

-- Tabel stok_akhir (cache saldo terakhir)
CREATE TABLE IF NOT EXISTS stok_akhir (
    item_id INTEGER PRIMARY KEY,
    qty_akhir REAL NOT NULL DEFAULT 0,
    harga_pokok_rata REAL NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE CASCADE
);
CREATE INDEX idx_stok_akhir_item ON stok_akhir(item_id);
```

### 9.2 Update `init_db()`

Tambahkan DDL di atas ke fungsi `init_db()` yang sudah ada.

### 9.3 Update Role Admin

Update seed data role admin untuk menambahkan permission menu baru:

```python
full_perms = json.dumps({
    'items': ['view', 'create', 'edit', 'delete'],
    'kategori': ['view', 'create', 'edit', 'delete'],
    'pelanggan': ['view', 'create', 'edit', 'delete'],
    'users': ['view', 'create', 'edit', 'delete'],
    'roles': ['view', 'create', 'edit', 'delete'],
    'supplier': ['view', 'create', 'edit', 'delete'],
    'pembelian': ['view', 'create', 'delete'],
})
```

---

## 10. Delete Pembelian (Rollback Stok)

### 10.1 Flow

```
User klik Hapus pembelian
        │
        ▼
┌───────────────────────────────────┐
│ 1. BEGIN IMMEDIATE                │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 2. Ambil semua stok_mutasi        │
│    related ke pembelian ini      │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 3. LOOP untuk setiap mutasi:      │
│    a. Hitung saldo rollback       │
│    b. Update stok_akhir           │
│    c. Hapus stok_mutasi           │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 4. Hapus pembelian_detail         │
│    (CASCADE)                      │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 5. Hapus pembelian header         │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 6. COMMIT                         │
└───────────────────────────────────┘
```

### 10.2 Pseudocode

```python
@app.route('/pembelian/<int:id>/delete', methods=['POST'])
@has_permission('pembelian', 'delete')
def delete_pembelian(id):
    """Delete pembelian dan rollback stok."""
    db = get_db()
    pembelian = db.execute('SELECT * FROM pembelian WHERE id = ?', (id,)).fetchone()
    
    if pembelian is None:
        flash('Pembelian tidak ditemukan!', 'error')
        return redirect(url_for('pembelian_index'))
    
    try:
        db.execute("BEGIN IMMEDIATE")
        
        # Ambil semua stok_mutasi related
        mutasis = db.execute(
            "SELECT * FROM stok_mutasi WHERE referensi_tipe = 'pembelian' AND referensi_id = ?",
            (id,)
        ).fetchall()
        
        # Rollback setiap mutasi
        for mutasi in mutasis:
            item_id = mutasi['item_id']
            qty = mutasi['qty']
            
            # Hitung saldo rollback (kurangi stok)
            saldo_terakhir = db.execute(
                "SELECT saldo_berjalan FROM stok_mutasi "
                "WHERE item_id = ? AND id != ? ORDER BY id DESC LIMIT 1",
                (item_id, mutasi['id'])
            ).fetchone()
            
            saldo_sebelumnya = saldo_terakhir['saldo_berjalan'] if saldo_terakhir else 0
            saldo_baru = saldo_sebelumnya - qty  # Rollback IN = kurangi
            
            # Update stok_akhir
            stok_akhir = db.execute(
                "SELECT qty_akhir, harga_pokok_rata FROM stok_akhir WHERE item_id = ?",
                (item_id,)
            ).fetchone()
            
            if stok_akhir:
                qty_akhir_baru = stok_akhir['qty_akhir'] - qty
                if qty_akhir_baru < 0:
                    qty_akhir_baru = 0  # Safety: jangan negatif
                
                db.execute('''
                    UPDATE stok_akhir SET qty_akhir = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                ''', (qty_akhir_baru, item_id))
            
            # Hapus mutasi
            db.execute("DELETE FROM stok_mutasi WHERE id = ?", (mutasi['id'],))
        
        # Hapus detail (CASCADE)
        db.execute("DELETE FROM pembelian_detail WHERE pembelian_id = ?", (id,))
        
        # Hapus header
        db.execute("DELETE FROM pembelian WHERE id = ?", (id,))
        
        db.commit()
        flash('Pembelian berhasil dihapus!', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Gagal menghapus pembelian: {str(e)}', 'error')
    
    return redirect(url_for('pembelian_index'))
```

---

## 11. Query untuk View Pembelian

### 11.1 Query Index Pembelian

```sql
SELECT 
    p.*,
    s.nama as supplier_nama,
    u.username as created_by_username
FROM pembelian p
JOIN supplier s ON p.supplier_id = s.id
JOIN users u ON p.created_by = u.id
ORDER BY p.created_at DESC
```

### 11.2 Query Detail Pembelian

```sql
-- Header
SELECT 
    p.*,
    s.nama as supplier_nama,
    u.username as created_by_username
FROM pembelian p
JOIN supplier s ON p.supplier_id = s.id
JOIN users u ON p.created_by = u.id
WHERE p.id = ?

-- Detail
SELECT 
    pd.*,
    i.nama as item_nama
FROM pembelian_detail pd
JOIN items i ON pd.item_id = i.id
WHERE pd.pembelian_id = ?
```

---

## 12. Estimasi Kompleksitas

| Komponen | Jumlah | Kompleksitas |
|----------|--------|--------------|
| Route supplier | 5 | Rendah |
| Route pembelian | 4 | Tinggi (atomic) |
| Template supplier | 4 | Rendah |
| Template pembelian | 3 | Sedang (dynamic form) |
| Helper functions | 5 | Sedang |
| DDL migration | 4 tabel | Rendah |
| **Total** | **25** | **Sedang** |

---

## 13. Acceptance Criteria Fase 2

- [ ] Supplier CRUD berfungsi penuh (tambah, lihat, edit, hapus)
- [ ] Pembelian form multi-item berfungsi (tambah item dinamis)
- [ ] Pembelian atomic: header + detail + stok_mutasi + stok_akhir
- [ ] Nomor transaksi otomatis `PB-YYYY-NNNN`
- [ ] Stok bertambah otomatis setelah pembelian
- [ ] HPP moving average terhitung dengan benar
- [ ] Validasi: qty > 0, harga >= 0, minimal 1 item
- [ ] Delete pembelian me-rollback stok dengan benar
- [ ] RBAC: menu `supplier` dan `pembelian` muncul di navigasi
- [ ] Security grade tetap A+
- [ ] Semua test lama masih lolos

---

## 14. Langkah Selanjutnya (Fase 3)

1. **Fase 3:** Implementasi Penjualan (stok keluar) + validasi stok
2. **Fase 4:** Implementasi Kartu Stok + Laporan
3. **Fase 5:** RBAC untuk menu penjualan + stok
4. **Fase 6:** Seed data awal
5. **Fase 7:** Test atomicity + deploy + verifikasi

---

## 15. Catatan Implementasi untuk OpenCode

### 15.1 Urutan Pengerjaan

1. **Database migration:** Tambah DDL untuk 4 tabel baru di `init_db()`
2. **Helper functions:** Tambah `get_suppliers()`, `get_items()`, `hitung_saldo_berjalan()`, `hitung_hpp_moving_average()`, `update_stok_akhir_setelah_pembelian()`, `generate_nomor_transaksi()`
3. **Supplier routes:** Implementasi 5 route supplier (CRUD lengkap)
4. **Supplier templates:** Buat 4 template supplier
5. **Pembelian routes:** Implementasi 4 route pembelian
6. **Pembelian templates:** Buat 3 template pembelian
7. **Update base.html:** Tambah navigasi untuk menu baru
8. **Update role admin:** Tambah permission untuk menu baru
9. **Test:** Jalankan aplikasi, test semua fitur

### 15.2 Hal yang Harus Diperhatikan

- **Jangan ubah kode existing** yang tidak terkait Fase 2
- **Pertahankan pola** `@has_permission`, CSRF, security headers
- **Gunakan `BEGIN IMMEDIATE`** untuk semua operasi atomic
- **Validasi di sisi server** untuk semua input
- **Flash message** untuk feedback ke user
- **Redirect setelah POST** (PRG pattern)

### 15.3 Testing Checklist

- [ ] Buka `/supplier` — harusnya muncul di navigasi
- [ ] Tambah supplier baru — harusnya berhasil
- [ ] Edit supplier — harusnya berhasil
- [ ] Hapus supplier — harusnya berhasil
- [ ] Buka `/pembelian` — harusnya muncul di navigasi
- [ ] Tambah pembelian dengan 2 item — harusnya berhasil
- [ ] Cek stok_akhir — stok harus bertambah
- [ ] Cek stok_mutasi — harus ada 2 baris IN
- [ ] Hapus pembelian — stok harus berkurang
- [ ] Cek nomor transaksi — harusnya `PB-2026-0001`, `PB-2026-0002`, dst
- [ ] Test validasi: qty = 0, harga = -100, kosongkan supplier
- [ ] Test dengan user non-admin (jika ada)

---

**End of Design Document Fase 2**
