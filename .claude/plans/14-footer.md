# Plan: Feature 14 — Footer (Flipkart-style + Social Links)

## Context

The current footer is a single line of text (`© 2024 Karvii`). This feature replaces it with a rich multi-column footer visible on every page: 5 columns (About, Help, Policy, Shop, Connect), all social platform icons (auto-hidden when URL is empty), a non-functional newsletter signup box, static info pages (About/Contact/Privacy/Terms), a copyright bottom bar, and a sticky-footer layout so it always sits at the bottom even on short pages. No DB changes — purely frontend.

---

## Step 1 — `app.py` — `SOCIAL_LINKS` config + context processor

Add the social links dict near the top of `app.py` (after `load_dotenv()`). Each entry has `name`, `icon` (slug for SVG lookup in template), and `url` (empty string = auto-hidden):

```python
SOCIAL_LINKS = [
    {'name': 'WhatsApp',  'icon': 'whatsapp',  'url': ''},
    {'name': 'Instagram', 'icon': 'instagram', 'url': ''},
    {'name': 'YouTube',   'icon': 'youtube',   'url': ''},
    {'name': 'Facebook',  'icon': 'facebook',  'url': ''},
    {'name': 'X',         'icon': 'twitter',   'url': ''},
    {'name': 'LinkedIn',  'icon': 'linkedin',  'url': ''},
    {'name': 'Pinterest', 'icon': 'pinterest', 'url': ''},
    {'name': 'Telegram',  'icon': 'telegram',  'url': ''},
    {'name': 'Email',     'icon': 'email',     'url': 'mailto:vaibhavtiw2008@gmail.com'},
]
```

Add a context processor so `social_links` is available in every template (like `cart_count`):

```python
@app.context_processor
def inject_footer_data():
    return dict(social_links=[s for s in SOCIAL_LINKS if s['url']])
```

The filter `if s['url']` hides platforms with empty URLs — auto-hide logic lives here, not in the template.

**To activate a platform:** fill in its `url` in `SOCIAL_LINKS` and restart the server. No template changes needed.

---

## Step 2 — `pages.py` — static info pages blueprint

New file. Simple blueprint for the 4 static pages linked from the footer:

```python
from flask import Blueprint, render_template

pages = Blueprint('pages', __name__)

@pages.route('/about')
def about():
    return render_template('pages/about.html')

@pages.route('/contact')
def contact():
    return render_template('pages/contact.html')

@pages.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')

@pages.route('/terms')
def terms():
    return render_template('pages/terms.html')
```

Register in `app.py`:

```python
from pages import pages as pages_blueprint
app.register_blueprint(pages_blueprint)
```

---

## Step 3 — Static page templates (`templates/pages/`)

Four templates, all extend `base.html`. Placeholder content — user fills in later.

### `templates/pages/about.html`
- Heading: "About Karvii"
- 2–3 short paragraphs: brand story, mission, what makes Karvii special.
- Placeholder text that looks real (not "Lorem ipsum").

### `templates/pages/contact.html`
- Heading: "Contact Us"
- Email link: `mailto:vaibhavtiw2008@gmail.com`
- WhatsApp placeholder line (update when number is confirmed).
- Simple message: "We respond within 24 hours."

### `templates/pages/privacy.html`
- Heading: "Privacy Policy"
- Sections: what data we collect, how we use it, cookies, third-party services, contact.
- Placeholder content — enough to look real.

### `templates/pages/terms.html`
- Heading: "Terms of Use"
- Sections: use of site, purchases, returns, liability, governing law.
- Placeholder content.

All 4 pages use the `.card` wrapper for consistent padding and the existing page-content styles.

---

## Step 4 — `templates/base.html` — replace footer

### 4a. Sticky-footer: restructure `<body>` layout

The content `<div class="container">` already sits between `<nav>` and `<footer>`. For sticky footer, the CSS step adds `flex: 1` to this div — no HTML change needed except ensuring the footer tag is correct.

### 4b. Replace the minimal footer block

Replace:
```html
<footer class="footer">
    <div class="container">
        <p>&copy; 2024 <a href="/">Karvii</a> &mdash; Premium Boutique Fashion</p>
    </div>
</footer>
```

With the full footer:

```html
<footer class="footer">
    <div class="container">

        {# ── Column grid ── #}
        <div class="footer-grid">

            {# Column 1 — About #}
            <div class="footer-col">
                <h4>ABOUT</h4>
                <ul>
                    <li><a href="{{ url_for('pages.about') }}">About Us</a></li>
                    <li><a href="{{ url_for('pages.contact') }}">Contact Us</a></li>
                    <li><a href="#">Our Story</a></li>
                    <li><a href="#">Careers</a></li>
                </ul>
            </div>

            {# Column 2 — Help #}
            <div class="footer-col">
                <h4>HELP</h4>
                <ul>
                    <li><a href="#">FAQ</a></li>
                    <li><a href="#">Shipping Info</a></li>
                    <li><a href="#">Returns & Refunds</a></li>
                    <li><a href="{{ url_for('orders.order_history') }}">Track Order</a></li>
                </ul>
            </div>

            {# Column 3 — Policy #}
            <div class="footer-col">
                <h4>POLICY</h4>
                <ul>
                    <li><a href="{{ url_for('pages.privacy') }}">Privacy Policy</a></li>
                    <li><a href="{{ url_for('pages.terms') }}">Terms of Use</a></li>
                    <li><a href="#">Return Policy</a></li>
                </ul>
            </div>

            {# Column 4 — Shop #}
            <div class="footer-col">
                <h4>SHOP</h4>
                <ul>
                    <li><a href="{{ url_for('catalog.product_list') }}">All Products</a></li>
                    <li><a href="{{ url_for('catalog.product_list') }}?category=Clothing">Clothing</a></li>
                    <li><a href="{{ url_for('orders.order_history') }}">My Orders</a></li>
                    <li><a href="{{ url_for('wishlist.view_wishlist') }}">Wishlist</a></li>
                    <li><a href="{{ url_for('account.dashboard') }}">My Account</a></li>
                </ul>
            </div>

            {# Column 5 — Connect (social) #}
            <div class="footer-col footer-col-connect">
                <h4>CONNECT</h4>
                {% if social_links %}
                <div class="footer-social">
                    {% for s in social_links %}
                    <a href="{{ s.url }}" class="social-btn" aria-label="{{ s.name }}"
                       {% if not s.url.startswith('mailto') %}target="_blank" rel="noopener"{% endif %}>
                        {% include 'partials/social_icon_' ~ s.icon ~ '.html' ignore missing %}
                    </a>
                    {% endfor %}
                </div>
                {% else %}
                <p class="footer-social-empty">Coming soon — find us online!</p>
                {% endif %}
            </div>

        </div>{# /footer-grid #}

        {# ── Newsletter ── #}
        <div class="footer-newsletter">
            <p class="footer-newsletter-label">Stay in the loop</p>
            <form class="footer-newsletter-form" onsubmit="return false;">
                <input type="email" placeholder="Your email address" aria-label="Email for newsletter">
                <button type="submit">Subscribe</button>
            </form>
            <p class="footer-newsletter-note">No spam. Unsubscribe anytime.</p>
        </div>

        {# ── Bottom bar ── #}
        <div class="footer-bottom">
            <span>&copy; 2026 <a href="/">Karvii</a>. All rights reserved.</span>
            <span class="footer-made">Crafted in India &#10084;&#65039;</span>
        </div>

    </div>
</footer>
```

### 4c. Social icon partials (`templates/partials/`)

One tiny HTML file per platform — just the SVG tag. Template uses `{% include 'partials/social_icon_whatsapp.html' %}` etc. `ignore missing` means an unknown icon silently renders nothing.

Files to create (each is ~5 lines with a `<svg>` tag):

| File | Icon |
|------|------|
| `templates/partials/social_icon_whatsapp.html` | WhatsApp logo SVG |
| `templates/partials/social_icon_instagram.html` | Instagram camera SVG |
| `templates/partials/social_icon_youtube.html` | YouTube play button SVG |
| `templates/partials/social_icon_facebook.html` | Facebook f SVG |
| `templates/partials/social_icon_twitter.html` | X / Twitter SVG |
| `templates/partials/social_icon_linkedin.html` | LinkedIn in SVG |
| `templates/partials/social_icon_pinterest.html` | Pinterest P SVG |
| `templates/partials/social_icon_telegram.html` | Telegram paper-plane SVG |
| `templates/partials/social_icon_email.html` | Envelope SVG |

Each SVG: `width="20" height="20" fill="currentColor" viewBox="0 0 24 24"` so CSS can control colour via `color`.

---

## Step 5 — `static/css/style.css` — footer styles

### Sticky footer (append to `body` rule)

```css
body {
  /* existing rules + add: */
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
/* Main content area grows to push footer down */
body > .container {
  flex: 1;
}
```

### Footer grid

```css
.footer {
  /* existing: background plum, color cream, padding */
  /* update padding for richer layout */
  padding: var(--space-6) 0 0;
}

.footer-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--space-4);
  padding-bottom: var(--space-5);
  border-bottom: 1px solid rgba(232,195,158,0.2);  /* subtle gold divider */
}

.footer-col h4 {
  font-family: var(--font-body);
  font-size: .7rem;
  font-weight: 600;
  letter-spacing: 1.5px;
  color: var(--color-gold);
  margin-bottom: var(--space-3);
}

.footer-col ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: .5rem;
}

.footer-col ul li a {
  color: rgba(247,237,226,0.75);
  font-size: var(--fs-sm);
  transition: color .15s;
}
.footer-col ul li a:hover { color: var(--color-gold); }
```

### Social icons

```css
.footer-social {
  display: flex;
  flex-wrap: wrap;
  gap: .6rem;
  margin-top: .25rem;
}

.social-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(232,195,158,0.12);
  color: var(--color-gold);
  border: 1px solid rgba(232,195,158,0.25);
  transition: background .15s, color .15s;
}
.social-btn:hover {
  background: var(--color-gold);
  color: var(--color-plum);
}

.footer-social-empty {
  font-size: var(--fs-sm);
  color: rgba(247,237,226,0.5);
  font-style: italic;
}
```

### Newsletter box

```css
.footer-newsletter {
  text-align: center;
  padding: var(--space-4) 0;
  border-bottom: 1px solid rgba(232,195,158,0.2);
}

.footer-newsletter-label {
  font-family: var(--font-head);
  color: var(--color-gold);
  font-size: var(--fs-lg);
  margin-bottom: var(--space-2);
}

.footer-newsletter-form {
  display: flex;
  justify-content: center;
  gap: .5rem;
  max-width: 420px;
  margin: 0 auto var(--space-1);
}

.footer-newsletter-form input[type="email"] {
  flex: 1;
  padding: .55rem 1rem;
  border: 1px solid rgba(232,195,158,0.4);
  border-radius: 4px;
  background: rgba(255,255,255,0.07);
  color: var(--color-cream);
  font-size: var(--fs-sm);
}
.footer-newsletter-form input::placeholder { color: rgba(247,237,226,0.45); }
.footer-newsletter-form input:focus {
  outline: none;
  border-color: var(--color-gold);
}

.footer-newsletter-form button {
  padding: .55rem 1.4rem;
  background: var(--color-gold);
  color: var(--color-plum);
  border: none;
  border-radius: 4px;
  font-weight: 600;
  font-size: var(--fs-sm);
  cursor: pointer;
  transition: background .15s;
}
.footer-newsletter-form button:hover { background: var(--color-gold-dark); }

.footer-newsletter-note {
  font-size: .72rem;
  color: rgba(247,237,226,0.4);
  margin: 0;
}
```

### Bottom bar

```css
.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) 0;
  font-size: .75rem;
  color: rgba(247,237,226,0.5);
}
.footer-bottom a { color: var(--color-gold); }
.footer-bottom a:hover { color: #fff; }
.footer-made { font-size: .72rem; }
```

### Responsive (mobile)

```css
@media (max-width: 768px) {
  .footer-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-4) var(--space-3);
  }
  .footer-col-connect { grid-column: 1 / -1; }
  .footer-bottom {
    flex-direction: column;
    gap: .3rem;
    text-align: center;
  }
}

@media (max-width: 480px) {
  .footer-grid { grid-template-columns: 1fr; }
  .footer-newsletter-form { flex-direction: column; }
  .footer-newsletter-form input,
  .footer-newsletter-form button { width: 100%; }
}
```

---

## Files Created

| File | Purpose |
|------|---------|
| `pages.py` | Blueprint for `/about`, `/contact`, `/privacy`, `/terms` |
| `templates/pages/about.html` | About Karvii page |
| `templates/pages/contact.html` | Contact Us page |
| `templates/pages/privacy.html` | Privacy Policy page |
| `templates/pages/terms.html` | Terms of Use page |
| `templates/partials/social_icon_whatsapp.html` | WhatsApp SVG icon |
| `templates/partials/social_icon_instagram.html` | Instagram SVG icon |
| `templates/partials/social_icon_youtube.html` | YouTube SVG icon |
| `templates/partials/social_icon_facebook.html` | Facebook SVG icon |
| `templates/partials/social_icon_twitter.html` | X/Twitter SVG icon |
| `templates/partials/social_icon_linkedin.html` | LinkedIn SVG icon |
| `templates/partials/social_icon_pinterest.html` | Pinterest SVG icon |
| `templates/partials/social_icon_telegram.html` | Telegram SVG icon |
| `templates/partials/social_icon_email.html` | Email/envelope SVG icon |

---

## Files Modified

| File | What changes |
|------|-------------|
| `app.py` | Add `SOCIAL_LINKS` list; add `inject_footer_data` context processor; import + register `pages_blueprint` |
| `templates/base.html` | Replace 3-line footer with full multi-column footer |
| `static/css/style.css` | Add `body` flex for sticky footer; add all `.footer-*`, `.social-btn`, `.footer-newsletter` styles |

---

## Reused Utilities

| Utility | Purpose |
|---------|---------|
| `url_for('pages.about')` etc. | Footer links to static pages |
| `url_for('catalog.product_list')` | "All Products" link in Shop column |
| `url_for('orders.order_history')` | "My Orders" / "Track Order" links |
| `url_for('wishlist.view_wishlist')` | "Wishlist" link |
| `url_for('account.dashboard')` | "My Account" link |
| `social_links` (context processor) | Injected globally — auto-filtered to non-empty URLs |

---

## Implementation Order

1. `app.py` — add `SOCIAL_LINKS` + context processor + register `pages_blueprint`
2. `pages.py` + 4 static page templates
3. 9 SVG icon partials in `templates/partials/`
4. `static/css/style.css` — all footer CSS
5. `templates/base.html` — replace footer block

This order ensures templates that reference `url_for('pages.about')` won't error when testing each step.

---

## Notes

- The newsletter form has `onsubmit="return false;"` — it renders the UI but does nothing on submit. Backend wiring is out of scope for this feature.
- "Careers" and "Our Story" links point to `#` for now — placeholder until real pages exist.
- "Return Policy" links to `#` — can be added to the `pages.py` blueprint later without touching the footer template.
- `ignore missing` on social icon includes means a typo in `icon` slug silently renders nothing rather than crashing.
