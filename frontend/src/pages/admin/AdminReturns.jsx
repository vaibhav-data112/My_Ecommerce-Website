import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getReturns, approveReturn, rejectReturn, processRefund } from '../../api/admin'
import Spinner from '../../components/Spinner'

export default function AdminReturns() {
  const [orders,        setOrders]        = useState([])
  const [loading,       setLoading]       = useState(true)
  const [msg,           setMsg]           = useState(null)
  const [rejectReasons, setRejectReasons] = useState({})
  const [busy,          setBusy]          = useState({})

  const flash = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 4000)
  }

  const load = () => {
    setLoading(true)
    getReturns().then(r => setOrders(r.data.orders)).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const setBusyFor = (id, val) => setBusy(prev => ({ ...prev, [id]: val }))

  const handleApprove = async (id) => {
    setBusyFor(id, true)
    try {
      await approveReturn(id)
      flash('success', `Order #${id} return approved.`)
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to approve.')
    } finally { setBusyFor(id, false) }
  }

  const handleReject = async (id) => {
    const reason = (rejectReasons[id] || '').trim()
    if (!reason) { flash('error', 'Rejection reason is required.'); return }
    setBusyFor(id, true)
    try {
      await rejectReturn(id, reason)
      flash('success', `Order #${id} return rejected.`)
      setRejectReasons(prev => { const n = { ...prev }; delete n[id]; return n })
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to reject.')
    } finally { setBusyFor(id, false) }
  }

  const handleRefund = async (order) => {
    const total    = parseFloat(order.total        || 0)
    const shipping = parseFloat(order.shipping_fee || 0)
    const refund   = Math.max(0, total - shipping)
    if (!window.confirm(
      `Process refund of ₹${refund.toFixed(0)} for Order #${order.id}?\n` +
      `(₹${total.toFixed(0)} paid − ₹${shipping.toFixed(0)} delivery charge)`
    )) return
    setBusyFor(order.id, true)
    try {
      const r = await processRefund(order.id)
      flash('success', r.data.message)
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Refund failed.')
    } finally { setBusyFor(order.id, false) }
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
        <Link to="/admin/contacts" className="admin-nav-link">Contact Messages</Link>
        <Link to="/"               className="admin-nav-link">← Back to Store</Link>
      </aside>

      <div className="admin-content">
        <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>
          Returns &amp; Refunds
          <span style={{ fontSize: 15, color: 'var(--color-text-soft)', fontFamily: 'var(--font-body)', fontWeight: 400, marginLeft: 10 }}>
            ({requested.length} pending, {returned.length} awaiting refund)
          </span>
        </h2>

        {msg && <div className={`alert alert-${msg.type}`} style={{ marginBottom: 20 }}>{msg.text}</div>}

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
                    <span style={{ marginLeft: 10, fontSize: 13, color: 'var(--color-text-soft)' }}>
                      {o.customer_name} ({o.customer_email})
                    </span>
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
                  <button className="btn btn-primary btn-sm"
                    onClick={() => handleApprove(o.id)}
                    disabled={busy[o.id]}>
                    ✓ Approve Return
                  </button>
                  <input className="form-input" style={{ padding: '6px 10px', fontSize: 13, flex: 1, minWidth: 160 }}
                    placeholder="Rejection reason (required to reject)"
                    value={rejectReasons[o.id] || ''}
                    onChange={e => setRejectReasons(prev => ({ ...prev, [o.id]: e.target.value }))} />
                  <button className="btn btn-sm" style={{ background: 'var(--color-danger)', color: '#fff', borderColor: 'var(--color-danger)' }}
                    onClick={() => handleReject(o.id)}
                    disabled={busy[o.id]}>
                    ✗ Reject
                  </button>
                </div>
              </div>
            ))}
          </>
        )}

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
                      <span style={{ marginLeft: 10, fontSize: 13, color: 'var(--color-text-soft)' }}>
                        {o.customer_name} ({o.customer_email})
                      </span>
                    </div>
                    <span className="status-badge badge-returned">Returned</span>
                  </div>
                  <div style={{ fontSize: 13, marginBottom: 12 }}>
                    <strong>Customer reason:</strong> {o.return_reason || '—'}
                  </div>
                  <div style={{ marginBottom: 16 }}>
                    <div className="return-refund-amount">₹{refund.toFixed(0)}</div>
                    <div style={{ fontSize: 12, color: 'var(--color-text-soft)' }}>
                      ₹{total.toFixed(0)} paid − ₹{shipping.toFixed(0)} delivery charge
                    </div>
                  </div>
                  <button className="btn btn-primary"
                    onClick={() => handleRefund(o)}
                    disabled={busy[o.id]}>
                    {busy[o.id] ? 'Processing...' : '💳 Process Refund via Razorpay'}
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
