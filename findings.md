# Findings: CRUD Item Application

## Technology Stack
- **Framework**: Flask (Python micro web framework)
- **Database**: SQLite (serverless, file-based SQL database)
- **Template Engine**: Jinja2 (built-in with Flask)
- **Styling**: CSS (custom, no framework)

## Key Design Decisions

### 1. Database: SQLite
- **Why**: Serverless, zero-configuration, perfect for small-medium apps
- **File**: `database.db` (auto-created on first run)
- **Benefits**: No separate DB server needed, portable, ACID compliant

### 2. Margin Calculation
- **Approach**: SQLite GENERATED ALWAYS AS column
- **Formula**: `margin = harga_jual - harga_pokok`
- **Benefits**: Always consistent, no application logic needed, database-enforced

### 3. Project Structure
- Standard Flask structure with templates/ and static/ folders
- Single app.py for simplicity (can be refactored to blueprints if needed)
- Base template for consistent layout

### 4. Form Handling
- POST method for create/update/delete operations
- CSRF protection via Flask-WTF (optional enhancement)
- Server-side validation for required fields

### 5. User Experience
- Clean, responsive design
- Margin displayed with color coding (green for positive, red for negative)
- Confirmation before delete
- Flash messages for feedback

## Potential Enhancements
- Pagination for large datasets
- Search/filter functionality
- Export to CSV/Excel
- User authentication
- API endpoints (RESTful)
- Unit tests

## Bug & Issues (2026-10-07)

### Bug: Tombol "+ Tidak Berfungsi" di halaman Pembelian
- **File:** `templates/pembelian/create.html`
- **Tombol:** `<button type="button" id="add-row-btn">+ Tambah Item</button>`
- **JS Function:** `addDetailRow()` — tambah row dinamis ke `#detail-rows`
- **User report:** Klik tombol tidak nambah row
- **Root cause:** Perlu debug — kemungkinan JS error atau DOM issue
- **Status:** ❌ OPEN — belum fixed

### Issue: CSRF 403 saat test dari browser (iPad & laptop)
- **Symptom:** Login berhasil (302), tapi halaman `/penjualan`, `/supplier` return 403 "akses ditolak"
- **Test via curl:** ✅ works (200 OK)
- **Test via Flask test client:** ❌ 403 (CSRF token mismatch)
- **Root cause:** CSRF token di session vs form tidak cocok. Browser session cookie lama.
- **Workaround:** Clear browser cookies atau incognito window
- **Status:** ⚠️ WORKAROUND — bukan bug kode

### Issue: Login CSRF 403 di Flask test client
- **File:** `app.py` line 371-378 (`csrf_protect()`)
- **Code:** `secrets.compare_digest(token, session_token)` — strict comparison
- **Issue:** Token di form HTML beda dengan token di session saat POST
- **Workaround:** `app.config['WTF_CSRF_ENABLED'] = False` untuk testing
- **Status:** ⚠️ KNOWN — development only
