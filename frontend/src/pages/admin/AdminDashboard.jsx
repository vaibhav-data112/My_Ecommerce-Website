import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard } from '../../api/admin'
import AdminSidebar from '../../components/AdminSidebar'
import Spinner from '../../components/Spinner'

export default function AdminDashboard() {
  const [data, setData]   = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard().then(r => setData(r.data)).finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  return (
    <div className="admin-layout">
      <AdminSidebar active="dashboard" />
      <div className="admin-content">
        <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 28 }}>Dashboard</h2>
        <div className="stats-grid">
          <div className="card stat-card">
            <div className="stat-number">{data?.product_count ?? 0}</div>
            <div className="stat-label">Products</div>
          </div>
          <div className="card stat-card">
            <div className="stat-number">{data?.order_count ?? 0}</div>
            <div className="stat-label">Orders</div>
          </div>
          <div className="card stat-card">
            <div className="stat-number">₹{data?.revenue?.toFixed(0) ?? 0}</div>
            <div className="stat-label">Revenue</div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <Link to="/admin/products" className="btn btn-primary">Manage Products</Link>
          <Link to="/admin/orders"   className="btn btn-outline">View Orders</Link>
        </div>
      </div>
    </div>
  )
}
