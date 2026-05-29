# 🔮 Future Ideas — E-Commerce Website (Backlog)

Ye un features ki list hai jo **abhi nahi banane** — par baad mein add kar sakte hain.
Inhe yahan likh diya hai taaki bhulein nahi, aur core website pehle complete ho jaye.

**Rule:** Pehle core flow complete karo (cart → checkout → payment → orders).
Website "bikne layak" ban jaye, uske baad ye polish/enhancement features banao —
har ek ko ek alag chhota feature (apni branch + spec) ki tarah, wahi 16-step SDD loop.

---

## 📦 Core features (pehle ye — abhi chal rahe hain)

| NN | Feature | Status |
| --- | --- | --- |
| 01 | Database Setup | ✅ Done |
| 02 | User Authentication | ✅ Done |
| 03 | Product Catalog | ✅ Done |
| 04 | Search & Filter | 🔄 In progress |
| 05 | Shopping Cart | ⬜ Next |
| 06 | Checkout | ⬜ |
| 07 | Payment | ⬜ |
| 08 | Order Management | ⬜ |
| 09 | Admin Dashboard | ⬜ |
| 10 | Reviews & Ratings | ⬜ |

---

## 🔮 Future / "baad mein" ideas (core ke baad)

### Search & Filter enhancements
- **Price-range slider** — filter products by min/max price.
  *Kab banayein:* jab products kaafi ho jayein (30-40+), ya core flow complete ho jaye. Tab tak slider ka faayda nahi dikhega kyunki products kam hain.
- **Search autocomplete** — type karte waqt suggestions dikhana.
- **Search inside description** — abhi sirf naam mein search hota hai; baad mein description text mein bhi.
- **Filter by brand / ratings** — jab brands aur reviews exist karein.

### Authentication enhancements
- **Forgot password / reset** — email pe reset link bhejna.
- **Email verification** — signup ke baad email confirm karwana (aapne ye pehle bhi socha tha — sahi soch thi, bas core ke baad).
- **Google login real setup** — abhi dummy credentials hain; real Google Cloud Client ID/Secret lena jab deploy karein.

### Profile & account
- **User profile page** — naam, address, password edit karna.
- **Saved addresses** — multiple delivery addresses.
- **Wishlist** — "save for later" products.

### Catalog enhancements
- **Real product images** — abhi placeholder dikhta hai; Admin Dashboard se asli images upload.
- **Product variants** — size, color options (clothing ke liye).
- **Related products** — "you may also like".

### Polish & growth (much later)
- **React frontend** — agar zyada interactive UI chahiye (aapne pucha tha). Pura frontend React mein, Flask ko API banana. Bada kaam — website ready hone ke baad.
- **Discount codes / coupons** — checkout pe.
- **Order tracking** — "where is my order" with status updates.
- **Email notifications** — order confirmation emails.
- **Deploy to internet** — website ko live server pe daalna taaki sab access kar sakein.

---

## 💡 Yaad rakhna

- Koi bhi future feature shuru karne se pehle uska **spec banao** (pehle features jaise), phir wahi 16-step loop.
- Ek baar mein ek hi feature — chhota aur focused.
- Ye list update karte raho: jo ban jaye usse ✅ karo, nayi ideas aaye to add karo.