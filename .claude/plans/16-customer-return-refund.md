# Plan 16 — Customer Self-Return + Refund

**Spec:** `.claude/specs/16-customer-return-refund.md`
**Branch:** `feature/return-refund`
**Builds on:** Feature 15 (`append_status_history`, `status_history`, timeline)
**Effort:** Hard (~5-6 hours)
**Risk:** HIGH — money-touching (Razorpay refund). Test Mode only.

---

## Phase 0 — Prerequisites Check (VERIFIED from code)

| Spec needs | Column in DB | Verified |
|---|---|---|
| Razorpay payment ID | `orders.payment_id` (set in `payment.py:verify_payment`) | ✅ |
| Delivery charge | `orders.shipping_fee` (set in `db.py:place_order`) | ✅ |
| Paid amount | `orders.total` | ✅ |
| `append_status_history()` | `db.py` (Feature 15) | ✅ |

No prerequisite missing — proceed directly to implementation.

---

## Implementation Order

1. `db.py` — 5 new columns + `can_self_return()` helper
2. `orders.py` — customer return-request endpoint + order_detail update
3. `admin.py` — `return_requested` in ALLOWED_STATUSES + 3 new endpoints
4. `frontend/src/api/orders.js` — add `requestReturn()`
5. `frontend/src/api/admin.js` — add `getReturns()`, `approveReturn()`, `rejectReturn()`, `processRefund()`
6. `frontend/src/index.css` — return/refund styles
7. `frontend/src/pages/OrderDetailPage.jsx` — return section UI
8. `frontend/src/pages/admin/AdminReturns.jsx` — NEW page
9. `frontend/src/App.jsx` — add `/admin/returns` route + Navbar link

---

## Step 1 — `db.py`

### 1a. Module-level constant (add after DATABASE line)
```python
RETURN_WINDOW_DAYS = 7
```

### 1b. `migrate_db()` — add 5 columns after the tracking timeline block

```python
# Feature 16: customer return + refund columns
orders_cols = [r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
for col, ddl in [
    ('return_requested_at',   "ALTER TABLE orders ADD COLUMN return_requested_at TEXT"),
    ('return_reason',         "ALTER TABLE orders ADD COLUMN return_reason TEXT"),
    ('return_rejected_reason',"ALTER TABLE orders ADD COLUMN return_rejected_reason TEXT"),
    ('refund_amount',         "ALTER TABLE orders ADD COLUMN refund_amount REAL"),
    ('razorpay_refund_id',    "ALTER TABLE orders ADD COLUMN razorpay_refund_id TEXT"),
]:
    if col not in orders_cols:
        conn.execute(ddl)
```

### 1c. New helper `can_self_return()` — add after `update_courier_details`

```python
def can_self_return(user_id, order_id):
    """Return (eligible: bool, reason: str|None). All 4 spec rules enforced."""
    import json as _json
    from datetime import datetime, timezone

    conn = get_db()
    try:
        order = conn.execute(
            "SELECT * FROM orders WHERE id=?", (order_id,)
        ).fetchone()
        if not order or order['user_id'] != user_id:
            return False, "Order not found"

        # Rule 1: must be delivered
        if order['status'] != 'delivered':
            return False, "Order must be delivered to request a return"

        # Rule 2: within return window — use delivered timestamp from history
        delivered_at = None
        raw_hist = order['status_history']
        if raw_hist:
            hist  = _json.loads(raw_hist)
            entry = next((e for e in hist if e['status'] == 'delivered'), None)
            if entry and entry.get('at'):
                try:
                    delivered_at = datetime.fromisoformat(entry['at']).replace(tzinfo=timezone.utc)
                except ValueError:
                    pass
        if delivered_at is None:
            try:
                delivered_at = datetime.fromisoformat(
                    order['created_at']
                ).replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass
        if delivered_at:
            if (datetime.now(timezone.utc) - delivered_at).days >= RETURN_WINDOW_DAYS:
                return False, f"Return window of {RETURN_WINDOW_DAYS} days has passed"

        # Rule 3: per-user lifetime limit (1 self-return only)
        used = conn.execute("""
            SELECT COUNT(*) FROM orders
            WHERE user_id=? AND status IN ('returned', 'refunded')
        """, (user_id,)).fetchone()[0]
        if used > 0:
            return False, "Self-return limit reached (1 per customer lifetime)"

        return True, None
    finally:
        conn.close()
```

---

## Step 2 — `orders.py`

### 2a. Imports — add at top
```python
from flask import Blueprint, jsonify, request
```
(already has jsonify — add `request`)

### 2b. Update `order_detail` to include return fields + `can_self_return`

```python
@orders.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    import json as _json
    from db import can_self_return
    uid   = int(current_user.id)
    order = get_order_by_id(order_id)
    if not order or order['user_id'] != uid:
        return jsonify({'error': 'Order not found.'}), 404
    items      = get_order_items(order_id)
    order_dict = dict(order)
    raw_hist   = order_dict.get('status_history')
    order_dict['status_history']  = _json.loads(raw_hist) if raw_hist else []
    order_dict['can_self_return'] = can_self_return(uid, order_id)[0]
    return jsonify({'order': order_dict, 'items': [dict(i) for i in items]})
```

### 2c. New endpoint — customer return request

Add after `order_detail`:
```python
@orders.route('/orders/<int:order_id>/return-request', methods=['POST'])
@login_required
def return_request(order_id):
    from db import can_self_return, append_status_history, get_db
    uid   = int(current_user.id)
    order = get_order_by_id(order_id)
    if not order or order['user_id'] != uid:
        return jsonify({'error': 'Order not found.'}), 404

    eligible, err = can_self_return(uid, order_id)
    if not eligible:
        return jsonify({'error': err}), 403

    data   = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip()[:500]
    if not reason:
        return jsonify({'error': 'Please provide a reason for the return.'}), 400

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET return_reason=?, return_requested_at=? WHERE id=?",
            (reason, now, order_id)
        )
        conn.commit()
    finally:
        conn.close()

    append_status_history(order_id, 'return_requested',
                          note=f"Customer return request: {reason}")
    return jsonify({'success': True,
                    'message': 'Return request submitted. Admin will review shortly.'})
```

---

## Step 3 — `admin.py`

### 3a. Add `return_requested` to `ALLOWED_STATUSES`

```python
ALLOWED_STATUSES = [
    'paid', 'packed', 'shipped', 'out_for_delivery', 'delivered',
    'cancelled', 'return_requested', 'returned', 'refunded',
]
```

### 3b. Add imports from db
```python
from db import (
    append_status_history, can_self_return, create_product, delete_product,
    get_all_orders_admin, get_all_products, get_db, get_order_by_id,
    get_product_by_id, update_courier_details, update_product,
)
```
(add `can_self_return`, `get_db`)

### 3c. New endpoint — GET /api/admin/returns

```python
@admin.route('/returns')
@admin_required
def returns():
    """Orders pending return action (return_requested or returned)."""
    import json as _json
    conn = get_db()
    try:
        rows = conn.execute("""
            SELECT o.*, u.name AS customer_name, u.email AS customer_email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.status IN ('return_requested', 'returned')
            ORDER BY o.return_requested_at DESC
        """).fetchall()
    finally:
        conn.close()
    result = []
    for row in rows:
        od  = dict(row)
        raw = od.get('status_history')
        od['status_history'] = _json.loads(raw) if raw else []
        result.append(od)
    return jsonify({'orders': result})
```

### 3d. New endpoint — approve return

```python
@admin.route('/orders/<int:order_id>/return-approve', methods=['POST'])
@admin_required
def return_approve(order_id):
    order = get_order_by_id(order_id)
    if not order:
        return jsonify({'error': 'Order not found.'}), 404
    if order['status'] != 'return_requested':
        return jsonify({'error': 'Order must be in return_requested status.'}), 400
    append_status_history(order_id, 'returned',
                          note='Return approved by admin. Please ship the item back.')
    return jsonify({'success': True,
                    'message': f'Order #{order_id} return approved.'})
```

### 3e. New endpoint — reject return

```python
@admin.route('/orders/<int:order_id>/return-reject', methods=['POST'])
@admin_required
def return_reject(order_id):
    order = get_order_by_id(order_id)
    if not order:
        return jsonify({'error': 'Order not found.'}), 404
    if order['status'] != 'return_requested':
        return jsonify({'error': 'Order must be in return_requested status.'}), 400
    data   = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip()[:500]
    if not reason:
        return jsonify({'error': 'Rejection reason is required.'}), 400
    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET return_rejected_reason=? WHERE id=?",
            (reason, order_id)
        )
        conn.commit()
    finally:
        conn.close()
    append_status_history(order_id, 'delivered',
                          note=f'Return rejected: {reason}')
    return jsonify({'success': True,
                    'message': f'Order #{order_id} return rejected.'})
```

### 3f. New endpoint — process refund (⚠️ money-touching)

```python
@admin.route('/orders/<int:order_id>/refund', methods=['POST'])
@admin_required
def process_refund(order_id):
    import razorpay as _rz
    order = get_order_by_id(order_id)
    if not order:
        return jsonify({'error': 'Order not found.'}), 404

    # Transition guard
    if order['status'] != 'returned':
        return jsonify({'error': 'Order must be in returned status to process refund.'}), 400

    # Double-refund protection
    if order['razorpay_refund_id'] or order['status'] == 'refunded':
        return jsonify({'error': 'Refund already processed for this order.'}), 400

    payment_id = order['payment_id']
    if not payment_id:
        return jsonify({'error': 'No Razorpay payment ID found — order may not have been paid online.'}), 400

    # Server-side refund computation (client amount ignored)
    total         = float(order['total']        or 0)
    shipping_fee  = float(order['shipping_fee'] or 0)
    refund_amount = max(0.0, round(total - shipping_fee, 2))
    refund_paise  = round(refund_amount * 100)

    if refund_paise <= 0:
        return jsonify({'error': 'Computed refund amount is ₹0 — nothing to refund.'}), 400

    # Razorpay refund call
    try:
        rz_client = _rz.Client(auth=(
            os.environ.get('RAZORPAY_KEY_ID', ''),
            os.environ.get('RAZORPAY_KEY_SECRET', ''),
        ))
        refund = rz_client.payment.refund(payment_id, {
            'amount': refund_paise,
            'speed':  'normal',
        })
        refund_id = refund.get('id', '')
    except Exception as e:
        return jsonify({'error': f'Razorpay refund failed: {str(e)}'}), 502

    # Persist refund details
    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET refund_amount=?, razorpay_refund_id=? WHERE id=?",
            (refund_amount, refund_id, order_id)
        )
        conn.commit()
    finally:
        conn.close()

    note = (f"Refunded ₹{refund_amount:.0f} "
            f"(₹{total:.0f} paid − ₹{shipping_fee:.0f} delivery). "
            f"Razorpay refund ID: {refund_id}")
    append_status_history(order_id, 'refunded', note=note)

    return jsonify({
        'success':       True,
        'refund_amount': refund_amount,
        'refund_id':     refund_id,
        'message':       note,
    })
```

---

## Step 4 — `frontend/src/api/orders.js`

Add one export:
```js
export const requestReturn = (id, reason) =>
  client.post(`/orders/${id}/return-request`, { reason })
```

---

## Step 5 — `frontend/src/api/admin.js`

Add four exports:
```js
export const getReturns    = ()             => client.get('/admin/returns')
export const approveReturn = (id)           => client.post(`/admin/orders/${id}/return-approve`)
export const rejectReturn  = (id, reason)   => client.post(`/admin/orders/${id}/return-reject`, { reason })
export const processRefund = (id)           => client.post(`/admin/orders/${id}/refund`)
```

---

## Step 6 — `frontend/src/index.css`

Add before the `/* UTILITIES */` section:

```css
/* ===========================
   RETURN / REFUND UI
   =========================== */
.return-section { margin-top: 20px; }

.return-banner {
  padding: 14px 18px; border-radius: var(--radius-md);
  font-size: var(--fs-sm); border-left: 4px solid;
}
.return-banner--requested { background: #fef9c3; color: #92400e; border-color: #B7860B; }
.return-banner--approved  { background: #e0f2fe; color: #0369a1; border-color: #0369a1; }
.return-banner--refunded  { background: #D1FAE5; color: #1a5c34; border-color: #2D6A4F; }
.return-banner--rejected  { background: #fef2f2; color: #991b1b; border-color: var(--color-danger); }
.return-banner--ineligible{ background: var(--color-surface-warm); color: var(--color-text-soft); border-color: var(--color-border); }

.return-reason-form { margin-top: 16px; display: flex; flex-direction: column; gap: 10px; }

/* Admin return cards */
.return-card {
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-md); padding: 20px; margin-bottom: 16px;
}
.return-card-header {
  display: flex; justify-content: space-between; align-items: flex-start;
  flex-wrap: wrap; gap: 8px; margin-bottom: 12px;
}
.return-card-actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.return-refund-amount {
  font-size: var(--fs-lg); font-weight: 700; color: #2D6A4F;
  font-family: var(--font-head);
}
```

---

## Step 7 — `frontend/src/pages/OrderDetailPage.jsx`

### 7a. Add imports
```jsx
import { useState } from 'react'     // already exists — add if not
import { requestReturn } from '../api/orders'
```

### 7b. Add return state inside component
```jsx
const [returnReason,  setReturnReason]  = useState('')
const [showReturnForm, setShowReturnForm] = useState(false)
const [returnMsg,     setReturnMsg]     = useState(null)
const [returnBusy,    setReturnBusy]    = useState(false)
```

### 7c. Add handler
```jsx
const handleReturnRequest = async () => {
  if (!returnReason.trim()) return
  setReturnBusy(true)
  try {
    await requestReturn(order.id, returnReason)
    setReturnMsg({ type: 'success', text: 'Return request submitted! Admin will review shortly.' })
    setShowReturnForm(false)
    load() // re-fetch order so UI reflects new status
  } catch (err) {
    setReturnMsg({ type: 'error', text: err.response?.data?.error || 'Failed to submit return.' })
  } finally { setReturnBusy(false) }
}
```

### 7d. Add return section JSX — after the Order Tracking card

```jsx
{/* Return / Refund Section */}
<div className="return-section">
  {/* Eligible for return */}
  {order.status === 'delivered' && order.can_self_return && (
    <div className="card" style={{ padding: 24 }}>
      <h4 style={{ fontWeight: 600, marginBottom: 12, color: 'var(--text-soft)', fontSize: 13, textTransform: 'uppercase', letterSpacing: 1 }}>Return Order</h4>
      {!showReturnForm ? (
        <button className="btn btn-outline" onClick={() => setShowReturnForm(true)}>
          ↩ Return Order
        </button>
      ) : (
        <div className="return-reason-form">
          <p style={{ fontSize: 13, color: 'var(--color-text-soft)' }}>
            Please tell us why you want to return this order. Refund = paid amount − delivery charge.
          </p>
          <textarea className="form-input" rows={3} placeholder="Reason for return..."
            value={returnReason} onChange={e => setReturnReason(e.target.value)} />
          <div style={{ display: 'flex', gap: 10 }}>
            <button className="btn btn-primary" onClick={handleReturnRequest} disabled={returnBusy || !returnReason.trim()}>
              {returnBusy ? 'Submitting...' : 'Submit Return Request'}
            </button>
            <button className="btn btn-outline" onClick={() => { setShowReturnForm(false); setReturnReason('') }}>
              Cancel
            </button>
          </div>
        </div>
      )}
      {returnMsg && <div className={`alert alert-${returnMsg.type}`} style={{ marginTop: 12 }}>{returnMsg.text}</div>}
    </div>
  )}

  {/* Not eligible */}
  {order.status === 'delivered' && !order.can_self_return && (
    <div className="return-banner return-banner--ineligible">
      Return is not available for this order. Need help?{' '}
      <a href="/contact" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Contact Us</a>
    </div>
  )}

  {/* Rejected — show note (status is back to delivered but rejection reason exists) */}
  {order.return_rejected_reason && order.status === 'delivered' && (
    <div className="return-banner return-banner--rejected" style={{ marginTop: 8 }}>
      Previous return was rejected: {order.return_rejected_reason}
    </div>
  )}

  {/* Return requested — waiting */}
  {order.status === 'return_requested' && (
    <div className="return-banner return-banner--requested">
      ⏳ Return request submitted — admin review pending.
      {order.return_reason && <div style={{ marginTop: 4, fontSize: 12 }}>Your reason: {order.return_reason}</div>}
    </div>
  )}

  {/* Returned — refund in progress */}
  {order.status === 'returned' && (
    <div className="return-banner return-banner--approved">
      ✅ Return approved — refund is being processed. Amount will reflect in 5–7 business days.
    </div>
  )}

  {/* Refunded */}
  {order.status === 'refunded' && (
    <div className="return-banner return-banner--refunded">
      ✅ Refund processed: <strong>₹{order.refund_amount?.toFixed(0)}</strong>
      {order.shipping_fee > 0 && ` (₹${order.total?.toFixed(0)} paid − ₹${order.shipping_fee?.toFixed(0)} delivery charge)`}
    </div>
  )}
</div>
```

---

## Step 8 — `frontend/src/pages/admin/AdminReturns.jsx` (NEW FILE)

```jsx
import { useEffect, useState } from 'react'
import { Link }                 from 'react-router-dom'
import { getReturns, approveReturn, rejectReturn, processRefund } from '../../api/admin'
import Spinner from '../../components/Spinner'

export default function AdminReturns() {
  const [orders,  setOrders]  = useState([])
  const [loading, setLoading] = useState(true)
  const [msg,     setMsg]     = useState(null)
  // rejectReason state: { [orderId]: string }
  const [rejectReasons, setRejectReasons] = useState({})

  const flash = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 4000)
  }

  const load = () => {
    setLoading(true)
    getReturns().then(r => setOrders(r.data.orders)).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const handleApprove = async (id) => {
    try {
      await approveReturn(id)
      flash('success', `Order #${id} return approved.`)
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to approve.')
    }
  }

  const handleReject = async (id) => {
    const reason = (rejectReasons[id] || '').trim()
    if (!reason) { flash('error', 'Rejection reason required.'); return }
    try {
      await rejectReturn(id, reason)
      flash('success', `Order #${id} return rejected.`)
      setRejectReasons(prev => { const n = {...prev}; delete n[id]; return n })
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to reject.')
    }
  }

  const handleRefund = async (order) => {
    const total    = parseFloat(order.total        || 0)
    const shipping = parseFloat(order.shipping_fee || 0)
    const refund   = Math.max(0, total - shipping)
    if (!window.confirm(
      `Process refund of ₹${refund.toFixed(0)} for Order #${order.id}?\n` +
      `(₹${total.toFixed(0)} paid − ₹${shipping.toFixed(0)} delivery)`
    )) return
    try {
      const r = await processRefund(order.id)
      flash('success', r.data.message)
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Refund failed.')
    }
  }

  const requested = orders.filter(o => o.status === 'return_requested')
  const returned  = orders.filter(o => o.status === 'returned')

  if (loading) return <Spinner />

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div style={{ padding: '0 20px 20px', fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, fontWeight: 700 }}>
          🌶 Admin
        </div>
        <Link to="/admin"          className="admin-nav-link">Dashboard</Link>
        <Link to="/admin/products" className="admin-nav-link">Products</Link>
        <Link to="/admin/orders"   className="admin-nav-link">Orders</Link>
        <Link to="/admin/returns"  className="admin-nav-link active">Returns</Link>
        <Link to="/"               className="admin-nav-link">← Back to Store</Link>
      </aside>

      <div className="admin-content">
        <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>
          Returns & Refunds
          <span style={{ fontSize: 15, color: 'var(--color-text-soft)', fontFamily: 'var(--font-body)', fontWeight: 400, marginLeft: 10 }}>
            ({requested.length} pending, {returned.length} awaiting refund)
          </span>
        </h2>

        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {/* Pending return requests */}
        {requested.length > 0 && (
          <>
            <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 16, fontSize: 16 }}>
              ⏳ Awaiting Review ({requested.length})
            </h3>
            {requested.map(o => (
              <div key={o.id} className="return-card">
                <div className="return-card-header">
                  <div>
                    <strong>Order #{o.id}</strong>
                    <span style={{ marginLeft: 10, fontSize: 13, color: 'var(--color-text-soft)' }}>{o.customer_name} ({o.customer_email})</span>
                  </div>
                  <span className="status-badge badge-return_requested">Return Requested</span>
                </div>
                <div style={{ fontSize: 13, marginBottom: 8 }}>
                  <strong>Customer reason:</strong> {o.return_reason || '—'}
                </div>
                <div style={{ fontSize: 13, color: 'var(--color-text-soft)', marginBottom: 12 }}>
                  Requested: {o.return_requested_at ? new Date(o.return_requested_at).toLocaleDateString('en-IN') : '—'}
                  &nbsp;|&nbsp; Order total: ₹{parseFloat(o.total || 0).toFixed(0)}
                  &nbsp;|&nbsp; Refund if approved: ₹{Math.max(0, parseFloat(o.total || 0) - parseFloat(o.shipping_fee || 0)).toFixed(0)}
                </div>
                <div className="return-card-actions">
                  <button className="btn btn-primary btn-sm" onClick={() => handleApprove(o.id)}>
                    ✓ Approve Return
                  </button>
                  <div style={{ display: 'flex', gap: 6, alignItems: 'center', flex: 1 }}>
                    <input className="form-input" style={{ padding: '6px 10px', fontSize: 13, flex: 1 }}
                      placeholder="Rejection reason (required)"
                      value={rejectReasons[o.id] || ''}
                      onChange={e => setRejectReasons(prev => ({ ...prev, [o.id]: e.target.value }))} />
                    <button className="btn btn-danger btn-sm" onClick={() => handleReject(o.id)}>
                      ✗ Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </>
        )}

        {/* Awaiting refund */}
        {returned.length > 0 && (
          <>
            <h3 style={{ fontFamily: 'var(--font-head)', color: '#0369a1', marginBottom: 16, fontSize: 16, marginTop: requested.length ? 32 : 0 }}>
              📦 Item Returned — Awaiting Refund ({returned.length})
            </h3>
            {returned.map(o => {
              const total    = parseFloat(o.total        || 0)
              const shipping = parseFloat(o.shipping_fee || 0)
              const refund   = Math.max(0, total - shipping)
              return (
                <div key={o.id} className="return-card">
                  <div className="return-card-header">
                    <div>
                      <strong>Order #{o.id}</strong>
                      <span style={{ marginLeft: 10, fontSize: 13, color: 'var(--color-text-soft)' }}>{o.customer_name} ({o.customer_email})</span>
                    </div>
                    <span className="status-badge badge-returned">Returned</span>
                  </div>
                  <div style={{ fontSize: 13, marginBottom: 12 }}>
                    <strong>Customer reason:</strong> {o.return_reason || '—'}
                  </div>
                  <div style={{ marginBottom: 12 }}>
                    <div className="return-refund-amount">₹{refund.toFixed(0)}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-soft)' }}>
                      ₹{total.toFixed(0)} paid − ₹{shipping.toFixed(0)} delivery charge
                    </div>
                  </div>
                  <button className="btn btn-primary" onClick={() => handleRefund(o)}>
                    💳 Process Refund via Razorpay
                  </button>
                </div>
              )
            })}
          </>
        )}

        {orders.length === 0 && (
          <div className="empty-state" style={{ padding: '48px 0' }}>
            <div className="empty-icon">✅</div>
            <div className="empty-title">No pending returns</div>
            <p className="empty-text">All return requests have been handled.</p>
          </div>
        )}
      </div>
    </div>
  )
}
```

---

## Step 9 — `frontend/src/App.jsx`

### 9a. Add import
```jsx
import AdminReturns from './pages/admin/AdminReturns'
```

### 9b. Add route (after `/admin/orders` route)
```jsx
<Route path="/admin/returns" element={<AdminGuard><AdminReturns /></AdminGuard>} />
```

### 9c. Add `badge-return_requested` CSS class in `index.css`

Find the badge section and add:
```css
.badge-return_requested { background: #fef9c3; color: #92400e; }
```

---

## File Change Summary

| File | Type | Key change |
|---|---|---|
| `db.py` | Edit | 5 new columns (migrate), `RETURN_WINDOW_DAYS`, `can_self_return()` |
| `orders.py` | Edit | `return_request` endpoint; `order_detail` adds `can_self_return` + return fields |
| `admin.py` | Edit | `return_requested` in ALLOWED_STATUSES; 4 new endpoints (returns list, approve, reject, refund) |
| `frontend/src/api/orders.js` | Edit | Add `requestReturn()` |
| `frontend/src/api/admin.js` | Edit | Add `getReturns()`, `approveReturn()`, `rejectReturn()`, `processRefund()` |
| `frontend/src/index.css` | Edit | Return/refund banner + card styles + badge |
| `frontend/src/pages/OrderDetailPage.jsx` | Edit | Return section (button/form/status messages) |
| `frontend/src/pages/admin/AdminReturns.jsx` | NEW | Returns management page |
| `frontend/src/App.jsx` | Edit | Add `/admin/returns` route |

---

## Security checklist (security-review agent will verify)

- [ ] `return_request` endpoint: ownership check (user_id == current_user.id) + server-side eligibility re-check
- [ ] `refund` endpoint: double-refund guard (`razorpay_refund_id` check before calling Razorpay)
- [ ] All amounts computed server-side; client-sent amount ignored
- [ ] Status transition guards on all 3 admin endpoints
- [ ] All admin endpoints behind `@admin_required`
- [ ] `return_reason` / `reject_reason` trimmed + length capped (500 chars)
- [ ] Razorpay secret never sent to frontend
- [ ] `can_self_return` called fresh on server per request (not trusting cached frontend state)

---

## Test plan (test-writer stage — after implementation)

1. Eligible return → request accepted, status = `return_requested`, history updated
2. Ineligible (already used) → 403
3. Outside window → 403
4. Missing reason → 400
5. Wrong user's order → 404
6. Admin approve → status = `returned`
7. Admin reject → status = `delivered`, reason saved
8. Refund compute: ₹699 − ₹49 = ₹650; free delivery = full refund
9. Double-refund block → 400 on second attempt
10. Non-`returned` status on refund → 400
11. Non-`return_requested` on approve/reject → 400
12. Unauthenticated → 401; non-admin → 403 on all admin endpoints
