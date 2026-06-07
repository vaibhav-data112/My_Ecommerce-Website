import { createContext, useContext, useEffect, useState } from 'react'
import { getMe, login as apiLogin, signup as apiSignup, logout as apiLogout } from '../api/auth'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMe()
      .then(r => setUser(r.data.user))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password, remember = false) => {
    const r = await apiLogin({ email, password, remember })
    setUser(r.data.user)
    return r.data.user
  }

  const signup = async (name, email, password, confirm_password) => {
    const r = await apiSignup({ name, email, password, confirm_password })
    setUser(r.data.user)
    return r.data.user
  }

  const logout = async () => {
    await apiLogout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
