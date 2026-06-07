import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getProducts } from '../api/products'
import ProductCard from '../components/ProductCard'
import Spinner from '../components/Spinner'

const CATEGORIES = ['Whole Spices', 'Ground Spices', 'Spice Blends', 'Organic']

export default function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [data, setData]     = useState(null)
  const [loading, setLoading] = useState(true)
  const [searchInput, setSearchInput] = useState(searchParams.get('q') || '')

  const q        = searchParams.get('q') || ''
  const category = searchParams.get('category') || ''
  const sort     = searchParams.get('sort') || 'newest'
  const page     = parseInt(searchParams.get('page') || '1')

  useEffect(() => {
    setLoading(true)
    getProducts({ q, category, sort, page })
      .then(r => setData(r.data))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [q, category, sort, page])

  const setParam = (key, value) => {
    const p = new URLSearchParams(searchParams)
    if (value) p.set(key, value); else p.delete(key)
    if (key !== 'page') p.delete('page')
    setSearchParams(p)
  }

  const handleSearch = (e) => {
    e.preventDefault()
    setParam('q', searchInput)
  }

  return (
    <div className="page">
      <div className="container">
        <h1 className="section-title">Our Spices</h1>
        <p style={{ color: 'var(--text-soft)', marginBottom: 28, fontSize: 14 }}>
          Authentic spices sourced from the finest farms across India
        </p>

        {/* Search */}
        <form className="search-bar" onSubmit={handleSearch}>
          <input
            className="search-input"
            placeholder="Search spices..."
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
          />
          <button type="submit" className="search-btn">Search</button>
        </form>

        {/* Categories */}
        <div className="category-pills">
          <button className={`category-pill${!category ? ' active' : ''}`} onClick={() => setParam('category', '')}>All</button>
          {CATEGORIES.map(c => (
            <button key={c} className={`category-pill${category === c ? ' active' : ''}`} onClick={() => setParam('category', c)}>{c}</button>
          ))}
        </div>

        {/* Header */}
        <div className="products-header">
          <span className="products-count">{data ? `${data.total} product${data.total !== 1 ? 's' : ''}` : ''}</span>
          <select className="form-select" style={{ width: 'auto' }} value={sort} onChange={e => setParam('sort', e.target.value)}>
            <option value="newest">Newest First</option>
            <option value="price_asc">Price: Low to High</option>
            <option value="price_desc">Price: High to Low</option>
          </select>
        </div>

        {/* Grid */}
        {loading ? <Spinner /> : data && data.products.length > 0 ? (
          <>
            <div className="products-grid">
              {data.products.map(p => <ProductCard key={p.id} product={p} />)}
            </div>
            {data.total_pages > 1 && (
              <div className="pagination">
                <button className="page-btn" disabled={page <= 1} onClick={() => setParam('page', String(page - 1))}>← Prev</button>
                {Array.from({ length: data.total_pages }, (_, i) => i + 1).map(n => (
                  <button key={n} className={`page-btn${n === page ? ' active' : ''}`} onClick={() => setParam('page', String(n))}>{n}</button>
                ))}
                <button className="page-btn" disabled={page >= data.total_pages} onClick={() => setParam('page', String(page + 1))}>Next →</button>
              </div>
            )}
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-icon">🔍</div>
            <div className="empty-title">No spices found</div>
            <p className="empty-text">Try a different search or category</p>
          </div>
        )}
      </div>
    </div>
  )
}
