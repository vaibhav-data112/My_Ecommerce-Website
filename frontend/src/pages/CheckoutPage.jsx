import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getCheckoutInfo, placeOrder } from '../api/orders'
import { validateCoupon } from '../api/coupons'
import { getAddresses } from '../api/account'
import { useCart } from '../context/CartContext'
import Spinner from '../components/Spinner'

export default function CheckoutPage() {
  const navigate          = useNavigate()
  const { fetchCart }     = useCart()
  const [info, setInfo]   = useState(null)
  const [loading, setLoading]   = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [errors, setErrors]     = useState({})
  const [form, setForm]         = useState({
    shipping_name: '', shipping_phone: '', shipping_address: '',
  })

  const [savedAddresses, setSavedAddresses]   = useState([])
  const [selectedAddrId, setSelectedAddrId]   = useState(null)
  const [paymentMethod, setPaymentMethod]     = useState('razorpay')

  const [couponCode,    setCouponCode]    = useState('')
  const [couponApplied, setCouponApplied] = useState(null)
  const [couponError,   setCouponError]   = useState(null)
  const [couponBusy,    setCouponBusy]    = useState(false)

  useEffect(() => {
    Promise.all([
      getCheckoutInfo().catch(() => null),
      getAddresses().catch(() => ({ data: { addresses: [] } })),
    ]).then(([checkoutRes, addrRes]) => {
      if (!checkoutRes) { navigate('/cart'); return }
      setInfo(checkoutRes.data)
      const addrs = addrRes?.data?.addresses || []
      setSavedAddresses(addrs)
      const def = addrs.find(a => a.is_default) || addrs[0]
      if (def) applyAddress(def)
    }).finally(() => setLoading(false))
  }, [])

  function applyAddress(addr) {
    setSelectedAddrId(addr.id)
    setForm({
      shipping_name:    addr.full_name,
      shipping_phone:   addr.phone,
      shipping_address: `${addr.address_line}, ${addr.city}, ${addr.state} - ${addr.pincode}`,
    })
  }

  function selectNewAddress() {
    setSelectedAddrId(null)
    setForm({ shipping_name: '', shipping_phone: '', shipping_address: '' })
  }

  const handleApplyCoupon = async () => {
    const trimmed = couponCode.trim().toUpperCase()
    if (!trimmed) return
    setCouponBusy(true)
    setCouponError(null)
    setCouponApplied(null)
    try {
      const r = await validateCoupon(trimmed, info.subtotal)
      if (r.data.valid) {
        setCouponApplied({
          code:             trimmed,
          discount_amount:  r.data.discount_amount,
          new_shipping_fee: r.data.new_shipping_fee,
          new_total:        r.data.new_total,
          message:          r.data.message,
        })
      } else {
        setCouponError(r.data.error)
      }
    } catch (err) {
      setCouponError(err.response?.data?.error || 'Could not validate coupon.')
    } finally {
      setCouponBusy(false)
    }
  }

  const handleRemoveCoupon = () => {
    setCouponApplied(null)
    setCouponCode('')
    setCouponError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setErrors({})
    try {
      const payload = {
        ...form,
        payment_method: paymentMethod,
        ...(couponApplied ? { coupon_code: couponApplied.code } : {}),
      }
      const r = await placeOrder(payload)
      await fetchCart()
      if (paymentMethod === 'cod') {
        navigate(`/orders/${r.data.order_id}`)
      } else {
        navigate(`/payment/${r.data.order_id}`)
      }
    } catch (err) {
      if (err.response?.data?.errors) setErrors(err.response.data.errors)
      else setErrors({ general: err.response?.data?.error || 'Something went wrong' })
    } finally { setSubmitting(false) }
  }

  if (loading) return <Spinner />
  if (!info)   return null

  const displaySubtotal = info.subtotal
  const displayDiscount = couponApplied ? couponApplied.discount_amount : 0
  const displayShipping = couponApplied ? couponApplied.new_shipping_fee : info.shipping_fee
  const displayTotal    = couponApplied ? couponApplied.new_total : info.total

  return (
    <div className="page">
      <div className="container">
        <h1 className="section-title" style={{ marginBottom: 28 }}>Checkout</h1>
        <div className="checkout-layout">
          <form onSubmit={handleSubmit}>
            <div className="card" style={{ padding: 28 }}>
              <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 20 }}>
                Shipping Details
              </h3>
              {errors.general && <div className="alert alert-error">{errors.general}</div>}

              {/* Saved address selector */}
              {savedAddresses.length > 0 && (
                <div className="saved-addresses-section">
                  <div className="saved-addresses-label">Saved Addresses</div>
                  <div className="address-cards">
                    {savedAddresses.map(addr => (
                      <div
                        key={addr.id}
                        className={`address-card${selectedAddrId === addr.id ? ' selected' : ''}`}
                        onClick={() => applyAddress(addr)}
                      >
                        <div className="address-card-name">
                          {addr.full_name}
                          {addr.is_default ? <span className="address-card-badge">Default</span> : null}
                        </div>
                        <div className="address-card-detail">
                          {addr.phone} &bull; {addr.address_line}, {addr.city}, {addr.state} - {addr.pincode}
                        </div>
                      </div>
                    ))}
                    {selectedAddrId && (
                      <button type="button" className="btn btn-outline btn-sm" onClick={selectNewAddress}>
                        + Use a different address
                      </button>
                    )}
                  </div>
                  {savedAddresses.length > 0 && !selectedAddrId && (
                    <div className="or-divider">Or enter a new address</div>
                  )}
                </div>
              )}

              {/* Manual form — show when no address selected */}
              {!selectedAddrId && (
                <>
                  <div className="form-group">
                    <label className="form-label">Full Name *</label>
                    <input
                      className={`form-input${errors.shipping_name ? ' error' : ''}`}
                      value={form.shipping_name}
                      onChange={e => setForm(f => ({ ...f, shipping_name: e.target.value }))}
                    />
                    {errors.shipping_name && <div className="form-error">{errors.shipping_name}</div>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">Phone Number *</label>
                    <input
                      className={`form-input${errors.shipping_phone ? ' error' : ''}`}
                      value={form.shipping_phone}
                      onChange={e => setForm(f => ({ ...f, shipping_phone: e.target.value }))}
                    />
                    {errors.shipping_phone && <div className="form-error">{errors.shipping_phone}</div>}
                  </div>
                  <div className="form-group">
                    <label className="form-label">Delivery Address *</label>
                    <textarea
                      className={`form-input${errors.shipping_address ? ' error' : ''}`}
                      rows={4}
                      value={form.shipping_address}
                      onChange={e => setForm(f => ({ ...f, shipping_address: e.target.value }))}
                      placeholder="House/Flat, Street, Area, City, State, PIN"
                    />
                    {errors.shipping_address && <div className="form-error">{errors.shipping_address}</div>}
                  </div>
                </>
              )}

              {/* Payment Method */}
              <div className="form-group" style={{ marginTop: 20 }}>
                <label className="form-label">Payment Method</label>
                <div className="payment-method-group">
                  <div
                    className={`payment-method-option${paymentMethod === 'razorpay' ? ' selected' : ''}`}
                    onClick={() => setPaymentMethod('razorpay')}
                  >
                    <input type="radio" name="payment" value="razorpay" readOnly checked={paymentMethod === 'razorpay'} />
                    <div>
                      <div className="payment-method-label">💳 Pay Online</div>
                      <div className="payment-method-sub">UPI, Card, Net Banking via Razorpay</div>
                    </div>
                  </div>
                  <div
                    className={`payment-method-option${paymentMethod === 'cod' ? ' selected' : ''}`}
                    onClick={() => setPaymentMethod('cod')}
                  >
                    <input type="radio" name="payment" value="cod" readOnly checked={paymentMethod === 'cod'} />
                    <div>
                      <div className="payment-method-label">
                        💵 Cash on Delivery
                        <span className="cod-badge">COD</span>
                      </div>
                      <div className="payment-method-sub">Pay when your order arrives</div>
                    </div>
                  </div>
                </div>
              </div>

              <button type="submit" className="btn btn-primary btn-full btn-lg" style={{ marginTop: 8 }} disabled={submitting}>
                {submitting ? 'Placing Order...' : paymentMethod === 'cod' ? 'Place Order (Pay on Delivery)' : 'Proceed to Payment'}
              </button>
            </div>
          </form>

          {/* Order Summary + Coupon */}
          <div>
            <div className="card" style={{ padding: 24, marginBottom: 16 }}>
              <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 16 }}>
                Order Summary
              </h3>
              {info.items?.map(i => (
                <div
                  key={i.product_id}
                  style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, marginBottom: 10 }}
                >
                  <span style={{ color: 'var(--text-soft)' }}>{i.name} × {i.quantity}</span>
                  <span>₹{(i.price * i.quantity).toFixed(2)}</span>
                </div>
              ))}
              <hr style={{ borderColor: 'var(--border)', margin: '14px 0' }} />

              <div className="summary-row">
                <span>Subtotal</span>
                <span>₹{displaySubtotal?.toFixed(2)}</span>
              </div>

              {couponApplied && (
                <div className="summary-discount">
                  <span>Discount ({couponApplied.code})</span>
                  <span>−₹{displayDiscount.toFixed(2)}</span>
                </div>
              )}

              <div className="summary-row">
                <span>Shipping</span>
                <span>
                  {displayShipping === 0
                    ? <span style={{ color: 'var(--success)' }}>Free</span>
                    : `₹${displayShipping}`}
                </span>
              </div>

              <div className="summary-total">
                <span>Total</span>
                <span>₹{displayTotal?.toFixed(2)}</span>
              </div>
            </div>

            {/* Coupon Section */}
            <div className="card" style={{ padding: 20 }}>
              <h4 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-soft)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                Have a coupon?
              </h4>

              {!couponApplied ? (
                <>
                  <div className="coupon-row">
                    <input
                      className="form-input"
                      placeholder="Enter code (e.g. SAVE10)"
                      value={couponCode}
                      onChange={e => setCouponCode(e.target.value.toUpperCase())}
                      onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), handleApplyCoupon())}
                    />
                    <button
                      type="button"
                      className="btn btn-outline"
                      onClick={handleApplyCoupon}
                      disabled={couponBusy || !couponCode.trim()}
                    >
                      {couponBusy ? '...' : 'Apply'}
                    </button>
                  </div>
                  {couponError && <div className="coupon-error">{couponError}</div>}
                </>
              ) : (
                <div className="coupon-applied">
                  <span>{couponApplied.message}</span>
                  <button
                    type="button"
                    className="btn btn-sm btn-outline"
                    onClick={handleRemoveCoupon}
                    style={{ fontSize: 12, padding: '4px 10px' }}
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
