import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getOrders, updateOrderStatus } from '../../api/admin'
import Spinner from '../../components/Spinner'

const STATUSES = ['paid', 'shipped', 'delivered', 'cancelled']
const statusClass = s => `status-badge badge-${s}`

export default function AdminOrders() {
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [msg, setMsg]         = useState(null)

  useEffect(() => {
    getOrders().then(r => setOrders(r.data.orders)).finally(() => setLoading(false))
  }, [])

  const handleStatus = async (id, status) => {
    await updateOrderStatus(id, { status })
    setOrders(prev => prev.map(o => o.id === id ? { ...o, status } : o))
    setMsg({ type: 'success', text: `Order #${id} updated to ${status}` })
    setTimeout(() => setMsg(null), 3000)
  }

  if (loading) return <Spinner />

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div style={{ padding: '0 20px 20px', fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, fontWeight: 700 }}>
          🌶 Admin
        </div>
        <Link to="/admin"          className="admin-nav-link">Dashboard</Link>
        <Link to="/admin/products" className="admin-nav-link">Products</Link>
        <Link to="/admin/orders"   className="admin-nav-link active">Orders</Link>
        <Link to="/"               className="admin-nav-link">← Back to Store</Link>
      </aside>
      <div className="admin-content">
        <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>Orders ({orders.length})</h2>
        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Customer</th>
                <th>Total</th>
                <th>Status</th>
                <th>Date</th>
                <th>Update Status</th>
              </tr>
            </thead>
            <tbody>
              {orders.map(o => (
                <tr key={o.id}>
                  <td style={{ fontWeight: 500 }}>#{o.id}</td>
                  <td>{o.shipping_name}<br /><span style={{ fontSize: 12, color: 'var(--color-text-soft)' }}>{o.shipping_phone}</span></td>
                  <td>₹{o.total?.toFixed(2)}</td>
                  <td><span className={statusClass(o.status)}>{o.status}</span></td>
                  <td style={{ fontSize: 13, color: 'var(--color-text-soft)' }}>{new Date(o.created_at).toLocaleDateString()}</td>
                  <td>
                    <select className="form-select" style={{ width: 'auto', padding: '5px 10px', fontSize: 13 }}
                      value={o.status} onChange={e => handleStatus(o.id, e.target.value)}>
                      {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
