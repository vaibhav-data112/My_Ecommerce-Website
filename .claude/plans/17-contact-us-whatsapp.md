# Plan 17 — Contact Us Page + WhatsApp

**Spec:** `.claude/specs/17-contact-us-whatsapp.md`
**Branch:** `feature/contact-us`
**Builds on:** Feature 16 (return ineligible message already has `/contact` link placeholder)
**Effort:** Medium (~2-3 hours)
**Risk:** LOW — no money-touching, no OAuth, public form

---

## Phase 0 — Verified State

| Check | Status |
|---|---|
| No `ContactPage.jsx` exists | ✅ confirmed (Glob returned empty) |
| No `contact.py` blueprint | ✅ confirmed |
| No `contact.js` API module | ✅ confirmed |
| Footer "Contact Us" = `mailto:` link | ✅ line 75 in Footer.jsx — needs to change to `<Link to="/contact">` |
| AdminDashboard sidebar missing Returns + Contacts | ✅ lines 22-25 — only 4 links, no Returns/Contacts |
| Feature 16 `/contact` link already in OrderDetailPage | ✅ already points to `/contact` |
| `app.py` blueprint registration pattern confirmed | ✅ each blueprint is a separate file, imported + registered |

---

## Implementation Order

1. `db.py` — `contact_messages` table in `migrate_db()`
2. `contact.py` — NEW file: public submit + admin list + resolve
3. `app.py` — import + register contact blueprint
4. `frontend/src/config.js` — NEW: WhatsApp number constant
5. `frontend/src/api/contact.js` — NEW: 3 API functions
6. `frontend/src/index.css` — WhatsApp button + contact page styles
7. `frontend/src/pages/ContactPage.jsx` — NEW: form + WhatsApp button
8. `frontend/src/pages/admin/AdminContacts.jsx` — NEW: admin messages view
9. `frontend/src/App.jsx` — add `/contact` + `/admin/contacts` routes
10. `frontend/src/components/Footer.jsx` — update Contact Us link
11. Admin sidebar updates — add Returns + Contacts to all 4 admin pages

---

## Step 1 — `db.py`

### Add to `migrate_db()` after the Feature 16 block (before the final `conn.commit()`):

```python
# Feature 17: contact messages table
conn.execute("""
    CREATE TABLE IF NOT EXISTS contact_messages (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id      INTEGER,
        name         TEXT    NOT NULL,
        email        TEXT    NOT NULL,
        order_number TEXT,
        category     TEXT    NOT NULL,
        message      TEXT    NOT NULL,
        status       TEXT    NOT NULL DEFAULT 'new',
        created_at   TEXT    DEFAULT (datetime('now'))
    )
""")
```

No FOREIGN KEY on user_id — guest submissions have NULL user_id, and enforcement would block those.

---

## Step 2 — `contact.py` (NEW FILE)

```python
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_login import current_user

from db import get_db

contact = Blueprint('contact', __name__, url_prefix='/api')

ALLOWED_CATEGORIES = ['Return issue', 'Product issue', 'Order issue', 'Other']


def _admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required', 'login_required': True}), 401
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated


# ---------------------------------------------------------------------------
# Public — submit contact message
# ---------------------------------------------------------------------------

@contact.route('/contact', methods=['POST'])
def submit_contact():
    data = request.get_json(silent=True) or {}

    # Honeypot: bot filled hidden field → silently discard
    if (data.get('website') or '').strip():
        return jsonify({'success': True,
                        'message': 'Your message has been sent!'}), 200

    name         = (data.get('name')         or '').strip()[:100]
    email        = (data.get('email')        or '').strip()[:200]
    order_number = (data.get('order_number') or '').strip()[:50] or None
    category     = (data.get('category')     or '').strip()
    message      = (data.get('message')      or '').strip()[:2000]

    errors = []
    if not name:
        errors.append('Name is required.')
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        errors.append('Please enter a valid email address.')
    if category not in ALLOWED_CATEGORIES:
        errors.append('Please select a valid category.')
    if not message:
        errors.append('Message is required.')
    if errors:
        return jsonify({'error': ' '.join(errors)}), 400

    user_id = int(current_user.id) if current_user.is_authenticated else None

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO contact_messages
              (user_id, name, email, order_number, category, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, order_number, category, message))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True,
                    'message': 'Message sent! We will get back to you within 24 hours.'})


# ---------------------------------------------------------------------------
# Admin — list messages
# ---------------------------------------------------------------------------

@contact.route('/admin/contacts')
@_admin_required
def get_contacts():
    status_filter = (request.args.get('status') or '').strip()
    conn = get_db()
    try:
        if status_filter in ('new', 'resolved'):
            rows = conn.execute(
                "SELECT * FROM contact_messages WHERE status=? ORDER BY created_at DESC",
                (status_filter,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contact_messages ORDER BY created_at DESC"
            ).fetchall()
    finally:
        conn.close()
    return jsonify({'messages': [dict(r) for r in rows]})


# ---------------------------------------------------------------------------
# Admin — mark resolved
# ---------------------------------------------------------------------------

@contact.route('/admin/contacts/<int:msg_id>/resolve', methods=['PATCH'])
@_admin_required
def resolve_contact(msg_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM contact_messages WHERE id=?", (msg_id,)
        ).fetchone()
        if not row:
            return jsonify({'error': 'Message not found.'}), 404
        conn.execute(
            "UPDATE contact_messages SET status='resolved' WHERE id=?", (msg_id,)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True, 'message': f'Message #{msg_id} marked resolved.'})
```

---

## Step 3 — `app.py`

### Add import:
```python
from contact import contact as contact_blueprint
```

### Add registration (after `wishlist`):
```python
app.register_blueprint(contact_blueprint)
```

---

## Step 4 — `frontend/src/config.js` (NEW FILE)

```js
// WhatsApp owner number: country code + number, no +, no spaces (e.g. 919876543210)
export const WHATSAPP_NUMBER = '919876543210'

const prefill = [
  'Namaste Karvii Spices',
  '',
  'Mujhe apne order mein problem hai.',
  'Order no: ____',
  'Problem: ____ (photo neeche bhej raha/rahi hun)',
].join('\n')

export const WHATSAPP_URL = `https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent(prefill)}`
```

> **Note for user:** `WHATSAPP_NUMBER` mein apna asli number dalo (country code ke saath, `+` ke bina).

---

## Step 5 — `frontend/src/api/contact.js` (NEW FILE)

```js
import client from './client'

export const submitContact  = (data)   => client.post('/contact', data)
export const getContacts    = (status) => client.get('/admin/contacts',
                                           { params: status ? { status } : {} })
export const resolveContact = (id)     => client.patch(`/admin/contacts/${id}/resolve`)
```

---

## Step 6 — `frontend/src/index.css`

Add before `/* ORDER TIMELINE */` section:

```css
/* ===========================
   CONTACT PAGE
   =========================== */
.contact-layout {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 40px;
  align-items: start;
}
.whatsapp-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #25D366;
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  padding: 14px 24px;
  font-size: var(--fs-base);
  font-weight: 600;
  font-family: var(--font-body);
  cursor: pointer;
  transition: background 0.18s;
  text-decoration: none;
}
.whatsapp-btn:hover { background: #1ebe57; color: #fff; }
.whatsapp-icon { font-size: 20px; }

.contact-sidebar-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: 28px;
}
.contact-sidebar-card h3 {
  font-family: var(--font-head);
  color: var(--color-primary-dark);
  margin-bottom: 12px;
  font-size: 18px;
}

/* Admin contacts table */
.contact-msg-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  margin-bottom: 14px;
}
.contact-msg-card.resolved { opacity: 0.65; }
.contact-msg-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
  margin-bottom: 10px;
  font-size: var(--fs-xs);
  color: var(--color-text-soft);
}
.contact-msg-body {
  font-size: var(--fs-sm);
  color: var(--color-text);
  line-height: 1.7;
  margin-bottom: 12px;
  white-space: pre-wrap;
}
.badge-new      { background: #dbeafe; color: #1d4ed8; }
.badge-resolved { background: #D1FAE5; color: #1a5c34; }

@media (max-width: 768px) {
  .contact-layout { grid-template-columns: 1fr; }
}
```

---

## Step 7 — `frontend/src/pages/ContactPage.jsx` (NEW FILE)

```jsx
import { useEffect, useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { submitContact } from '../api/contact'
import { WHATSAPP_URL } from '../config'

const CATEGORIES = ['Return issue', 'Product issue', 'Order issue', 'Other']

export default function ContactPage() {
  const { user } = useAuth()
  const [form, setForm]     = useState({
    name: '', email: '', order_number: '', category: '', message: '', website: '',
  })
  const [busy,  setBusy]   = useState(false)
  const [msg,   setMsg]    = useState(null)

  // Pre-fill name + email for logged-in users
  useEffect(() => {
    if (user) {
      setForm(prev => ({ ...prev, name: user.name || '', email: user.email || '' }))
    }
  }, [user])

  const set = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setMsg(null)
    try {
      const r = await submitContact(form)
      setMsg({ type: 'success', text: r.data.message })
      setForm({ name: '', email: '', order_number: '', category: '', message: '', website: '' })
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.error || 'Something went wrong. Please try again.' })
    } finally { setBusy(false) }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 960, paddingTop: 40, paddingBottom: 60 }}>
        <h1 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 8 }}>
          Contact Us
        </h1>
        <p style={{ color: 'var(--color-text-soft)', marginBottom: 36, fontSize: 'var(--fs-sm)' }}>
          Koi problem hai? Hamein batayein — hum 24 ghante mein jawab denge.
        </p>

        <div className="contact-layout">

          {/* Left — Form */}
          <div>
            <div className="card" style={{ padding: 32 }}>
              {msg && (
                <div className={`alert alert-${msg.type}`} style={{ marginBottom: 20 }}>
                  {msg.text}
                </div>
              )}
              <form onSubmit={handleSubmit}>
                {/* Honeypot — hidden from real users, bots fill it */}
                <input
                  name="website"
                  value={form.website}
                  onChange={e => set('website', e.target.value)}
                  style={{ display: 'none' }}
                  tabIndex={-1}
                  autoComplete="off"
                  aria-hidden="true"
                />

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                  <div>
                    <label className="form-label">Name *</label>
                    <input className="form-input" placeholder="Your name"
                      value={form.name} onChange={e => set('name', e.target.value)} required />
                  </div>
                  <div>
                    <label className="form-label">Email *</label>
                    <input className="form-input" type="email" placeholder="you@example.com"
                      value={form.email} onChange={e => set('email', e.target.value)} required />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                  <div>
                    <label className="form-label">Order Number (optional)</label>
                    <input className="form-input" placeholder="e.g. #42"
                      value={form.order_number} onChange={e => set('order_number', e.target.value)} />
                  </div>
                  <div>
                    <label className="form-label">Category *</label>
                    <select className="form-select" value={form.category}
                      onChange={e => set('category', e.target.value)} required>
                      <option value="">Select a category</option>
                      {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>

                <div style={{ marginBottom: 24 }}>
                  <label className="form-label">Message *</label>
                  <textarea className="form-input" rows={5}
                    placeholder="Please describe your issue in detail..."
                    value={form.message} onChange={e => set('message', e.target.value)} required />
                </div>

                <button className="btn btn-primary" type="submit" disabled={busy}
                  style={{ width: '100%', padding: '14px' }}>
                  {busy ? 'Sending...' : 'Send Message'}
                </button>
              </form>
            </div>
          </div>

          {/* Right — WhatsApp + Info */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <div className="contact-sidebar-card">
              <h3>💬 WhatsApp pe baat karein</h3>
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-soft)', lineHeight: 1.7, marginBottom: 20 }}>
                Photo ke saath problem dikhana chahte hain? WhatsApp pe seedha message karein — hum jaldi reply karenge.
              </p>
              <a className="whatsapp-btn" href={WHATSAPP_URL} target="_blank" rel="noopener noreferrer">
                <span className="whatsapp-icon">💬</span>
                WhatsApp pe bhejo
              </a>
            </div>

            <div className="contact-sidebar-card">
              <h3 style={{ fontSize: 15 }}>Response time</h3>
              <ul style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-soft)', lineHeight: 2, paddingLeft: 16 }}>
                <li>Form: 24 ghante ke andar</li>
                <li>WhatsApp: typically same day</li>
                <li>Mon–Sat: 9 AM – 7 PM IST</li>
              </ul>
            </div>

            <div className="contact-sidebar-card">
              <h3 style={{ fontSize: 15 }}>Return chahiye?</h3>
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-soft)', lineHeight: 1.7 }}>
                Agar aapka order deliver hua hai aur 7 din se kam hue hain, to seedha{' '}
                <a href="/orders" style={{ color: 'var(--color-primary)' }}>My Orders</a>{' '}
                se return request karo.
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
```

---

## Step 8 — `frontend/src/pages/admin/AdminContacts.jsx` (NEW FILE)

```jsx
import { useEffect, useState } from 'react'
import { Link }               from 'react-router-dom'
import { getContacts, resolveContact } from '../../api/contact'
import Spinner from '../../components/Spinner'

const FILTERS = [
  { label: 'All',      value: '' },
  { label: 'New',      value: 'new' },
  { label: 'Resolved', value: 'resolved' },
]

export default function AdminContacts() {
  const [messages, setMessages] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [filter,   setFilter]   = useState('')
  const [msg,      setMsg]      = useState(null)

  const flash = (type, text) => {
    setMsg({ type, text }); setTimeout(() => setMsg(null), 3500)
  }

  const load = (f) => {
    setLoading(true)
    getContacts(f).then(r => setMessages(r.data.messages)).finally(() => setLoading(false))
  }
  useEffect(() => { load(filter) }, [filter])

  const handleResolve = async (id) => {
    try {
      await resolveContact(id)
      flash('success', `Message #${id} marked resolved.`)
      load(filter)
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to resolve.')
    }
  }

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div style={{ padding: '0 20px 20px', fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, fontWeight: 700 }}>
          🌶 Admin
        </div>
        <Link to="/admin"           className="admin-nav-link">Dashboard</Link>
        <Link to="/admin/products"  className="admin-nav-link">Products</Link>
        <Link to="/admin/orders"    className="admin-nav-link">Orders</Link>
        <Link to="/admin/returns"   className="admin-nav-link">Returns</Link>
        <Link to="/admin/contacts"  className="admin-nav-link active">Contact Messages</Link>
        <Link to="/"                className="admin-nav-link">← Back to Store</Link>
      </aside>

      <div className="admin-content">
        <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>
          Contact Messages
          <span style={{ fontSize: 15, color: 'var(--color-text-soft)', fontFamily: 'var(--font-body)', fontWeight: 400, marginLeft: 10 }}>
            ({messages.filter(m => m.status === 'new').length} new)
          </span>
        </h2>

        {msg && <div className={`alert alert-${msg.type}`} style={{ marginBottom: 16 }}>{msg.text}</div>}

        {/* Filter tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          {FILTERS.map(f => (
            <button key={f.value}
              className={`btn btn-sm ${filter === f.value ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setFilter(f.value)}>
              {f.label}
            </button>
          ))}
        </div>

        {loading ? <Spinner /> : (
          <>
            {messages.map(m => (
              <div key={m.id} className={`contact-msg-card${m.status === 'resolved' ? ' resolved' : ''}`}>
                <div className="contact-msg-meta">
                  <strong style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text)' }}>#{m.id} — {m.name}</strong>
                  <span>{m.email}</span>
                  {m.order_number && <span>Order: #{m.order_number}</span>}
                  <span className={`status-badge badge-${m.status}`}>{m.category}</span>
                  <span className={`status-badge badge-${m.status}`}>{m.status}</span>
                  <span>{new Date(m.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}</span>
                </div>
                <div className="contact-msg-body">{m.message}</div>
                {m.status === 'new' && (
                  <button className="btn btn-outline btn-sm" onClick={() => handleResolve(m.id)}>
                    ✓ Mark Resolved
                  </button>
                )}
              </div>
            ))}
            {messages.length === 0 && (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <div className="empty-title">No messages</div>
                <p className="empty-text">No contact messages {filter ? `with status "${filter}"` : ''}.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
```

---

## Step 9 — `frontend/src/App.jsx`

### Add imports:
```jsx
import ContactPage     from './pages/ContactPage'
import AdminContacts   from './pages/admin/AdminContacts'
```

### Add routes (after existing routes):
```jsx
<Route path="/contact" element={<ContactPage />} />
<Route path="/admin/contacts" element={<AdminGuard><AdminContacts /></AdminGuard>} />
```

---

## Step 10 — `frontend/src/components/Footer.jsx`

### Add Link import (already has `Link` from react-router-dom — ✅)

### Change Contact Us:
```jsx
// Before (line 75):
<li><a href="mailto:hello@karvii.in">Contact Us</a></li>

// After:
<li><Link to="/contact">Contact Us</Link></li>
```

---

## Step 11 — Admin sidebar updates (4 pages)

All 4 admin page sidebars need Returns + Contacts links. Current state:

| Page | Has Returns link | Has Contacts link |
|---|---|---|
| AdminDashboard | ❌ | ❌ |
| AdminProducts | (need to check) | ❌ |
| AdminOrders | ✅ (Feature 16) | ❌ |
| AdminReturns | ✅ self | ❌ |

Add to **AdminDashboard** and **AdminProducts** sidebars:
```jsx
<Link to="/admin/returns"  className="admin-nav-link">Returns</Link>
<Link to="/admin/contacts" className="admin-nav-link">Contact Messages</Link>
```

Add to **AdminOrders** and **AdminReturns** sidebars:
```jsx
<Link to="/admin/contacts" className="admin-nav-link">Contact Messages</Link>
```

---

## File Change Summary

| File | Type | Key change |
|---|---|---|
| `db.py` | Edit | `contact_messages` table in `migrate_db()` |
| `contact.py` | NEW | Public submit + admin list + resolve endpoints |
| `app.py` | Edit | Import + register contact blueprint |
| `frontend/src/config.js` | NEW | `WHATSAPP_NUMBER` + `WHATSAPP_URL` constant |
| `frontend/src/api/contact.js` | NEW | `submitContact`, `getContacts`, `resolveContact` |
| `frontend/src/index.css` | Edit | Contact layout, WhatsApp button, message card styles |
| `frontend/src/pages/ContactPage.jsx` | NEW | Form + WhatsApp button page |
| `frontend/src/pages/admin/AdminContacts.jsx` | NEW | Admin messages list + resolve |
| `frontend/src/App.jsx` | Edit | `/contact` route + `/admin/contacts` route |
| `frontend/src/components/Footer.jsx` | Edit | `mailto:` → `<Link to="/contact">` |
| `frontend/src/pages/admin/AdminDashboard.jsx` | Edit | Add Returns + Contacts to sidebar |
| `frontend/src/pages/admin/AdminProducts.jsx` | Edit | Add Returns + Contacts to sidebar |
| `frontend/src/pages/admin/AdminOrders.jsx` | Edit | Add Contacts to sidebar |
| `frontend/src/pages/admin/AdminReturns.jsx` | Edit | Add Contacts to sidebar |

Total: 5 new files, 9 edits.

---

## Security Checklist

- [ ] Honeypot field silently discards bot submissions (no error returned)
- [ ] All user input trimmed + length-capped server-side (name ≤100, message ≤2000)
- [ ] `category` validated against allowed list (no arbitrary strings saved)
- [ ] Email basic format check (`@` + `.` in domain)
- [ ] Admin endpoints behind `_admin_required` decorator
- [ ] `user_id` set from `current_user.id` server-side — never from client body
- [ ] React auto-escapes output in AdminContacts (no `dangerouslySetInnerHTML`)
- [ ] WhatsApp URL uses `encodeURIComponent` for prefill text

---

## Test Plan (`test_contact_us.py` — after implementation)

1. Valid submit (guest) → 200, saved with `user_id=NULL`
2. Valid submit (logged-in) → 200, `user_id` set
3. Missing name → 400
4. Missing email / bad email → 400
5. Missing message → 400
6. Invalid category → 400
7. Honeypot filled → 200 (silently discarded, nothing saved)
8. Admin GET /admin/contacts → returns messages
9. Admin filter `?status=new` → only new messages
10. Admin resolve → status = `resolved`
11. Unauthenticated admin endpoints → 401
12. Non-admin → 403
