import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  getDashboard, updateProfile, deleteAvatar,
  getAddresses, addAddress, updateAddress, deleteAddress, setDefaultAddress,
  getSettings, changePassword, updateNotifications,
} from '../api/account'
import { useAuth } from '../context/AuthContext'
import Spinner from '../components/Spinner'

const EMPTY_ADDR = { full_name: '', phone: '', address_line: '', city: '', state: '', pincode: '' }

// ---------------------------------------------------------------------------
// Address form (shared for add + edit)
// ---------------------------------------------------------------------------
function AddressForm({ initial = EMPTY_ADDR, onSave, onCancel, busy }) {
  const [form, setForm] = useState(initial)
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSubmit = (e) => {
    e.preventDefault()
    onSave(form)
  }

  return (
    <form onSubmit={handleSubmit} style={{ marginTop: 16 }}>
      <div className="form-grid-2">
        <div className="form-group">
          <label className="form-label">Full Name *</label>
          <input className="form-input" required value={form.full_name}
            onChange={e => set('full_name', e.target.value)} placeholder="Name on delivery" />
        </div>
        <div className="form-group">
          <label className="form-label">Phone *</label>
          <input className="form-input" required value={form.phone}
            onChange={e => set('phone', e.target.value)} placeholder="10-digit mobile" />
        </div>
        <div className="form-group" style={{ gridColumn: '1 / -1' }}>
          <label className="form-label">Address *</label>
          <input className="form-input" required value={form.address_line}
            onChange={e => set('address_line', e.target.value)} placeholder="House, street, locality" />
        </div>
        <div className="form-group">
          <label className="form-label">City *</label>
          <input className="form-input" required value={form.city}
            onChange={e => set('city', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">State *</label>
          <input className="form-input" required value={form.state}
            onChange={e => set('state', e.target.value)} />
        </div>
        <div className="form-group">
          <label className="form-label">PIN Code *</label>
          <input className="form-input" required value={form.pincode}
            onChange={e => set('pincode', e.target.value)} placeholder="6-digit PIN" />
        </div>
      </div>
      <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
        <button type="submit" className="btn btn-primary" disabled={busy}>
          {busy ? 'Saving…' : 'Save Address'}
        </button>
        <button type="button" className="btn btn-outline" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  )
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function AccountPage() {
  const { user, setUser }       = useAuth()
  const [tab, setTab]           = useState('profile')
  const [data, setData]         = useState(null)
  const [loading, setLoading]   = useState(true)
  const [msg, setMsg]           = useState(null)

  // Profile
  const [form, setForm]             = useState({ name: '', phone: '' })
  const [profileBusy, setProfileBusy] = useState(false)

  // Addresses
  const [addresses, setAddresses]   = useState([])
  const [addrLoading, setAddrLoading] = useState(false)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingAddr, setEditingAddr] = useState(null)
  const [addrBusy, setAddrBusy]     = useState(false)

  // Settings
  const [settings, setSettings]     = useState(null)
  const [pwForm, setPwForm]         = useState({ current_password: '', new_password: '', confirm_password: '' })
  const [pwBusy, setPwBusy]         = useState(false)
  const [notifyBusy, setNotifyBusy] = useState(false)

  const flash = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 4000)
  }

  useEffect(() => {
    getDashboard()
      .then(r => {
        setData(r.data)
        setForm({ name: r.data.user.name || '', phone: r.data.user.phone || '' })
      })
      .finally(() => setLoading(false))
  }, [])

  const switchTab = (t) => {
    setTab(t)
    setMsg(null)
    if (t === 'addresses' && addresses.length === 0) {
      setAddrLoading(true)
      getAddresses().then(r => setAddresses(r.data.addresses)).finally(() => setAddrLoading(false))
    }
    if (t === 'settings' && !settings) {
      getSettings().then(r => setSettings(r.data))
    }
  }

  // ── Profile ──────────────────────────────────────────────────────────────

  const handleProfileUpdate = async (e) => {
    e.preventDefault()
    setProfileBusy(true)
    const fd = new FormData()
    fd.append('name', form.name)
    fd.append('phone', form.phone)
    const fileInput = document.getElementById('avatar-input')
    if (fileInput?.files[0]) fd.append('avatar', fileInput.files[0])
    try {
      const r = await updateProfile(fd)
      setData(prev => ({ ...prev, user: r.data.user }))
      setUser(prev => ({ ...prev, name: r.data.user.name, avatar: r.data.user.avatar }))
      flash('success', r.data.message)
    } catch (err) {
      flash('error', err.response?.data?.error || 'Update failed.')
    } finally { setProfileBusy(false) }
  }

  const handleDeleteAvatar = async () => {
    await deleteAvatar()
    setData(prev => ({ ...prev, user: { ...prev.user, avatar: null } }))
    setUser(prev => ({ ...prev, avatar: null }))
    flash('success', 'Profile photo removed.')
  }

  // ── Addresses ────────────────────────────────────────────────────────────

  const handleAddAddress = async (form) => {
    setAddrBusy(true)
    try {
      const r = await addAddress(form)
      setAddresses(r.data.addresses)
      setShowAddForm(false)
      flash('success', 'Address saved!')
    } catch (err) {
      flash('error', err.response?.data?.error || 'Could not save address.')
    } finally { setAddrBusy(false) }
  }

  const handleEditAddress = async (form) => {
    setAddrBusy(true)
    try {
      await updateAddress(editingAddr.id, form)
      const r = await getAddresses()
      setAddresses(r.data.addresses)
      setEditingAddr(null)
      flash('success', 'Address updated!')
    } catch (err) {
      flash('error', err.response?.data?.error || 'Could not update address.')
    } finally { setAddrBusy(false) }
  }

  const handleDeleteAddress = async (id) => {
    if (!confirm('Remove this address?')) return
    await deleteAddress(id)
    setAddresses(prev => prev.filter(a => a.id !== id))
    flash('success', 'Address removed.')
  }

  const handleSetDefault = async (id) => {
    await setDefaultAddress(id)
    const r = await getAddresses()
    setAddresses(r.data.addresses)
    flash('success', 'Default address updated.')
  }

  // ── Settings ─────────────────────────────────────────────────────────────

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setPwBusy(true)
    try {
      const r = await changePassword(pwForm)
      flash('success', r.data.message)
      setPwForm({ current_password: '', new_password: '', confirm_password: '' })
    } catch (err) {
      flash('error', err.response?.data?.error || 'Password change failed.')
    } finally { setPwBusy(false) }
  }

  const handleNotifyToggle = async (val) => {
    setNotifyBusy(true)
    try {
      await updateNotifications({ notify_email: val })
      setSettings(prev => ({ ...prev, user: { ...prev.user, notify_email: val } }))
      flash('success', 'Notification preference saved.')
    } catch {
      flash('error', 'Could not update preferences.')
    } finally { setNotifyBusy(false) }
  }

  // ── Render ───────────────────────────────────────────────────────────────

  if (loading) return <Spinner />
  if (!data) return null

  const u = data.user

  return (
    <div className="page">
      <div className="container">
        <div className="account-layout">

          {/* Sidebar */}
          <div className="card account-nav">
            {u.avatar
              ? <img src={`/static/${u.avatar}`} alt="avatar"
                  style={{ width: 64, height: 64, borderRadius: '50%', objectFit: 'cover', marginBottom: 12 }} />
              : <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--color-surface-warm)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: 24, marginBottom: 12, color: 'var(--color-primary-dark)' }}>
                  {u.name?.[0]?.toUpperCase()}
                </div>
            }
            <div style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontWeight: 600, marginBottom: 4 }}>{u.name}</div>
            <div style={{ fontSize: 'var(--fs-xs)', color: 'var(--color-text-soft)', marginBottom: 20 }}>{u.email}</div>
            <button className={`account-nav-link${tab === 'profile'   ? ' active' : ''}`} onClick={() => switchTab('profile')}>Profile</button>
            <button className={`account-nav-link${tab === 'addresses' ? ' active' : ''}`} onClick={() => switchTab('addresses')}>Saved Addresses</button>
            <button className={`account-nav-link${tab === 'settings'  ? ' active' : ''}`} onClick={() => switchTab('settings')}>Settings</button>
            <Link to="/orders"   className="account-nav-link">My Orders ({data.order_count})</Link>
            <Link to="/wishlist" className="account-nav-link">Wishlist ({data.wishlist_count})</Link>
          </div>

          {/* Content */}
          <div>
            {msg && <div className={`alert alert-${msg.type}`} style={{ marginBottom: 20 }}>{msg.text}</div>}

            {/* ── Profile tab ─────────────────────────────────────────── */}
            {tab === 'profile' && (
              <div className="card" style={{ padding: 28 }}>
                <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>Edit Profile</h2>
                <form onSubmit={handleProfileUpdate}>
                  <div className="form-group">
                    <label className="form-label">Full Name</label>
                    <input className="form-input" required value={form.name}
                      onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Phone (optional)</label>
                    <input className="form-input" value={form.phone}
                      onChange={e => setForm(f => ({ ...f, phone: e.target.value }))}
                      placeholder="10-digit mobile number" />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Profile Photo</label>
                    <input id="avatar-input" type="file" accept="image/jpg,image/jpeg,image/png,image/webp"
                      className="form-input" style={{ padding: '6px 10px' }} />
                    {u.avatar && (
                      <button type="button" className="btn btn-danger btn-sm" style={{ marginTop: 8 }}
                        onClick={handleDeleteAvatar}>
                        Remove Photo
                      </button>
                    )}
                  </div>
                  <button type="submit" className="btn btn-primary" disabled={profileBusy}>
                    {profileBusy ? 'Saving…' : 'Save Changes'}
                  </button>
                </form>
              </div>
            )}

            {/* ── Addresses tab ───────────────────────────────────────── */}
            {tab === 'addresses' && (
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
                  <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)' }}>Saved Addresses</h2>
                  {!showAddForm && !editingAddr && (
                    <button className="btn btn-primary" onClick={() => setShowAddForm(true)}>+ Add Address</button>
                  )}
                </div>

                {showAddForm && (
                  <div className="card" style={{ padding: 24, marginBottom: 20 }}>
                    <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 4 }}>New Address</h3>
                    <AddressForm
                      onSave={handleAddAddress}
                      onCancel={() => setShowAddForm(false)}
                      busy={addrBusy}
                    />
                  </div>
                )}

                {addrLoading
                  ? <Spinner />
                  : addresses.length === 0 && !showAddForm
                    ? (
                      <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-soft)' }}>
                        No saved addresses yet.
                        <br />
                        <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => setShowAddForm(true)}>
                          Add Your First Address
                        </button>
                      </div>
                    )
                    : addresses.map(addr => (
                      <div key={addr.id} className="card" style={{ padding: 20, marginBottom: 16, borderLeft: addr.is_default ? '3px solid var(--color-primary)' : undefined }}>
                        {editingAddr?.id === addr.id
                          ? (
                            <>
                              <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 4 }}>Edit Address</h3>
                              <AddressForm
                                initial={{ full_name: addr.full_name, phone: addr.phone, address_line: addr.address_line, city: addr.city, state: addr.state, pincode: addr.pincode }}
                                onSave={handleEditAddress}
                                onCancel={() => setEditingAddr(null)}
                                busy={addrBusy}
                              />
                            </>
                          )
                          : (
                            <>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
                                <div>
                                  <div style={{ fontWeight: 600, marginBottom: 2 }}>
                                    {addr.full_name}
                                    {addr.is_default
                                      ? <span style={{ marginLeft: 8, fontSize: 'var(--fs-xs)', background: 'var(--color-primary)', color: '#fff', borderRadius: 4, padding: '2px 8px' }}>Default</span>
                                      : null}
                                  </div>
                                  <div style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-soft)' }}>{addr.phone}</div>
                                  <div style={{ fontSize: 'var(--fs-sm)', marginTop: 6 }}>{addr.address_line}</div>
                                  <div style={{ fontSize: 'var(--fs-sm)' }}>{addr.city}, {addr.state} – {addr.pincode}</div>
                                </div>
                                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                  {!addr.is_default && (
                                    <button className="btn btn-outline btn-sm" onClick={() => handleSetDefault(addr.id)}>
                                      Set Default
                                    </button>
                                  )}
                                  <button className="btn btn-outline btn-sm" onClick={() => { setEditingAddr(addr); setShowAddForm(false) }}>
                                    Edit
                                  </button>
                                  <button className="btn btn-danger btn-sm" onClick={() => handleDeleteAddress(addr.id)}>
                                    Remove
                                  </button>
                                </div>
                              </div>
                            </>
                          )
                        }
                      </div>
                    ))
                }
              </div>
            )}

            {/* ── Settings tab ────────────────────────────────────────── */}
            {tab === 'settings' && (
              <div>
                <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>Settings</h2>

                {!settings
                  ? <Spinner />
                  : (
                    <>
                      {/* Change Password */}
                      <div className="card" style={{ padding: 28, marginBottom: 20 }}>
                        <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 16 }}>Change Password</h3>
                        {settings.is_google_only
                          ? <p style={{ color: 'var(--color-text-soft)', fontSize: 'var(--fs-sm)' }}>
                              You signed in with Google. Password change is not available for Google accounts.
                            </p>
                          : (
                            <form onSubmit={handleChangePassword}>
                              <div className="form-group">
                                <label className="form-label">Current Password</label>
                                <input type="password" className="form-input" required
                                  value={pwForm.current_password}
                                  onChange={e => setPwForm(f => ({ ...f, current_password: e.target.value }))} />
                              </div>
                              <div className="form-group">
                                <label className="form-label">New Password</label>
                                <input type="password" className="form-input" required minLength={8}
                                  value={pwForm.new_password}
                                  onChange={e => setPwForm(f => ({ ...f, new_password: e.target.value }))}
                                  placeholder="At least 8 characters" />
                              </div>
                              <div className="form-group">
                                <label className="form-label">Confirm New Password</label>
                                <input type="password" className="form-input" required
                                  value={pwForm.confirm_password}
                                  onChange={e => setPwForm(f => ({ ...f, confirm_password: e.target.value }))} />
                              </div>
                              <button type="submit" className="btn btn-primary" disabled={pwBusy}>
                                {pwBusy ? 'Updating…' : 'Update Password'}
                              </button>
                            </form>
                          )
                        }
                      </div>

                      {/* Email Notifications */}
                      <div className="card" style={{ padding: 28 }}>
                        <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 16 }}>Notifications</h3>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
                          <input
                            type="checkbox"
                            id="notify-email"
                            checked={!!settings.user?.notify_email}
                            disabled={notifyBusy}
                            onChange={e => handleNotifyToggle(e.target.checked)}
                            style={{ width: 18, height: 18, cursor: 'pointer' }}
                          />
                          <label htmlFor="notify-email" style={{ cursor: 'pointer', fontSize: 'var(--fs-sm)' }}>
                            Receive order updates and offers by email
                          </label>
                        </div>
                      </div>
                    </>
                  )
                }
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
