import { useEffect, useState } from 'react'
import AdminSidebar from '../../components/AdminSidebar'
import Spinner from '../../components/Spinner'
import { getCoupons, createCoupon, toggleCoupon } from '../../api/admin'

const EMPTY_FORM = {
  code: '',
  discount_type: 'percentage',
  discount_value: '',
  min_order_amount: '',
  max_uses: '',
  expiry_date: '',
}

export default function AdminCoupons() {
  const [coupons,    setCoupons]    = useState([])
  const [loading,    setLoading]    = useState(true)
  const [form,       setForm]       = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [msg,        setMsg]        = useState(null)

  const flash = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 4000)
  }

  const load = () => {
    setLoading(true)
    getCoupons()
      .then(r => setCoupons(r.data.coupons))
      .catch(() => flash('error', 'Failed to load coupons.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  const handleChange = e => {
    const { name, value } = e.target
    setForm(f => ({ ...f, [name]: value }))
  }

  const handleCreate = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await createCoupon({
        code:             form.code.trim().toUpperCase(),
        discount_type:    form.discount_type,
        discount_value:   parseFloat(form.discount_value),
        min_order_amount: parseFloat(form.min_order_amount) || 0,
        max_uses:         parseInt(form.max_uses) || 0,
        expiry_date:      form.expiry_date || null,
      })
      flash('success', `Coupon "${form.code.toUpperCase()}" created.`)
      setForm(EMPTY_FORM)
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to create coupon.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleToggle = async (coupon) => {
    try {
      await toggleCoupon(coupon.id)
      flash('success', `Coupon "${coupon.code}" ${coupon.is_active ? 'deactivated' : 'activated'}.`)
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to toggle coupon.')
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="admin-layout">
      <AdminSidebar active="coupons" />
      <div className="admin-content">
        <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>
          Coupon Codes
        </h2>

        {msg && (
          <div className={`alert alert-${msg.type}`} style={{ marginBottom: 20 }}>
            {msg.text}
          </div>
        )}

        {/* Create Form */}
        <div className="card" style={{ padding: 24, marginBottom: 32 }}>
          <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 18, fontSize: 18 }}>
            Create New Coupon
          </h3>
          <form onSubmit={handleCreate}>
            <div className="form-grid-2">
              <div className="form-group">
                <label className="form-label">Code *</label>
                <input
                  className="form-input"
                  name="code"
                  value={form.code}
                  onChange={handleChange}
                  placeholder="SAVE10"
                  required
                  style={{ textTransform: 'uppercase' }}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Discount Type *</label>
                <select className="form-input" name="discount_type" value={form.discount_type} onChange={handleChange}>
                  <option value="percentage">Percentage (%)</option>
                  <option value="fixed">Fixed Amount (₹)</option>
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">
                  {form.discount_type === 'percentage' ? 'Discount %' : 'Discount ₹'} *
                </label>
                <input
                  className="form-input"
                  name="discount_value"
                  type="number"
                  min="0.01"
                  max={form.discount_type === 'percentage' ? 100 : undefined}
                  step="0.01"
                  value={form.discount_value}
                  onChange={handleChange}
                  placeholder={form.discount_type === 'percentage' ? '10' : '50'}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Min Order Amount (₹)</label>
                <input
                  className="form-input"
                  name="min_order_amount"
                  type="number"
                  min="0"
                  step="1"
                  value={form.min_order_amount}
                  onChange={handleChange}
                  placeholder="0 = no minimum"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Max Uses</label>
                <input
                  className="form-input"
                  name="max_uses"
                  type="number"
                  min="0"
                  step="1"
                  value={form.max_uses}
                  onChange={handleChange}
                  placeholder="0 = unlimited"
                />
              </div>
              <div className="form-group">
                <label className="form-label">Expiry Date</label>
                <input
                  className="form-input"
                  name="expiry_date"
                  type="date"
                  value={form.expiry_date}
                  onChange={handleChange}
                />
              </div>
            </div>
            <button type="submit" className="btn btn-primary" style={{ marginTop: 8 }} disabled={submitting}>
              {submitting ? 'Creating...' : '+ Create Coupon'}
            </button>
          </form>
        </div>

        {/* Coupon List */}
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)' }}>
            <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, margin: 0 }}>
              All Coupons ({coupons.length})
            </h3>
          </div>
          {coupons.length === 0 ? (
            <div className="empty-state" style={{ padding: '40px 0' }}>
              <div className="empty-icon">🎟️</div>
              <div className="empty-title">No coupons yet</div>
              <p className="empty-text">Create your first coupon above.</p>
            </div>
          ) : (
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Code</th>
                    <th>Type</th>
                    <th>Value</th>
                    <th>Min Order</th>
                    <th>Used / Max</th>
                    <th>Expiry</th>
                    <th>Status</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {coupons.map(c => (
                    <tr key={c.id}>
                      <td><strong style={{ fontFamily: 'monospace', fontSize: 13 }}>{c.code}</strong></td>
                      <td style={{ textTransform: 'capitalize', fontSize: 13 }}>{c.discount_type}</td>
                      <td>
                        {c.discount_type === 'percentage'
                          ? `${c.discount_value}%`
                          : `₹${c.discount_value}`}
                      </td>
                      <td>{c.min_order_amount > 0 ? `₹${c.min_order_amount}` : '—'}</td>
                      <td>{c.used_count} / {c.max_uses === 0 ? '∞' : c.max_uses}</td>
                      <td style={{ fontSize: 13 }}>{c.expiry_date || '—'}</td>
                      <td>
                        <span className={`status-badge ${c.is_active ? 'badge-paid' : 'badge-cancelled'}`}>
                          {c.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </td>
                      <td>
                        <button
                          className={`btn btn-sm ${c.is_active ? 'btn-outline' : 'btn-primary'}`}
                          onClick={() => handleToggle(c)}
                        >
                          {c.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
