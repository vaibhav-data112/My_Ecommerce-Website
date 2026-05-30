# Spec 11 — Product Image Upload

## 1. Maksad (Overview)
Admin ko product **add/edit** karte waqt apne **computer se image file** (jpg/png/webp) upload karne ki facility deni hai.
Abhi sirf URL field se image daal sakte hain ya grey placeholder (letter box) dikhta hai.
Iske baad uploaded image **catalog grid** aur **product detail page** dono pe dikhegi.

## 2. Scope (kya banega / kya nahi)
**In scope:**
- Admin "Add Product" form mein file upload input
- Admin "Edit Product" form mein current image preview + replace
- Uploaded file server pe save (`static/uploads/products/`)
- File validation (type + size)
- DB mein image path store
- Display priority: uploaded image → URL → placeholder

**Out of scope (abhi nahi):**
- Ek product ke 1 se zyada image
- Image crop / edit
- Cloud storage (abhi local folder hi)

## 3. Users
- **Admin** (`vaibhavtiw2008@gmail.com`) — upload / replace karta hai
- **Customer** — sirf image dekhta hai

## 4. Functional Requirements
1. Add-product form mein **file input (optional)**. URL field bhi rahega (optional alternative).
2. Allowed types: `.jpg .jpeg .png .webp`. Max size: **5 MB**.
3. File `static/uploads/products/` mein **unique + safe filename** se save ho (folder na ho to auto-create).
4. DB ke products table mein image column update ho (existing column reuse — naam confirm karna hai).
5. Edit form mein **current image dikhe** + naya upload karke replace kar sake.
6. Display priority: **uploaded file → URL → placeholder letter box**.
7. Invalid file aaye to **friendly error** dikhe, form wapas dikhe, kuch save na ho.

## 5. Non-Functional Requirements
- **Security:** filename sanitize (`secure_filename`), sirf allowed extensions, size check.
- **Backward compatible:** purane products (URL ya placeholder wale) bilkul waise hi chalte rahein.
- `static/uploads/products/` ko `.gitignore` mein daalna (taaki repo bhari na ho) — optional note.

## 6. Data / DB changes
- products table ke image column ka **exact naam confirm karna** (shayad `image_url`).
- Sabse simple plan: wahi ek column use karo — usme ya to full URL ho **ya** local path jaise `uploads/products/xyz.jpg`. Display logic dono handle kar lega.
- Agar naya column chahiye to `migrate_db()` mein add karna.

## 7. User Stories + Acceptance Criteria

**US-1 — Admin image upload karta hai (add)**
- Given: main admin hun aur add-product form pe hun
- When: ek valid `.jpg` file choose karke product save karta hun
- Then: file server pe save hoti hai aur catalog + detail page pe wahi image dikhti hai

**US-2 — Admin image replace karta hai (edit)**
- Given: ek product ke paas pehle se image hai
- When: edit form pe naya file upload karke save karta hun
- Then: nayi image purani ki jagah dikhne lagti hai

**US-3 — Galat file reject ho**
- Given: main ek 5 MB ki `.pdf` file choose karta hun
- When: save dabata hun
- Then: error message dikhta hai aur product **save nahi** hota

**US-4 — Fallback kaam kare**
- Given: product ke paas na uploaded image hai na URL
- When: customer use dekhta hai
- Then: pehle jaisa grey placeholder letter box dikhta hai

**US-5 — Purane URL products pe asar na ho**
- Given: ek product jiska image URL se set hai
- When: koi change nahi hota
- Then: wo image pehle jaisi dikhti rehti hai

## 8. Edge Cases
- Same filename 2 baar → unique suffix lag jaye
- Bahut bada file → save se pehle hi reject
- Upload folder na ho → automatically ban jaye
- (Optional, abhi nahi) product delete pe uski image file bhi delete — backlog

## 9. Open Questions (Vaibhav confirm kare)
1. products table mein image column ka exact naam kya hai? — **Claude Code confirm karega**
2. URL field rakhein ya hata dein? — ✅ **RAKHO** (dono support)
3. Max size 5 MB theek hai? — ✅ **CONFIRMED** (HD AI images ke liye)

---

## 10. Definition of Done ✅

- [ ] Admin "Add Product" form mein file upload input dikh raha hai
- [ ] Admin "Edit Product" form mein current image preview + replace option hai
- [ ] Valid image upload hoti hai aur `static/uploads/products/` mein save hoti hai
- [ ] Catalog grid pe uploaded image dikh rahi hai
- [ ] Product detail page pe uploaded image dikh rahi hai
- [ ] Invalid file (galat type ya > 5 MB) pe friendly error dikh raha hai
- [ ] Purane products (URL/placeholder wale) bilkul pehle jaisi tarah kaam kar rahe hain
- [ ] Browser mein khud test karke confirm kiya