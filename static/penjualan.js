// Multi-row form for PENJUALAN (stock out).
//
// Loaded as an EXTERNAL file on purpose: the app sends
//   Content-Security-Policy: script-src 'self'
// which allows same-origin .js files but BLOCKS every inline <script> and every
// onclick=/onchange=/oninput= attribute -- including attributes written from JS
// onto dynamically created rows. Every handler below therefore uses
// addEventListener, and server data arrives through a non-executable
// <script type="application/json" id="items-data"> block.

(function () {
    'use strict';

    var dataEl = document.getElementById('items-data');
    var tbody = document.getElementById('detail-rows');
    var addBtn = document.getElementById('add-row-btn');

    if (!dataEl || !tbody || !addBtn) {
        return;
    }

    var items = JSON.parse(dataEl.textContent);
    var byId = {};
    items.forEach(function (item) {
        byId[String(item.id)] = item;
    });

    function escapeHtml(value) {
        return String(value)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    var itemOptionsHtml = items.map(function (item) {
        return '<option value="' + item.id + '">' + escapeHtml(item.nama) + '</option>';
    }).join('');

    function formatRupiah(value) {
        return 'Rp ' + value.toLocaleString('id-ID');
    }

    function updateTotal() {
        var total = 0;
        tbody.querySelectorAll('tr').forEach(function (row) {
            var qty = parseFloat(row.querySelector('input[name="qty[]"]').value) || 0;
            var harga = parseFloat(row.querySelector('input[name="harga_jual[]"]').value) || 0;
            total += qty * harga;
        });
        document.getElementById('total-display').textContent = formatRupiah(total);
    }

    function updateSubtotal(row) {
        var qty = parseFloat(row.querySelector('input[name="qty[]"]').value) || 0;
        var harga = parseFloat(row.querySelector('input[name="harga_jual[]"]').value) || 0;
        row.querySelector('.subtotal-display').textContent = formatRupiah(qty * harga);
        updateTotal();
    }

    function updateStokInfo(select) {
        var row = select.closest('tr');
        var stokDisplay = row.querySelector('.stok-display');
        var hargaInput = row.querySelector('input[name="harga_jual[]"]');
        var item = byId[String(select.value)];

        if (item) {
            stokDisplay.textContent = item.stok_akhir;
            // Suggest harga jual = harga_pokok * 1.2 (20% margin) when empty.
            if (!hargaInput.value) {
                hargaInput.value = Math.round(item.harga_pokok * 1.2);
            }
        } else {
            stokDisplay.textContent = '-';
        }
        updateSubtotal(row);
    }

    function removeRow(button) {
        button.closest('tr').remove();
        updateTotal();
    }

    function addDetailRow(itemId, qty, harga) {
        var row = document.createElement('tr');
        row.innerHTML =
            '<td>' +
                '<select name="item_id[]" required>' +
                    '<option value="">-- Pilih Item --</option>' + itemOptionsHtml +
                '</select>' +
            '</td>' +
            '<td><span class="stok-display">-</span></td>' +
            '<td>' +
                '<input type="number" name="qty[]" min="0.01" step="0.01" required placeholder="0">' +
            '</td>' +
            '<td>' +
                '<input type="number" name="harga_jual[]" min="0" step="0.01" required placeholder="0">' +
            '</td>' +
            '<td><span class="subtotal-display">Rp 0</span></td>' +
            '<td><button type="button" class="btn btn-sm btn-delete">Hapus</button></td>';

        tbody.appendChild(row);

        var select = row.querySelector('select[name="item_id[]"]');
        var qtyInput = row.querySelector('input[name="qty[]"]');
        var hargaInput = row.querySelector('input[name="harga_jual[]"]');

        // Listeners, not inline attributes -- CSP forbids on* here.
        select.addEventListener('change', function () {
            updateStokInfo(select);
        });
        qtyInput.addEventListener('input', function () {
            updateSubtotal(row);
        });
        hargaInput.addEventListener('input', function () {
            updateSubtotal(row);
        });
        row.querySelector('.btn-delete').addEventListener('click', function (event) {
            removeRow(event.currentTarget);
        });

        if (itemId) {
            select.value = itemId;
            updateStokInfo(select);
        }
        if (qty) {
            qtyInput.value = qty;
        }
        if (harga) {
            hargaInput.value = harga;
        }
        if (itemId || qty || harga) {
            updateSubtotal(row);
        }
    }

    addBtn.addEventListener('click', function () {
        addDetailRow();
    });

    // Add the first row exactly once, whether this script runs during parsing
    // (classic <script> at end of body) or after the DOM is already ready.
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            addDetailRow();
        });
    } else {
        addDetailRow();
    }
})();
