# Spec Document — Reviews & Ratings

## 1. Overview

Implement **Reviews & Ratings** — the feature that lets customers leave a star rating and a written review on products, and lets everyone see those reviews.

This is the last core feature. On every real e-commerce site, products show stars (e.g. ★★★★☆ 4.2) and customer reviews — they're a huge part of how shoppers decide what to buy. This feature adds: a star rating + review on each product page, an average rating shown on the product, and a fair rule about who can review (only people who actually bought the product, like Amazon's "Verified Purchase").

**Why this matters:** Reviews build trust and help customers choose. They also give the store owner feedback. With this, the catalog stops being a plain list and becomes a social, trustworthy shop — completing the e-commerce experience.

---

## 2. Depends on

- **Product Catalog** (feature 03) — reviews appear on the product detail page.
- **User Authentication** (feature 02) — a review belongs to a logged-in user.
- **Order Management / Payment** (features 07, 08) — used to check whether the user actually bought the product ("verified purchase").
- **Database Setup** (feature 01) — needs a new `reviews` table.

Built on the existing **Flask + HTML templates** stack (same as previous features — no React).

---

## 3. User Stories

- **As a customer who bought a product**, I want to leave a star rating and a written review, so that I can share my experience.
- **As any shopper**, I want to see a product's average rating and number of reviews at a glance, so that I can quickly judge its quality.
- **As a shopper**, I want to read other customers' written reviews on the product page, so that I can make an informed decision.
- **As a customer**, I want to edit or delete my own review, so that I can correct or remove it.
- **As a shopper**, I want reviews to come only from real buyers, so that ratings are trustworthy ("verified purchase").
- **As a customer**, I want to be stopped from reviewing the same product twice, so that ratings stay fair.

---

## 4. Database Schema

> One new table.

### reviews (new)

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| product_id | INTEGER | Foreign key → products.id, not null |
| user_id | INTEGER | Foreign key → users.id, not null |
| rating | INTEGER | Not null, between 1 and 5 |
| comment | TEXT | Nullable (a rating without text is allowed) |
| created_at | TEXT | Default datetime('now') |

> Rule: **one review per (user + product)** — a user can have at most one review per product (they can edit it, but not stack multiple).

---

## 5. Routes / Functions to Implement

> Flask routes + Jinja templates. Actions that change data are POST.

### A. Show reviews on the product page  (enhances `GET /products/<id>` from feature 03)
- Displays the product's **average rating** (e.g. ★ 4.2) and **review count**.
- Lists existing reviews: reviewer name, star rating, comment, date.
- If the logged-in user is eligible to review (bought it, hasn't reviewed yet) → show a review form.
- If they already reviewed → show their review with edit/delete options.

### B. Add a review  (`POST /products/<id>/review`)
- Requires login.
- Allowed **only if** the user purchased this product (has a paid order containing it) **and** hasn't already reviewed it.
- Validates the rating (1–5).
- Saves the review.

### C. Edit own review  (`POST /reviews/<id>/edit`)
- Requires login + ownership (only the author can edit).

### D. Delete own review  (`POST /reviews/<id>/delete`)
- Requires login + ownership.

### E. Helper functions
- `get_product_reviews(product_id)` → all reviews for a product.
- `get_average_rating(product_id)` → average rating + count.
- `can_user_review(user_id, product_id)` → true only if they bought it and haven't reviewed yet.

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Buyer can leave a review
- **Given** a logged-in user who has a paid order containing the product
- **When** they submit a star rating (and optional comment)
- **Then** the review is saved and appears on the product page.

### AC-2: Non-buyers cannot review
- **Given** a logged-in user who never bought the product
- **When** they try to review it
- **Then** they are not allowed, and the review form is not available to them.

### AC-3: Average rating shown
- **Given** a product with several reviews
- **When** anyone opens its page
- **Then** the average star rating and the number of reviews are shown.

### AC-4: Reviews are listed
- **Given** a product with reviews
- **When** the product page loads
- **Then** each review shows the reviewer's name, stars, comment, and date.

### AC-5: One review per user per product
- **Given** a user who already reviewed a product
- **When** they try to add another review for the same product
- **Then** they cannot; instead they see their existing review with edit/delete options.

### AC-6: Edit own review
- **Given** a user's own review
- **When** they edit the rating or comment
- **Then** the change is saved and the average rating updates accordingly.

### AC-7: Delete own review
- **Given** a user's own review
- **When** they delete it
- **Then** it is removed and the average rating/count update.

### AC-8: Cannot edit/delete others' reviews
- **Given** a review written by user A
- **When** user B tries to edit or delete it
- **Then** they are blocked.

### AC-9: Rating must be valid
- **Given** the review form
- **When** a rating outside 1–5 is submitted (or none)
- **Then** the review is not saved and a clear message is shown.

### AC-10: Login required to review
- **Given** a logged-out visitor
- **When** they try to submit a review
- **Then** they are redirected to login (but they can still *read* reviews without logging in).

### AC-11: No-reviews state
- **Given** a product with no reviews yet
- **When** its page loads
- **Then** a friendly "No reviews yet" message is shown (and the buy/review options still work).

---

## 7. Files to Change

- The database setup/helper → add the `reviews` table (safe migration) and the review helper functions.
- The product detail template (feature 03) → show average rating, list reviews, and the review form / edit-delete controls.
- The product detail route → load reviews + average + eligibility and pass them to the template.
- (Optional) the catalog listing cards → show the average star rating on each card.

## 8. Files to Create

- A reviews module/blueprint with the add/edit/delete routes and helpers.
- A reviews section template/partial (can live within the product detail template or as an include).

---

## 9. Dependencies

- No new external services or libraries.
- Reuses existing auth, database helpers, base template, and the orders data (to check verified purchase).

---

## 10. Rules for Implementation

- A review requires **login**; reading reviews does not.
- **Only verified buyers** can review: the user must have a **paid** order that contains the product.
- **One review per (user + product)** — enforce this; adding again should edit, not duplicate.
- Rating must be an integer **1–5**; reject anything else.
- Only the **author** can edit or delete their own review.
- Average rating computed from actual reviews (handle the no-reviews case without dividing by zero); display rounded (e.g. 4.2).
- Use **parameterized queries only**.
- Deleting a review must update the average/count correctly.
- Keep reviewer identity light (show first name or a display name, not the email).

---

## 11. Error Handling Expectations

- Non-buyer or logged-out trying to review → blocked / redirected gracefully, no crash.
- Invalid rating → clear validation message, nothing saved.
- Editing/deleting a review you don't own, or one that doesn't exist → handled gracefully, no crash.
- Product with no reviews → friendly "No reviews yet", no divide-by-zero or blank page.

---

## 12. Out of Scope (handled later / future)

- Review images/photos uploaded by customers → future feature.
- "Was this review helpful?" voting / sorting reviews by helpfulness → future feature.
- Replies from the seller to a review → future feature.
- Moderation / reporting abusive reviews → future feature (basic version: admin could delete via DB for now).
- This feature covers rating, writing, reading, editing, and deleting reviews by verified buyers; nothing more advanced.

---

## 13. Definition of Done

- [ ] A `reviews` table exists with rating (1–5), comment, and the user/product links.
- [ ] A verified buyer (paid order containing the product) can leave a star rating + optional comment.
- [ ] A non-buyer cannot review (no form shown / submission blocked).
- [ ] The product page shows the average rating and review count.
- [ ] Existing reviews are listed with reviewer name, stars, comment, and date.
- [ ] A user can have only one review per product (edit instead of duplicate).
- [ ] A user can edit and delete their own review, and the average updates.
- [ ] A user cannot edit or delete someone else's review.
- [ ] Invalid ratings (outside 1–5) are rejected.
- [ ] Logged-out users can read reviews but are redirected to login to write one.
- [ ] A product with no reviews shows a friendly "No reviews yet" message.
- [ ] All review queries use parameterized SQL.