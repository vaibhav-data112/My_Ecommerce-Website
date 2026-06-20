# Spec 13 — Customer Self-Return + Refund

> **Feature:** B — Customer apne delivered order ka return request kare; admin approve/reject kare; Razorpay se refund (delivery charge kaat ke).
> **Branch:** `feature/return-refund`
> **Builds on:** Spec 12 (statuses + `status_history` timeline already mojood). Yahi feature `return_requested / returned / refunded` ko asli flow deta hai.
> **⚠️ MONEY-TOUCHING:** Razorpay refund = asli paisa wapas. **Test Mode only** jab tak go-live KYC nahi. Security review ZAROORI.
> **Out of scope:** Contact Us page + WhatsApp complaint path → **Feature C** (yahan sirf us page ka link/placeholder).

---

## ⚠️ 0. Confirm-before-implement (3 business decisions)

Default maine rakh diye hain — agar badalna ho to mujhe batao, warna inhi pe spec final:

1. **Return window:** order `delivered` hone ke baad kitne din tak return allowed? → **Default: 7 din.**
2. **"First time" ka matlab:** ek user ko **poori zindagi mein 1 hi** self-return milega (uske baad Contact Us/WhatsApp wala route — Feature C)? → **Default: haan, per-user lifetime = 1 self-return.**
3. **Kya return hota hai:** poora order return (saare items) ya ek-ek item alag? → **Default: poora order return** (item-level baad mein, abhi nahi).

(Chhota technical decision: admin "approve" aur "refund" **do alag steps** honge — pehle return approve, item wapas aane par phir refund — taaki paisa pehle se na chala jaaye. Merge karna ho to batao.)

---

## 1. Goal

Delivered order pe customer ek "Return" request kar sake (sirf pehli baar). Admin us request ko approve/reject kare. Approve hone par admin refund process kare — refund = **paid amount − delivery charge** — jo Razorpay se wapas jaaye. Saari progress Spec 12 wali timeline mein dikhe.

**In scope**
- Customer self-return request (eligibility rules ke saath).
- Admin approve / reject (reason ke saath).
- Refund calculation (delivery charge deduct).
- Razorpay refund (Test Mode) + double-refund se bachaav.
- `delivered → return_requested → returned → refunded` flow; reject par `→ delivered`.
- Ineligible case par customer ko Contact Us ki taraf bhejna (link placeholder).

**NOT in scope**
- Item-level (partial) return. ❌ (poora order only)
- Contact Us page + WhatsApp complaint form → **Feature C**.
- Real courier reverse-pickup API. ❌
- Live/production refunds (KYC ke baad).

---

## 2. Prerequisites — implement karne se PEHLE verify karo (db.py mein)

Ye feature in cheezon par depend karta hai. Phase 0 mein in 3 ko confirm karo; agar nahi hain to pehle add karo:

1. Order ke paas **`razorpay_payment_id`** stored hai? (refund isi se hota hai). Agar payment ke time save nahi ho raha → ise save karna pehli zaroorat hai.
2. Order ke paas **delivery/shipping charge** ki value hai? (`delivery_charge` / `shipping`). Refund isse ghata kar nikalega. ("Free Shipping above ₹799" wala rule yahin se aata hai — free hua to deduct = 0.)
3. Order ke paas **paid amount / total** hai? (haan, hona chahiye).

> Agar in fields ke naam alag hain to spec ke andar wahi naam use karo — concept wahi rahega.

---

## 3. Return State Model (Spec 12 ke statuses ke upar)

```
delivered
   │  (customer: Return request, reason ke saath)
   ▼
return_requested
   ├─ (admin: Reject + reason) ──────────► delivered   (timeline mein note: "Return rejected: <reason>")
   │
   └─ (admin: Approve) ──► returned
                              │  (admin: Process refund → Razorpay success)
                              ▼
                           refunded
```

- Har transition Spec 12 ke `status_history` mein append ho (timestamp + note) — timeline khud-ba-khud update.
- Naya status value chahiye: **`return_requested`** (Spec 12 ke 8 mein ye add karo → `ALLOWED_STATUSES`).

---

## 4. Eligibility Rules (customer ka "Return" button kab dikhe)

Self-return button SIRF tab available ho jab **saari** sharten sachi hon (server-side enforce karna — sirf button chhupana kaafi nahi):

1. Order ka current status `delivered` hai.
2. Delivery ko **return window (default 7 din)** se zyada nahi hua.
3. Is user ne **pehle kabhi self-return nahi kiya** (per-user lifetime = 1). → "is user ke kisi bhi order ka status `returned` ya `refunded` ho chuka hai" = ineligible.
4. Is order pe abhi koi pending return nahi hai.

Agar koi sharte fail: button **na dikhe**; uski jagah message — "Is order ke liye direct return available nahi. Problem hai to **Contact Us** se request karein." (link `/contact` par — page Feature C mein banegi).

> Order-detail API customer ko ek boolean `can_self_return` bheje (ye saari sharten server pe check karke), taaki frontend bas dikhaye/chhupaye.

---

## 5. Refund Calculation (server pe, client par bharosa NAHI)

```
refund_amount = amount_paid − delivery_charge
(agar delivery free thi → delivery_charge = 0 → poora refund)
refund_amount kabhi negative nahi (0 se neeche na jaaye)
```

- Server hi compute kare. Client jo bheje wo **ignore** karo.
- Razorpay ko amount **paise mein** chahiye → `refund_paise = round(refund_amount * 100)`.
- Refund se pehle admin ko computed amount dikhe (e.g., "Refund ₹650 = ₹699 − ₹49 delivery") taaki confirm kar sake.

---

## 6. Data Model Changes (additive)

`orders` table mein naye columns (sab nullable, `migrate_db()` se, idempotent):

- `return_requested_at` — DATETIME
- `return_reason` — TEXT (customer ne kya likha)
- `return_rejected_reason` — TEXT (admin ne reject kyun kiya)
- `refund_amount` — number (rupees) — process hone par set
- `razorpay_refund_id` — TEXT (Razorpay refund id — idempotency ke liye bhi)

> Naya `users` column **zaroori nahi** — "first time" eligibility orders se derive ho jaati hai (section 4). Migration purane data ko chhua nahi karegi.

---

## 7. Backend Changes (API)

**`ALLOWED_STATUSES`** mein `return_requested` add (baaki Spec 12 se already hain).

**Customer endpoint — `POST /api/orders/<id>/return-request`** (auth zaroori)
- Verify: logged-in user **isi order ka maalik** hai.
- Server-side eligibility re-check (section 4) — fail to `403/400` clear message.
- Set `status = return_requested`, `return_reason`, `return_requested_at`; `status_history` append.
- Return updated order.

**Admin endpoints (admin-only):**
- `POST /api/admin/orders/<id>/return-approve` → guard: current status `return_requested` hona chahiye. Set `status = returned`; history append.
- `POST /api/admin/orders/<id>/return-reject` (body: `reason`) → guard: `return_requested`. Set `status = delivered`, `return_rejected_reason`; history append.
- `POST /api/admin/orders/<id>/refund` → **money endpoint, sabse careful:**
  - Guard: status `returned` hona chahiye.
  - **Idempotency:** agar `razorpay_refund_id` already set hai ya status `refunded` hai → reject (double refund block).
  - Server-side `refund_amount` compute (section 5).
  - Razorpay refund call: `client.payment.refund(order.razorpay_payment_id, {"amount": refund_paise, "speed": "normal"})`.
  - Success → save `refund_amount`, `razorpay_refund_id`; `status = refunded`; history append ("Refunded ₹X, delivery ₹Y deducted").
  - Razorpay error → status na badlo, clear error message, log karo.

**Order detail response** mein add: `can_self_return` (bool), `refund_amount`, `return_reason`, `return_rejected_reason`.

---

## 8. Frontend Changes (React)

**`frontend/src/pages/OrderDetailPage.jsx`** — status ke hisaab se customer ko dikhe:
- `delivered` + `can_self_return` true → **"Return Order"** button → ek chhota modal/box jisme reason likhe → submit → `return-request` API.
- `delivered` + `can_self_return` false → message + **Contact Us** link (`/contact`).
- `return_requested` → "Return request bheja gaya — admin review pending."
- `returned` → "Return approve ho gaya — refund process ho raha hai."
- `refunded` → "Refund ho gaya: ₹X (delivery ₹Y deducted)."
- reject hua to (status `delivered` + `return_rejected_reason`) → "Pichhla return reject hua: <reason>." (subtle note)

**Admin return management** (`AdminOrders.jsx` ya naya `admin/AdminReturns.jsx`):
- `return_requested` orders ki list (filter).
- Har ek pe: customer ka reason dikhe + **Approve** / **Reject (reason)** buttons.
- `returned` orders pe: **Process Refund** button — computed refund amount (₹X = ₹total − ₹delivery) confirm dikhae, phir refund API.
- Loading/disabled state taaki double-click se double request na jaaye.

**`frontend/src/api/orders.js` / `admin.js`** — naye API calls add (return-request, approve, reject, refund).

**`frontend/src/index.css`** — return/refund badges + button states (brand colors: terracotta CTA, green success, red/grey reject).

---

## 9. User Stories

- **As a customer**, I want a "Return" button on a delivered order so I can request a return myself (the first time), and clearly see if I'm not eligible and where to go instead.
- **As a customer**, I want to see my return's progress (requested → approved → refunded) and the exact refund amount with delivery deducted.
- **As an admin**, I want to approve or reject return requests with a reason.
- **As an admin**, I want to process the refund with a server-computed amount and have the money returned via Razorpay, without any risk of double-refunding.

---

## 10. Acceptance Criteria (Given / When / Then)

1. **Eligible self-return**
   - Given a delivered order within the return window for a user who has never self-returned,
   - When the customer opens it, Then a "Return Order" button shows; submitting a reason sets status to `return_requested` and the timeline logs it.

2. **Ineligible (already used)**
   - Given a user who already has a `returned`/`refunded` order,
   - When they open another delivered order, Then no Return button shows — instead a Contact Us message/link.

3. **Outside window**
   - Given a delivered order older than the return window,
   - When the customer opens it, Then no Return button (Contact Us message instead).

4. **Admin approve**
   - Given an order in `return_requested`,
   - When admin approves, Then status → `returned`, timeline logs it, customer sees "refund processing."

5. **Admin reject**
   - Given an order in `return_requested`,
   - When admin rejects with a reason, Then status → `delivered`, reason stored, customer sees the reject note, and (since no returned/refunded order exists) the user may still be eligible later per policy.

6. **Refund (happy path)**
   - Given an order in `returned` with a valid `razorpay_payment_id`,
   - When admin processes refund, Then server computes `paid − delivery`, calls Razorpay (test), saves `razorpay_refund_id` + `refund_amount`, status → `refunded`, timeline shows refunded amount.

7. **No double refund**
   - Given an order already `refunded`,
   - When a refund is attempted again, Then it is rejected (no second Razorpay call).

8. **Refund amount correctness**
   - Given paid ₹699 with ₹49 delivery, Then refund = ₹650. Given free delivery, Then refund = full paid amount.

---

## 11. Security Requirements (review ka focus)

- **AuthZ:** customer sirf apne order pe return-request kar sake; saare admin endpoints admin-only.
- **Server-side eligibility:** button chhupana kaafi nahi — return-request endpoint khud delivered + window + first-time re-check kare.
- **Idempotent refund:** `razorpay_refund_id`/`refunded` set ho to dobaara refund block (double-spend roko).
- **Amount integrity:** refund amount **server** compute kare; client-sent amount totally ignore.
- **Status-transition guards:** approve sirf `return_requested` se, refund sirf `returned` se; warna 400.
- **Razorpay secret** sirf server-side; refund call kabhi frontend se nahi.
- **Input sanitize:** `return_reason`, `reject_reason` trim + length cap.
- **Test Mode only** jab tak go-live KYC nahi — spec/README mein note.
- security-review agent in sab ko explicitly check kare.

---

## 12. Definition of Done

- [ ] Prerequisites (section 2) verified/added: `razorpay_payment_id`, delivery charge, paid amount available.
- [ ] `migrate_db()` adds 5 columns idempotently; no data loss.
- [ ] `return_requested` added to `ALLOWED_STATUSES`.
- [ ] Customer return-request endpoint with server-side eligibility + ownership check.
- [ ] Admin approve / reject(reason) / refund endpoints with transition guards.
- [ ] Refund: server-computed amount, Razorpay test refund, idempotent, fields saved.
- [ ] `can_self_return` + return/refund fields in order detail API.
- [ ] OrderDetailPage: button/message per status; AdminReturns/AdminOrders management UI.
- [ ] Brand-styled + responsive (375/768/1280).
- [ ] Existing tests pass; new tests cover eligibility, transitions, refund calc, double-refund block (test-writer stage).
- [ ] **security-review pass** (section 11).

---

## 13. Browser Test Script (user khud browser mein check kare)

> Backend `python app.py` + frontend `npm run dev` dono chalu. Razorpay **Test Mode**.

1. **Setup:** ek order ko (Spec 12 ke admin controls se) `delivered` tak le jao. Wahi customer se login raho.
2. **Eligible return:** order detail kholo → "Return Order" button dikhe. Reason likh ke submit karo → status "Return requested" dikhe, timeline mein naya step.
3. **Admin reject:** admin se us request ko reason ke saath reject karo → customer page pe order wapas `delivered` + reject note dikhe.
4. **Admin approve:** customer dobaara return request kare (abhi bhi eligible, kyunki koi returned/refunded nahi) → admin approve kare → status `returned`, customer ko "refund processing" dikhe.
5. **Process refund:** admin "Process Refund" daba ke confirm kare → refund amount sahi dikhe (₹total − ₹delivery) → Razorpay test refund success → status `refunded`, customer ko "Refund ₹X (delivery ₹Y deducted)" dikhe. Razorpay test dashboard pe refund entry check karo.
6. **Double-refund block:** wahi order phir se refund karne ki koshish → block ho (error), dobaara paisa na jaaye.
7. **First-time limit:** ab usi user ke kisi doosre delivered order par jao → "Return Order" button NA dikhe, balki Contact Us message dikhe.
8. **Window check:** ek delivered order jiski delivery purani hai (window se zyada) → button na dikhe.
9. **Refund calc:** ek free-delivery order (₹799+) return karo → refund poora aaye (kuch deduct na ho).
10. **Mobile (375px):** button, modal, admin controls saaf dikhein. Regression: ek normal naya order checkout/pay karke dekho kuch toota to nahi.

---

## 14. Risks / Notes

- **Asli paisa:** Razorpay Test Mode mein hi sab test karo. Live refunds KYC ke baad. Galat refund amount/double-refund se asli nuksan ho sakta — isliye section 11 strict follow ho.
- **"First time" policy:** thodi strict hai (ek hi self-return). Genuine repeat customers ko Contact Us route milega (Feature C) — wo path banne tak ineligible customers sirf message dekhte rahenge (link dead ho sakta jab tak C nahi banti). Theek hai? Chaho to window/limit baad mein loosen kar sakte ho.
- **Reverse pickup:** item physically wapas kaise aayega — wo offline/WhatsApp se (Feature C). Yahan sirf status + paisa handle ho raha.
- **Admin manual returned/refunded (Spec 12):** agar admin ne manually set kiya tha, wo bhi first-time count mein aa sakta — minor edge case, abhi ignore.