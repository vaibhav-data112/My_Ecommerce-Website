import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getWishlist, toggleWishlist, wishlistAddToCart } from '../api/wishlist'
import { useCart } from '../context/CartContext'
import Spinner from '../components/Spinner'

export default function WishlistPage() {
  const [items, setItems]     = useState([])
  const [loading, setLoading] = useState(true)
  const { fetchCart }         = useCart()
  const [msg, setMsg]         = useState(null)

  const load = () => {
    setLoading(true)
    getWishlist().then(r => setItems(r.data.items)).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const handleRemove = async (product_id) => {
    await toggleWishlist({ product_id })
    setItems(prev => prev.filter(i => i.id !== product_id))
  }

  const handleAddToCart = async (product_id) => {
    const r = await wishlistAddToCart({ product_id })
    setMsg({ type: r.data.success ? 'success' : 'error', text: r.data.message })
    await fetchCart()
    setTimeout(() => setMsg(null), 3000)
  }

  if (loading) return <Spinner />

  return (
    <div className="page">
      <div className="container">
        <h1 className="section-title" style={{ marginBottom: 28 }}>My Wishlist</h1>
        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {items.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🤍</div>
            <div className="empty-title">Your wishlist is empty</div>
            <p className="empty-text">Save spices you love for later</p>
            <Link to="/products" className="btn btn-primary">Browse Spices</Link>
          </div>
        ) : (
          <div className="products-grid">
            {items.map(item => (
              <div key={item.id} className="product-card">
                <Link to={`/products/${item.id}`}>
                  {item.image_url
                    ? <img src={item.image_url.startsWith('http') ? item.image_url : `/static/${item.image_url}`} alt={item.name} className="product-card-img" />
                    : <div className="product-card-placeholder">🌶</div>
                  }
                  <div className="product-card-body">
                    <div className="product-card-category">{item.category}</div>
                    <div className="product-card-name">{item.name}</div>
                    <div className="product-card-price">₹{item.price}</div>
                  </div>
                </Link>
                <div style={{ padding: '0 14px 14px', display: 'flex', gap: 8 }}>
                  <button className="btn btn-brown btn-sm" style={{ flex: 1 }} onClick={() => handleAddToCart(item.id)}>Add to Cart</button>
                  <button className="btn btn-outline btn-sm" onClick={() => handleRemove(item.id)}>❤️</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
