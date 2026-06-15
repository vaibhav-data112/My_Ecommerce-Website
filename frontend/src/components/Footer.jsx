import { Link } from 'react-router-dom'

const TRUST = [
  { icon: '🌿', title: '100% Natural', sub: 'No additives or preservatives' },
  { icon: '🚜', title: 'Farm Sourced', sub: 'Direct from Indian farmers' },
  { icon: '🚚', title: 'Free Delivery', sub: 'On orders above ₹499' },
  { icon: '↩', title: '7-Day Returns', sub: 'Hassle-free return policy' },
]

export default function Footer() {
  return (
    <footer className="footer">

      {/* Trust strip */}
      <div className="footer-trust">
        {TRUST.map(t => (
          <div key={t.title} className="footer-trust-item">
            <span>{t.icon}</span>
            <div>
              <strong>{t.title}</strong>
              <small>{t.sub}</small>
            </div>
          </div>
        ))}
      </div>

      {/* Main grid */}
      <div className="footer-main">
        <div className="container">
          <div className="footer-grid">

            {/* Brand */}
            <div>
              <div className="footer-brand">🌿 Karvii Spices</div>
              <p className="footer-tagline">
                Authentic Indian spices, carefully sourced and packed to bring the true
                flavours of India to your kitchen. Farm-fresh, no additives, always pure.
              </p>
              <div className="footer-social" style={{ marginTop: 20 }}>
                <a href="#" title="WhatsApp" aria-label="WhatsApp">💬</a>
                <a href="#" title="Instagram" aria-label="Instagram">📸</a>
                <a href="#" title="YouTube" aria-label="YouTube">▶</a>
              </div>
            </div>

            {/* Shop */}
            <div>
              <div className="footer-heading">Shop</div>
              <ul className="footer-links">
                <li><Link to="/products">All Spices</Link></li>
                <li><Link to="/products?category=Whole+Spices">Whole Spices</Link></li>
                <li><Link to="/products?category=Ground+Spices">Ground Spices</Link></li>
                <li><Link to="/products?category=Spice+Blends">Spice Blends</Link></li>
                <li><Link to="/products?category=Organic">Organic</Link></li>
              </ul>
            </div>

            {/* Account */}
            <div>
              <div className="footer-heading">Account</div>
              <ul className="footer-links">
                <li><Link to="/account">My Account</Link></li>
                <li><Link to="/orders">My Orders</Link></li>
                <li><Link to="/wishlist">Wishlist</Link></li>
                <li><Link to="/cart">Cart</Link></li>
                <li><Link to="/signup">Sign Up</Link></li>
              </ul>
            </div>

            {/* Help */}
            <div>
              <div className="footer-heading">Help & Info</div>
              <ul className="footer-links">
                <li><Link to="/products">Browse Products</Link></li>
                <li><a href="mailto:hello@karvii.in">Contact Us</a></li>
                <li><span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 'var(--fs-sm)' }}>Shipping Policy</span></li>
                <li><span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 'var(--fs-sm)' }}>Returns Policy</span></li>
                <li><span style={{ color: 'rgba(255,255,255,0.5)', fontSize: 'var(--fs-sm)' }}>Privacy Policy</span></li>
              </ul>
            </div>

          </div>

          <div className="footer-bottom">
            <span>© {new Date().getFullYear()} Karvii Spices. Crafted with ❤️ in India.</span>
            <span>Pure Spices · Farm to Table · No Additives</span>
          </div>
        </div>
      </div>

    </footer>
  )
}
