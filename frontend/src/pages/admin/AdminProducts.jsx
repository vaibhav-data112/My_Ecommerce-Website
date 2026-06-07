import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProducts, addProduct, deleteProduct } from '../../api/admin'
import Spinner from '../../components/Spinner'

const CATEGORIES = ['Whole Spices', 'Ground Spices', 'Spice Blends', 'Organic']

export default function AdminProducts() {
  const [products, setProducts] = useState([])
  const [loading, setLoading]   = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [msg, setMsg]           = useState(null)
  const [form, setForm]         = useState({ name: '', description: '', price: '', stock: '', category: CATEGORIES[0], image_url: '' })
  const [submitting, setSubmitting] = useState(false)

  const load = () => {
    setLoading(true)
    getProducts().then(r => setProducts(r.data.products)).finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setMsg(null)
    const fd = new FormData()
    Object.entries(form).forEach(([k, v]) => fd.append(k, v))
    const fileInput = document.getElementById('product-img')
    if (fileInput?.files[0]) fd.append('image_file', fileInput.files[0])
    try {
      await addProduct(fd)
      setMsg({ type: 'success', text: 'Product added!' })
      setShowForm(false)
      setForm({ name: '', description: '', price: '', stock: '', category: CATEGORIES[0], image_url: '' })
      load()
    } catch (err) {
      setMsg({ type: 'error', text: err.response?.data?.error || 'Failed to add product' })
    } finally { setSubmitting(false) }
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete "${name}"?`)) return
    await deleteProduct(id)
    setProducts(prev => prev.filter(p => p.id !== id))
    setMsg({ type: 'success', text: `"${name}" deleted.` })
  }

  if (loading) return <Spinner />

  return (
    <div className="admin-layout">
      <aside className="admin-sidebar">
        <div style={{ padding: '0 20px 20px', fontFamily: 'var(--font-head)', color: 'var(--brown)', fontSize: 18, fontWeight: 700 }}>
          🌶 Admin
        </div>
        <Link to="/admin"          className="admin-nav-link">Dashboard</Link>
        <Link to="/admin/products" className="admin-nav-link active">Products</Link>
        <Link to="/admin/orders"   className="admin-nav-link">Orders</Link>
        <Link to="/"               className="admin-nav-link">← Back to Store</Link>
      </aside>
      <div className="admin-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)' }}>Products</h2>
          <button className="btn btn-primary" onClick={() => setShowForm(v => !v)}>
            {showForm ? 'Cancel' : '+ Add Product'}
          </button>
        </div>

        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {showForm && (
          <div className="card" style={{ padding: 24, marginBottom: 28 }}>
            <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 20 }}>Add New Product</h3>
            <form onSubmit={handleAdd}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div className="form-group">
                  <label className="form-label">Product Name *</label>
                  <input className="form-input" required value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Category *</label>
                  <select className="form-select" value={form.category} onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
                    {CATEGORIES.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label">Price (₹) *</label>
                  <input type="number" step="0.01" min="0" className="form-input" required value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Stock *</label>
                  <input type="number" min="0" className="form-input" required value={form.stock} onChange={e => setForm(f => ({ ...f, stock: e.target.value }))} />
                </div>
                <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                  <label className="form-label">Description</label>
                  <textarea className="form-input" rows={3} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label className="form-label">Image URL (optional)</label>
                  <input className="form-input" value={form.image_url} onChange={e => setForm(f => ({ ...f, image_url: e.target.value }))} placeholder="https://..." />
                </div>
                <div className="form-group">
                  <label className="form-label">Upload Image (optional)</label>
                  <input id="product-img" type="file" accept="image/*" className="form-input" style={{ padding: '6px 10px' }} />
                </div>
              </div>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? 'Adding...' : 'Add Product'}
              </button>
            </form>
          </div>
        )}

        <div className="card">
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Price</th>
                <th>Stock</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.map(p => (
                <tr key={p.id}>
                  <td style={{ fontWeight: 500 }}>{p.name}</td>
                  <td><span style={{ background: 'var(--beige)', padding: '2px 10px', borderRadius: 20, fontSize: 12 }}>{p.category}</span></td>
                  <td>₹{p.price}</td>
                  <td style={{ color: p.stock === 0 ? 'var(--danger)' : 'var(--success)' }}>{p.stock}</td>
                  <td>
                    <button className="btn btn-danger btn-sm" onClick={() => handleDelete(p.id, p.name)}>Delete</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
