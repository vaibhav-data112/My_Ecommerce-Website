# Spec Document — Payment

## 1. Overview

Implement **Payment** — the step where a customer actually pays for the order created during checkout.

After checkout creates a "pending" order, this feature takes over: it shows the amount due, lets the customer pay through a real payment gateway (**Razorpay** — popular and easy in India, supports UPI, cards, netbanking), and when the payment succeeds, it marks the order as **paid**.

This feature uses **Razorpay in Test Mode**, which means you can test the whole flow with fake test cards/UPI — no real money moves. Going live with real money is a later step (and needs business verification with Razorpay).

**Why this matters:** This is where the store actually earns. It must be reliable and secure: an order should be marked paid **only** when payment truly succeeds, and never on a failed or fake payment. This is the most security-sensitive feature, so verification of the payment is the heart of it.

---

## 2. Depends on

- **Checkout** (feature 06) — provides the "pending" order (with an order id and total) that this feature collects payment for.
- **User Authentication** (feature 02) — only the logged-in owner of the order can pay for it.
- **Database Setup** (feature 01) — the `orders` table stores the status.

Built on the existing **Flask + HTML templates** stack (same as previous features — no React).

---

## 3. User Stories

- **As a customer who just checked out**, I want to pay for my order securely, so that I can complete my purchase.
- **As a customer**, I want to see exactly how much I'm paying before I pay, so that there are no surprises.
- **As a customer**, I want a clear confirmation when my payment succeeds, so that I know my order is placed.
- **As a customer**, I want a clear message if my payment fails or is cancelled, so that I can try again without losing my order.
- **As the store owner**, I want an order to be marked "paid" only when the payment is genuinely verified, so that no one can fake a payment.
- **As the store owner**, I want my secret payment keys kept safe (never on GitHub), so that no one can misuse them.

---

## 4. Database Schema

> Small addition to the existing `orders` table from feature 01 / 06.

### orders (updated)

| Column | Type | Note |
| --- | --- | --- |
| id | INTEGER | order id (existing) |
| user_id | INTEGER | owner (existing) |
| status | TEXT | `'pending'` → becomes `'paid'` (or `'failed'`) — existing column, new values used |
| total | REAL | amount to pay (existing) |
| ... | | other existing checkout columns |
| payment_id | TEXT | **new** — the gateway's payment reference, stored on success |
| payment_order_id | TEXT | **new** — the gateway's order reference created before payment |

---

## 5. Routes / Functions to Implement

> Flask routes + Razorpay's checkout widget. The exact field names follow Razorpay's documentation.

### A. Start payment  (`GET /pay/<order_id>`)
- Requires login; the order must belong to the current user and be `pending`.
- Creates a payment order with Razorpay for the order's total amount.
- Shows a payment page with the amount and Razorpay's "Pay" button (the gateway widget handles card/UPI entry securely — we never touch card details ourselves).

### B. Payment success/verify  (`POST /pay/verify`)
- Razorpay sends back a payment result after the user pays.
- **Verify the payment signature** using the secret key (this is the critical security step — it proves the payment is real and not faked).
- If valid → mark the order `paid`, store `payment_id`, and show a success page.
- If invalid → do NOT mark paid; show a failure message.

### C. Payment failure / cancel  (handled on the payment page)
- If the user cancels or payment fails → keep the order `pending`, show a friendly "Payment not completed, you can try again" message with a link back to pay.

### D. Order confirmation page  (`GET /order/<order_id>/success`)
- Requires login + ownership.
- Shows the confirmed order summary (items, total, "paid" status).

### E. Helper functions
- `create_payment_order(order)` → talks to Razorpay to create a payment order.
- `verify_payment(data)` → verifies the signature; returns true/false.

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Start payment for a pending order
- **Given** a logged-in user who owns a `pending` order
- **When** they open the payment page for it
- **Then** they see the correct amount and a working "Pay" button.

### AC-2: Only the owner can pay
- **Given** an order belonging to user A
- **When** user B tries to open its payment page
- **Then** they are blocked (not allowed to pay for someone else's order).

### AC-3: Successful, verified payment marks order paid
- **Given** a user completes payment with a valid Razorpay test payment
- **When** the result is verified successfully
- **Then** the order status becomes `paid`, the payment id is stored, and a success page is shown.

### AC-4: Fake/invalid payment is rejected
- **Given** a payment result with an invalid signature (tampered or fake)
- **When** it reaches the verify step
- **Then** the order is NOT marked paid and a failure message is shown.

### AC-5: Cancelled payment keeps order pending
- **Given** a user opens the payment page but cancels
- **When** they leave without paying
- **Then** the order stays `pending` and they can try paying again later.

### AC-6: Cannot pay an already-paid order
- **Given** an order already marked `paid`
- **When** the user tries to pay for it again
- **Then** they are redirected to the confirmation page (no double payment).

### AC-7: Amount matches the order
- **Given** an order with a specific total
- **When** the payment is started
- **Then** the amount charged equals the order total (taken from the database, never from the browser).

### AC-8: Login required
- **Given** a logged-out user
- **When** they try to open a payment page
- **Then** they are redirected to login first.

### AC-9: Secret keys never exposed
- **Given** the payment integration
- **When** the code runs
- **Then** the Razorpay secret key is only used on the server, never sent to the browser, and never committed to GitHub.

---

## 7. Files to Change

- Main app/routes file → register the payment routes.
- The cart's "Proceed to Checkout" / checkout's hand-off → after checkout creates the order, direct the user to `/pay/<order_id>`.
- The database helper → add `payment_id` / `payment_order_id` columns (safe migration) and status updates.

## 8. Files to Create

- A payment module/blueprint with the routes and helper functions.
- `templates/payment/pay.html` → the payment page with the Razorpay button.
- `templates/payment/success.html` → the order confirmation page.
- A payment failure message/template (can be simple).

---

## 9. Dependencies

- **Razorpay** account (free to create) in **Test Mode**, which gives a Test **Key ID** and **Key Secret**.
- The Razorpay Python library and its JavaScript checkout widget (loaded on the payment page).
- Keys go in the existing **`.env`** file (already git-ignored) as `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
- The plan should explain step-by-step where to get the test keys from the Razorpay dashboard.

---

## 10. Rules for Implementation

- **Always verify the payment signature** on the server before marking an order paid — this is non-negotiable; it's what prevents fake payments.
- The **Key Secret must NEVER** be sent to the browser or committed to GitHub — server-side only, in `.env`.
- The amount charged must come from the **order total in the database**, never from a value sent by the browser.
- Only the **order's owner** can pay for it, and only if it's still `pending`.
- An order already `paid` must not be payable again (no double charge).
- We never collect or store raw card/UPI details ourselves — Razorpay's widget handles that securely.
- Use **Test Mode** throughout; going live is a separate, later step.
- Use **parameterized queries only** for any database updates.

---

## 11. Error Handling Expectations

- Payment fails or is cancelled → order stays `pending`, friendly "try again" message, no crash.
- Invalid/tampered payment result → rejected at verification, order not marked paid.
- Trying to pay for someone else's order, or an already-paid order → blocked gracefully with a clear message.
- Razorpay/network error while creating the payment → friendly error, order stays `pending`, user can retry.
- Logged-out access → redirect to login.

---

## 12. Out of Scope (handled by other features / later)

- **Going live with real money** → needs Razorpay business/KYC verification; a separate later step. This feature is Test Mode only.
- Refunds / cancellations after payment → future feature.
- Order history / tracking screen → **Order Management feature** (next).
- Invoices / receipts by email → future feature.
- This feature only collects and verifies payment for a single order; it doesn't manage past orders or refunds.

---

## 13. Definition of Done

- [ ] A logged-in owner of a pending order can open its payment page and see the correct amount.
- [ ] A user cannot open the payment page for someone else's order.
- [ ] A logged-out user is redirected to login.
- [ ] A successful, verified test payment marks the order `paid` and stores the payment id.
- [ ] An invalid/fake payment result is rejected and the order is NOT marked paid.
- [ ] A cancelled payment leaves the order `pending` and the user can retry.
- [ ] An already-paid order cannot be paid again (redirects to confirmation).
- [ ] The charged amount always equals the order total from the database.
- [ ] A clear success/confirmation page is shown after payment.
- [ ] The Razorpay secret key is only used server-side, in `.env`, never on GitHub.
- [ ] All database updates use parameterized SQL.