import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useCart } from '../context/CartContext'
import Spinner from '../components/Spinner'

export default function CartPage() {
  const { cartItems, fetchCart, updateCart, removeFromCart } = useCart()
  const navigate = useNavigate()
  const loading  = cartItems === null

  useEffect(() => { fetchCart() }, [])

  const subtotal    = cartItems?.reduce((s, i) => s + i.price * i.quantity, 0) || 0
  const shippingFee = subtotal >= 500 ? 0 : 40
  const total       = subtotal + shippingFee

  if (loading) return <Spinner />

  if (!cartItems?.length) return (
    <div className="page container">
      <div className="empty-state">
        <div className="empty-icon">🛒</div>
        <div className="empty-title">Your cart is empty</div>
        <p className="empty-text">Add some spices to get started!</p>
        <Link to="/products" className="btn btn-primary">Shop Now</Link>
      </div>
    </div>
  )

  return (
    <div className="page">
      <div className="container">
        <h1 className="section-title" style={{ marginBottom: 28 }}>Your Cart</h1>
        <div className="cart-layout">
          {/* Items */}
          <div className="card" style={{ padding: 0 }}>
            {cartItems.map(item => (
              <div key={item.product_id} className="cart-item">
                {item.image_url
                  ? <img src={`/static/${item.image_url}`} alt={item.name} className="cart-item-img" />
                  : <div className="cart-item-img" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 30 }}>🌶</div>
                }
                <div style={{ flex: 1 }}>
                  <div className="cart-item-name">{item.name}</div>
                  <div className="cart-item-price">₹{item.price} each</div>
                  <div className="cart-item-actions">
                    <input type="number" min={1} max={item.stock} value={item.quantity} className="qty-input"
                      onChange={e => {
                        const v = Math.min(item.stock, Math.max(1, parseInt(e.target.value) || 1))
                        updateCart(item.product_id, v)
                      }} />
                    <button className="btn btn-danger btn-sm" onClick={() => removeFromCart(item.product_id)}>Remove</button>
                  </div>
                </div>
                <div style={{ fontWeight: 600, color: 'var(--brown)', minWidth: 70, textAlign: 'right' }}>
                  ₹{(item.price * item.quantity).toFixed(2)}
                </div>
              </div>
            ))}
          </div>

          {/* Summary */}
          <div className="card" style={{ padding: 24 }}>
            <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 20 }}>Order Summary</h3>
            <div className="summary-row"><span>Subtotal</span><span>₹{subtotal.toFixed(2)}</span></div>
            <div className="summary-row">
              <span>Shipping</span>
              <span>{shippingFee === 0 ? <span style={{ color: 'var(--success)' }}>Free</span> : `₹${shippingFee}`}</span>
            </div>
            {subtotal < 500 && <p style={{ fontSize: 12, color: 'var(--text-soft)', marginBottom: 10 }}>Add ₹{(500 - subtotal).toFixed(2)} more for free shipping</p>}
            <div className="summary-total"><span>Total</span><span>₹{total.toFixed(2)}</span></div>
            <button className="btn btn-primary btn-full btn-lg" style={{ marginTop: 20 }} onClick={() => navigate('/checkout')}>
              Proceed to Checkout
            </button>
            <Link to="/products" className="btn btn-outline btn-full" style={{ marginTop: 10 }}>Continue Shopping</Link>
          </div>
        </div>
      </div>
    </div>
  )
}
