// Confirmation prompt for destructive forms (delete item/pelanggan/supplier/...).
//
// Loaded as an EXTERNAL file on purpose: the app sends
//   Content-Security-Policy: script-src 'self'
// which BLOCKS inline onsubmit="return confirm(...)" attributes. Forms declare
// their message with a data-confirm attribute instead, and the handler is bound
// here with addEventListener.

(function () {
    'use strict';

    function bind(root) {
        (root || document).querySelectorAll('form[data-confirm]').forEach(function (form) {
            if (form.dataset.confirmBound === '1') {
                return;
            }
            form.dataset.confirmBound = '1';
            form.addEventListener('submit', function (event) {
                if (!window.confirm(form.dataset.confirm)) {
                    event.preventDefault();
                }
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function () {
            bind(document);
        });
    } else {
        bind(document);
    }
})();
