# Spec 12 — Order Tracking Timeline

> **Feature:** A — Order tracking timeline (customer ko Flipkart-jaisa status timeline dikhe; admin status update kare)
> **Branch:** `feature/order-tracking`
> **Out of scope (alag specs):** B = customer self-return + refund, C = Contact Us page + WhatsApp.
> **Approach:** Additive only — koi purani table/feature todni nahi. Tech-lead health report ke mutabik base already mojood hai (status column, admin update API, order detail page).

---

## 1. Goal

Har order ke liye ek visual status timeline dikhana, jisme har step pe date/time aur (zaroorat ho to) ek note ho. Customer apne order ki progress dekh sake; admin status aage badha sake aur shipped pe courier + tracking + "kahaan se nikla" note daal sake.

**In scope**
- 8 order statuses (5 linear + 3 terminal) — niche section 3.
- Order detail page pe vertical timeline component.
- Admin order page se status update + courier/tracking/note inputs.
- Brand-styled, responsive (mobile/tablet/desktop).
- Chhota bug-fix: review sirf `paid` pe allow hota tha — ab `delivered` (aur baad ke stages) pe bhi allow.

**NOT in scope (future)**
- Real-time GPS location / live map. ❌
- Real courier API auto-update (Shiprocket/Delhivery etc.). ❌
- Customer self-return button + refund calculation + Razorpay refund. → **Feature B**
- Contact Us / complaint form / WhatsApp link. → **Feature C**
- (Terminal states `cancelled`/`returned`/`refunded` is feature mein **sirf admin manually** set karega; customer-facing return flow Feature B mein.)

---

## 2. Current State (health report se)

- `orders` table mein `status` column hai. Current allowed values: `paid`, `shipped`, `delivered`, `cancelled`.
- Admin status-update API already exists (admin.py).
- Customer OrderDetailPage exists — abhi sirf ek single status badge dikhta hai, koi timeline nahi.
- **Known bug:** `can_user_review()` sirf `status='paid'` check karta hai (db.py ~line 629 hardcoded). Isse `delivered` orders pe review nahi ho pata. Statuses waise bhi badal rahe hain, to ye yahin fix hoga.

---

## 3. Status Model

**Linear steps (timeline stepper, isi order mein):**

| value | Display name (UI) |
|---|---|
| `paid` | Order Confirmed |
| `packed` | Packed |
| `shipped` | Shipped |
| `out_for_delivery` | Out for Delivery |
| `delivered` | Delivered |

`STEP_ORDER = ['paid', 'packed', 'shipped', 'out_for_delivery', 'delivered']`

- Current status se **pehle** ke steps = **done** (green).
- Current status = **active** (terracotta highlight).
- Current status se **baad** ke steps = **pending** (grey).

**Terminal / side states (linear stepper se bahar, ek banner ke roop mein dikhao):**

| value | Display name | Banner color (suggestion) |
|---|---|---|
| `cancelled` | Cancelled | red/grey |
| `returned` | Returned | amber |
| `refunded` | Refunded | blue/grey |

Terminal state hone par: linear stepper ke upar ek clear banner dikhe (jaise "Ye order cancel ho gaya hai"). Jo steps tak order pahuncha tha, wo history se waise hi dikhte rahein.

---

## 4. Data Model Changes (additive — koi nayi table nahi)

`orders` table mein **3 naye columns** (sab nullable, `migrate_db()` se add):

1. `status_history` — TEXT, JSON list. Har status change pe ek entry append hoti hai.
   ```json
   [
     { "status": "paid",    "at": "2026-06-14T18:10:00", "note": null },
     { "status": "packed",  "at": "2026-06-14T20:30:00", "note": null },
     { "status": "shipped", "at": "2026-06-15T11:00:00", "note": "Kanpur warehouse se nikal gaya" }
   ]
   ```
2. `courier_name` — TEXT, nullable (shipped pe set hota hai).
3. `tracking_number` — TEXT, nullable (shipped pe set hota hai).

**Migration rules (`migrate_db()`):**
- Teeno columns add karo agar mojood nahi (idempotent — dobaara chalane pe error na de).
- **Back-fill:** har existing order ke liye agar `status_history` khaali hai, to ek single entry banao current `status` + order ke `created_at` (ya `now()`) se. Isse purane orders ka timeline khaali na dikhe.
- Existing data delete/modify nahi hogi.

**Order create hone par:** `status_history` ek entry `{status: "paid", at: now, note: null}` se initialize ho.

---

## 5. Backend Changes (API)

**`db.py`**
- `migrate_db()` mein 3 columns add + back-fill (upar section 4).
- Helper: `append_status_history(order, new_status, note=None)` — JSON load → entry append → save. Saath hi order ka `status` update kare.
- `can_user_review()` fix: review allow ho jab order status `paid`, `packed`, `shipped`, `out_for_delivery`, ya `delivered` ho (matlab `paid` ke alawa baad ke stages bhi). Purana behavior na toote (paid abhi bhi allowed).

**`admin.py`**
- `ALLOWED_STATUSES` ko 8 values tak expand karo: `paid, packed, shipped, out_for_delivery, delivered, cancelled, returned, refunded`.
- Status-update endpoint (jo already hai) ko extend karo:
  - `status` ke saath optional `note` accept kare → `append_status_history()` call kare (timestamp server set kare).
  - Jab `status == "shipped"`: optional `courier_name` + `tracking_number` bhi accept karke save kare.
  - Invalid status aaye to 400 with clear message.

**Orders route (jo order detail JSON deta hai)**
- Response mein 3 naye fields include karo: `status_history`, `courier_name`, `tracking_number` (status_history parsed list ke roop mein bheje).

---

## 6. Frontend Changes (React)

**NAYA component: `frontend/src/components/OrderTimeline.jsx`**
- Props: `statusHistory` (list), `currentStatus`, `courierName`, `trackingNumber`.
- Linear steps `STEP_ORDER` ke hisaab se render: done (green ✓), active (terracotta, highlighted), pending (grey).
- Har done/active step pe: display name + us status ki `at` history se date/time + note (agar ho).
- Shipped step pe: note + `courier_name` + `tracking_number` dikhe (agar mojood).
- Agar `currentStatus` terminal hai (cancelled/returned/refunded): upar ek banner + jitne steps history mein hain wo dikhe.
- Mobile pe vertical stack, theek se padhne layak (responsive-design skill).

**`frontend/src/pages/OrderDetailPage.jsx`**
- Existing single badge ke jagah / saath `<OrderTimeline ... />` integrate karo, order data se props pass karke.

**`frontend/src/pages/admin/AdminOrders.jsx`**
- `STATUSES` array ko 8 values tak expand karo (dropdown/options).
- Status change UI: admin status chune. Jab `shipped` chune, to 3 chhote inputs dikhe — `courier_name`, `tracking_number`, aur ek optional `note`. Baaki statuses ke liye sirf optional `note`.
- Save pe updated API call.

**`frontend/src/api/admin.js`** (admin API module)
- `updateOrderStatus` call mein optional `note`, `courier_name`, `tracking_number` bhejne ka support add karo.

**`frontend/src/index.css`**
- Timeline CSS (~60 lines) + status badge classes. Brand tokens use karo:
  - done = Forest Green `#2D6A4F`
  - active = Terracotta `#D4580A`
  - pending = grey/muted
  - terminal banners: cancelled (red/grey), returned (turmeric/amber `#B7860B`), refunded (blue/grey)

---

## 7. User Stories

- **As a customer**, I want to see my order's progress as a step-by-step timeline with dates, so I know exactly where my order is and when it moves.
- **As a customer**, when my order is shipped, I want to see which courier has it, the tracking number, and that it has left the warehouse.
- **As an admin**, I want to move an order through each status and add courier/tracking/note, so customers stay informed without me messaging each one.
- **As an admin**, I want to mark special states (cancelled/returned/refunded) so the order page reflects reality.

---

## 8. Acceptance Criteria (Given / When / Then)

1. **Timeline shows on order detail**
   - Given an order with status `paid`,
   - When the customer opens its detail page,
   - Then a vertical timeline shows "Order Confirmed" as done (green) with its date/time, and Packed/Shipped/Out for Delivery/Delivered as pending (grey).

2. **Admin advances status**
   - Given admin opens an order in AdminOrders,
   - When admin sets status to `packed` and saves,
   - Then `status` becomes `packed`, a new history entry with server timestamp is appended, and the customer's timeline now shows Packed as done and Packed... wait → Packed becomes the active step.

3. **Shipped with courier details**
   - Given admin sets status to `shipped` with `courier_name`, `tracking_number`, and note "Kanpur warehouse se nikal gaya",
   - When saved,
   - Then those values are stored, and the customer's Shipped step shows the note + courier + tracking number.

4. **Terminal state banner**
   - Given an order set to `cancelled`,
   - When the customer opens it,
   - Then a clear "Cancelled" banner is shown above the timeline.

5. **Old orders don't break**
   - Given an order created before this feature,
   - When the migration runs and the customer opens it,
   - Then a back-filled single-step timeline shows (no crash, no empty timeline).

6. **Review bug fixed**
   - Given a `delivered` order containing a product,
   - When the customer tries to review that product,
   - Then the review is allowed (previously blocked).

---

## 9. Definition of Done

- [ ] `migrate_db()` adds 3 columns idempotently + back-fills existing orders; no data loss.
- [ ] `ALLOWED_STATUSES` = the 8 statuses; admin can set each one.
- [ ] Status-update endpoint appends history (server timestamp) + saves courier/tracking on shipped.
- [ ] Order detail API returns `status_history`, `courier_name`, `tracking_number`.
- [ ] `OrderTimeline.jsx` created; integrated into OrderDetailPage; renders done/active/pending + terminal banner correctly.
- [ ] AdminOrders supports all 8 statuses + shipped extra inputs.
- [ ] Brand-styled (green/terracotta/grey) + responsive at 375 / 768 / 1280 px.
- [ ] `can_user_review()` fixed; existing review behavior not broken.
- [ ] Existing 110 tests still pass; new tests cover history append + status display (test-writer stage).
- [ ] Security review pass (admin-only status changes; input validation on status/courier/tracking).

---

## 10. Browser Test Script (user khud browser mein check kare)

> Backend `python app.py` (127.0.0.1:5000) + frontend `cd frontend && npm run dev` (localhost:5173) dono chalu rakho.

1. **Migration check:** backend start karo — koi error nahi aana chahiye. Ek purana order kholo → timeline khaali na ho (kam se kam 1 step dikhe).
2. **Admin login** karo (`vaibhavtiw2008@gmail.com`) → Admin Orders kholo.
3. Ek order pe status **`packed`** set karke save karo. → AdminOrders mein status badla dikhe.
4. Usi order ko status **`shipped`** karo, aur courier = "BlueDart", tracking = "7712 3456 8890", note = "Kanpur warehouse se nikal gaya" daal ke save karo.
5. **Customer account** se (us order wale user se) wahi order detail page kholo:
   - Timeline dikhe: Order Confirmed ✅, Packed ✅, **Shipped** active — note + courier + tracking dikhe, Out for Delivery & Delivered grey/pending.
   - Har done step pe date/time dikhe.
6. Admin se status **`out_for_delivery`** → phir **`delivered`** karke dekho — har baar customer page pe active step aage badhe.
7. Ek doosre order ko **`cancelled`** karo → customer page pe upar "Cancelled" banner dikhe.
8. **Review bug check:** `delivered` order ke product pe customer review likh paaye (pehle block hota tha).
9. **Mobile check:** browser ko 375px (DevTools) pe le jao → timeline saaf vertical dikhe, text na kate. 768px aur 1280px bhi theek dikhe.
10. **Regression:** ek normal order place karke checkout/payment (Razorpay test) ek baar chala ke dekho — kuch toota to nahi.

---

## 11. Risks / Notes

- `status_history` JSON column hai (alag table nahi) — display-ke-liye perfect, query simple. Agar future mein per-status analytics chahiye to tab table mein nikalenge (abhi zaroorat nahi).
- `cancelled/returned/refunded` abhi sirf admin set karega; **asli paisa wapas (Razorpay refund) is feature mein nahi** — wo Feature B mein, apne security review ke saath.
- Inputs validate karo: status sirf allowed values; courier/tracking length cap; note basic sanitize (XSS se bachne ke liye React already escape karta hai, par backend pe bhi trim).