import { useEffect, useState } from 'react'
import { getContacts, resolveContact } from '../../api/contact'
import AdminSidebar from '../../components/AdminSidebar'
import Spinner from '../../components/Spinner'

const FILTERS = [
  { label: 'All',      value: '' },
  { label: 'New',      value: 'new' },
  { label: 'Resolved', value: 'resolved' },
]

export default function AdminContacts() {
  const [messages, setMessages] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [filter,   setFilter]   = useState('')
  const [msg,      setMsg]      = useState(null)

  const flash = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 3500)
  }

  const load = (f) => {
    setLoading(true)
    getContacts(f).then(r => setMessages(r.data.messages)).finally(() => setLoading(false))
  }
  useEffect(() => { load(filter) }, [filter])

  const handleResolve = async (id) => {
    try {
      await resolveContact(id)
      flash('success', `Message #${id} marked resolved.`)
      load(filter)
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to resolve.')
    }
  }

  const newCount = messages.filter(m => m.status === 'new').length

  return (
    <div className="admin-layout">
      <AdminSidebar active="contacts" />

      <div className="admin-content">
        <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 24 }}>
          Contact Messages
          {newCount > 0 && (
            <span style={{ fontSize: 15, color: 'var(--color-text-soft)', fontFamily: 'var(--font-body)', fontWeight: 400, marginLeft: 10 }}>
              ({newCount} new)
            </span>
          )}
        </h2>

        {msg && <div className={`alert alert-${msg.type}`} style={{ marginBottom: 16 }}>{msg.text}</div>}

        <div style={{ display: 'flex', gap: 8, marginBottom: 24 }}>
          {FILTERS.map(f => (
            <button key={f.value}
              className={`btn btn-sm ${filter === f.value ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setFilter(f.value)}>
              {f.label}
            </button>
          ))}
        </div>

        {loading ? <Spinner /> : (
          <>
            {messages.map(m => (
              <div key={m.id} className={`contact-msg-card${m.status === 'resolved' ? ' resolved' : ''}`}>
                <div className="contact-msg-meta">
                  <strong style={{ fontSize: 'var(--fs-sm)', color: 'var(--color-text)' }}>
                    #{m.id} — {m.name}
                  </strong>
                  <span>{m.email}</span>
                  {m.order_number && <span>Order: #{m.order_number}</span>}
                  <span className={`status-badge badge-${m.category.toLowerCase().replace(/ /g, '_')}`}
                    style={{ background: '#f3f4f6', color: '#374151' }}>
                    {m.category}
                  </span>
                  <span className={`status-badge badge-${m.status}`}>{m.status}</span>
                  <span style={{ marginLeft: 'auto' }}>
                    {new Date(m.created_at).toLocaleDateString('en-IN', {
                      day: 'numeric', month: 'short', year: 'numeric',
                    })}
                  </span>
                </div>
                <div className="contact-msg-body">{m.message}</div>
                {m.status === 'new' && (
                  <button className="btn btn-outline btn-sm" onClick={() => handleResolve(m.id)}>
                    ✓ Mark Resolved
                  </button>
                )}
              </div>
            ))}

            {messages.length === 0 && (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <div className="empty-title">No messages</div>
                <p className="empty-text">
                  No contact messages{filter ? ` with status "${filter}"` : ''}.
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
