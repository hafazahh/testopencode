# Desain Fase 3: Penjualan (Stok Keluar) + Validasi Stok

**Project:** `/home/choirulhaq/venvProject/testopencode/`
**Status:** Draft untuk review user
**Tanggal:** 2026-10-07
**Fase sebelumnya:** Fase 2 (Supplier + Pembelian) — ✅ approved & implemented

---

## 1. Ringkasan

Fase 3 menambahkan **1 menu baru** ke sistem:
- **Penjualan** — Transaksi penjualan barang (stok keluar) dengan validasi stok, atomic insert, dan HPP snapshot

**Total route baru:** 4 route
**Total template baru:** 3 file
**Tabel baru:** 0 (penjualan + penjualan_detail sudah dirancang di Fase 1)
**Tabel yang dimodifikasi:** 0

---

## 2. Route Lengkap

### 2.1 Route Penjualan (4 route)

| # | Route | Method | Permission | Fungsi |
|---|-------|--------|------------|--------|
| 1 | `/penjualan` | GET | `penjualan.view` | Daftar semua penjualan |
| 2 | `/penjualan/create` | GET, POST | `penjualan.create` | Form tambah penjualan (multi-item) |
| 3 | `/penjualan/<int:id>` | GET | `penjualan.view` | Detail penjualan (header + detail) |
| 4 | `/penjualan/<int:id>/delete` | POST | `penjualan.delete` | Hapus penjualan (rollback stok) |

**Catatan:** Route penjualan delete akan me-rollback stok_mutasi dan stok_akhir terkait (tambah stok kembali).

---

## 3. Template Lengkap

### 3.1 Struktur Template

```
templates/
└── penjualan/
    ├── index.html      — Daftar penjualan (tabel + aksi)
    ├── create.html     — Form penjualan multi-item (dynamic rows)
    └── view.html       — Detail penjualan (header + detail)
```

### 3.2 Template: `penjualan/index.html`

```html
{% extends "base.html" %}

{% block title %}Daftar Penjualan - CRUD Item{% endblock %}

{% block content %}
<div class="list-header">
    <h2>Daftar Penjualan</h2>
    {% if 'create' in user_perms.get('penjualan', []) %}
    <a href="{{ url_for('create_penjualan') }}" class="btn btn-primary">+ Tambah Penjualan</a>
    {% endif %}
</div>

{% if penjualan %}
    <table class="data-table">
        <thead>
            <tr>
                <th scope="col">No</th>
                <th scope="col">No. Transaksi</th>
                <th scope="col">Tanggal</th>
                <th scope="col">Pelanggan</th>
                <th scope="col">Total</th>
                <th scope="col">Aksi</th>
            </tr>
        </thead>
        <tbody>
            {% for p in penjualan %}
            <tr>
                <td>{{ loop.index }}</td>
                <td>{{ p.nomor_transaksi }}</td>
                <td>{{ p.tanggal }}</td>
                <td>{{ p.pelanggan_nama }}</td>
                <td>Rp {{ "{:,.0f}".format(p.total) }}</td>
                <td class="actions">
                    <a href="{{ url_for('view_penjualan', id=p.id) }}" class="btn btn-sm btn-view">Lihat</a>
                    {% if 'delete' in user_perms.get('penjualan', []) %}
                    <form action="{{ url_for('delete_penjualan', id=p.id) }}" method="POST" class="inline-form" onsubmit="return confirm('Yakin ingin hapus penjualan ini? Stok akan dikembalikan.');">
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
        <p>Belum ada penjualan. <a href="{{ url_for('create_penjualan') }}">Tambah penjualan pertama</a></p>
    </div>
{% endif %}
{% endblock %}
```

### 3.3 Template: `penjualan/create.html`

```html
{% extends "base.html" %}

{% block title %}Tambah Penjualan - CRUD Item{% endblock %}

{% block content %}
<h2>Tambah Penjualan Baru</h2>

<form method="POST" action="{{ url_for('create_penjualan') }}" class="form" id="penjualan-form">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    
    <div class="form-row">
        <div class="form-group">
            <label for="pelanggan_id">Pelanggan</label>
            <select id="pelanggan_id" name="pelanggan_id" required>
                <option value="">-- Pilih Pelanggan --</option>
                {% for p in pelanggans %}
                <option value="{{ p.id }}" {% if pelanggan_id == p.id %}selected{% endif %}>{{ p.nama }}</option>
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
                <th scope="col">Stok Tersedia</th>
                <th scope="col">Qty</th>
                <th scope="col">Harga Jual</th>
                <th scope="col">Subtotal</th>
                <th scope="col">Aksi</th>
            </tr>
        </thead>
        <tbody id="detail-rows">
            <!-- Dynamic rows will be added here -->
        </tbody>
        <tfoot>
            <tr>
                <td colspan="4" style="text-align: right;"><strong>Total:</strong></td>
                <td colspan="2"><strong id="total-display">Rp 0</strong></td>
            </tr>
        </tfoot>
    </table>

    <button type="button" class="btn btn-secondary" id="add-row-btn">+ Tambah Item</button>

    <div class="form-actions">
        <button type="submit" class="btn btn-primary">Simpan Penjualan</button>
        <a href="{{ url_for('penjualan_index') }}" class="btn btn-secondary">Batal</a>
    </div>
</form>

<script>
// Template untuk baris item
const itemOptions = `{% for item in items %}
    <option value="{{ item.id }}">{{ item.nama }}</option>
{% endfor %}`;

// Data items untuk lookup stok dan harga
const itemsData = {
    {% for item in items %}
    {{ item.id }}: { 
        nama: "{{ item.nama }}", 
        stok: {{ item.stok_akhir }},
        harga_pokok: {{ item.harga_pokok }}
    },
    {% endfor %}
};

let rowCount = 0;

function addDetailRow(itemId = '', qty = '', harga = '') {
    rowCount++;
    const tbody = document.getElementById('detail-rows');
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            <select name="item_id[]" required onchange="updateStokInfo(this)">
                <option value="">-- Pilih Item --</option>
                ${itemOptions}
            </select>
        </td>
        <td>
            <span class="stok-display">-</span>
        </td>
        <td>
            <input type="number" name="qty[]" value="${qty}" min="0.01" step="0.01" required placeholder="0" oninput="updateSubtotal(this)">
        </td>
        <td>
            <input type="number" name="harga_jual[]" value="${harga}" min="0" step="0.01" required placeholder="0" oninput="updateSubtotal(this)">
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
        updateStokInfo(row.querySelector('select[name="item_id[]"]'));
    }
}

function removeRow(btn) {
    btn.closest('tr').remove();
    updateTotal();
}

function updateStokInfo(select) {
    const itemId = select.value;
    const row = select.closest('tr');
    const stokDisplay = row.querySelector('.stok-display');
    const hargaInput = row.querySelector('input[name="harga_jual[]"]');
    
    if (itemId && itemsData[itemId]) {
        stokDisplay.textContent = itemsData[itemId].stok;
        // Suggest harga jual = harga_pokok * 1.2 (20% margin) jika harga kosong
        if (!hargaInput.value) {
            hargaInput.value = Math.round(itemsData[itemId].harga_pokok * 1.2);
        }
    } else {
        stokDisplay.textContent = '-';
    }
    updateSubtotal(hargaInput);
}

function updateSubtotal(input) {
    const row = input.closest('tr');
    const qty = parseFloat(row.querySelector('input[name="qty[]"]').value) || 0;
    const harga = parseFloat(row.querySelector('input[name="harga_jual[]"]').value) || 0;
    const subtotal = qty * harga;
    row.querySelector('.subtotal-display').textContent = 'Rp ' + subtotal.toLocaleString('id-ID');
    updateTotal();
}

function updateTotal() {
    let total = 0;
    document.querySelectorAll('#detail-rows tr').forEach(row => {
        const qty = parseFloat(row.querySelector('input[name="qty[]"]').value) || 0;
        const harga = parseFloat(row.querySelector('input[name="harga_jual[]"]').value) || 0;
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

### 3.4 Template: `penjualan/view.html`

```html
{% extends "base.html" %}

{% block title %}{{ penjualan.nomor_transaksi }} - CRUD Item{% endblock %}

{% block content %}
<h2>Detail Penjualan</h2>

<div class="detail-card">
    <div class="detail-row">
        <span class="detail-label">No. Transaksi</span>
        <span class="detail-value">{{ penjualan.nomor_transaksi }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Tanggal</span>
        <span class="detail-value">{{ penjualan.tanggal }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Pelanggan</span>
        <span class="detail-value">{{ penjualan.pelanggan_nama }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Catatan</span>
        <span class="detail-value">{{ penjualan.catatan if penjualan.catatan else '-' }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Dibuat oleh</span>
        <span class="detail-value">{{ penjualan.created_by_username }}</span>
    </div>
    <div class="detail-row">
        <span class="detail-label">Dibuat pada</span>
        <span class="detail-value">{{ penjualan.created_at }}</span>
    </div>
</div>

<h3>Detail Item</h3>
<table class="data-table">
    <thead>
        <tr>
            <th scope="col">No</th>
            <th scope="col">Item</th>
            <th scope="col">Qty</th>
            <th scope="col">Harga Jual</th>
            <th scope="col">Harga Pokok</th>
            <th scope="col">Subtotal</th>
        </tr>
    </thead>
    <tbody>
        {% for d in detail %}
        <tr>
            <td>{{ loop.index }}</td>
            <td>{{ d.item_nama }}</td>
            <td>{{ d.qty }}</td>
            <td>Rp {{ "{:,.0f}".format(d.harga_jual) }}</td>
            <td>Rp {{ "{:,.0f}".format(d.harga_pokok) }}</td>
            <td>Rp {{ "{:,.0f}".format(d.subtotal) }}</td>
        </tr>
        {% endfor %}
    </tbody>
    <tfoot>
        <tr>
            <td colspan="5" style="text-align: right;"><strong>Total:</strong></td>
            <td><strong>Rp {{ "{:,.0f}".format(penjualan.total) }}</strong></td>
        </tr>
    </tfoot>
</table>

<div class="form-actions">
    {% if 'delete' in user_perms.get('penjualan', []) %}
    <form action="{{ url_for('delete_penjualan', id=penjualan.id) }}" method="POST" class="inline-form" onsubmit="return confirm('Yakin ingin hapus penjualan ini? Stok akan dikembalikan.');">
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
        <button type="submit" class="btn btn-delete">Hapus</button>
    </form>
    {% endif %}
    <a href="{{ url_for('penjualan_index') }}" class="btn btn-secondary">Kembali</a>
</div>
{% endblock %}
```

---

## 4. Integrasi RBAC

### 4.1 Permission Structure

Permission untuk menu penjualan mengikuti pola yang sama dengan menu existing:

```json
{
    "penjualan": ["view", "create", "delete"]
}
```

**Catatan:** Penjualan tidak punya permission `edit` karena transaksi penjualan tidak bisa diedit setelah dibuat (hanya bisa dihapus dan dibuat ulang).

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
    'penjualan': ['view', 'create', 'delete'],
})
```

### 4.3 Navigasi Sidebar

Tambahkan di `base.html`:

```html
{% if 'view' in user_perms.get('penjualan', []) %}
<a href="{{ url_for('penjualan_index') }}" class="btn btn-nav">Penjualan</a>
{% endif %}
```

---

## 5. Alur Penjualan Atomic

### 5.1 Flowchart

```
User submit form penjualan
        │
        ▼
┌───────────────────────────────────┐
│ 1. Validasi form                  │
│    - pelanggan_id wajib          │
│    - tanggal wajib               │
│    - minimal 1 item               │
│    - qty > 0 untuk setiap item    │
│    - harga_jual >= 0              │
└───────────────────────────────────┘
        │
        ▼ (valid)
┌───────────────────────────────────┐
│ 2. Validasi stok                  │
│    - Cek stok_akhir >= qty        │
│    - Jika tidak cukup → error     │
└───────────────────────────────────┘
        │
        ▼ (stok cukup)
┌───────────────────────────────────┐
│ 3. BEGIN IMMEDIATE                │
│    (kunci database)               │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 4. Generate nomor transaksi       │
│    PJ-YYYY-NNNN                   │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 5. INSERT header penjualan        │
│    (pelanggan_id, nomor, tanggal, │
│     catatan, total, created_by)   │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 6. LOOP untuk setiap item:        │
│    a. INSERT penjualan_detail     │
│       (dengan harga_pokok snap)   │
│    b. Hitung saldo berjalan       │
│    c. UPDATE stok_akhir           │
│    d. INSERT stok_mutasi (OUT)    │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 7. COMMIT                         │
└───────────────────────────────────┘
        │
        ▼ (sukses)
   Redirect ke detail penjualan

        │
        ▼ (gagal)
┌───────────────────────────────────┐
│ 8. ROLLBACK                       │
│    (tidak ada perubahan)          │
└───────────────────────────────────┘
        │
        ▼
   Flash error, redirect ke form
```

### 5.2 Pseudocode Implementasi

```python
@app.route('/penjualan/create', methods=['GET', 'POST'])
@has_permission('penjualan', 'create')
def create_penjualan():
    if request.method == 'POST':
        pelanggan_id = request.form.get('pelanggan_id', '').strip()
        tanggal = request.form.get('tanggal', '').strip()
        catatan = request.form.get('catatan', '').strip()
        
        # Ambil array dari form
        item_ids = request.form.getlist('item_id[]')
        qtys = request.form.getlist('qty[]')
        hargas = request.form.getlist('harga_jual[]')
        
        # Validasi
        errors = []
        if not pelanggan_id:
            errors.append('Pelanggan wajib dipilih!')
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
                continue  # Skip baris kosong
            
            try:
                qty = float(qty_str)
                harga = float(harga_str)
                if qty <= 0:
                    errors.append(f'Item {i+1}: Qty harus lebih dari 0!')
                    continue
                if harga < 0:
                    errors.append(f'Item {i+1}: Harga jual tidak boleh negatif!')
                    continue
                
                # Validasi stok cukup
                stok_cukup, pesan_stok = validasi_stok_cukup(int(item_id), qty)
                if not stok_cukup:
                    errors.append(f'Item {i+1}: {pesan_stok}')
                    continue
                
                valid_items.append({
                    'item_id': int(item_id),
                    'qty': qty,
                    'harga_jual': harga,
                    'subtotal': qty * harga
                })
            except ValueError:
                errors.append(f'Item {i+1}: Qty dan harga harus berupa angka!')
        
        if len(valid_items) == 0 and len(errors) == 0:
            errors.append('Minimal 1 item harus ditambahkan!')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('penjualan/create.html', 
                                   pelanggans=get_pelanggans(),
                                   items=get_items_with_stok(),
                                   pelanggan_id=pelanggan_id,
                                   tanggal=tanggal,
                                   catatan=catatan)
        
        # Hitung total
        total = sum(item['subtotal'] for item in valid_items)
        
        # Atomic insert
        db = get_db()
        try:
            db.execute("BEGIN IMMEDIATE")
            
            # Generate nomor transaksi
            nomor = generate_nomor_transaksi('PJ')
            
            # Insert header
            cursor = db.execute('''
                INSERT INTO penjualan (pelanggan_id, nomor_transaksi, tanggal, catatan, total, created_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (int(pelanggan_id), nomor, tanggal, catatan, total, session['user_id']))
            
            penjualan_id = cursor.lastrowid
            
            # Insert detail + update stok
            for item in valid_items:
                # Ambil HPP snapshot dari stok_akhir
                stok_akhir = db.execute(
                    "SELECT harga_pokok_rata FROM stok_akhir WHERE item_id = ?",
                    (item['item_id'],)
                ).fetchone()
                harga_pokok = stok_akhir['harga_pokok_rata'] if stok_akhir else 0
                
                # Insert detail
                db.execute('''
                    INSERT INTO penjualan_detail (penjualan_id, item_id, qty, harga_jual, harga_pokok, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (penjualan_id, item['item_id'], item['qty'], item['harga_jual'], harga_pokok, item['subtotal']))
                
                # Update stok_akhir (kurangi stok)
                update_stok_akhir_setelah_penjualan(item['item_id'], item['qty'])
                
                # Insert stok_mutasi
                saldo_berjalan = hitung_saldo_berjalan(item['item_id'], 'OUT', item['qty'])
                db.execute('''
                    INSERT INTO stok_mutasi (item_id, jenis_mutasi, qty, harga, saldo_berjalan,
                                             referensi_tipe, referensi_id, nomor_referensi, tanggal, created_by)
                    VALUES (?, 'OUT', ?, ?, ?, 'penjualan', ?, ?, ?, ?)
                ''', (item['item_id'], item['qty'], harga_pokok, saldo_berjalan,
                      penjualan_id, nomor, tanggal, session['user_id']))
            
            db.commit()
            flash(f'Penjualan {nomor} berhasil dibuat!', 'success')
            return redirect(url_for('view_penjualan', id=penjualan_id))
            
        except Exception as e:
            db.rollback()
            flash(f'Gagal membuat penjualan: {str(e)}', 'error')
            return render_template('penjualan/create.html',
                                   pelanggans=get_pelanggans(),
                                   items=get_items_with_stok(),
                                   pelanggan_id=pelanggan_id,
                                   tanggal=tanggal,
                                   catatan=catatan)
    
    # GET request
    return render_template('penjualan/create.html',
                           pelanggans=get_pelanggans(),
                           items=get_items_with_stok(),
                           today=datetime.now().strftime('%Y-%m-%d'))
```

---

## 6. Validasi Stok

### 6.1 Validasi di Level Aplikasi

```python
def validasi_stok_cukup(item_id, qty_diminta):
    """
    Cek apakah stok cukup untuk penjualan.
    
    Returns:
        (bool, str): (cukup, pesan_error)
    """
    db = get_db()
    
    # Ambil saldo terakhir dari stok_akhir
    stok_akhir = db.execute(
        "SELECT qty_akhir FROM stok_akhir WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    
    saldo_akhir = stok_akhir['qty_akhir'] if stok_akhir else 0
    
    if saldo_akhir < qty_diminta:
        return False, f"Stok tidak cukup. Tersedia: {saldo_akhir}, Diminta: {qty_diminta}"
    
    return True, ""
```

### 6.2 Validasi di Level Database

```sql
-- Constraint di stok_mutasi
CHECK(saldo_berjalan >= 0)

-- Trigger untuk validasi tambahan
CREATE TRIGGER IF NOT EXISTS trg_validasi_stok_negatif
BEFORE INSERT ON stok_mutasi
BEGIN
    SELECT CASE
        WHEN NEW.saldo_berjalan < 0 THEN
            RAISE(ABORT, 'Stok tidak boleh negatif')
    END;
END;
```

### 6.3 Validasi Form

| Field | Aturan | Pesan Error |
|-------|--------|-------------|
| `pelanggan_id` | Wajib dipilih | "Pelanggan wajib dipilih!" |
| `tanggal` | Wajib diisi, format date | "Tanggal wajib diisi!" |
| `catatan` | Opsional, max 500 karakter | "Catatan maksimal 500 karakter!" |
| `item_id[]` | Minimal 1 item valid | "Minimal 1 item harus ditambahkan!" |
| `qty[]` | > 0, angka valid | "Qty harus lebih dari 0!" / "Qty harus berupa angka!" |
| `harga_jual[]` | >= 0, angka valid | "Harga jual tidak boleh negatif!" / "Harga jual harus berupa angka!" |
| Stok | qty <= stok_akhir | "Stok tidak cukup. Tersedia: X, Diminta: Y" |

---

## 7. HPP Snapshot

### 7.1 Konsep

Saat penjualan dibuat:
1. Ambil HPP saat ini dari `stok_akhir.harga_pokok_rata`
2. Simpan HPP ini di kolom `harga_pokok` di `penjualan_detail`
3. HPP ini **tidak berubah** meski ada pembelian setelahnya

### 7.2 Implementasi

```python
# Ambil HPP snapshot dari stok_akhir
stok_akhir = db.execute(
    "SELECT harga_pokok_rata FROM stok_akhir WHERE item_id = ?",
    (item['item_id'],)
).fetchone()
harga_pokok = stok_akhir['harga_pokok_rata'] if stok_akhir else 0

# Insert detail dengan harga_pokok snapshot
db.execute('''
    INSERT INTO penjualan_detail (penjualan_id, item_id, qty, harga_jual, harga_pokok, subtotal)
    VALUES (?, ?, ?, ?, ?, ?)
''', (penjualan_id, item['item_id'], item['qty'], item['harga_jual'], harga_pokok, item['subtotal']))
```

---

## 8. Delete Penjualan (Rollback Stok)

### 8.1 Flow

```
User klik Hapus penjualan
        │
        ▼
┌───────────────────────────────────┐
│ 1. BEGIN IMMEDIATE                │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 2. Ambil semua stok_mutasi        │
│    related ke penjualan ini      │
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
│ 4. Hapus penjualan_detail         │
│    (CASCADE)                      │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 5. Hapus penjualan header         │
└───────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────┐
│ 6. COMMIT                         │
└───────────────────────────────────┘
```

### 8.2 Pseudocode

```python
@app.route('/penjualan/<int:id>/delete', methods=['POST'])
@has_permission('penjualan', 'delete')
def delete_penjualan(id):
    """Delete penjualan dan rollback stok."""
    db = get_db()
    penjualan = db.execute('SELECT * FROM penjualan WHERE id = ?', (id,)).fetchone()
    
    if penjualan is None:
        flash('Penjualan tidak ditemukan!', 'error')
        return redirect(url_for('penjualan_index'))
    
    try:
        db.execute("BEGIN IMMEDIATE")
        
        # Ambil semua stok_mutasi related
        mutasis = db.execute(
            "SELECT * FROM stok_mutasi WHERE referensi_tipe = 'penjualan' AND referensi_id = ?",
            (id,)
        ).fetchall()
        
        # Rollback setiap mutasi
        for mutasi in mutasis:
            item_id = mutasi['item_id']
            qty = mutasi['qty']
            
            # Update stok_akhir (tambah stok kembali)
            stok_akhir = db.execute(
                "SELECT qty_akhir FROM stok_akhir WHERE item_id = ?",
                (item_id,)
            ).fetchone()
            
            if stok_akhir:
                qty_akhir_baru = stok_akhir['qty_akhir'] + qty  # Rollback OUT = tambah stok
                
                db.execute('''
                    UPDATE stok_akhir SET qty_akhir = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = ?
                ''', (qty_akhir_baru, item_id))
            
            # Hapus mutasi
            db.execute("DELETE FROM stok_mutasi WHERE id = ?", (mutasi['id'],))
        
        # Hapus detail (CASCADE)
        db.execute("DELETE FROM penjualan_detail WHERE penjualan_id = ?", (id,))
        
        # Hapus header
        db.execute("DELETE FROM penjualan WHERE id = ?", (id,))
        
        db.commit()
        flash('Penjualan berhasil dihapus!', 'success')
        
    except Exception as e:
        db.rollback()
        flash(f'Gagal menghapus penjualan: {str(e)}', 'error')
    
    return redirect(url_for('penjualan_index'))
```

---

## 9. Helper Functions

### 9.1 `get_pelanggans()`

```python
def get_pelanggans():
    """Return all pelanggans ordered by nama."""
    db = get_db()
    return db.execute('SELECT * FROM pelanggan ORDER BY nama ASC').fetchall()
```

### 9.2 `get_items_with_stok()`

```python
def get_items_with_stok():
    """Return all items with current stock from stok_akhir."""
    db = get_db()
    return db.execute('''
        SELECT 
            i.*,
            COALESCE(sa.qty_akhir, 0) as stok_akhir,
            COALESCE(sa.harga_pokok_rata, 0) as harga_pokok
        FROM items i
        LEFT JOIN stok_akhir sa ON i.id = sa.item_id
        ORDER BY i.nama ASC
    ''').fetchall()
```

### 9.3 `validasi_stok_cukup(item_id, qty_diminta)`

```python
def validasi_stok_cukup(item_id, qty_diminta):
    """
    Cek apakah stok cukup untuk penjualan.
    
    Returns:
        (bool, str): (cukup, pesan_error)
    """
    db = get_db()
    
    stok_akhir = db.execute(
        "SELECT qty_akhir FROM stok_akhir WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    
    saldo_akhir = stok_akhir['qty_akhir'] if stok_akhir else 0
    
    if saldo_akhir < qty_diminta:
        return False, f"Stok tidak cukup. Tersedia: {saldo_akhir}, Diminta: {qty_diminta}"
    
    return True, ""
```

### 9.4 `update_stok_akhir_setelah_penjualan(item_id, qty_jual)`

```python
def update_stok_akhir_setelah_penjualan(item_id, qty_jual):
    """
    Update stok_akhir setelah penjualan (kurangi stok).
    HPP tidak berubah saat penjualan.
    """
    db = get_db()
    
    stok_akhir = db.execute(
        "SELECT qty_akhir, harga_pokok_rata FROM stok_akhir WHERE item_id = ?",
        (item_id,)
    ).fetchone()
    
    if stok_akhir:
        qty_akhir_baru = stok_akhir['qty_akhir'] - qty_jual
        if qty_akhir_baru < 0:
            qty_akhir_baru = 0  # Safety: jangan negatif
        
        db.execute('''
            UPDATE stok_akhir SET qty_akhir = ?, updated_at = CURRENT_TIMESTAMP
            WHERE item_id = ?
        ''', (qty_akhir_baru, item_id))
```

### 9.5 `generate_nomor_transaksi(prefix)` — Update

```python
def generate_nomor_transaksi(prefix):
    """
    Generate nomor transaksi otomatis.
    
    Args:
        prefix: 'PB' atau 'PJ'
    
    Returns:
        nomor_transaksi: string seperti 'PJ-2026-0001'
    """
    from datetime import datetime
    
    tahun = datetime.now().year
    pattern = f"{prefix}-{tahun}-%"
    
    db = get_db()
    
    # Tabel dan kolom berdasarkan prefix
    if prefix == 'PB':
        tabel = 'pembelian'
    else:  # PJ
        tabel = 'penjualan'
    
    # Ambil nomor terakhir
    terakhir = db.execute(
        f"SELECT nomor_transaksi FROM {tabel} WHERE nomor_transaksi LIKE ? ORDER BY nomor_transaksi DESC LIMIT 1",
        (pattern,)
    ).fetchone()
    
    if terakhir:
        nomor_urut = int(terakhir['nomor_transaksi'].split('-')[-1]) + 1
    else:
        nomor_urut = 1
    
    return f"{prefix}-{tahun}-{nomor_urut:04d}"
```

---

## 10. Query untuk View Penjualan

### 10.1 Query Index Penjualan

```sql
SELECT 
    p.*,
    pl.nama as pelanggan_nama,
    u.username as created_by_username
FROM penjualan p
JOIN pelanggan pl ON p.pelanggan_id = pl.id
JOIN users u ON p.created_by = u.id
ORDER BY p.created_at DESC
```

### 10.2 Query Detail Penjualan

```sql
-- Header
SELECT 
    p.*,
    pl.nama as pelanggan_nama,
    u.username as created_by_username
FROM penjualan p
JOIN pelanggan pl ON p.pelanggan_id = pl.id
JOIN users u ON p.created_by = u.id
WHERE p.id = ?

-- Detail
SELECT 
    pd.*,
    i.nama as item_nama
FROM penjualan_detail pd
JOIN items i ON pd.item_id = i.id
WHERE pd.penjualan_id = ?
```

---

## 11. Database Migration

### 11.1 DDL untuk Tabel Penjualan (sudah ada di Fase 1)

Tabel `penjualan` dan `penjualan_detail` sudah dirancang di Fase 1. Tidak perlu migration baru.

### 11.2 Update `init_db()`

Pastikan DDL untuk `penjualan` dan `penjualan_detail` sudah ada di `init_db()` (sudah ditambahkan di Fase 1).

### 11.3 Update Role Admin

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
    'penjualan': ['view', 'create', 'delete'],
})
```

---

## 12. Estimasi Kompleksitas

| Komponen | Jumlah | Kompleksitas |
|----------|--------|--------------|
| Route penjualan | 4 | Tinggi (atomic + validasi stok) |
| Template penjualan | 3 | Sedang (dynamic form) |
| Helper functions | 3 | Sedang |
| DDL migration | 0 tabel | - |
| **Total** | **10** | **Sedang** |

---

## 13. Acceptance Criteria Fase 3

- [ ] Penjualan form multi-item berfungsi (tambah item dinamis)
- [ ] Penjualan atomic: header + detail + stok_mutasi + stok_akhir
- [ ] Validasi stok: tidak bisa jual melebihi stok tersedia
- [ ] HPP snapshot tersimpan di `penjualan_detail.harga_pokok`
- [ ] Nomor transaksi otomatis `PJ-YYYY-NNNN`
- [ ] Stok berkurang otomatis setelah penjualan
- [ ] Delete penjualan me-rollback stok dengan benar (tambah stok kembali)
- [ ] RBAC: menu `penjualan` muncul di navigasi
- [ ] Security grade tetap A+
- [ ] Semua test lama masih lolos

---

## 14. Langkah Selanjutnya (Fase 4)

1. **Fase 4:** Implementasi Kartu Stok + Laporan
2. **Fase 5:** RBAC untuk menu stok
3. **Fase 6:** Seed data awal
4. **Fase 7:** Test atomicity + deploy + verifikasi

---

## 15. Catatan Implementasi untuk OpenCode

### 15.1 Urutan Pengerjaan

1. **Helper functions:** Tambah `get_pelanggans()`, `get_items_with_stok()`, `validasi_stok_cukup()`, `update_stok_akhir_setelah_penjualan()`, update `generate_nomor_transaksi()`
2. **Penjualan routes:** Implementasi 4 route penjualan
3. **Penjualan templates:** Buat 3 template penjualan
4. **Update base.html:** Tambah navigasi untuk menu penjualan
5. **Update role admin:** Tambah permission untuk menu penjualan
6. **Test:** Jalankan aplikasi, test semua fitur

### 15.2 Hal yang Harus Diperhatikan

- **Jangan ubah kode existing** yang tidak terkait Fase 3
- **Pertahankan pola** `@has_permission`, CSRF, security headers
- **Gunakan `BEGIN IMMEDIATE`** untuk semua operasi atomic
- **Validasi stok di sisi server** untuk semua input
- **Flash message** untuk feedback ke user
- **Redirect setelah POST** (PRG pattern)
- **HPP snapshot** harus diambil dari `stok_akhir` sebelum update

### 15.3 Testing Checklist

- [ ] Buka `/penjualan` — harusnya muncul di navigasi
- [ ] Tambah penjualan dengan 2 item — harusnya berhasil
- [ ] Cek stok_akhir — stok harus berkurang
- [ ] Cek stok_mutasi — harus ada 2 baris OUT
- [ ] Cek penjualan_detail — harga_pokok harus terisi
- [ ] Hapus penjualan — stok harus bertambah kembali
- [ ] Cek nomor transaksi — harusnya `PJ-2026-0001`, `PJ-2026-0002`, dst
- [ ] Test validasi: qty = 0, harga = -100, stok tidak cukup
- [ ] Test dengan user non-admin (jika ada)

---

**End of Design Document Fase 3**
