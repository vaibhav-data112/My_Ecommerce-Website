import { Link } from 'react-router-dom'

const NAV = [
  { to: '/admin',          label: 'Dashboard',        key: 'dashboard' },
  { to: '/admin/products', label: 'Products',          key: 'products'  },
  { to: '/admin/orders',   label: 'Orders',            key: 'orders'    },
  { to: '/admin/returns',  label: 'Returns',           key: 'returns'   },
  { to: '/admin/contacts', label: 'Contact Messages',  key: 'contacts'  },
  { to: '/admin/coupons',  label: 'Coupons',           key: 'coupons'   },
]

export default function AdminSidebar({ active }) {
  return (
    <aside className="admin-sidebar">
      <div style={{ padding: '0 20px 20px', fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, fontWeight: 700 }}>
        🌶 Admin
      </div>
      {NAV.map(({ to, label, key }) => (
        <Link key={key} to={to}
          className={`admin-nav-link${active === key ? ' active' : ''}`}>
          {label}
        </Link>
      ))}
      <Link to="/" className="admin-nav-link">← Back to Store</Link>
    </aside>
  )
}
