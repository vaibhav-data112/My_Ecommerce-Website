export default function PrivacyPolicyPage() {
  return (
    <div className="page">
      <div className="container" style={{ maxWidth: 720, paddingTop: 48, paddingBottom: 64 }}>
        <h1 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', marginBottom: 8 }}>
          Privacy Policy
        </h1>
        <p style={{ color: 'var(--color-text-soft)', marginBottom: 36, fontSize: 'var(--fs-sm)' }}>
          Last updated: June 2026
        </p>

        <div className="card" style={{ padding: 32, lineHeight: 1.85, color: 'var(--color-text)' }}>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Information We Collect
          </h2>
          <p style={{ marginBottom: 24 }}>
            When you create an account or place an order, we collect your <strong>name, email address,
            phone number, and shipping address</strong>. If you sign in with Google, we receive your
            public Google profile (name, email, profile picture) as permitted by Google OAuth.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            How We Use Your Information
          </h2>
          <ul style={{ paddingLeft: 20, marginBottom: 24 }}>
            <li>To process and deliver your orders</li>
            <li>To send order confirmations and shipping updates</li>
            <li>To handle returns, refunds, and support requests</li>
            <li>To improve our products and website experience</li>
          </ul>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Payment Information
          </h2>
          <p style={{ marginBottom: 24 }}>
            We do not store your card or payment details. All payments are processed securely
            by <strong>Razorpay</strong>. We only store the Razorpay order and payment IDs for
            order tracking and refund purposes.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Data Sharing
          </h2>
          <p style={{ marginBottom: 24 }}>
            We do not sell, rent, or share your personal data with third parties for marketing.
            We share only what is necessary with our logistics partners to deliver your order.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Cookies
          </h2>
          <p style={{ marginBottom: 24 }}>
            We use session cookies to keep you logged in. No third-party tracking cookies are used.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Your Rights
          </h2>
          <p style={{ marginBottom: 24 }}>
            You can request deletion of your account and personal data at any time by contacting us
            via the <a href="/contact" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>Contact Us</a> page.
          </p>

          <h2 style={{ fontFamily: 'var(--font-head)', color: 'var(--color-primary-dark)', fontSize: 18, marginBottom: 12 }}>
            Contact
          </h2>
          <p>
            For privacy-related questions, email us at{' '}
            <a href="mailto:vaibhavtiw2008@gmail.com" style={{ color: 'var(--color-primary)', fontWeight: 600 }}>
              vaibhavtiw2008@gmail.com
            </a>.
          </p>

        </div>
      </div>
    </div>
  )
}
