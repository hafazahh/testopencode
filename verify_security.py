"""Security hardening verification — headers, cookie flags, rate limiting, CSRF.

Run:  /home/choirulhaq/venvProject/bin/python3 verify_security.py
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import app as appmod

app = appmod.app
app.config['TESTING'] = True

fails = []


def check(label, condition, detail=''):
    mark = 'PASS' if condition else 'FAIL'
    if not condition:
        fails.append(label)
    print(f"  [{mark}] {label}" + (f"  — {detail}" if detail else ''))


print('=' * 68)
print('1. SECURITY HEADERS')
print('=' * 68)
with app.test_client() as c:
    r = c.get('/login')
    h = r.headers
    check('Content-Security-Policy present', 'Content-Security-Policy' in h)
    csp = h.get('Content-Security-Policy', '')
    check("CSP has frame-ancestors 'none'", "frame-ancestors 'none'" in csp)
    check("CSP has object-src 'none'", "object-src 'none'" in csp)
    check("CSP has base-uri 'self'", "base-uri 'self'" in csp)
    check("CSP script-src has NO unsafe-inline", "'unsafe-inline'" not in csp.split('style-src')[0],
          'checked script-src portion')
    check('X-Content-Type-Options: nosniff', h.get('X-Content-Type-Options') == 'nosniff')
    check('X-Frame-Options: DENY', h.get('X-Frame-Options') == 'DENY')
    check('Referrer-Policy set', bool(h.get('Referrer-Policy')))
    check('Permissions-Policy set', bool(h.get('Permissions-Policy')))
    check('Cross-Origin-Opener-Policy set', bool(h.get('Cross-Origin-Opener-Policy')))
    check('Cross-Origin-Resource-Policy set', bool(h.get('Cross-Origin-Resource-Policy')))

print()
print('=' * 68)
print('2. SESSION COOKIE FLAGS')
print('=' * 68)
with app.test_client() as c:
    r = c.get('/login')
    raw = '; '.join(r.headers.getlist('Set-Cookie')) if hasattr(r.headers, 'getlist') else r.headers.get('Set-Cookie', '')
    check('cookie present', 'session=' in raw, raw[:70])
    check('HttpOnly set', 'HttpOnly' in raw)
    check('SameSite set', 'SameSite' in raw)
    # Secure is set in config; Flask only emits it when the request is secure
    check('config SESSION_COOKIE_SECURE=True', app.config.get('SESSION_COOKIE_SECURE') is True)
    check('config SESSION_COOKIE_HTTPONLY=True', app.config.get('SESSION_COOKIE_HTTPONLY') is True)
    check('config SESSION_COOKIE_SAMESITE=Lax', app.config.get('SESSION_COOKIE_SAMESITE') == 'Lax')
    check('permanent lifetime set', app.config.get('PERMANENT_SESSION_LIFETIME') is not None)

print()
print('=' * 68)
print('3. SECURE COOKIE + HSTS OVER SIMULATED HTTPS')
print('=' * 68)
with app.test_client() as c:
    r = c.get('/login', base_url='https://crud.choirulhaq.com')
    raw = r.headers.get('Set-Cookie', '')
    check('Secure attribute emitted over HTTPS', 'Secure' in raw, raw[:80])
    hsts = r.headers.get('Strict-Transport-Security')
    check('HSTS present over HTTPS', bool(hsts), str(hsts))
    check('HSTS has max-age >= 1 year', 'max-age=31536000' in (hsts or ''), str(hsts))
    check('HSTS has includeSubDomains', 'includeSubDomains' in (hsts or ''))

print()
print('=' * 68)
print('3b. HSTS ABSENT OVER PLAIN HTTP (must not pin non-TLS hosts)')
print('=' * 68)
with app.test_client() as c:
    r = c.get('/login', base_url='http://crud.choirulhaq.com')
    check('HSTS NOT sent over http://', r.headers.get('Strict-Transport-Security') is None,
          str(r.headers.get('Strict-Transport-Security')))

print()
print('=' * 68)
print('4. LOGIN RATE LIMITING')
print('=' * 68)
appmod._login_attempts.clear()
with app.test_client() as c:
    # get a CSRF token first
    page = c.get('/login').get_data(as_text=True)
    m = re.search(r'name="csrf_token" value="([^"]+)"', page)
    token = m.group(1) if m else None
    check('CSRF token rendered on login page', token is not None)

    statuses = []
    for i in range(7):
        rr = c.post('/login', data={
            'username': 'admin', 'password': f'wrong{i}', 'csrf_token': token or ''
        }, follow_redirects=False)
        statuses.append(rr.status_code)
    body = rr.get_data(as_text=True)
    check('wrong password does NOT log in (no 302 to index)', 302 not in statuses[:4],
          f'statuses={statuses}')
    check('lockout message appears after threshold', 'Terlalu banyak percobaan gagal' in body
          or 'terkunci' in body)
    check('lockout key registered in store', bool(appmod._login_attempts))

    # a correct password while locked must ALSO be refused
    locked_before = appmod.login_locked_for('admin')
    check('login_locked_for() reports active lockout', locked_before > 0, f'{locked_before}s')

print()
print('=' * 68)
print('5. CSRF ENFORCEMENT')
print('=' * 68)
appmod._login_attempts.clear()
with app.test_client() as c:
    r = c.post('/login', data={'username': 'admin', 'password': 'admin123'})
    check('POST without CSRF token -> 403', r.status_code == 403, f'got {r.status_code}')
    r = c.post('/login', data={'username': 'admin', 'password': 'admin123', 'csrf_token': 'bogus'})
    check('POST with wrong CSRF token -> 403', r.status_code == 403, f'got {r.status_code}')

print()
print('=' * 68)
print('5b. 403 RESPONDS WITH REAL STATUS (not a redirect)')
print('=' * 68)
with app.test_client() as c:
    r = c.post('/login', data={'username': 'admin', 'password': 'admin123'})
    check('403 is not masked as 302', r.status_code != 302, f'got {r.status_code}')
    check('403 body is HTML, not a Location redirect', b'<!DOCTYPE' in r.data or b'<html' in r.data)
    check('403 renders the error template', b'Akses Ditolak' in r.data)

print()
print('=' * 68)
print('6. AUTHORIZATION (unauthenticated access blocked)')
print('=' * 68)
with app.test_client() as c:
    for path in ['/', '/users', '/roles', '/kategori', '/pelanggan']:
        r = c.get(path, follow_redirects=False)
        check(f'{path} redirects anonymous -> login', r.status_code == 302, f'got {r.status_code}')

print()
print('=' * 68)
print(f"RESULT: {'ALL CHECKS PASSED' if not fails else f'{len(fails)} FAILED: ' + ', '.join(fails)}")
print('=' * 68)
sys.exit(0 if not fails else 1)
