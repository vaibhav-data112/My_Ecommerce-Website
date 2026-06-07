import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getProduct, addReview, editReview, deleteReview } from '../api/products'
import { toggleWishlist } from '../api/wishlist'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import Spinner from '../components/Spinner'

const stars = n => '★'.repeat(n) + '☆'.repeat(5 - n)

export default function ProductDetailPage() {
  const { id }        = useParams()
  const { user }      = useAuth()
  const { addToCart } = useCart()
  const [data, setData]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [qty, setQty]         = useState(1)
  const [msg, setMsg]         = useState(null)
  const [rating, setRating]   = useState(5)
  const [comment, setComment] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const load = () => {
    setLoading(true)
    getProduct(id).then(r => setData(r.data)).finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [id])

  const handleAddToCart = async () => {
    if (!user) { window.location.href = '/login'; return }
    const r = await addToCart(data.product.id, qty)
    setMsg({ type: r.success ? 'success' : 'error', text: r.message })
    setTimeout(() => setMsg(null), 3000)
  }

  const handleWishlist = async () => {
    if (!user) { window.location.href = '/login'; return }
    const r = await toggleWishlist({ product_id: data.product.id })
    setData(prev => ({ ...prev, in_wishlist: r.data.in_wishlist }))
  }

  const handleReview = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      await addReview(id, { rating, comment })
      load()
      setComment('')
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.error || 'Failed to submit review' })
    } finally { setSubmitting(false) }
  }

  const handleDeleteReview = async (reviewId) => {
    if (!confirm('Delete this review?')) return
    await deleteReview(reviewId)
    load()
  }

  if (loading) return <Spinner />
  if (!data)   return <div className="page container"><p>Product not found.</p></div>

  const { product, reviews, avg_rating, review_count, user_review, can_review, in_wishlist } = data

  return (
    <div className="page">
      <div className="container">
        <p style={{ marginBottom: 20, fontSize: 13, color: 'var(--text-soft)' }}>
          <Link to="/">Home</Link> / <Link to="/products">Products</Link> / {product.name}
        </p>

        <div className="detail-layout">
          {/* Image */}
          <div>
            {product.image_url
              ? <img src={`/static/${product.image_url}`} alt={product.name} className="detail-img" />
              : <div className="detail-placeholder">🌶</div>
            }
          </div>

          {/* Info */}
          <div>
            <div className="detail-category">{product.category}</div>
            <h1 className="detail-name">{product.name}</h1>
            {avg_rating && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, fontSize: 14 }}>
                <span style={{ color: 'var(--star)' }}>{stars(Math.round(avg_rating))}</span>
                <span style={{ color: 'var(--text-soft)' }}>{Number(avg_rating).toFixed(1)} ({review_count} review{review_count !== 1 ? 's' : ''})</span>
              </div>
            )}
            <div className="detail-price">₹{product.price}</div>
            <p className="detail-desc">{product.description}</p>
            <div className={`detail-stock${product.stock === 0 ? ' out' : ''}`}>
              {product.stock > 0 ? `✓ In Stock (${product.stock} available)` : '✗ Out of Stock'}
            </div>

            {product.stock > 0 && (
              <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16, flexWrap: 'wrap' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <label style={{ fontSize: 13, fontWeight: 500 }}>Qty:</label>
                  <input type="number" min={1} max={product.stock} value={qty}
                    onChange={e => setQty(Math.min(product.stock, Math.max(1, parseInt(e.target.value) || 1)))}
                    className="qty-input" />
                </div>
                <button className="btn btn-brown btn-lg" onClick={handleAddToCart}>Add to Cart</button>
              </div>
            )}

            <button className="btn btn-outline btn-sm" onClick={handleWishlist}>
              {in_wishlist ? '❤️ Remove from Wishlist' : '🤍 Add to Wishlist'}
            </button>

            {msg && <div className={`alert alert-${msg.type}`} style={{ marginTop: 16 }}>{msg.text}</div>}
          </div>
        </div>

        {/* Reviews */}
        <div style={{ marginTop: 48 }}>
          <h2 className="section-title">Customer Reviews</h2>
          {avg_rating ? (
            <div className="rating-summary" style={{ maxWidth: 240, marginBottom: 28 }}>
              <div className="rating-big">{Number(avg_rating).toFixed(1)}</div>
              <div className="rating-stars-big">{stars(Math.round(avg_rating))}</div>
              <div className="rating-count">{review_count} review{review_count !== 1 ? 's' : ''}</div>
            </div>
          ) : null}

          {reviews.length === 0 && !can_review && (
            <div className="empty-state" style={{ padding: '30px 0' }}>
              <div className="empty-icon">💬</div>
              <p className="empty-text">No reviews yet. Be the first to review!</p>
            </div>
          )}

          {reviews.map(r => (
            <div key={r.id} className="review-card">
              <div className="review-header">
                <span className="review-author">{r.user_name || 'Customer'}</span>
                <span className="review-date">{new Date(r.created_at).toLocaleDateString()}</span>
              </div>
              <div className="review-stars">{stars(r.rating)}</div>
              {r.comment && <p className="review-comment">{r.comment}</p>}
              {user && user.id === String(r.user_id) && (
                <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
                  <button className="btn btn-danger btn-sm" onClick={() => handleDeleteReview(r.id)}>Delete</button>
                </div>
              )}
            </div>
          ))}

          {/* Write a review */}
          {user && can_review && !user_review && (
            <div className="card" style={{ padding: 24, marginTop: 24 }}>
              <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 16 }}>Write a Review</h3>
              <form onSubmit={handleReview}>
                <div className="form-group">
                  <label className="form-label">Rating</label>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {[1, 2, 3, 4, 5].map(n => (
                      <button key={n} type="button" onClick={() => setRating(n)}
                        style={{ fontSize: 24, background: 'none', border: 'none', color: n <= rating ? 'var(--star)' : 'var(--border)' }}>
                        ★
                      </button>
                    ))}
                  </div>
                </div>
                <div className="form-group">
                  <label className="form-label">Comment (optional)</label>
                  <textarea className="form-input" value={comment} onChange={e => setComment(e.target.value)} placeholder="Share your experience..." />
                </div>
                <button type="submit" className="btn btn-primary" disabled={submitting}>
                  {submitting ? 'Submitting...' : 'Submit Review'}
                </button>
              </form>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
