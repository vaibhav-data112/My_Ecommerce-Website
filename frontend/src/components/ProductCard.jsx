import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { toggleWishlist } from '../api/wishlist'

const SPICE_EMOJI = { 'Whole Spices': '🌿', 'Ground Spices': '🟡', 'Spice Blends': '🫙', 'Organic': '🌱' }

export default function ProductCard({ product, wishlistIds = new Set(), onWishlistChange }) {
  const { user }      = useAuth()
  const { addToCart } = useCart()

  const handleAddToCart = async (e) => {
    e.preventDefault()
    if (!user) { window.location.href = '/login'; return }
    await addToCart(product.id, 1)
  }

  const handleWishlist = async (e) => {
    e.preventDefault()
    if (!user) { window.location.href = '/login'; return }
    const r = await toggleWishlist({ product_id: product.id })
    onWishlistChange?.(product.id, r.data.in_wishlist)
  }

  const inWishlist = wishlistIds.has ? wishlistIds.has(product.id) : product.in_wishlist

  return (
    <Link to={`/products/${product.id}`} className="product-card" style={{ display: 'block' }}>
      {product.stock === 0 && <span className="oos-badge">Out of Stock</span>}
      <button className="wishlist-btn" onClick={handleWishlist} title={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}>
        {inWishlist ? '❤️' : '🤍'}
      </button>
      {product.image_url
        ? <img src={`/static/${product.image_url}`} alt={product.name} className="product-card-img" />
        : <div className="product-card-placeholder">{SPICE_EMOJI[product.category] || '🌶'}</div>
      }
      <div className="product-card-body">
        <div className="product-card-category">{product.category}</div>
        <div className="product-card-name">{product.name}</div>
        <div className="product-card-footer">
          <span className="product-card-price">₹{product.price}</span>
          {product.avg_rating && (
            <span className="product-rating">
              <span className="star">★</span> {Number(product.avg_rating).toFixed(1)}
            </span>
          )}
        </div>
        {product.stock > 0 && (
          <button className="btn btn-brown btn-full btn-sm" style={{ marginTop: 10 }} onClick={handleAddToCart}>
            Add to Cart
          </button>
        )}
      </div>
    </Link>
  )
}
