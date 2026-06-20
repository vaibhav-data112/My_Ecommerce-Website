import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { CartProvider } from './context/CartContext'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import AuthGuard from './components/AuthGuard'
import AdminGuard from './components/AdminGuard'

import HomePage          from './pages/HomePage'
import ProductsPage      from './pages/ProductsPage'
import ProductDetailPage from './pages/ProductDetailPage'
import CartPage          from './pages/CartPage'
import CheckoutPage      from './pages/CheckoutPage'
import PaymentPage       from './pages/PaymentPage'
import OrdersPage        from './pages/OrdersPage'
import OrderDetailPage   from './pages/OrderDetailPage'
import LoginPage         from './pages/LoginPage'
import SignupPage        from './pages/SignupPage'
import WishlistPage      from './pages/WishlistPage'
import AccountPage       from './pages/AccountPage'
import AdminDashboard    from './pages/admin/AdminDashboard'
import AdminProducts     from './pages/admin/AdminProducts'
import AdminOrders       from './pages/admin/AdminOrders'
import AdminReturns      from './pages/admin/AdminReturns'
import AdminContacts       from './pages/admin/AdminContacts'
import ContactPage         from './pages/ContactPage'
import ShippingPolicyPage  from './pages/ShippingPolicyPage'
import ReturnsPolicyPage   from './pages/ReturnsPolicyPage'
import PrivacyPolicyPage   from './pages/PrivacyPolicyPage'
import NotFoundPage        from './pages/NotFoundPage'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <Navbar />
          <Routes>
            <Route path="/"             element={<HomePage />} />
            <Route path="/products"     element={<ProductsPage />} />
            <Route path="/products/:id" element={<ProductDetailPage />} />
            <Route path="/login"        element={<LoginPage />} />
            <Route path="/signup"       element={<SignupPage />} />
            <Route path="/contact"          element={<ContactPage />} />
            <Route path="/shipping-policy"  element={<ShippingPolicyPage />} />
            <Route path="/returns-policy"   element={<ReturnsPolicyPage />} />
            <Route path="/privacy-policy"   element={<PrivacyPolicyPage />} />

            <Route path="/cart"        element={<AuthGuard><CartPage /></AuthGuard>} />
            <Route path="/checkout"    element={<AuthGuard><CheckoutPage /></AuthGuard>} />
            <Route path="/payment/:id" element={<AuthGuard><PaymentPage /></AuthGuard>} />
            <Route path="/orders"      element={<AuthGuard><OrdersPage /></AuthGuard>} />
            <Route path="/orders/:id"  element={<AuthGuard><OrderDetailPage /></AuthGuard>} />
            <Route path="/wishlist"    element={<AuthGuard><WishlistPage /></AuthGuard>} />
            <Route path="/account"     element={<AuthGuard><AccountPage /></AuthGuard>} />

            <Route path="/admin"          element={<AdminGuard><AdminDashboard /></AdminGuard>} />
            <Route path="/admin/products" element={<AdminGuard><AdminProducts /></AdminGuard>} />
            <Route path="/admin/orders"   element={<AdminGuard><AdminOrders /></AdminGuard>} />
            <Route path="/admin/returns"   element={<AdminGuard><AdminReturns /></AdminGuard>} />
            <Route path="/admin/contacts"  element={<AdminGuard><AdminContacts /></AdminGuard>} />

            <Route path="*" element={<NotFoundPage />} />
          </Routes>
          <Footer />
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
