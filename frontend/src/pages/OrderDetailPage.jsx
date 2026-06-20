import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getOrder, requestReturn } from '../api/orders'
import OrderTimeline from '../components/OrderTimeline'
import Spinner from '../components/Spinner'

const statusClass = s => `status-badge badge-${s}`

const STATUS_LABELS = {
  pending:          'Order Confirmed',
  cod_pending:      'Cash Due on Delivery',
  cod_paid:         'Cash Collected',
  paid:             'Payment Received',
  packed:           'Being Packed',
  shipped:          'Shipped',
  out_for_delivery: 'Out for Delivery',
  delivered:        'Delivered',
  cancelled:        'Cancelled',
  return_requested: 'Return Requested',
  returned:         'Return Approved',
  refunded:         'Refunded',
}

export default function OrderDetailPage() {
  const { id }    = useParams()
  const navigate  = useNavigate()
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [returnReason,   setReturnReason]   = useState('')
  const [showReturnForm, setShowReturnForm] = useState(false)
  const [returnMsg,      setReturnMsg]      = useState(null)
  const [returnBusy,     setReturnBusy]     = useState(false)

  const load = () => {
    setLoading(true)
    getOrder(id).then(r => setData(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  const handleReturnRequest = async () => {
    if (!returnReason.trim()) return
    setReturnBusy(true)
    try {
      await requestReturn(order.id, returnReason)
      setReturnMsg({ type: 'success', text: 'Return request submitted! Admin will review shortly.' })
      setShowReturnForm(false)
      setReturnReason('')
      load()
    } catch (err) {
      setReturnMsg({ type: 'error', text: err.response?.data?.error || 'Failed to submit return.' })
    } finally { setReturnBusy(false) }
  }

  if (loading) return <Spinner />
  if (!data)   return <div className="page container"><p>Order not found.</p></div>

  const { order, items } = data

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 740 }}>
        <p style={{ marginBottom: 20, fontSize: 13, color: 'var(--text-soft)' }}>
          <Link to="/orders">← Back to Orders</Link>
        </p>

        {order.status === 'paid' && (
          <div className="alert alert-success" style={{ marginBottom: 24 }}>
            ✓ Payment received! Your order has been confirmed.
          </div>
        )}

        {/* COD Payment Info Card */}
        {order.payment_method === 'cod' && order.status === 'cod_pending' && (
          <div className="cod-info-card" style={{ marginBottom: 24 }}>
            <div className="cod-info-header">
              <span className="cod-info-icon">💵</span>
              <div>
                <div className="cod-info-title">Cash on Delivery</div>
                <div className="cod-info-sub">Keep <strong>₹{order.total?.toFixed(0)}</strong> cash ready when delivery arrives</div>
              </div>
            </div>
            <div className="cod-info-actions">
              <button className="btn btn-outline btn-sm" onClick={() => navigate(`/payment/${order.id}`)}>
                💳 Switch to Online Payment
              </button>
            </div>
          </div>
        )}
        {order.payment_method === 'cod' && order.status === 'cod_paid' && (
          <div className="alert alert-success" style={{ marginBottom: 24 }}>
            ✓ Cash payment collected. Thank you!
          </div>
        )}

        <div className="card" style={{ padding: 28, marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
            <div>
              <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 4 }}>Order #{order.id}</h2>
              <div style={{ fontSize: 13, color: 'var(--text-soft)' }}>
                Placed on {new Date(order.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
              </div>
            </div>
            <span className={statusClass(order.status)}>{STATUS_LABELS[order.status] || order.status}</span>
          </div>

          <h4 style={{ fontWeight: 600, marginBottom: 12, color: 'var(--text-soft)', fontSize: 13, textTransform: 'uppercase', letterSpacing: 1 }}>Items Ordered</h4>
          {items.map(i => (
            <div key={i.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 0', borderBottom: '1px solid var(--border)', fontSize: 14 }}>
              <div>
                <div style={{ fontWeight: 500 }}>{i.product_name}</div>
                <div style={{ color: 'var(--text-soft)', fontSize: 13 }}>₹{i.unit_price} × {i.quantity}</div>
              </div>
              <div style={{ fontWeight: 600 }}>₹{i.line_total?.toFixed(2)}</div>
            </div>
          ))}

          <div style={{ marginTop: 16 }}>
            <div className="summary-row"><span>Subtotal</span><span>₹{order.subtotal?.toFixed(2)}</span></div>
            <div className="summary-row">
              <span>Shipping</span>
              <span>{order.shipping_fee === 0 ? <span style={{ color: 'var(--success)' }}>Free</span> : `₹${order.shipping_fee}`}</span>
            </div>
            <div className="summary-total"><span>Total</span><span>₹{order.total?.toFixed(2)}</span></div>
          </div>
        </div>

        <div className="card" style={{ padding: 24, marginBottom: 20 }}>
          <h4 style={{ fontWeight: 600, marginBottom: 12, color: 'var(--text-soft)', fontSize: 13, textTransform: 'uppercase', letterSpacing: 1 }}>Delivery Address</h4>
          <div style={{ fontSize: 14, lineHeight: 1.8 }}>
            <strong>{order.shipping_name}</strong><br />
            {order.shipping_phone}<br />
            {order.shipping_address}
          </div>
        </div>

        <div className="card" style={{ padding: 28 }}>
          <h4 style={{ fontWeight: 600, marginBottom: 4, color: 'var(--text-soft)', fontSize: 13, textTransform: 'uppercase', letterSpacing: 1 }}>Order Tracking</h4>
          <OrderTimeline
            statusHistory={order.status_history || []}
            currentStatus={order.status}
            courierName={order.courier_name}
            trackingNumber={order.tracking_number}
          />
        </div>

        {/* Return / Refund Section */}
        <div className="return-section">
          {order.status === 'delivered' && order.can_self_return && (
            <div className="card" style={{ padding: 24 }}>
              <h4 style={{ fontWeight: 600, marginBottom: 12, color: 'var(--color-text-soft)', fontSize: 13, textTransform: 'uppercase', letterSpacing: 1 }}>Return Order</h4>
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
                    <button className="btn btn-primary" onClick={handleReturnRequest}
                      disabled={returnBusy || !returnReason.trim()}>
                      {returnBusy ? 'Submitting...' : 'Submit Return Request'}
                    </button>
                    <button className="btn btn-outline"
                      onClick={() => { setShowReturnForm(false); setReturnReason('') }}>
                      Cancel
                    </button>
                  </div>
                </div>
              )}
              {returnMsg && (
                <div className={`alert alert-${returnMsg.type}`} style={{ marginTop: 12 }}>
                  {returnMsg.text}
                </div>
              )}
            </div>
          )}

          {order.status === 'delivered' && !order.can_self_return && (
            <div className="return-banner return-banner--ineligible">
              Return is not available for this order. Need help?{' '}
              <a href="/contact" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Contact Us</a>
            </div>
          )}

          {order.return_rejected_reason && order.status === 'delivered' && (
            <div className="return-banner return-banner--rejected" style={{ marginTop: 8 }}>
              Previous return was rejected: {order.return_rejected_reason}
            </div>
          )}

          {order.status === 'return_requested' && (
            <div className="return-banner return-banner--requested">
              ⏳ Return request submitted — admin review pending.
              {order.return_reason && (
                <div style={{ marginTop: 4, fontSize: 12 }}>Your reason: {order.return_reason}</div>
              )}
            </div>
          )}

          {order.status === 'returned' && (
            <div className="return-banner return-banner--approved">
              ✅ Return approved — refund is being processed. Amount will reflect in 5–7 business days.
            </div>
          )}

          {order.status === 'refunded' && (
            <div className="return-banner return-banner--refunded">
              ✅ Refund processed: <strong>₹{order.refund_amount?.toFixed(0)}</strong>
              {order.shipping_fee > 0 && (
                <> (₹{order.total?.toFixed(0)} paid − ₹{order.shipping_fee?.toFixed(0)} delivery charge)</>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
