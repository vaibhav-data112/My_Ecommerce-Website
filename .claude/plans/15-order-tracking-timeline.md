# Plan 15 — Order Tracking Timeline

**Spec:** `.claude/specs/15-order-tracking-timeline.md`  
**Branch:** `feature/order-tracking`  
**Effort:** Medium (~3-4 hours)  
**Risk:** Low — fully additive, no existing data deleted

---

## Pre-conditions (already true — verified by tech-lead)

- `orders.status` column exists (TEXT, default `'pending'`)
- `get_order_by_id()` in `db.py:310` — returns `SELECT *`
- `update_order_status()` in `db.py:780` — updates status only
- Admin status-update endpoint at `POST /api/admin/orders/<id>/status` exists
- `orders.py` order detail at `GET /api/orders/<id>` returns `dict(order)` — new columns auto-included
- `can_user_review()` bug at `db.py:629` — hardcoded `status = 'paid'`

---

## Implementation Order

### Step 1 — `db.py` (4 changes)

#### 1a. `migrate_db()` — add 3 columns + back-fill

Find the last migration block in `migrate_db()` (around line 354-359, `payment_id / payment_order_id` block). After it, add:

```python
# ── Feature 15: order tracking timeline ──────────────────────
orders_cols = [r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
for col, ddl in [
    ('status_history',  "ALTER TABLE orders ADD COLUMN status_history TEXT"),
    ('courier_name',    "ALTER TABLE orders ADD COLUMN courier_name TEXT"),
    ('tracking_number', "ALTER TABLE orders ADD COLUMN tracking_number TEXT"),
]:
    if col not in orders_cols:
        conn.execute(ddl)

# Back-fill: existing orders get a single-entry history from their current status
import json as _json
backfill = conn.execute(
    "SELECT id, status, created_at FROM orders WHERE status_history IS NULL"
).fetchall()
for row in backfill:
    hist = _json.dumps([{"status": row['status'],
                         "at": row['created_at'] or '',
                         "note": None}])
    conn.execute("UPDATE orders SET status_history = ? WHERE id = ?",
                 (hist, row['id']))
```

Call `conn.commit()` once at the end of `migrate_db()` (already done — verify it's there).

#### 1b. New helper `append_status_history()` — add after `update_order_status`

```python
def append_status_history(order_id, new_status, note=None):
    """Append one status entry, update status column, optionally save courier/tracking."""
    import json as _json
    from datetime import datetime, timezone
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT status_history FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        history = _json.loads(row['status_history'] or '[]')
        history.append({
            "status": new_status,
            "at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S'),
            "note": note or None,
        })
        conn.execute(
            "UPDATE orders SET status = ?, status_history = ? WHERE id = ?",
            (new_status, _json.dumps(history), order_id)
        )
        conn.commit()
    finally:
        conn.close()


def update_courier_details(order_id, courier_name, tracking_number):
    """Save courier + tracking on the order row (called alongside shipped status)."""
    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET courier_name = ?, tracking_number = ? WHERE id = ?",
            (courier_name or None, tracking_number or None, order_id)
        )
        conn.commit()
    finally:
        conn.close()
```

#### 1c. Fix `can_user_review()` bug (line 629)

Change:
```python
AND o.status = 'paid'
```
To:
```python
AND o.status IN ('paid', 'packed', 'shipped', 'out_for_delivery', 'delivered')
```

#### 1d. Export the two new helpers

Add `append_status_history` and `update_courier_details` to the import line in `admin.py`.

---

### Step 2 — `admin.py` (2 changes)

#### 2a. Expand `ALLOWED_STATUSES` (line 17)

```python
ALLOWED_STATUSES = [
    'paid', 'packed', 'shipped', 'out_for_delivery', 'delivered',
    'cancelled', 'returned', 'refunded',
]
```

#### 2b. Extend `update_status` endpoint to accept note / courier / tracking

Replace existing `update_status` function body:

```python
@admin.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_status(order_id):
    order = get_order_by_id(order_id)
    if not order:
        return jsonify({'error': 'Order not found.'}), 404
    data       = request.get_json(silent=True) or {}
    new_status = data.get('status', '').strip()
    if new_status not in ALLOWED_STATUSES:
        return jsonify({'error': 'Invalid status.'}), 400

    note            = (data.get('note') or '').strip() or None
    courier_name    = (data.get('courier_name') or '').strip() or None
    tracking_number = (data.get('tracking_number') or '').strip() or None

    append_status_history(order_id, new_status, note=note)
    if new_status == 'shipped':
        update_courier_details(order_id, courier_name, tracking_number)

    return jsonify({'success': True,
                    'message': f'Order #{order_id} updated to {new_status}.'})
```

Update the import from `db`:
```python
from db import (
    ..., append_status_history, update_courier_details,
)
```
(Remove `update_order_status` from db import in admin.py if it's there — it's no longer called directly.)

---

### Step 3 — `orders.py` (1 change)

Parse `status_history` JSON before returning to frontend:

```python
@orders.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    import json as _json
    order = get_order_by_id(order_id)
    if not order or order['user_id'] != int(current_user.id):
        return jsonify({'error': 'Order not found.'}), 404
    items     = get_order_items(order_id)
    order_dict = dict(order)
    # Parse JSON string → list so frontend doesn't need to JSON.parse()
    raw_hist = order_dict.get('status_history')
    order_dict['status_history'] = _json.loads(raw_hist) if raw_hist else []
    return jsonify({'order': order_dict, 'items': [dict(i) for i in items]})
```

---

### Step 4 — `frontend/src/index.css` (2 additions)

#### 4a. New badge classes — add alongside existing `.badge-paid`, `.badge-shipped` etc.

```css
.badge-packed          { background: #e0f2fe; color: #0369a1; }
.badge-out_for_delivery{ background: #fef9c3; color: #854d0e; }
.badge-returned        { background: #fef3c7; color: #92400e; }
.badge-refunded        { background: #ede9fe; color: #6d28d9; }
```

#### 4b. Order Timeline CSS block — add before `/* RESPONSIVE */` section

```css
/* ===========================
   ORDER TIMELINE
   =========================== */
.order-timeline { margin: 24px 0; }

.timeline-banner {
  padding: 12px 16px; border-radius: var(--radius-md);
  font-weight: 600; font-size: var(--fs-sm); margin-bottom: 20px;
  border-left: 4px solid;
}
.timeline-banner--cancelled { background: #fee2e2; color: #991b1b; border-color: var(--color-danger); }
.timeline-banner--returned  { background: #fef3c7; color: #92400e; border-color: #B7860B; }
.timeline-banner--refunded  { background: #e0f2fe; color: #0369a1; border-color: #0369a1; }

.timeline-steps { position: relative; padding-left: 36px; }

.timeline-step {
  position: relative;
  padding-bottom: 28px;
}
.timeline-step:last-child { padding-bottom: 0; }

/* Vertical connecting line */
.timeline-step:not(:last-child)::before {
  content: ''; position: absolute;
  left: -21px; top: 18px; bottom: 0; width: 2px;
  background: var(--color-border);
}
.timeline-step--done:not(:last-child)::before  { background: #2D6A4F; }
.timeline-step--active:not(:last-child)::before { background: var(--color-border); }

/* Step dot */
.timeline-dot {
  position: absolute; left: -29px; top: 0;
  width: 18px; height: 18px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; border: 2px solid var(--color-border);
  background: var(--color-surface);
}
.timeline-step--done   .timeline-dot { background: #2D6A4F; color: #fff; border-color: #2D6A4F; }
.timeline-step--active .timeline-dot { background: #D4580A; color: #fff; border-color: #D4580A; width: 20px; height: 20px; left: -30px; }
.timeline-step--pending .timeline-dot { background: var(--color-surface); color: var(--color-text-soft); }

.timeline-label {
  font-weight: 600; font-size: var(--fs-sm); line-height: 18px;
}
.timeline-step--done    .timeline-label { color: #2D6A4F; }
.timeline-step--active  .timeline-label { color: #D4580A; font-size: var(--fs-base); }
.timeline-step--pending .timeline-label { color: var(--color-text-soft); font-weight: 400; }

.timeline-meta { margin-top: 3px; display: flex; flex-direction: column; gap: 2px; }
.timeline-date { font-size: var(--fs-xs); color: var(--color-text-soft); }
.timeline-note { font-size: var(--fs-xs); color: var(--color-text-soft); font-style: italic; }

.timeline-courier {
  margin-top: 6px; display: flex; flex-wrap: wrap; gap: 10px;
  font-size: var(--fs-xs); color: var(--color-primary-dark); font-weight: 500;
}
.timeline-courier span {
  background: var(--color-surface-warm); padding: 2px 8px; border-radius: 99px;
}
```

---

### Step 5 — `frontend/src/components/OrderTimeline.jsx` (NEW FILE)

```jsx
const STEPS = [
  { key: 'paid',             label: 'Order Confirmed' },
  { key: 'packed',           label: 'Packed' },
  { key: 'shipped',          label: 'Shipped' },
  { key: 'out_for_delivery', label: 'Out for Delivery' },
  { key: 'delivered',        label: 'Delivered' },
]

const TERMINAL = {
  cancelled: { label: 'This order has been cancelled.',   cls: 'timeline-banner--cancelled' },
  returned:  { label: 'This order has been returned.',    cls: 'timeline-banner--returned'  },
  refunded:  { label: 'Refund has been processed.',       cls: 'timeline-banner--refunded'  },
}

function fmt(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleString('en-IN', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', hour12: true,
  })
}

export default function OrderTimeline({ statusHistory = [], currentStatus, courierName, trackingNumber }) {
  const isTerminal    = currentStatus in TERMINAL
  const currentStepIdx = STEPS.findIndex(s => s.key === currentStatus)

  // Build lookup: status key → history entry
  const histMap = {}
  for (const entry of statusHistory) {
    histMap[entry.status] = entry
  }

  return (
    <div className="order-timeline">
      {isTerminal && (
        <div className={`timeline-banner ${TERMINAL[currentStatus].cls}`}>
          {TERMINAL[currentStatus].label}
        </div>
      )}
      <div className="timeline-steps">
        {STEPS.map((step, idx) => {
          const hist  = histMap[step.key]
          let   state = 'pending'
          if (isTerminal) {
            state = hist ? 'done' : 'pending'
          } else {
            if      (idx < currentStepIdx)  state = 'done'
            else if (idx === currentStepIdx) state = 'active'
          }

          return (
            <div key={step.key} className={`timeline-step timeline-step--${state}`}>
              <div className="timeline-dot">
                {state === 'done' ? '✓' : state === 'active' ? '●' : '○'}
              </div>
              <div className="timeline-content">
                <div className="timeline-label">{step.label}</div>
                {hist && (
                  <div className="timeline-meta">
                    <span className="timeline-date">{fmt(hist.at)}</span>
                    {hist.note && <span className="timeline-note">{hist.note}</span>}
                  </div>
                )}
                {step.key === 'shipped' && state !== 'pending' && (courierName || trackingNumber) && (
                  <div className="timeline-courier">
                    {courierName    && <span>📦 {courierName}</span>}
                    {trackingNumber && <span>Tracking: {trackingNumber}</span>}
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
```

---

### Step 6 — `frontend/src/pages/OrderDetailPage.jsx` (1 change)

Add import at top:
```jsx
import OrderTimeline from '../components/OrderTimeline'
```

Find the existing status badge section (in the product detail grid, right side). Replace or supplement it with:
```jsx
{/* Order Timeline */}
<OrderTimeline
  statusHistory={order.status_history || []}
  currentStatus={order.status}
  courierName={order.courier_name}
  trackingNumber={order.tracking_number}
/>
```

Keep the existing single badge if it appears in the order header card — just also add the timeline below.

---

### Step 7 — `frontend/src/pages/admin/AdminOrders.jsx` (2 changes)

#### 7a. Expand STATUSES array (line 6)
```js
const STATUSES = [
  'paid', 'packed', 'shipped', 'out_for_delivery', 'delivered',
  'cancelled', 'returned', 'refunded',
]
```

#### 7b. Replace the inline select with a per-row expandable update panel

Add state at top of component:
```jsx
const [updating, setUpdating] = useState({}) // { [orderId]: {status, note, courier_name, tracking_number} }

const startUpdate = (o) => setUpdating(prev => ({
  ...prev,
  [o.id]: { status: o.status, note: '', courier_name: '', tracking_number: '' }
}))
const cancelUpdate = (id) => setUpdating(prev => { const n = {...prev}; delete n[id]; return n })
const setField = (id, field, val) => setUpdating(prev => ({
  ...prev, [id]: { ...prev[id], [field]: val }
}))

const handleStatus = async (id) => {
  const draft = updating[id]
  if (!draft) return
  await updateOrderStatus(id, {
    status:          draft.status,
    note:            draft.note,
    courier_name:    draft.courier_name,
    tracking_number: draft.tracking_number,
  })
  setOrders(prev => prev.map(o => o.id === id ? { ...o, status: draft.status } : o))
  setMsg({ type: 'success', text: `Order #${id} updated to ${draft.status}` })
  cancelUpdate(id)
  setTimeout(() => setMsg(null), 3000)
}
```

Replace existing `<td>` with select:
```jsx
<td>
  {updating[o.id] ? (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 200 }}>
      <select className="form-select" style={{ padding: '5px 8px', fontSize: 13 }}
        value={updating[o.id].status}
        onChange={e => setField(o.id, 'status', e.target.value)}>
        {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
      </select>
      {updating[o.id].status === 'shipped' && (
        <>
          <input className="form-input" style={{ padding: '4px 8px', fontSize: 12 }}
            placeholder="Courier name (e.g. BlueDart)"
            value={updating[o.id].courier_name}
            onChange={e => setField(o.id, 'courier_name', e.target.value)} />
          <input className="form-input" style={{ padding: '4px 8px', fontSize: 12 }}
            placeholder="Tracking number"
            value={updating[o.id].tracking_number}
            onChange={e => setField(o.id, 'tracking_number', e.target.value)} />
        </>
      )}
      <input className="form-input" style={{ padding: '4px 8px', fontSize: 12 }}
        placeholder="Note (optional)"
        value={updating[o.id].note}
        onChange={e => setField(o.id, 'note', e.target.value)} />
      <div style={{ display: 'flex', gap: 6 }}>
        <button className="btn btn-primary btn-sm" onClick={() => handleStatus(o.id)}>Save</button>
        <button className="btn btn-outline btn-sm" onClick={() => cancelUpdate(o.id)}>Cancel</button>
      </div>
    </div>
  ) : (
    <button className="btn btn-outline btn-sm" onClick={() => startUpdate(o)}>
      Update Status
    </button>
  )}
</td>
```

---

### Step 8 — Verify `frontend/src/api/admin.js`

`updateOrderStatus` already accepts an object `data`. No change needed — it will pass the new fields automatically.

---

## File Change Summary

| File | Type | What changes |
|------|------|------|
| `db.py` | Edit | migrate_db adds 3 cols + back-fill; new helpers; can_user_review fix |
| `admin.py` | Edit | ALLOWED_STATUSES expands; update_status accepts note/courier/tracking |
| `orders.py` | Edit | order_detail parses status_history JSON → list |
| `index.css` | Edit | New badge classes + ~80 lines timeline CSS |
| `OrderTimeline.jsx` | NEW | Timeline component with done/active/pending + terminal banner |
| `OrderDetailPage.jsx` | Edit | Import + render OrderTimeline |
| `AdminOrders.jsx` | Edit | STATUSES expands + per-row update panel with extra shipped inputs |

`frontend/src/api/admin.js` — no change needed.

---

## Implementation sequence (to avoid breaking the app mid-way)

1. `db.py` — migrate + helpers + bug fix ← start here (backend foundation)
2. `admin.py` — expand statuses + endpoint ← backend complete
3. `orders.py` — parse history ← API ready
4. `index.css` — CSS ← can be done any time
5. `OrderTimeline.jsx` ← new component
6. `OrderDetailPage.jsx` ← integrate component
7. `AdminOrders.jsx` ← admin UI
8. `npm run build` ← verify no compile errors
9. `python app.py` ← verify migration runs cleanly
10. Browser test (spec section 10)

---

## Test plan (for test-writer agent after implementation)

Key test cases to cover:
1. `migrate_db()` idempotent — run twice, no error; existing order gets back-filled history
2. `append_status_history()` — appends entry, updates status, timestamp is set
3. Admin `PATCH /orders/<id>/status` with valid status → 200, history appended
4. Admin with `shipped` + courier/tracking → courier saved in DB
5. Admin with invalid status → 400
6. `GET /orders/<id>` returns `status_history` as list (not string)
7. `can_user_review()` — `delivered` order → review allowed
8. Non-admin → 403; unauthenticated → 401
9. Order owned by another user → 404
10. Terminal status → order still returns history list
