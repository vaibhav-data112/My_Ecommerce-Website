# Spec 14 — Footer (Flipkart-style, with Social Links)

## 1. Maksad (Overview)
Har page ke bottom mein ek **rich footer section** banana hai — Flipkart/Amazon jaisa. Multiple columns mein useful links + social media buttons (WhatsApp, Instagram, YouTube, etc.) taaki customer aasaani se brand tak pahunch sake aur trust bane.
Footer `base.html` mein hoga, isliye **automatically har page pe** dikhega.

## 2. Scope (kya banega / kya nahi)
**In scope:**
- Multi-column footer (Flipkart jaisa): About, Help, Policy, Shop, Social/Contact
- **Social media buttons**: WhatsApp, Instagram, YouTube (aur jagah Facebook/X ke liye)
- Quick links: Home, All Products, My Orders, Wishlist, My Account
- Static info pages ke links: About Us, Contact Us, Privacy Policy, Terms (chhote simple pages)
- Newsletter / "Stay connected" signup box (UI ban jaye, abhi non-functional — baad mein backend)
- Bottom bar: copyright + "Made in India" type line
- Premium design (skill follow) — plum background, gold accents

**Out of scope (abhi nahi):**
- Working newsletter email backend (abhi sirf UI dikhega)
- Live chat widget
- App download badges (Play Store / App Store) — koi app nahi hai
- Language/currency switcher

## 3. Users
- **Sab users** (guest + logged-in) — footer sabko dikhe
- Logged-in user ko "My Orders / Wishlist / Account" links kaam karein; guest click kare to login pe jaye (existing behaviour)

## 4. Functional Requirements

### 4.1 Footer structure (columns)
1. **Column 1 — ABOUT**: About Us, Contact Us, Careers (optional), Our Story
2. **Column 2 — HELP**: FAQ, Shipping Info, Returns & Refunds, Track Order
3. **Column 3 — POLICY**: Privacy Policy, Terms of Use, Return Policy
4. **Column 4 — SHOP**: All Products, Categories, My Orders, Wishlist, My Account
5. **Column 5 — CONNECT (Social)**: WhatsApp, Instagram, YouTube, Facebook, X (Twitter), LinkedIn, Pinterest, Telegram, Email — clickable icons (jo link bhara hai sirf wahi dikhe)

### 4.2 Social links (saare platforms — config se editable)
6. Footer mein **saare common social platforms** ke buttons honge (bhale abhi link khaali ho):
   - **WhatsApp** → `https://wa.me/<NUMBER>`
   - **Instagram** → `https://instagram.com/<USERNAME>`
   - **YouTube** → channel link
   - **Facebook** → page link
   - **X (Twitter)** → profile link
   - **LinkedIn** → page link
   - **Pinterest** → profile link (fashion brand ke liye useful)
   - **Telegram** → channel link
   - **Email** → `mailto:<EMAIL>`
7. **Central config**: ye saare links ek hi jagah ek Python dict mein hon (app.py mein, jaise `SOCIAL_LINKS = {...}`), template usi se loop karke icons dikhaye. Taaki user ek file mein link bharkar update kar sake.
8. **Smart display**: agar kisi platform ka link khaali (`""`) hai to wo icon footer mein **na dikhe** (auto-hide). Jaise-jaise user link bharega, wo icon apne aap dikhne lagega.
9. Saare external links `target="_blank" rel="noopener"` ke saath (naya tab, secure).

### 4.3 Static info pages
12. Chhote simple pages banao (About, Contact, Privacy, Terms) — har ek ek template, footer se linked. Content placeholder/basic (user baad mein bhar le). Routes: `/about`, `/contact`, `/privacy`, `/terms`.

### 4.4 Bottom bar
13. Footer ke neeche ek patli bar: "© 2026 Karvii. All rights reserved." + optional "Crafted in India ❤️"

### 4.5 Placement
14. Footer `base.html` mein content ke baad — har page pe automatically dikhe.
15. Footer hamesha page ke bottom mein (agar content chhota ho to bhi neeche chipke — sticky-footer layout).

## 5. Non-Functional Requirements
- **Design:** `ecommerce-ui-design` skill — plum background (`--color-plum`), gold links/icons (`--color-gold`), cream text. Premium, clean, organized.
- **Responsive:** desktop pe columns side-by-side, mobile pe stack (ek ke neeche ek). Toote na.
- **Social icons:** simple inline SVG ya icon font — koi external heavy library na ho (plain CSS site).
- **Accessibility:** links pe proper text/aria-label.
- Existing pages/features pe koi asar na pade.

## 6. Data / DB changes
- **Koi DB change nahi** — footer + static pages purely frontend/template hain.
- Social links/email aseter ek jagah (config/constant in app.py ya base.html) se aayein taaki badalna aasaan ho.

## 7. User Stories + Acceptance Criteria

**US-1 — Footer har page pe**
- Given: main site pe kisi bhi page pe hun
- When: neeche scroll karun
- Then: ek organized footer dikhe with columns + social buttons

**US-2 — WhatsApp link**
- Given: footer mein WhatsApp button hai
- When: use click karun
- Then: WhatsApp chat naye tab mein khule (wa.me link)

**US-3 — Instagram/YouTube link**
- Given: footer mein Instagram aur YouTube icons hain
- When: click karun
- Then: respective profile/channel naye tab mein khule

**US-4 — Quick links kaam karein**
- Given: footer ke SHOP column mein All Products, My Orders links hain
- When: click karun
- Then: sahi page khule (orders pe login-required behaviour kaam kare)

**US-5 — Static pages**
- Given: footer mein About / Privacy links hain
- When: click karun
- Then: us page ka content khule (basic placeholder content)

**US-6 — Responsive**
- Given: main mobile/chhoti screen pe hun
- When: footer dekhun
- Then: columns ek ke neeche ek stack ho jaayein, sab readable rahe

**US-7 — Design**
- Given: footer dikh raha hai
- When: dekhun
- Then: plum background, gold links, premium look — baaki site se match kare

## 8. Edge Cases
- Social link na bhara ho (placeholder) → button dikhe par "#" pe jaye (ya hide) — user baad mein bharega
- Bahut chhota page content → footer phir bhi bottom pe (sticky footer)
- Lamba footer mobile pe → scroll ho, toote na
- External link → hamesha naye tab mein (current site se na hate)

## 9. Decisions (Vaibhav ne confirm kiya — "sab kuch daal do")
1. Social platforms — **SAARE** daalo (WhatsApp, Instagram, YouTube, Facebook, X, LinkedIn, Pinterest, Telegram, Email). Khaali wale auto-hide. ✅
2. Static pages (About/Contact/Privacy/Terms) — **sab bana do** placeholder content ke saath, user baad mein bharega. ✅
3. Newsletter signup box — **daal do** (UI bana do, abhi non-functional — sirf "Subscribe" dikhe, baad mein backend judega). ✅
4. App download badges — **skip** (koi app nahi hai abhi). ✅

## 10. Definition of Done ✅

- [ ] Footer har page ke bottom pe dikh raha hai (base.html se)
- [ ] Multi-column layout (About, Help, Policy, Shop, Connect)
- [ ] WhatsApp button → wa.me link, naye tab
- [ ] Instagram button → profile link, naye tab
- [ ] YouTube button → channel link, naye tab
- [ ] Email link (mailto) kaam karta hai
- [ ] Quick links (All Products, Orders, Wishlist, Account) sahi pages pe jaate hain
- [ ] Static pages (About/Contact/Privacy/Terms) ban gaye + linked
- [ ] Bottom bar mein copyright dikhta hai
- [ ] Footer responsive hai (mobile pe stack)
- [ ] Premium design (skill follow) — plum/gold/cream
- [ ] Social links ek jagah se editable hain
- [ ] Browser mein khud test kiya

## 11. Browser Test Script 🧪 (step-by-step kya check karo)

**Test 1 — Footer dikhta hai**
1. `python app.py`, koi bhi page kholo
2. Neeche scroll karo
3. ✅ Organized footer with columns + social buttons dikha? → Pass
4. Doosra page kholo (cart/product) — ✅ wahi footer dikha? → Pass

**Test 2 — WhatsApp**
1. Footer mein WhatsApp button click karo
2. ✅ Naye tab mein WhatsApp/wa.me khula? → Pass
   (Note: asli number daalne ke baad hi sahi chat khulega)

**Test 3 — Instagram & YouTube**
1. Instagram icon click → ✅ naye tab mein Instagram khula? → Pass
2. YouTube icon click → ✅ naye tab mein YouTube khula? → Pass

**Test 4 — Email**
1. Email link click karo
2. ✅ Mail app/compose khula? → Pass

**Test 5 — Quick links**
1. SHOP column → "All Products" click → ✅ products page khula? → Pass
2. "My Orders" click → ✅ orders (ya login) page khula? → Pass
3. "Wishlist" click → ✅ wishlist page khula? → Pass

**Test 6 — Static pages**
1. "About Us" click → ✅ about page khula (basic content)? → Pass
2. "Privacy Policy" click → ✅ privacy page khula? → Pass

**Test 7 — Responsive**
1. Browser window chhoti karo (ya phone pe kholo)
2. ✅ Footer columns ek ke neeche ek stack ho gaye, sab readable? → Pass
3. ✅ Kuch toota/overlap nahi hua? → Pass

**Test 8 — Bottom bar**
1. ✅ Sabse neeche "© 2026 Karvii..." copyright dikh raha? → Pass

**Test 9 — Design**
1. ✅ Footer plum background + gold links/icons hai?
2. ✅ Baaki site (navbar etc.) se match kar raha, premium lag raha? → Pass

**Test 10 — External link safety**
1. ✅ Social links naye tab mein khulte hain (current site band nahi hoti)? → Pass