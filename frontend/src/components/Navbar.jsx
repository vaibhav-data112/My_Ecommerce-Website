import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'

export default function Navbar() {
  const { user, logout }  = useAuth()
  const { cartCount }     = useCart()
  const navigate          = useNavigate()
  const [open, setOpen]   = useState(false)

  const handleLogout = async () => {
    setOpen(false)
    await logout()
    navigate('/login')
  }

  return (
    <nav className="navbar">
      <div className="container navbar-inner">
        <Link to="/" className="navbar-brand">
          <div className="brand-icon">🌿</div>
          Karvii Spices
        </Link>

        <div className="navbar-links">
          <Link to="/products" className="navbar-link">Shop</Link>

          {user ? (
            <>
              <Link to="/wishlist" className="navbar-link">♡ Wishlist</Link>
              <Link to="/orders"   className="navbar-link">Orders</Link>
              {user.is_admin && <Link to="/admin" className="navbar-link">Admin</Link>}
              <Link to="/cart" className="cart-btn">
                🛒 Cart
                {cartCount > 0 && <span className="cart-badge">{cartCount}</span>}
              </Link>
              <div className="user-menu">
                <button className="user-btn" onClick={() => setOpen(v => !v)}>
                  <span className="avatar-circle">{user.name.charAt(0).toUpperCase()}</span>
                  {user.name.split(' ')[0]}
                </button>
                {open && (
                  <div className="user-dropdown">
                    <Link to="/account" onClick={() => setOpen(false)}>My Account</Link>
                    <Link to="/orders"  onClick={() => setOpen(false)}>My Orders</Link>
                    <hr />
                    <button onClick={handleLogout}>Logout</button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login"  className="navbar-link">Login</Link>
              <Link to="/signup" className="btn btn-cart btn-sm">Sign Up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
