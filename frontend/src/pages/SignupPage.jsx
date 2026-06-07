import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function SignupPage() {
  const { signup }      = useAuth()
  const navigate        = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', password: '', confirm_password: '' })
  const [error, setError]         = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await signup(form.name, form.email, form.password, form.confirm_password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.error || 'Signup failed')
    } finally { setSubmitting(false) }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">🌶 Karvii Spices</div>
        <h2 className="auth-title">Create your account</h2>
        <p className="auth-subtitle">Join thousands of happy customers</p>

        {error && <div className="alert alert-error">{error}</div>}

        <a href="/login/google" className="google-btn">
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" width={18} alt="Google" />
          Sign up with Google
        </a>
        <div className="auth-divider"><span>or</span></div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Full Name</label>
            <input type="text" className="form-input" required value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input type="email" className="form-input" required value={form.email}
              onChange={e => setForm(f => ({ ...f, email: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Password (min 8 characters)</label>
            <input type="password" className="form-input" required minLength={8} value={form.password}
              onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Confirm Password</label>
            <input type="password" className="form-input" required value={form.confirm_password}
              onChange={e => setForm(f => ({ ...f, confirm_password: e.target.value }))} />
          </div>
          <button type="submit" className="btn btn-brown btn-full btn-lg" disabled={submitting}>
            {submitting ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  )
}
