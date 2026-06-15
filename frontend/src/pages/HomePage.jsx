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
]

const WHY_KARVII = [
  { icon: '🏆', title: 'Premium Quality',  desc: 'Sourced from certified farms across India' },
  { icon: '📦', title: 'Fresh & Pure',     desc: 'Packed to preserve maximum aroma and flavour' },
  { icon: '🚀', title: 'Fast Delivery',    desc: 'Pan-India delivery with careful packaging' },
  { icon: '🌿', title: 'No Additives',     desc: '100% natural, no artificial colours or preservatives' },
]

const TESTIMONIALS = [
  {
    stars: 5,
    text: 'The Kashmiri chilli powder is absolutely stunning — deep red colour and mild heat. My curries have never looked or tasted better. Will definitely order again!',
    name: 'Priya Sharma',
    location: 'Mumbai',
    avatar: '👩',
  },
  {
    stars: 5,
    text: 'I\'ve tried many garam masala brands but Karvii\'s blend is in a different league. You can smell the freshness the moment you open the pack. Highly recommend.',
    name: 'Rajesh Kumar',
    location: 'Delhi',
    avatar: '👨',
  },
  {
    stars: 4,
    text: 'Ordered the cumin seeds and turmeric powder. Packaging was excellent and both arrived fresh. The turmeric colour is so vibrant — this is clearly a quality product.',
    name: 'Ananya Nair',
    location: 'Bengaluru',
    avatar: '👩',
  },
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
        🌿 Free Shipping on orders above ₹499
        <span>|</span>
        Pan-India Delivery
        <span>|</span>
        100% Natural &amp; Pure
      </div>

      {/* Hero */}
      <section className="hero">
        <div className="container">
          <div className="hero-grid">
            <div>
              <div className="hero-eyebrow">Premium Indian Spices</div>
              <h1 className="hero-title">
                Pure Spices,<br /><span>Authentic Flavours</span>
              </h1>
              <p className="hero-subtitle">
                Carefully sourced from the finest farms across India. From smoky whole
                peppercorns to vibrant Kashmiri chilli — bring real flavour to your kitchen.
              </p>
              <div className="hero-btns">
                <Link to="/products" className="btn btn-primary btn-lg">Shop Now</Link>
                <Link to="/products?category=Organic" className="btn btn-lg btn-hero-outline">Organic Range</Link>
              </div>
            </div>
            <div>
              <img
                src="https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=600&q=80"
                alt="Colorful Indian spices"
                className="hero-img"
              />
            </div>
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
            <div className="featured-grid">
              {products.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
          )}
          <div style={{ textAlign: 'center', marginTop: 32 }}>
            <Link to="/products" className="btn btn-primary btn-lg">View All Products</Link>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section style={{ background: 'var(--color-surface-warm)', padding: '64px 0', marginBottom: 0 }}>
        <div className="container">
          <h2 className="section-title" style={{ textAlign: 'center' }}>What Our Customers Say</h2>
          <p className="section-subtitle" style={{ textAlign: 'center' }}>Real reviews from real spice lovers</p>
          <div className="testimonials-grid">
            {TESTIMONIALS.map(t => (
              <div key={t.name} className="testimonial-card">
                <div className="testimonial-stars">{'★'.repeat(t.stars)}{'☆'.repeat(5 - t.stars)}</div>
                <p className="testimonial-text">"{t.text}"</p>
                <div className="testimonial-author">
                  <div className="testimonial-avatar">{t.avatar}</div>
                  <div>
                    <div className="testimonial-name">{t.name}</div>
                    <div className="testimonial-location">{t.location}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why Karvii */}
      <section style={{ padding: '64px 0' }}>
        <div className="container">
          <h2 className="section-title" style={{ textAlign: 'center', marginBottom: 40 }}>Why Choose Karvii?</h2>
          <div className="why-grid">
            {WHY_KARVII.map(f => (
              <div key={f.title}>
                <div className="why-icon">{f.icon}</div>
                <div className="why-title">{f.title}</div>
                <p className="why-desc">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </>
  )
}
