# Spec 12 — Wishlist (Saved Products)

## 1. Maksad (Overview)
Logged-in customer kisi product ko **dil/heart icon** se "Wishlist" mein save kar sake, taaki baad mein aasaani se dekh sake ya khareed sake.
Ek alag **"My Wishlist"** page ho jahan saare saved products dikhein. Wahaan se product detail pe ja sake, cart mein daal sake, ya wishlist se hata sake.

## 2. Scope (kya banega / kya nahi)
**In scope:**
- Product card aur product detail page pe **heart icon** (saved / not-saved do state)
- Click pe wishlist mein add/remove (toggle)
- Navbar mein **"Wishlist"** link (count ke saath, optional)
- Alag **My Wishlist page** — saved products grid
- Wishlist se product hatana
- Wishlist se direct "Add to Cart"
- **Per-user** wishlist (har user ki apni, private)

**Out of scope (abhi nahi):**
- Wishlist share karna (link bhejna)
- Price-drop notification
- Guest (bina login) wishlist
- Multiple wishlists / folders

## 3. Users
- **Logged-in customer** — apni wishlist manage karta hai
- **Guest (not logged in)** — heart dabaye to login pe bheja jaye (login-required)

## 4. Functional Requirements
1. Ek naya DB table `wishlist_items` (ya jo db.py ke pattern se match kare): `user_id`, `product_id`, `added_at`. Ek user + ek product ka **sirf ek hi entry** (duplicate na ho).
2. Product card aur detail page pe **heart icon button**:
   - Agar product wishlist mein hai → bhara (filled) gold dil
   - Nahi hai → khaali (outline) dil
3. Heart click → wishlist mein add/remove **toggle** ho, page wahi rahe (ya turant update dikhe).
4. Guest heart dabaye → login page pe redirect (login ke baad wapas).
5. **My Wishlist page** (`/wishlist`): saved products ka grid (wahi product-card style), each pe "Add to Cart" + "Remove" button.
6. Navbar mein "Wishlist" link (My Orders ke paas).
7. Wishlist se "Add to Cart" → product cart mein jaye (wishlist se hate ya rahe — **suggestion: wishlist mein rehne do**, sirf cart mein add ho).

## 5. Non-Functional Requirements
- **Privacy:** ek user doosre ki wishlist na dekh paye.
- **Backward compatible:** baaki saare pages/features waise hi chalein.
- **Design:** `ecommerce-ui-design` skill follow kare — gold heart, plum/cream theme, product-card reuse.
- Agar product delete ho jaye (admin se) to wishlist mein wo gracefully handle ho (na dikhe / skip).

## 6. Data / DB changes
- Naya table `wishlist_items`:
  - `id` (primary key)
  - `user_id` (foreign key → users)
  - `product_id` (foreign key → products)
  - `added_at` (timestamp)
  - UNIQUE(user_id, product_id) — duplicate rokne ke liye
- `db.py` ke `migrate_db()` / init pattern follow karke add karna.
- Helper functions: add_to_wishlist, remove_from_wishlist, get_user_wishlist, is_in_wishlist.

## 7. User Stories + Acceptance Criteria

**US-1 — Product wishlist mein add karna**
- Given: main logged-in hun aur ek product dekh raha hun jo wishlist mein nahi hai
- When: heart icon dabata hun
- Then: dil bhar jaata hai (filled gold) aur product meri wishlist mein add ho jaata hai

**US-2 — Wishlist se remove karna**
- Given: ek product meri wishlist mein hai (filled heart)
- When: heart dobara dabata hun
- Then: product wishlist se hat jaata hai aur dil khaali (outline) ho jaata hai

**US-3 — My Wishlist page dekhna**
- Given: meri wishlist mein 3 products hain
- When: navbar se "Wishlist" kholta hun
- Then: teeno products grid mein dikhte hain, each pe Add-to-Cart aur Remove

**US-4 — Wishlist se cart mein daalna**
- Given: My Wishlist page pe ek product hai
- When: uska "Add to Cart" dabata hun
- Then: product cart mein add ho jaata hai (cart count badhe)

**US-5 — Guest ko login pe bhejna**
- Given: main logged-in nahi hun
- When: kisi product ka heart dabata hun
- Then: login page khulta hai (login ke baad wapas product pe)

**US-6 — Privacy**
- Given: do alag users (A aur B)
- When: A apni wishlist dekhe
- Then: A ko sirf apne saved products dikhein, B ke nahi

## 8. Edge Cases
- Same product 2 baar add → duplicate na bane (UNIQUE constraint)
- Empty wishlist → "Aapki wishlist khaali hai" friendly message + "Shop now" button
- Wishlist ka product admin ne delete kar diya → wishlist mein na dikhe (skip)
- Out-of-stock product wishlist mein → dikhe, par "Add to Cart" disable ya "Out of stock" label

## 9. Open Questions (Vaibhav confirm kare)
1. Navbar mein wishlist count number dikhana hai? — **suggestion: haan, chhota gold badge** (cart jaisa)
2. Wishlist se "Add to Cart" karne pe product wishlist mein rahe ya hat jaye? — **suggestion: rehne do**
3. Heart icon kahan-kahan dikhe — sirf detail page pe ya product card pe bhi? — **suggestion: dono jagah**

## 10. Definition of Done ✅

- [ ] `wishlist_items` table ban gaya (unique constraint ke saath)
- [ ] Product card pe heart icon dikh raha hai (filled/outline state sahi)
- [ ] Product detail page pe heart icon dikh raha hai
- [ ] Heart click se add/remove toggle kaam kar raha hai
- [ ] Guest heart dabaye to login pe jaata hai
- [ ] Navbar mein "Wishlist" link (+ count badge) dikh raha hai
- [ ] My Wishlist page pe saved products grid dikh raha hai
- [ ] Wishlist se "Add to Cart" kaam kar raha hai
- [ ] Wishlist se "Remove" kaam kar raha hai
- [ ] Empty wishlist pe friendly message dikhta hai
- [ ] Doosre user ki wishlist nahi dikhti (privacy)
- [ ] Design `ecommerce-ui-design` skill ke hisaab se premium dikhta hai
- [ ] Browser mein khud test karke confirm kiya