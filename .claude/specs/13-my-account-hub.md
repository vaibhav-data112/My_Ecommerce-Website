# Spec 13 — My Account Hub (Profile Section)

## 1. Maksad (Overview)
Ek poora **"My Account"** area banana hai — Flipkart/Amazon jaisa — jahan logged-in user apni profile dekhe aur manage kare.
Navbar ke right side pe ek **avatar circle** (naam ka pehla letter) dikhe, jise click karne pe ek **dropdown menu** khule (My Profile, Orders, Wishlist, Addresses, Settings, Logout).
"My Account" page pe **left sidebar menu + right content** layout ho (Flipkart jaisa).

## 2. Scope (kya banega / kya nahi)
**In scope:**
- **Avatar circle** navbar ke right side pe — naam ka pehla letter (jaise "V"), gold/plum circle mein
- **Account dropdown menu** — avatar click pe khule: My Profile, My Orders, Wishlist, Saved Addresses, Settings, Logout. Guest ko: Login / Sign Up
- **Navbar layout fix** — account/naam/Admin badge sab **right side** pe (abhi left mein hai)
- **My Account page** (`/account`) — left sidebar + right content layout
- **Profile edit** — naam, phone number, profile photo (upload), basic info dikhe
- **Member since** date + email (read-only) + basic account info
- **Saved Addresses** — multiple address add / edit / delete, ek "default" address
- **Password change** — old password daalo, naya 2 baar
- **Notification preferences** — email notifications on/off (checkbox)
- **Quick links** — profile dashboard pe My Orders, Wishlist ke shortcut cards

**Out of scope (abhi nahi — backlog):**
- Membership/Prime/Plus
- Gift cards, wallet, saved payment cards
- Account delete
- KYC, GST details
- Recently viewed products
- 2-factor auth

## 3. Users
- **Logged-in customer** — apni profile/address/settings manage kare
- **Admin** — wahi profile area, plus avatar dropdown mein "Admin Dashboard" link extra dikhe
- **Guest** — avatar ki jagah "Login / Sign Up" dikhe

## 4. Functional Requirements

### 4.1 Navbar links (revised design)
1. **After login** → koi avatar circle ya dropdown nahi. Har feature **seedha navbar mein alag link** ke roop mein dikhe: My Profile | My Orders | My Wishlist (badge) | Saved Addresses | Settings | Cart (badge) | Admin (agar admin ho) | Logout button.
2. **Before login (guest)** → "Login" button pe **hover** karne par ek preview dropdown dikhe jisme My Profile, My Orders, My Wishlist, Saved Addresses, Settings listed ho — **greyed out / disabled** (click nahi hoga, sirf preview). "Sign Up" button bhi rahe.
3. Guest ko avatar ya real links nahi dikhte — sirf hover preview as a teaser.

### 4.2 My Account page (`/account`)
5. Layout: **left sidebar** (menu: Profile, Addresses, Settings, Password) + **right content area**.
6. Top pe greeting: "Hello, <Naam>" + avatar (bada) + member-since date.
7. Quick-link cards: "My Orders", "My Wishlist" — click pe respective page khule.

### 4.3 Profile edit
8. Naam aur phone edit kar sake. Email read-only (login identity hai).
9. Profile photo upload (jpg/png/webp, max 5MB) — save `static/uploads/avatars/`. Default = letter avatar.
10. Save pe success message.

### 4.4 Saved Addresses
11. User multiple address add kar sake: naam, phone, full address (line, city, state, pincode).
12. Har address edit / delete kar sake.
13. Ek address ko "Default" mark kar sake — checkout pe wo pre-fill ho (agar checkout integration easy ho; warna sirf store karo).

### 4.5 Password change
14. Form: current password, new password, confirm new password.
15. Current password galat → error. New ≠ confirm → error. Sahi → update + success message.
16. Google-login-only users (no password) ke liye gracefully handle (message dikhe).

### 4.6 Notification preferences
17. Checkbox: "Email notifications" on/off. User ki choice DB mein save ho.

## 5. Non-Functional Requirements
- **Security:** password change pe current password verify; passwords hashed (existing auth pattern). Address/profile sirf apna edit ho (privacy).
- **Design:** `ecommerce-ui-design` skill — plum sidebar, gold accents, cream content, cards, premium feel.
- **Backward compatible:** existing login/logout/cart/orders sab waise chalein.
- **Mobile:** sidebar mobile pe top pe stack ho jaye, toote na.

## 6. Data / DB changes
- `users` table mein columns add (migrate_db pattern): `phone`, `avatar` (path), `notify_email` (boolean, default 1), `created_at` (member since — agar pehle se na ho).
- Naya table `addresses`: `id`, `user_id`, `full_name`, `phone`, `address_line`, `city`, `state`, `pincode`, `is_default`, `created_at`.
- Helper functions: update_profile, get_addresses, add_address, edit_address, delete_address, set_default_address, change_password, update_notify_pref.

## 7. User Stories + Acceptance Criteria

**US-1 — Direct navbar links after login**
- Given: main "Vaibhav" naam se login hun
- When: koi bhi page kholun
- Then: navbar mein seedhe dikhe: My Profile, My Orders, My Wishlist, Saved Addresses, Settings, Cart, Logout (koi avatar ya dropdown nahi)

**US-2 — Guest hover preview**
- Given: main logged-in nahi hun
- When: "Login" button pe hover karun
- Then: ek preview dropdown dikhe jisme My Profile, My Orders, My Wishlist, Saved Addresses, Settings greyed-out dikhein (click nahi kaam karta)

**US-3 — Profile edit**
- Given: My Account → Profile pe hun
- When: naam/phone badal ke ya photo upload karke Save karun
- Then: changes save ho jaayein aur success message dikhe

**US-4 — Address add**
- Given: Saved Addresses pe hun
- When: ek naya address bharke save karun
- Then: address list mein dikhe; edit/delete option ho

**US-5 — Default address**
- Given: mere 2 addresses hain
- When: ek ko "Set as default" karun
- Then: wahi default mark ho jaye (sirf ek default ho)

**US-6 — Password change**
- Given: Settings → Password pe hun
- When: sahi current + matching naya password daalun
- Then: password update ho, success message; galat current → error

**US-7 — Notification toggle**
- Given: Settings pe hun
- When: email notification checkbox off karun aur save
- Then: choice save ho, dobara aane pe wahi state dikhe

**US-8 — Quick links**
- Given: My Account dashboard pe hun
- When: "My Orders" / "My Wishlist" card click karun
- Then: respective page khule

**US-9 — Guest**
- Given: main logged-in nahi hun
- When: navbar dekhun
- Then: avatar ki jagah "Login / Sign Up" dikhe

**US-10 — Privacy**
- Given: do users A aur B
- When: A apni profile/addresses dekhe
- Then: sirf A ka data dikhe, B ka nahi

## 8. Edge Cases
- Naam khaali / na ho → avatar mein "?" ya email ka pehla letter
- Bahut bada avatar file → reject (5MB limit)
- Sirf 1 address aur wo default → delete pe gracefully handle
- Google-only user (no password) → password change pe friendly message
- Phone invalid format → simple validation (10 digit)
- Default address delete → koi aur default ban jaye ya none

## 9. Open Questions (Vaibhav confirm kare)
1. Avatar circle ka color — **gold background + plum letter** (theme match)? — suggestion: haan
2. Phone number mandatory ya optional? — suggestion: optional
3. Address pe "Set as default" abhi checkout se jode ya sirf store karein? — suggestion: abhi sirf store + mark, checkout integration baad mein

## 10. Definition of Done ✅

- [ ] Login ke baad navbar mein seedhe alag links dikhte hain: My Profile, My Orders, My Wishlist, Saved Addresses, Settings, Cart, Logout
- [ ] Koi avatar circle ya click dropdown nahi hai (removed)
- [ ] Admin ko navbar mein seedha "Admin" link dikhta hai
- [ ] Guest ko "Login" + "Sign Up" dikhta hai
- [ ] Guest "Login" button pe hover karne par greyed-out preview dropdown dikhe (My Profile, My Orders, etc.) — click nahi hota
- [ ] `/account` page left-sidebar + right-content layout mein khulta hai
- [ ] Profile edit (naam, phone, photo) kaam karta hai
- [ ] Member since + email basic info dikhta hai
- [ ] Address add / edit / delete kaam karta hai
- [ ] Default address mark hota hai (sirf ek)
- [ ] Password change kaam karta hai (current verify + match check)
- [ ] Notification on/off save hota hai
- [ ] Quick-link cards (Orders, Wishlist) kaam karte hain
- [ ] Doosre user ka data nahi dikhta (privacy)
- [ ] Design premium dikhta hai (skill follow)
- [ ] Browser mein khud test kiya

## 11. Browser Test Script 🧪 (step-by-step kya check karo)

**Test 1 — Avatar circle**
1. `python app.py` chalaao, login karo
2. ✅ Navbar ke RIGHT side ek circle mein naam ka pehla letter dikh raha hai? → Pass
3. ✅ Pura naam ("Vaibhav Tiwari") ab navbar mein nahi dikh raha? → Pass

**Test 2 — Dropdown menu**
1. Avatar circle pe click karo
2. ✅ Menu khula with: My Profile, My Orders, Wishlist, Saved Addresses, Settings, Logout? → Pass
3. ✅ (Admin ho to) "Admin Dashboard" bhi dikh raha? → Pass

**Test 3 — My Account page**
1. Dropdown se "My Profile" click karo
2. ✅ `/account` page khula — left mein menu, right mein content? → Pass
3. ✅ "Hello, <naam>" + member since date dikh raha? → Pass
4. ✅ My Orders / My Wishlist quick-link cards dikh rahe? → Pass

**Test 4 — Profile edit**
1. Naam badlo, phone daalo, ek photo upload karo → Save
2. ✅ Success message aaya? → Pass
3. ✅ Page refresh karo — changes save rahe? → Pass
4. ✅ Avatar ab uploaded photo dikha raha (letter ki jagah)? → Pass

**Test 5 — Address add**
1. Saved Addresses → naya address bharo → Save
2. ✅ Address list mein dikha? → Pass
3. ✅ Edit karke save — change dikha? → Pass
4. ✅ Delete karo — hat gaya? → Pass

**Test 6 — Default address**
1. 2 addresses banao, ek ko "Set as default"
2. ✅ Wahi default mark hua? → Pass
3. ✅ Doosre ko default karo — pehla wala default hat gaya (sirf ek default)? → Pass

**Test 7 — Password change**
1. Settings → Password: galat current password daalo → Save
2. ✅ Error aaya? → Pass
3. Sahi current + naya (dono baar same) daalo → Save
4. ✅ Success? Logout-login karke naya password kaam karta hai? → Pass

**Test 8 — Notification toggle**
1. Settings → email notification checkbox off → Save
2. ✅ Save hua? Page refresh — abhi bhi off? → Pass

**Test 9 — Quick links**
1. Dashboard pe "My Orders" card click
2. ✅ Orders page khula? → Pass
3. "My Wishlist" card click
4. ✅ Wishlist page khula? → Pass

**Test 10 — Guest**
1. Logout karo
2. ✅ Navbar mein avatar ki jagah "Login / Sign Up" dikha? → Pass

**Test 11 — Privacy**
1. Doosre account se login karo
2. ✅ Account page pe sirf isi user ka data (naam, addresses) dikh raha, pehle wale ka nahi? → Pass

**Test 12 — Design check**
1. ✅ Avatar circle gold/plum theme mein hai?
2. ✅ Account page sidebar + cards premium dikhte hain (baaki site jaisa)?
3. ✅ Mobile/chhoti window pe layout toot nahi raha?