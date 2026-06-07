import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCheckoutInfo, placeOrder } from '../api/orders'
import { useCart } from '../context/CartContext'
import Spinner from '../components/Spinner'

export default function CheckoutPage() {
  const navigate          = useNavigate()
  const { fetchCart }     = useCart()
  const [info, setInfo]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors]   = useState({})
  const [form, setForm]       = useState({ shipping_name: '', shipping_phone: '', shipping_address: '' })

  useEffect(() => {
    getCheckoutInfo()
      .then(r => setInfo(r.data))
      .catch(() => navigate('/cart'))
      .finally(() => setLoading(false))
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setErrors({})
    try {
      const r = await placeOrder(form)
      await fetchCart()
      navigate(`/payment/${r.data.order_id}`)
    } catch (err) {
      if (err.response?.data?.errors) setErrors(err.response.data.errors)
      else setErrors({ general: err.response?.data?.error || 'Something went wrong' })
    } finally { setSubmitting(false) }
  }

  if (loading) return <Spinner />
  if (!info)   return null

  return (
    <div className="page">
      <div className="container">
        <h1 className="section-title" style={{ marginBottom: 28 }}>Checkout</h1>
        <div className="checkout-layout">
          <form onSubmit={handleSubmit}>
            <div className="card" style={{ padding: 28 }}>
              <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 20 }}>Shipping Details</h3>
              {errors.general && <div className="alert alert-error">{errors.general}</div>}

              <div className="form-group">
                <label className="form-label">Full Name *</label>
                <input className={`form-input${errors.shipping_name ? ' error' : ''}`} value={form.shipping_name}
                  onChange={e => setForm(f => ({ ...f, shipping_name: e.target.value }))} />
                {errors.shipping_name && <div className="form-error">{errors.shipping_name}</div>}
              </div>
              <div className="form-group">
                <label className="form-label">Phone Number *</label>
                <input className={`form-input${errors.shipping_phone ? ' error' : ''}`} value={form.shipping_phone}
                  onChange={e => setForm(f => ({ ...f, shipping_phone: e.target.value }))} />
                {errors.shipping_phone && <div className="form-error">{errors.shipping_phone}</div>}
              </div>
              <div className="form-group">
                <label className="form-label">Delivery Address *</label>
                <textarea className={`form-input${errors.shipping_address ? ' error' : ''}`} rows={4}
                  value={form.shipping_address} onChange={e => setForm(f => ({ ...f, shipping_address: e.target.value }))}
                  placeholder="House/Flat, Street, Area, City, State, PIN" />
                {errors.shipping_address && <div className="form-error">{errors.shipping_address}</div>}
              </div>
              <button type="submit" className="btn btn-primary btn-full btn-lg" disabled={submitting}>
                {submitting ? 'Placing Order...' : 'Place Order'}
              </button>
            </div>
          </form>

          {/* Order Summary */}
          <div className="card" style={{ padding: 24 }}>
            <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 16 }}>Order Summary</h3>
            {info.items?.map(i => (
              <div key={i.product_id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, marginBottom: 10 }}>
                <span style={{ color: 'var(--text-soft)' }}>{i.name} × {i.quantity}</span>
                <span>₹{(i.price * i.quantity).toFixed(2)}</span>
              </div>
            ))}
            <hr style={{ borderColor: 'var(--border)', margin: '14px 0' }} />
            <div className="summary-row"><span>Subtotal</span><span>₹{info.subtotal?.toFixed(2)}</span></div>
            <div className="summary-row">
              <span>Shipping</span>
              <span>{info.shipping_fee === 0 ? <span style={{ color: 'var(--success)' }}>Free</span> : `₹${info.shipping_fee}`}</span>
            </div>
            <div className="summary-total"><span>Total</span><span>₹{info.total?.toFixed(2)}</span></div>
          </div>
        </div>
      </div>
    </div>
  )
}
