import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getFeatured } from '../api/products'
import ProductCard from '../components/ProductCard'
import Spinner from '../components/Spinner'

const CATEGORIES = [
  { name: 'Whole Spices',  icon: '🌿', desc: 'Jeera, kali mirch, laung & more' },
  { name: 'Ground Spices', icon: '🟡', desc: 'Haldi, mirchi, dhaniya powder' },
  { name: 'Spice Blends',  icon: '🫙', desc: 'Garam masala, chaat masala & more' },
  { name: 'Organic',       icon: '🌱', desc: 'Certified organic & natural' },
  { name: 'Salt',          icon: '🧂', desc: 'Rock salt, black salt & more' },
  { name: 'Chilli',        icon: '🌶️', desc: 'Kashmiri, Byadgi, Guntur' },
]

const WHY_KARVII = [
  { icon: '🏆', title: 'Premium Quality',  desc: 'Sourced from certified farms across India' },
  { icon: '📦', title: 'Fresh & Pure',     desc: 'Packed to preserve maximum aroma and flavour' },
  { icon: '🚀', title: 'Fast Delivery',    desc: 'Pan-India delivery with careful packaging' },
  { icon: '🌿', title: 'No Additives',     desc: '100% natural, no artificial colours or preservatives' },
]

export default function HomePage() {
  const [products, setProducts] = useState([])
  const [loading, setLoading]   = useState(true)

  useEffect(() => {
    getFeatured()
      .then(r => setProducts(r.data.featured_products))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  return (
    <>
      {/* Offer Banner */}
      <div className="offer-banner">
        🌿 Free Shipping above ₹799
        <span>|</span>
        Pan-India Delivery
        <span>|</span>
        100% Natural & Pure
      </div>

      {/* Hero */}
      <section className="hero">
        <div className="container">
          <div className="hero-eyebrow">Premium Indian Spices</div>
          <h1 className="hero-title">
            Pure Spices,<br /><span>Authentic Flavours</span>
          </h1>
          <p className="hero-subtitle">
            Carefully sourced from the finest farms across India. From smoky whole peppercorns
            to vibrant Kashmiri chilli — bring real flavour to your kitchen.
          </p>
          <div className="hero-btns">
            <Link to="/products" className="btn btn-primary btn-lg">Shop Now</Link>
            <Link to="/products?category=Organic" className="btn btn-lg btn-hero-outline">Organic Range</Link>
          </div>
        </div>
      </section>

      {/* Categories */}
      <section style={{ marginBottom: 60 }}>
        <div className="container">
          <h2 className="section-title">Shop by Category</h2>
          <p className="section-subtitle">Explore our full range of authentic Indian spices</p>
          <div className="category-grid">
            {CATEGORIES.map(c => (
              <Link
                key={c.name}
                to={`/products?category=${encodeURIComponent(c.name)}`}
                className="category-card"
              >
                <div className="category-icon">{c.icon}</div>
                <div className="category-name">{c.name}</div>
                <div className="category-desc">{c.desc}</div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section style={{ marginBottom: 60 }}>
        <div className="container">
          <h2 className="section-title">Featured Products</h2>
          <p className="section-subtitle">Our most loved spices, handpicked for you</p>
          {loading ? <Spinner /> : (
            <div className="products-grid">
              {products.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          )}
          <div style={{ textAlign: 'center', marginTop: 32 }}>
            <Link to="/products" className="btn btn-outline btn-lg">View All Products</Link>
          </div>
        </div>
      </section>

      {/* Why Karvii */}
      <section style={{ background: 'var(--color-surface-warm)', padding: '64px 0' }}>
        <div className="container">
          <h2 className="section-title" style={{ textAlign: 'center', marginBottom: 40 }}>Why Karvii?</h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 32, textAlign: 'center' }}>
            {WHY_KARVII.map(f => (
              <div key={f.title}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>{f.icon}</div>
                <div style={{ fontFamily: 'var(--font-head)', fontSize: 17, color: 'var(--color-primary-dark)', marginBottom: 6 }}>{f.title}</div>
                <p style={{ fontSize: 13, color: 'var(--color-text-soft)', lineHeight: 1.7 }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
