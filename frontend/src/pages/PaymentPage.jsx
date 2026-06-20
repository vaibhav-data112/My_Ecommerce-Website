import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getPaymentInfo, verifyPayment } from '../api/orders'
import Spinner from '../components/Spinner'

function loadRazorpayScript() {
  return new Promise(resolve => {
    if (window.Razorpay) { resolve(true); return }
    const s = document.createElement('script')
    s.src = 'https://checkout.razorpay.com/v1/checkout.js'
    s.onload  = () => resolve(true)
    s.onerror = () => resolve(false)
    document.body.appendChild(s)
  })
}

export default function PaymentPage() {
  const { id }       = useParams()
  const navigate     = useNavigate()
  const [data, setData]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [paying, setPaying]   = useState(false)

  useEffect(() => {
    getPaymentInfo(id)
      .then(r => {
        if (r.data.already_paid) { navigate(`/orders/${id}`); return }
        if (r.data.is_cod)       { navigate(`/orders/${id}`); return }
        setData(r.data)
      })
      .catch(err => setError(err.response?.data?.error || 'Failed to load payment info'))
      .finally(() => setLoading(false))
  }, [id])

  const handlePay = async () => {
    setPaying(true)
    const ok = await loadRazorpayScript()
    if (!ok) { setError('Failed to load payment gateway. Please try again.'); setPaying(false); return }

    const options = {
      key:         data.key_id,
      amount:      data.amount_paisa,
      currency:    'INR',
      order_id:    data.rz_order_id,
      name:        'Karvii Spices',
      description: `Order #${id}`,
      handler: async (response) => {
        try {
          await verifyPayment({
            razorpay_order_id:   response.razorpay_order_id,
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_signature:  response.razorpay_signature,
          })
          navigate(`/orders/${id}`)
        } catch {
          setError('Payment verification failed. Please contact support.')
        } finally { setPaying(false) }
      },
      modal: { ondismiss: () => setPaying(false) },
      theme: { color: '#C8960C' },
    }

    const rzp = new window.Razorpay(options)
    rzp.open()
  }

  if (loading) return <Spinner />

  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 500 }}>
        <div className="card" style={{ padding: 40, textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>💳</div>
          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--brown)', marginBottom: 8 }}>Complete Payment</h2>
          <p style={{ color: 'var(--text-soft)', marginBottom: 24, fontSize: 14 }}>Order #{id}</p>

          {error && <div className="alert alert-error">{error}</div>}

          {data && (
            <>
              <div style={{ background: 'var(--beige)', borderRadius: 'var(--radius-lg)', padding: 20, marginBottom: 28 }}>
                <div style={{ fontSize: 14, color: 'var(--text-soft)', marginBottom: 4 }}>Amount to Pay</div>
                <div style={{ fontFamily: 'var(--font-head)', fontSize: 36, color: 'var(--brown)', fontWeight: 700 }}>
                  ₹{(data.amount_paisa / 100).toFixed(2)}
                </div>
              </div>
              <button className="btn btn-primary btn-full btn-lg" onClick={handlePay} disabled={paying}>
                {paying ? 'Processing...' : 'Pay with Razorpay'}
              </button>
              <p style={{ fontSize: 12, color: 'var(--text-soft)', marginTop: 12 }}>
                🔒 Secure payment powered by Razorpay
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
