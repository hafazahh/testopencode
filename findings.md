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
