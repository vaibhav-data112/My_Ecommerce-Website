# Spec 14 — Contact Us Page + WhatsApp

> **Feature:** C — Ek "Contact Us" page: complaint/contact form (DB mein save) + ek WhatsApp button (`wa.me` link). Repeat-problem wale customers (jo Feature B mein self-return ke eligible nahi) yahan se problem bhej sakein.
> **Branch:** `feature/contact-us`
> **Closes loop:** Feature B ka "Contact Us" link (`/contact`) ab asli page kholega.
> **Key point:** WhatsApp **integrate nahi** hota — button bas owner ke number par WhatsApp khol deta hai (prefilled text ke saath). Customer photo khud WhatsApp mein attach karta hai. Hum koi WhatsApp API use nahi kar rahe.

---

## ⚠️ 0. Confirm-before-implement (3 chhote decisions)

Defaults maine rakh diye — badalna ho to batao:

1. **WhatsApp number:** owner ka asli number country code ke saath chahiye (jaise `919336768655`). → **Tum doge** (spec mein placeholder hai).
2. **Form messages kahaan jaayein:** abhi **DB mein save** + admin page pe dikhein (koi email nahi — email feature alag/future hai). → **Default: DB + admin view(vaibhavtiw2008@gmail.com).**
3. **Form kaun bhar sake:** sabhi (guest bhi) — login ho to name/email auto-fill. → **Default: public form.**

---

## 1. Goal

Ek public Contact Us page jahan koi bhi apni problem (especially return/product issue) likh ke bhej sake. Message DB mein save ho aur admin ek page se dekh/resolve kar sake. Saath hi ek WhatsApp button jo owner ke number par chat khol de (prefilled message), jahan customer photo ke saath detail bhej sake.

**In scope**
- `/contact` page: contact/complaint form + WhatsApp button.
- Form submit → message DB mein save.
- Admin page: messages list + "mark resolved".
- Footer aur Feature B ke ineligible-return message se `/contact` link.

**NOT in scope**
- Email notification on submit (SMTP) → **future feature** (#4).
- WhatsApp API / auto-reply / photo upload on website. ❌ (photo WhatsApp khud handle karega)
- Live chat. ❌

---

## 2. Prerequisites / Assumptions

- Maan rahe hain abhi koi dedicated Contact page nahi hai (Footer feature alag hai). Agar hai to extend karo.
- Owner ka WhatsApp number country-code ke saath milega (section 0).

---

## 3. WhatsApp Button (kaise kaam karega)

- Link format:
  ```
  https://wa.me/<NUMBER>?text=<URL-encoded prefilled message>
  ```
  - `<NUMBER>` = country code + number, bina `+`, bina space (e.g., `919876543210`).
  - `text` = prefilled message, **URL-encoded**.
- Prefilled text example:
  ```
  Namaste Karvii Spices 🌶️ — mujhe apne order mein problem hai. Order no: ____.
  Problem: ____ (photo neeche bhej raha/rahi hun)
  ```
- Button click → naye tab mein WhatsApp khule (mobile pe app, desktop pe WhatsApp Web). Customer apni baat + photo wahin bhejta hai.
- **Number kahaan rakhein:** beginner-friendly — `frontend/src/config.js` mein ek constant (`WHATSAPP_NUMBER`), ya `frontend/.env` mein `VITE_WHATSAPP_NUMBER`. (Number public hi hota hai — contact button hai — to frontend mein theek hai.)

---

## 4. Data Model (naya chhota table)

Naya table `contact_messages` (`migrate_db()` se banao):

| column | type | note |
|---|---|---|
| `id` | INTEGER PK | |
| `user_id` | INTEGER nullable | login ho to set, guest ke liye null |
| `name` | TEXT | required |
| `email` | TEXT | required |
| `order_number` | TEXT nullable | optional |
| `category` | TEXT | "Return issue" / "Product issue" / "Order issue" / "Other" |
| `message` | TEXT | required |
| `status` | TEXT | default `new` (`new` / `resolved`) |
| `created_at` | DATETIME | default now |

> Migration idempotent (table na ho to banao); purane data se koi lena-dena nahi.

---

## 5. Backend Changes (API)

**Public endpoint — `POST /api/contact`**
- Body: `name, email, order_number?, category, message`.
- Validate: required fields present; `email` basic format; lengths cap (name ≤100, message ≤2000, order_number ≤50); `category` allowed list mein ho.
- **Anti-spam:** ek honeypot field (jaise hidden `website`) — bhara hua aaye to silently ignore. (Optional: simple rate-limit per IP.)
- Logged-in ho to `user_id` set karo (warna null).
- DB mein save → success message return.

**Admin endpoints (admin-only):**
- `GET /api/admin/contacts` → saari messages (latest pehle), optional `status` filter.
- `PATCH /api/admin/contacts/<id>` → `status = resolved`.

---

## 6. Frontend Changes (React)

**Naya page `frontend/src/pages/ContactPage.jsx`** (route `/contact`):
- Heading + chhota intro ("Koi problem? Hamein batayein").
- **Form:** name, email (login ho to pre-filled), order number (optional), category (dropdown), message (textarea), + hidden honeypot. Submit → `POST /api/contact`. Success/error message dikhe. Submit ke baad form clear.
- **WhatsApp button** (terracotta, WhatsApp icon): `wa.me` link (section 3) — naye tab mein khule.
- Brand-styled + responsive (375/768/1280).

**Routing:** `/contact` route add (App router mein).

**Links to `/contact`:**
- Footer mein "Contact Us".
- Feature B (Spec 13) ka ineligible-return message — ab uska `/contact` link asli page kholega. ✅

**Admin page `frontend/src/pages/admin/AdminContacts.jsx`:**
- Messages list: name, email, category, order no, message, date, status.
- "Mark resolved" button → `PATCH`.
- Admin nav/sidebar mein "Contact Messages" link add.

**`frontend/src/api/` mein** contact API module (submit + admin list + resolve).

**`frontend/src/index.css`** — form + WhatsApp button + admin list styling.

---

## 7. User Stories

- **As a customer (especially one not eligible for self-return)**, I want a Contact Us page to describe my problem, and a WhatsApp button to quickly message the owner with a photo.
- **As an admin**, I want to see all contact messages in one place and mark them resolved.

---

## 8. Acceptance Criteria (Given / When / Then)

1. **Submit form**
   - Given a visitor on `/contact`,
   - When they fill required fields and submit, Then the message is saved with status `new` and a success message shows.

2. **Validation**
   - Given a submit with a missing required field or bad email,
   - When submitted, Then a clear error shows and nothing is saved.

3. **Logged-in prefill**
   - Given a logged-in customer opens `/contact`,
   - Then name and email are pre-filled (still editable), and the saved message has their `user_id`.

4. **WhatsApp button**
   - Given the page,
   - When the WhatsApp button is clicked, Then WhatsApp opens in a new tab to the owner's number with the prefilled text.

5. **Admin view + resolve**
   - Given submitted messages,
   - When admin opens AdminContacts, Then they see all messages; clicking "Mark resolved" sets status to `resolved`.

6. **B loop closed**
   - Given an ineligible-return order (Spec 13),
   - When the customer clicks its "Contact Us" link, Then `/contact` opens.

7. **Honeypot**
   - Given a bot fills the hidden honeypot field,
   - When submitted, Then it is silently ignored (not saved).

---

## 9. Security Requirements

- Public endpoint: validate + sanitize all inputs; length caps; allowed `category` only.
- Honeypot (+ optional simple rate-limit) for spam.
- Admin endpoints admin-only; ek user doosre ki messages na dekh sake (sirf admin dekhe).
- Output safe (React escape karta hai; admin list mein bhi raw HTML render mat karo).
- WhatsApp number sahi format; prefilled text URL-encoded (injection na ho).

---

## 10. Definition of Done

- [ ] `contact_messages` table migration (idempotent).
- [ ] `POST /api/contact` with validation + honeypot + optional user_id.
- [ ] Admin list + mark-resolved endpoints (admin-only).
- [ ] `ContactPage.jsx` with form + WhatsApp button; `/contact` route.
- [ ] Footer + Feature B message link to `/contact`.
- [ ] `AdminContacts.jsx` + admin nav link.
- [ ] WhatsApp number configured (config/env); link opens correctly.
- [ ] Brand-styled + responsive (375/768/1280).
- [ ] Existing tests pass; new tests cover submit + validation + honeypot + admin resolve.
- [ ] security-review pass (section 9).

---

## 11. Browser Test Script (user khud browser mein check kare)

> Backend `python app.py` + frontend `npm run dev` chalu.

1. **Page khule:** `/contact` par jao — form + WhatsApp button dikhe.
2. **WhatsApp:** button click karo → WhatsApp naye tab mein owner ke number + prefilled text ke saath khule (desktop pe WhatsApp Web).
3. **Validation:** khaali form ya galat email se submit karo → clear error, kuch save na ho.
4. **Submit success:** sahi data bharke submit → success message; form clear.
5. **Prefill:** customer login karke `/contact` kholo → name/email already bhare hon.
6. **Admin view:** admin se AdminContacts kholo → tumhara bheja message dikhe (category, order no, date, status = new).
7. **Resolve:** "Mark resolved" daba → status `resolved` ho jaaye.
8. **B link:** Spec 13 ke ineligible-return wale order par "Contact Us" link daba → `/contact` khule.
9. **Footer link:** footer ka "Contact Us" bhi `/contact` khole.
10. **Mobile (375px):** form, dropdown, WhatsApp button saaf dikhein. Regression: koi aur page toota to nahi.

---

## 12. Risks / Notes

- WhatsApp number **galat** hua to button kaam nahi karega — sahi country-code format zaroor (section 3).
- Abhi submit par admin ko **email notification nahi** jaata (sirf DB). Jab Email/SMTP feature banega, tab admin ko alert email add kar sakte ho.
- Spam zyada aaye to baad mein captcha/rate-limit strong kar sakte ho — abhi honeypot kaafi hai MVP ke liye.
- Photo website pe upload nahi hoti — wo intentionally WhatsApp ke through hai (simple aur free).