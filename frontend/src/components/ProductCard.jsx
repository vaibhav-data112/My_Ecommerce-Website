import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { toggleWishlist } from '../api/wishlist'

const SPICE_EMOJI = { 'Whole Spices': '🌿', 'Ground Spices': '🟡', 'Spice Blends': '🫙', 'Organic': '🌱', 'Salt': '🧂', 'Chilli': '🌶️' }

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
      <button
        className={`wishlist-btn${inWishlist ? ' wishlist-btn--filled' : ''}`}
        onClick={handleWishlist}
        title={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
      >
        ♥
      </button>

      {product.image_url
        ? <img
            src={product.image_url.startsWith('http') ? product.image_url : `/static/${product.image_url}`}
            alt={product.name}
            className="product-card-img"
          />
        : <div className="product-card-placeholder">{SPICE_EMOJI[product.category] || '🌶'}</div>
      }

      <div className="product-card-body">
        <span className="product-category-tag">{product.category}</span>
        <div className="product-card-name">{product.name}</div>

        {product.avg_rating && (
          <div className="rating-row">
            <span className="star">★</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--color-star)' }}>{Number(product.avg_rating).toFixed(1)}</span>
          </div>
        )}

        <div className="product-card-price">₹{product.price}</div>

        {product.stock > 0 && (
          <button className="btn btn-cart btn-full btn-sm" style={{ marginTop: 12 }} onClick={handleAddToCart}>
            Add to Cart
          </button>
        )}
      </div>
    </Link>
  )
}
