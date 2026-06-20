import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOrders } from '../api/orders'
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

export default function OrdersPage() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getOrders().then(r => setOrders(r.data.orders)).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div className="page">
      <div className="container">
        <h1 className="section-title" style={{ marginBottom: 28 }}>My Orders</h1>
        {orders.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📦</div>
            <div className="empty-title">No orders yet</div>
            <p className="empty-text">Place your first order and it will appear here</p>
            <Link to="/products" className="btn btn-primary">Shop Now</Link>
          </div>
        ) : orders.map(o => (
          <div key={o.id} className="card order-card">
            <div className="order-header">
              <div>
                <div className="order-id">Order #{o.id}</div>
                <div style={{ fontSize: 13, color: 'var(--text-soft)', marginTop: 2 }}>
                  {new Date(o.created_at).toLocaleDateString('en-IN', { day: 'numeric', month: 'long', year: 'numeric' })}
                </div>
              </div>
              <span className={statusClass(o.status)}>{STATUS_LABELS[o.status] || o.status}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
              <div style={{ fontSize: 14, color: 'var(--text-soft)' }}>
                {o.shipping_name} · {o.shipping_phone}
                {o.payment_method === 'cod' && (
                  <span style={{ marginLeft: 8, background: '#FEF3C7', color: '#92400E', fontSize: 11, fontWeight: 600, padding: '2px 7px', borderRadius: 4 }}>COD</span>
                )}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                {o.status === 'cod_pending' ? (
                  <span style={{ fontWeight: 700, fontSize: 16, color: '#92400E' }}>₹{o.total?.toFixed(0)} due</span>
                ) : (
                  <span style={{ fontWeight: 600, fontSize: 16, color: 'var(--brown)' }}>₹{o.total?.toFixed(2)}</span>
                )}
                <Link to={`/orders/${o.id}`} className="btn btn-outline btn-sm">View Details</Link>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
