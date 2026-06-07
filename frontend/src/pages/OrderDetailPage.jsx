import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getOrder } from '../api/orders'
import Spinner from '../components/Spinner'

const statusClass = s => `status-badge badge-${s}`

export default function OrderDetailPage() {
  const { id }    = useParams()
  const [data, setData]   = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOrder(id).then(r => setData(r.data)).finally(() => setLoading(false))
  }, [id])

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
            ✓ Payment successful! Your order has been confirmed.
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
            <span className={statusClass(order.status)}>{order.status}</span>
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

        <div className="card" style={{ padding: 24 }}>
          <h4 style={{ fontWeight: 600, marginBottom: 12, color: 'var(--text-soft)', fontSize: 13, textTransform: 'uppercase', letterSpacing: 1 }}>Delivery Address</h4>
          <div style={{ fontSize: 14, lineHeight: 1.8 }}>
            <strong>{order.shipping_name}</strong><br />
            {order.shipping_phone}<br />
            {order.shipping_address}
          </div>
        </div>
      </div>
    </div>
  )
}
