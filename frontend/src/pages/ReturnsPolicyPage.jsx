export default function ReturnsPolicyPage() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 720, paddingTop: 48, paddingBottom: 64 }}>
        <h1 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 8 }}>
          Returns &amp; Refund Policy
        </h1>
        <p style={{ color: 'var(--color-text-soft)', marginBottom: 36, fontSize: 'var(--fs-sm)' }}>
          Last updated: June 2026
        </p>

        <div className="card" style={{ padding: 32, lineHeight: 1.85, color: 'var(--color-text)' }}>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Return Window
          </h2>
          <p style={{ marginBottom: 24 }}>
            You may request a return within <strong>7 days</strong> of delivery for orders that are
            delivered and paid via Razorpay. Self-return requests can be initiated directly from
            <a href="/orders" style={{ color: 'var(--color-primary)', fontWeight: 600, marginLeft: 4 }}>My Orders</a>.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Eligible Products
          </h2>
          <p style={{ marginBottom: 24 }}>
            Products must be unused, in original packaging, and in the same condition as received.
            Opened / partially used spice packets are not eligible for return unless the product
            is genuinely defective or damaged.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Refund Process
          </h2>
          <p style={{ marginBottom: 24 }}>
            Once your return is approved by our team, a full refund will be initiated via Razorpay
            to your original payment method within <strong>5–7 business days</strong>.
            You will see a status update in My Orders.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Non-Returnable Items
          </h2>
          <ul style={{ paddingLeft: 20, marginBottom: 24 }}>
            <li>Orders placed more than 7 days ago</li>
            <li>Cash-on-delivery orders (not applicable — we do not offer COD)</li>
            <li>Products with tampered or missing original packaging</li>
          </ul>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Questions?
          </h2>
          <p>
            For any return or refund queries, visit our{' '}
            <a href="/contact" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Contact Us</a>{' '}
            page or reach us on WhatsApp.
          </p>

        </div>
      </div>
    </div>
  )
}
