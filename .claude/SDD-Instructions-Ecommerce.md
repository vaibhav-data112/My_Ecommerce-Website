# 🛒 E-Commerce Website — Spec-Driven Development (SDD) Guide

Yeh aapki poori e-commerce website banane ka structure hai.

**Sabse zaroori rule:** Yeh 16 steps **ek feature ke liye ek baar** chalte hain — poori website ek saath nahi. Har feature ke liye yeh pura loop dobara repeat hoga.

Folders jo aap use karoge:
- `.claude/specs/`  → har feature ka spec document (kya banana hai)
- `.claude/plans/`  → har feature ka implementation plan (kaise banega)

---

## 📋 PART 1 — Reusable Instruction Card (har feature ke liye)

> Neeche `{feature-name}` aur `{NN}` (number jaise 01, 02) ko apne feature ke hisaab se replace karna hai.

1. **Start a new Claude session** — naya Claude Code session kholo.

2. **Rename the session** to `{feature-name}` — taaki baad mein dhoondhna easy ho.

3. **Pull the most recent code** —
   ```bash
   git pull origin main
   ```

4. **Create and switch to a new branch** —
   ```bash
   git checkout -b feature/{feature-name}
   ```

5. **Create Spec document manually** — Claude se spec likhwao (user stories, requirements, acceptance criteria, edge cases). Code abhi nahi.

6. **Review the spec document** — khud padho. Kuch missing/galat ho to Claude se fix karwao. Jab tak satisfy na ho, aage mat badho.

7. **Save the spec** in `.claude/specs/` folder by the name `{NN}-{feature-name}.md`

8. **Enter Plan mode and create a plan** based on the spec —
   > "Read `.claude/specs/{NN}-{feature-name}.md` and the existing relevant files, then generate an implementation plan. Save this plan to `.claude/plans/{NN}-{feature-name}.md`"

9. **Implement the plan** — review edits manually (har change dekho, blindly accept mat karo).

10. **Validate the implementation** against the spec document — kya saare acceptance criteria meet ho rahe hain?

11. **Iterate if required** — kuch chhoot gaya to step 9–10 dobara.

12. **Commit the changes** —
    ```bash
    git add .
    git commit -m "{feature-name}"
    ```

13. **Push the code to GitHub** —
    ```bash
    git push origin feature/{feature-name}
    ```

14. **Create and merge the PR** — GitHub pe Pull Request banao aur merge karo.

15. **Checkout to the main branch** —
    ```bash
    git checkout main
    ```

16. **Delete the feature branch** —
    ```bash
    git branch -D feature/{feature-name}
    ```

✅ Ek feature done. Ab agle feature ke liye step 1 se dobara shuru.

---

## 📋 PART 2 — Example: Pehla Feature (Database Setup)

Yahan upar wala template fill karke dikhaya hai, taaki exact format clear ho jaye.

1. Start a new Claude session
2. Rename the session to `database setup`
3. `git pull origin main`
4. `git checkout -b feature/database-setup`
5. Create Spec document manually
6. Review the spec document
7. Save the spec in `.claude/specs/` as `01-database-setup.md`
8. Enter Plan mode:
   > "Read `.claude/specs/01-database-setup.md` and the existing project files, then generate an implementation plan. Save this plan to `.claude/plans/01-database-setup.md`"
9. Implement the plan — review edits manually
10. Validate the implementation against the spec
11. Iterate if required
12. `git add .` → `git commit -m "database setup"`
13. `git push origin feature/database-setup`
14. Create and merge the PR
15. `git checkout main`
16. `git branch -D feature/database-setup`

---

## 📋 PART 3 — Poori Website ka Feature Order

Isi order mein banaoge to dependencies clean rahengi. Har feature ke liye upar wala 16-step loop chalega.

| NN | Feature Name (branch ke liye) | Kya banega |
|----|-------------------------------|------------|
| 01 | `database-setup` | Database schema, tables (users, products, orders) |
| 02 | `user-auth` | Signup, login, logout, password security |
| 03 | `product-catalog` | Product list + detail page |
| 04 | `search-filter` | Search bar, category filters, pagination |
| 05 | `shopping-cart` | Add/remove items, quantity update |
| 06 | `checkout-flow` | Address, order summary, confirm order |
| 07 | `payment` | Razorpay / Stripe integration |
| 08 | `order-management` | Order history, status tracking |
| 09 | `admin-dashboard` | Products/orders manage karne ke liye |
| 10 | `reviews-ratings` | Product reviews aur star ratings |

---

## 💡 Yaad Rakhne Wali Baatein

- **Ek branch = ek feature.** Adhura kaam `main` branch pe kabhi mat le jao.
- **Spec aur Plan dono `.claude/` folder mein commit karte raho** — taaki Claude ko baad mein context dena easy ho.
- **Review steps (6, 10) skip mat karna** — yahin pe zyaadatar problems pakdi jaati hain.
- **Build phase mein ek time pe ek task** banwao, sab ek saath mat maango.
- Branch tabhi merge karo jab feature **poora validate** ho jaye.

---

*Note: Image wale example mein `db.py` aur `app.py` (Python files) the. Aapka tech stack abhi decide nahi hua — wo feature 01 ke Spec/Design phase mein Claude ke saath milke decide karoge. Tab in file names ko apne stack ke hisaab se badal lena.*
