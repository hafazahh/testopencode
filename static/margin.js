// Margin preview for the item create/edit forms.
//
// Loaded as an EXTERNAL file on purpose: the app sends
//   Content-Security-Policy: script-src 'self'
// which allows same-origin .js files but BLOCKS every inline <script> and every
// onclick=/onchange=/oninput= attribute. Keeping the logic here means the CSP
// stays strict (grade A+) and the preview still works.

(function () {
    'use strict';

    var hargaPokokInput = document.getElementById('harga_pokok');
    var hargaJualInput = document.getElementById('harga_jual');
    var marginPreview = document.getElementById('marginPreview');

    if (!hargaPokokInput || !hargaJualInput || !marginPreview) {
        return;
    }

    function updateMargin() {
        var pokok = parseFloat(hargaPokokInput.value) || 0;
        var jual = parseFloat(hargaJualInput.value) || 0;
        var margin = jual - pokok;

        marginPreview.textContent = 'Rp ' + margin.toLocaleString('id-ID');

        if (margin > 0) {
            marginPreview.className = 'margin-preview margin-positive';
        } else if (margin < 0) {
            marginPreview.className = 'margin-preview margin-negative';
        } else {
            marginPreview.className = 'margin-preview';
        }
    }

    hargaPokokInput.addEventListener('input', updateMargin);
    hargaJualInput.addEventListener('input', updateMargin);
})();
