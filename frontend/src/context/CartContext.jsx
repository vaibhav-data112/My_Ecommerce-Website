import { createContext, useContext, useEffect, useState } from 'react'
import { getCart, addToCart as apiAdd, updateCart as apiUpdate, removeFromCart as apiRemove } from '../api/cart'
import { useAuth } from './AuthContext'

const CartContext = createContext(null)

export function CartProvider({ children }) {
  const { user }              = useAuth()
  const [cartCount, setCartCount] = useState(0)
  const [cartItems, setCartItems] = useState([])

  const fetchCart = async () => {
    if (!user) { setCartCount(0); setCartItems([]); return }
    try {
      const r = await getCart()
      setCartItems(r.data.items)
      setCartCount(r.data.cart_count)
    } catch {
      setCartCount(0)
      setCartItems([])
    }
  }

  useEffect(() => { fetchCart() }, [user])

  const addToCart = async (product_id, quantity = 1) => {
    const r = await apiAdd({ product_id, quantity })
    setCartCount(r.data.cart_count)
    return r.data
  }

  const updateCart = async (product_id, quantity) => {
    const r = await apiUpdate({ product_id, quantity })
    setCartCount(r.data.cart_count)
    await fetchCart()
    return r.data
  }

  const removeFromCart = async (product_id) => {
    const r = await apiRemove({ product_id })
    setCartCount(r.data.cart_count)
    setCartItems(prev => prev.filter(i => i.product_id !== product_id))
    return r.data
  }

  return (
    <CartContext.Provider value={{ cartCount, cartItems, fetchCart, addToCart, updateCart, removeFromCart }}>
      {children}
    </CartContext.Provider>
  )
}

export const useCart = () => useContext(CartContext)
