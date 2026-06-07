import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Spinner from './Spinner'

export default function AdminGuard({ children }) {
  const { user, loading } = useAuth()
  if (loading)          return <Spinner />
  if (!user)            return <Navigate to="/login" replace />
  if (!user.is_admin)   return <Navigate to="/" replace />
  return children
}
