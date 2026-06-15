import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getProducts, getProduct, addProduct, editProduct, deleteProduct } from '../../api/admin'
import Spinner from '../../components/Spinner'

const EMPTY_FORM = { name: '', description: '', price: '', stock: '', category: 'Whole Spices', image_url: '' }

function AdminSidebar({ active }) {
  return (
    <aside className="admin-sidebar">
      <div style={{ padding: '0 20px 20px', fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, fontWeight: 700 }}>
        🌶 Admin
      </div>
      <Link to="/admin"          className={`admin-nav-link${active === 'dashboard' ? ' active' : ''}`}>Dashboard</Link>
      <Link to="/admin/products" className={`admin-nav-link${active === 'products'  ? ' active' : ''}`}>Products</Link>
      <Link to="/admin/orders"   className={`admin-nav-link${active === 'orders'    ? ' active' : ''}`}>Orders</Link>
      <Link to="/"               className="admin-nav-link">← Back to Store</Link>
    </aside>
  )
}

function ProductForm({ title, form, setForm, categories, onSubmit, onCancel, submitting, imageInputId }) {
  return (
    <div className="card" style={{ padding: 24, marginBottom: 28 }}>
      <h3 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 20 }}>{title}</h3>
      <form onSubmit={onSubmit}>
        <div className="form-grid-2">
          <div className="form-group">
            <label className="form-label">Product Name *</label>
            <input className="form-input" required value={form.name}
              onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Category *</label>
            <select className="form-select" value={form.category}
              onChange={e => setForm(f => ({ ...f, category: e.target.value }))}>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Price (₹) *</label>
            <input type="number" step="0.01" min="0" className="form-input" required
              value={form.price} onChange={e => setForm(f => ({ ...f, price: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Stock *</label>
            <input type="number" min="0" className="form-input" required
              value={form.stock} onChange={e => setForm(f => ({ ...f, stock: e.target.value }))} />
          </div>
          <div className="form-group" style={{ gridColumn: '1 / -1' }}>
            <label className="form-label">Description</label>
            <textarea className="form-input" rows={3}
              value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
          </div>
          <div className="form-group">
            <label className="form-label">Image URL (optional)</label>
            <input className="form-input" value={form.image_url}
              onChange={e => setForm(f => ({ ...f, image_url: e.target.value }))}
              placeholder="https://..." />
          </div>
          <div className="form-group">
            <label className="form-label">Upload Image (optional)</label>
            {form.image_url && (
              <div style={{ marginBottom: 8 }}>
                <img
                  src={form.image_url.startsWith('http') ? form.image_url : `/static/${form.image_url}`}
                  alt="Current"
                  style={{ width: 64, height: 64, objectFit: 'contain', borderRadius: 6, border: '1px solid var(--color-border)', padding: 4, display: 'block' }}
                />
                <small style={{ color: 'var(--color-text-soft)', fontSize: 12 }}>Current image — upload a new file to replace</small>
              </div>
            )}
            <input id={imageInputId} type="file" accept="image/*"
              className="form-input" style={{ padding: '6px 10px' }} />
          </div>
        </div>
        <div style={{ display: 'flex', gap: 12, marginTop: 4 }}>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Saving...' : 'Save'}
          </button>
          <button type="button" className="btn btn-outline" onClick={onCancel}>Cancel</button>
        </div>
      </form>
    </div>
  )
}

export default function AdminProducts() {
  const [products,   setProducts]   = useState([])
  const [categories, setCategories] = useState(['Whole Spices', 'Ground Spices', 'Spice Blends', 'Organic'])
  const [loading,    setLoading]    = useState(true)
  const [msg,        setMsg]        = useState(null)

  const [showAdd,     setShowAdd]    = useState(false)
  const [addForm,     setAddForm]    = useState(EMPTY_FORM)
  const [addBusy,     setAddBusy]    = useState(false)

  const [editingId,   setEditingId]  = useState(null)
  const [editForm,    setEditForm]   = useState(EMPTY_FORM)
  const [editBusy,    setEditBusy]   = useState(false)

  const flash = (type, text) => {
    setMsg({ type, text })
    setTimeout(() => setMsg(null), 4000)
  }

  const load = () => {
    setLoading(true)
    getProducts()
      .then(r => {
        setProducts(r.data.products)
        if (r.data.categories?.length) setCategories(r.data.categories)
      })
      .finally(() => setLoading(false))
  }
  useEffect(() => { load() }, [])

  const handleAdd = async (e) => {
    e.preventDefault()
    setAddBusy(true)
    const fd = new FormData()
    Object.entries(addForm).forEach(([k, v]) => fd.append(k, v))
    const file = document.getElementById('add-img')?.files[0]
    if (file) fd.append('image_file', file)
    try {
      await addProduct(fd)
      flash('success', 'Product added!')
      setShowAdd(false)
      setAddForm(EMPTY_FORM)
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to add product.')
    } finally { setAddBusy(false) }
  }

  const startEdit = async (id) => {
    try {
      const r = await getProduct(id)
      const p = r.data.product
      setEditForm({
        name:        p.name        ?? '',
        description: p.description ?? '',
        price:       p.price       ?? '',
        stock:       p.stock       ?? '',
        category:    p.category    ?? categories[0],
        image_url:   p.image_url   ?? '',
      })
      if (r.data.categories?.length) setCategories(r.data.categories)
      setEditingId(id)
      setShowAdd(false)
    } catch {
      flash('error', 'Could not load product.')
    }
  }

  const handleEdit = async (e) => {
    e.preventDefault()
    setEditBusy(true)
    const fd = new FormData()
    Object.entries(editForm).forEach(([k, v]) => fd.append(k, v))
    const file = document.getElementById('edit-img')?.files[0]
    if (file) fd.append('image_file', file)
    try {
      await editProduct(editingId, fd)
      flash('success', 'Product updated!')
      setEditingId(null)
      load()
    } catch (err) {
      flash('error', err.response?.data?.error || 'Failed to update product.')
    } finally { setEditBusy(false) }
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete "${name}"? This cannot be undone.`)) return
    try {
      await deleteProduct(id)
      setProducts(prev => prev.filter(p => p.id !== id))
      flash('success', `"${name}" deleted.`)
    } catch {
      flash('error', 'Failed to delete product.')
    }
  }

  if (loading) return <Spinner />

  return (
    <div className="admin-layout">
      <AdminSidebar active="products" />
      <div className="admin-content">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 12 }}>
          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)' }}>
            Products <span style={{ fontSize: 16, color: 'var(--color-text-soft)', fontFamily: 'var(--font-body)' }}>({products.length})</span>
          </h2>
          <button className="btn btn-primary" onClick={() => { setShowAdd(v => !v); setEditingId(null) }}>
            {showAdd ? 'Cancel' : '+ Add Product'}
          </button>
        </div>

        {msg && <div className={`alert alert-${msg.type}`}>{msg.text}</div>}

        {showAdd && (
          <ProductForm
            title="Add New Product"
            form={addForm}
            setForm={setAddForm}
            categories={categories}
            onSubmit={handleAdd}
            onCancel={() => setShowAdd(false)}
            submitting={addBusy}
            imageInputId="add-img"
          />
        )}

        {editingId && (
          <ProductForm
            title={`Edit: ${editForm.name}`}
            form={editForm}
            setForm={setEditForm}
            categories={categories}
            onSubmit={handleEdit}
            onCancel={() => setEditingId(null)}
            submitting={editBusy}
            imageInputId="edit-img"
          />
        )}

        <div className="card">
          <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Category</th>
                <th>Price</th>
                <th>Stock</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 && (
                <tr><td colSpan={5} style={{ textAlign: 'center', color: 'var(--color-text-soft)', padding: 32 }}>No products yet.</td></tr>
              )}
              {products.map(p => (
                <tr key={p.id} style={{ background: editingId === p.id ? 'var(--color-surface-warm)' : undefined }}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      {p.image_url && (
                        <img
                          src={p.image_url.startsWith('http') ? p.image_url : `/static/${p.image_url}`}
                          alt={p.name}
                          style={{ width: 36, height: 36, objectFit: 'contain', borderRadius: 6, background: 'var(--color-surface-warm)', padding: 2 }}
                        />
                      )}
                      <span style={{ fontWeight: 500 }}>{p.name}</span>
                    </div>
                  </td>
                  <td>
                    <span className="product-category-tag">{p.category}</span>
                  </td>
                  <td style={{ fontWeight: 600, color: 'var(--color-primary-dark)' }}>₹{p.price}</td>
                  <td style={{ color: p.stock === 0 ? 'var(--color-danger)' : 'var(--color-success)', fontWeight: 500 }}>
                    {p.stock === 0 ? 'Out of stock' : p.stock}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button className="btn btn-outline btn-sm" style={{ marginRight: 8 }}
                      onClick={() => startEdit(p.id)}>
                      Edit
                    </button>
                    <button className="btn btn-danger btn-sm"
                      onClick={() => handleDelete(p.id, p.name)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      </div>
    </div>
  )
}
