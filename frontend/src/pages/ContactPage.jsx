import { useEffect, useState } from 'react'
import { useAuth }             from '../context/AuthContext'
import { submitContact }       from '../api/contact'
import { WHATSAPP_URL }        from '../config'

const CATEGORIES = ['Return issue', 'Product issue', 'Order issue', 'Other']

export default function ContactPage() {
  const { user } = useAuth()
  const [form, setForm] = useState({
    name: '', email: '', order_number: '', category: '', message: '', website: '',
  })
  const [busy, setBusy] = useState(false)
  const [msg,  setMsg]  = useState(null)

  useEffect(() => {
    if (user) {
      setForm(prev => ({ ...prev, name: user.name || '', email: user.email || '' }))
    }
  }, [user])

  const set = (field, value) => setForm(prev => ({ ...prev, [field]: value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setBusy(true)
    setMsg(null)
    try {
      const r = await submitContact(form)
      setMsg({ type: 'success', text: r.data.message })
      setForm(prev => ({ ...prev, order_number: '', category: '', message: '' }))
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.error || 'Something went wrong. Please try again.' })
    } finally { setBusy(false) }
  }

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 960, paddingTop: 40, paddingBottom: 60 }}>

        <h1 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 8 }}>
          Contact Us
        </h1>
        <p style={{ color: 'var(--color-text-soft)', marginBottom: 36, fontSize: 'var(--fs-sm)' }}>
          Koi problem hai? Hamein batayein — hum 24 ghante mein jawab denge.
        </p>

        <div className="contact-layout">

          {/* Left — Form */}
          <div>
            <div className="card" style={{ padding: 32 }}>
              {msg && (
                <div className={`alert alert-${msg.type}`} style={{ marginBottom: 20 }}>
                  {msg.text}
                </div>
              )}
              <form onSubmit={handleSubmit}>
                {/* Honeypot — hidden from real users */}
                <input
                  name="website"
                  value={form.website}
                  onChange={e => set('website', e.target.value)}
                  style={{ display: 'none' }}
                  tabIndex={-1}
                  autoComplete="off"
                  aria-hidden="true"
                />

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                  <div>
                    <label className="form-label">Name *</label>
                    <input className="form-input" placeholder="Your name"
                      value={form.name} onChange={e => set('name', e.target.value)} required />
                  </div>
                  <div>
                    <label className="form-label">Email *</label>
                    <input className="form-input" type="email" placeholder="you@example.com"
                      value={form.email} onChange={e => set('email', e.target.value)} required />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
                  <div>
                    <label className="form-label">Order Number <span style={{ fontWeight: 400, color: 'var(--color-text-soft)' }}>(optional)</span></label>
                    <input className="form-input" placeholder="e.g. 42"
                      value={form.order_number} onChange={e => set('order_number', e.target.value)} />
                  </div>
                  <div>
                    <label className="form-label">Category *</label>
                    <select className="form-select" value={form.category}
                      onChange={e => set('category', e.target.value)} required>
                      <option value="">Select a category</option>
                      {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                    </select>
                  </div>
                </div>

                <div style={{ marginBottom: 24 }}>
                  <label className="form-label">Message *</label>
                  <textarea className="form-input" rows={5}
                    placeholder="Please describe your issue in detail..."
                    value={form.message} onChange={e => set('message', e.target.value)} required />
                </div>

                <button className="btn btn-primary" type="submit" disabled={busy}
                  style={{ width: '100%', padding: '14px' }}>
                  {busy ? 'Sending...' : 'Send Message'}
                </button>
              </form>
            </div>
          </div>

          {/* Right — WhatsApp + Info */}
          <div>
            <div className="contact-sidebar-card">
              <h3>💬 WhatsApp pe baat karein</h3>
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-soft)', lineHeight: 1.7, marginBottom: 20 }}>
                Photo ke saath problem dikhana chahte hain? WhatsApp pe seedha message karein — hum jaldi reply karenge.
              </p>
              <a className="whatsapp-btn" href={WHATSAPP_URL} target="_blank" rel="noopener noreferrer">
                <span style={{ fontSize: 20 }}>💬</span>
                WhatsApp pe bhejo
              </a>
            </div>

            <div className="contact-sidebar-card">
              <h3 style={{ fontSize: 15 }}>Response time</h3>
              <ul style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-soft)', lineHeight: 2.2, paddingLeft: 18 }}>
                <li>Form reply: 24 ghante ke andar</li>
                <li>WhatsApp: same day (typically)</li>
                <li>Mon–Sat: 9 AM – 7 PM IST</li>
              </ul>
            </div>

            <div className="contact-sidebar-card">
              <h3 style={{ fontSize: 15 }}>Return chahiye?</h3>
              <p style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text-soft)', lineHeight: 1.7 }}>
                Agar order deliver hua hai aur 7 din se kam hue hain, seedha{' '}
                <a href="/orders" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>My Orders</a>{' '}
                se return request karo.
              </p>
            </div>
          </div>

        </div>
      </div>
    </div>
  )
}
