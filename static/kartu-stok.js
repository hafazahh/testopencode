// Kartu stok: submit form saat item diganti.
// Loaded as an external file because CSP script-src 'self' blocks inline
// handlers (onchange=) silently, with no server-side error.
document.addEventListener('DOMContentLoaded', function () {
    var sel = document.getElementById('item_id');
    if (!sel) return;
    sel.addEventListener('change', function () {
        sel.form.submit();
    });
});
