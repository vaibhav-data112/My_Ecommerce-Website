import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="page">
      <div className="container">
        <div className="empty-state">
          <div className="empty-icon">🌶</div>
          <div className="empty-title">Page Not Found</div>
          <p className="empty-text">The page you're looking for doesn't exist.</p>
          <Link to="/" className="btn btn-primary">Go Home</Link>
        </div>
      </div>
    </div>
  )
}
