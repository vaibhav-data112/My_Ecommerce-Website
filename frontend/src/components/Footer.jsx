import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="container">
        <div className="footer-grid">
          <div>
            <div className="footer-brand">🌶 Karvii Spices</div>
            <p className="footer-tagline">
              Authentic Indian spices, carefully sourced and packed to bring the true flavours
              of India to your kitchen.
            </p>
          </div>
          <div>
            <div className="footer-heading">Shop</div>
            <ul className="footer-links">
              <li><Link to="/products?category=Whole+Spices">Whole Spices</Link></li>
              <li><Link to="/products?category=Ground+Spices">Ground Spices</Link></li>
              <li><Link to="/products?category=Spice+Blends">Spice Blends</Link></li>
              <li><Link to="/products?category=Organic">Organic</Link></li>
            </ul>
          </div>
          <div>
            <div className="footer-heading">Account</div>
            <ul className="footer-links">
              <li><Link to="/account">My Account</Link></li>
              <li><Link to="/orders">My Orders</Link></li>
              <li><Link to="/wishlist">Wishlist</Link></li>
              <li><Link to="/cart">Cart</Link></li>
            </ul>
          </div>
        </div>
        <div className="footer-bottom">
          © {new Date().getFullYear()} Karvii Spices. All rights reserved.
        </div>
      </div>
    </footer>
  )
}
