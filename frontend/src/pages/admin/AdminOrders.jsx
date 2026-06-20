import { useEffect, useState } from 'react'
import { getOrders, updateOrderStatus } from '../../api/admin'
import AdminSidebar from '../../components/AdminSidebar'
import Spinner from '../../components/Spinner'

const STATUSES = [
  'paid', 'packed', 'shipped', 'out_for_delivery', 'delivered',
  'cancelled', 'return_requested', 'returned', 'refunded',
]
const statusClass = s => `status-badge badge-${s}`

export default function AdminOrders() {
  const [orders,   setOrders]   = useState([])
  const [loading,  setLoading]  = useState(true)
  const [msg,      setMsg]      = useState(null)
  const [updating, setUpdating] = useState({})

  useEffect(() => {
    getOrders().then(r => setOrders(r.data.orders)).finally(() => setLoading(false))
  }, [])

  const startUpdate = (o) => setUpdating(prev => ({
    ...prev,
    [o.id]: { status: o.status, note: '', courier_name: '', tracking_number: '' },
  }))
  const cancelUpdate = (id) => setUpdating(prev => {
    const n = { ...prev }; delete n[id]; return n
  })
  const setField = (id, field, val) => setUpdating(prev => ({
    ...prev, [id]: { ...prev[id], [field]: val },
  }))

  const handleStatus = async (id) => {
    const draft = updating[id]
    if (!draft) return
    try {
      await updateOrderStatus(id, {
        status:          draft.status,
        note:            draft.note,
        courier_name:    draft.courier_name,
        tracking_number: draft.tracking_number,
      })
      setOrders(prev => prev.map(o => o.id === id ? { ...o, status: draft.status } : o))
      setMsg({ type: 'success', text: `Order #${id} updated to ${draft.status}` })
      cancelUpdate(id)
    } catch {
      setMsg({ type: 'error', text: 'Failed to update order status.' })
    }
    setTimeout(() => setMsg(null), 3000)
  }

  if (loading) return <Spinner />

  return (
    <div className="admin-layout">
      <AdminSidebar active="orders" />
      <div className="admin-content">
        <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>Orders ({orders.length})</h2>
        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
        <div className="card">
          <div className="table-wrap">
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
                    {updating[o.id] ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, minWidth: 210 }}>
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
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      </div>
    </div>
  )
}
