export default function ShippingPolicyPage() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 720, paddingTop: 48, paddingBottom: 64 }}>
        <h1 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 8 }}>
          Shipping Policy
        </h1>
        <p style={{ color: 'var(--color-text-soft)', marginBottom: 36, fontSize: 'var(--fs-sm)' }}>
          Last updated: June 2026
        </p>

        <div className="card" style={{ padding: 32, lineHeight: 1.85, color: 'var(--color-text)' }}>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Delivery Time
          </h2>
          <p style={{ marginBottom: 24 }}>
            Orders are dispatched within <strong>1–2 business days</strong> of payment confirmation.
            Estimated delivery is <strong>4–7 business days</strong> depending on your location.
            Remote areas may take up to 10 business days.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Shipping Charges
          </h2>
          <p style={{ marginBottom: 24 }}>
            A flat shipping fee of <strong>₹40</strong> applies to all orders.
            Orders above <strong>₹500</strong> qualify for <strong>free shipping</strong>.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Tracking
          </h2>
          <p style={{ marginBottom: 24 }}>
            Once your order is shipped, you will receive tracking details (courier name and tracking number)
            visible in <a href="/orders" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>My Orders</a>.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Coverage
          </h2>
          <p style={{ marginBottom: 24 }}>
            We currently ship across India. International shipping is not available at this time.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Damaged or Lost Shipment
          </h2>
          <p>
            If your package arrives damaged or does not arrive within the expected window, please
            contact us via the <a href="/contact" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Contact Us</a> page
            or WhatsApp. We will resolve the issue promptly.
          </p>

        </div>
      </div>
    </div>
  )
}
