import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, getProfile, updateProfile, deleteAvatar } from '../api/account'
import { useAuth } from '../context/AuthContext'
import Spinner from '../components/Spinner'

export default function AccountPage() {
  const { user, setUser } = useAuth()
  const [tab, setTab]     = useState('profile')
  const [data, setData]   = useState(null)
  const [loading, setLoading]     = useState(true)
  const [form, setForm]           = useState({ name: '', phone: '' })
  const [msg, setMsg]             = useState(null)
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    getDashboard()
      .then(r => {
        setData(r.data)
        setForm({ name: r.data.user.name || '', phone: r.data.user.phone || '' })
      })
      .finally(() => setLoading(false))
  }, [])

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('phone', form.phone)
    const fileInput = document.getElementById('avatar-input')
    if (fileInput?.files[0]) fd.append('avatar', fileInput.files[0])
    try {
      const r = await updateProfile(fd)
      setData(prev => ({ ...prev, user: r.data.user }))
      setUser(prev => ({ ...prev, name: r.data.user.name, avatar: r.data.user.avatar }))
      setMsg({ type: 'success', text: r.data.message })
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.error || 'Update failed' })
    } finally { setSubmitting(false) }
  }

  const handleDeleteAvatar = async () => {
    await deleteAvatar()
    setData(prev => ({ ...prev, user: { ...prev.user, avatar: null } }))
    setUser(prev => ({ ...prev, avatar: null }))
    setMsg({ type: 'success', text: 'Profile photo removed.' })
  }

  if (loading) return <Spinner />
  if (!data) return null

  const u = data.user

  return (
    <div className="page">
      <div className="container">
        <div className="account-layout">
          {/* Sidebar */}
          <div className="card account-nav">
            {u.avatar && <img src={`/static/${u.avatar}`} alt="avatar" style={{ width: 64, height: 64, borderRadius: '50%', objectFit: 'cover', marginBottom: 12 }} />}
            <div style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', fontWeight: 600, marginBottom: 4 }}>{u.name}</div>
            <div style={{ fontSize: 12, color: 'var(--text-soft)', marginBottom: 20 }}>{u.email}</div>
            <button className={`account-nav-link${tab === 'profile' ? ' active' : ''}`} onClick={() => setTab('profile')}>Profile</button>
            <Link to="/orders" className="account-nav-link">My Orders ({data.order_count})</Link>
            <Link to="/wishlist" className="account-nav-link">Wishlist ({data.wishlist_count})</Link>
          </div>

          {/* Content */}
          <div>
            {tab === 'profile' && (
              <div className="card" style={{ padding: 28 }}>
                <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 24 }}>Edit Profile</h2>
                {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}
                <form onSubmit={handleProfileUpdate}>
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input className="form-input" required value={form.name}
                      onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Phone (optional)</label>
                    <input className="form-input" value={form.phone}
                      onChange={e => setForm(f => ({ ...f, phone: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Profile Photo</label>
                    <input id="avatar-input" type="file" accept="image/jpg,image/jpeg,image/png,image/webp" className="form-input" style={{ padding: '6px 10px' }} />
                    {u.avatar && (
                      <button type="button" className="btn btn-danger btn-sm" style={{ marginTop: 8 }} onClick={handleDeleteAvatar}>
                        Remove Photo
                      </button>
                    )}
                  </div>
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? 'Saving...' : 'Save Changes'}
                  </button>
                </form>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
