# Spec Document — User Authentication

## 1. Overview

Implement **User Authentication** for the e-commerce website — the system that lets people create an account, log in, stay logged in, and log out.

This is the "front door" of the shop. Real e-commerce sites (Amazon, Flipkart, Myntra) all work the same way: you sign up once, log in, and the site remembers who you are while you shop.

This feature supports **two ways to log in**, exactly like real sites:
1. **Email + Password** (the classic way)
2. **Google login** ("Continue with Google" button)

**Why this matters:** Almost every other feature needs to know *who* the user is — the cart belongs to a user, orders belong to a user, checkout needs a logged-in user. So authentication must be correct and secure before cart/checkout can work.

---

## 2. Depends on

- **Database Setup** (the `users` table already exists from feature 01).

Note: the existing `users` table may need a small addition to support Google login (a `google_id` column and making `password_hash` optional for Google-only users). The plan should handle this safely.

---

## 3. User Stories

- **As a new visitor**, I want to create an account with my email and a password, so that I can save my cart and place orders.
- **As a returning user**, I want to log in with my email and password, so that I get back into my account.
- **As a user**, I want to log in with one click using my Google account, so that I don't have to remember another password.
- **As a logged-in user**, I want the site to remember me as I move between pages, so that I'm not asked to log in again and again.
- **As a privacy-conscious user**, I want a "Remember me" option so I can choose to stay logged in on my own device, or be logged out when I close the browser on a shared device.
- **As a user**, I want to log out, so that no one else using my device can access my account.
- **As any user**, I want clear error messages when something is wrong (wrong password, email already used), so that I know what to fix.

---

## 4. Database Schema

> Small additions to the existing `users` table from feature 01.

### users (updated)

| Column | Type | Constraints | Note |
| --- | --- | --- | --- |
| id | INTEGER | Primary key, autoincrement | (existing) |
| name | TEXT | Not null | (existing) |
| email | TEXT | Unique, not null | (existing) |
| password_hash | TEXT | **Nullable** | now optional — empty for Google-only users |
| google_id | TEXT | Nullable, unique | **new** — stores the Google account id |
| created_at | TEXT | Default datetime('now') | (existing) |

> A user is valid if they have EITHER a password_hash (email/password user) OR a google_id (Google user). Some users may have both.

---

## 5. Routes / Functions to Implement

> Behaviour described below is the contract. Exact names depend on the stack.

### A. Signup page  (`GET /signup`)
- Shows a form: name, email, password, confirm password.
- Also shows a "Continue with Google" button.

### B. Create account  (`POST /signup`)
- Validates the form (valid email, password long enough, passwords match).
- Rejects if the email is already registered.
- Hashes the password (never stores plain text).
- Creates the user, logs them in, and redirects to the home page.

### C. Login page  (`GET /login`)
- Shows a form: email, password, and a "Remember me" checkbox.
- Also shows a "Continue with Google" button.

### D. Log in  (`POST /login`)
- Checks email + password against the stored hash.
- On success → starts a session (respecting "Remember me") and redirects to home/intended page.
- On failure → shows a generic "Invalid email or password" message (does not reveal which one was wrong).

### E. Google login  (`GET /login/google` and a callback route)
- Sends the user to Google to approve.
- On return, finds or creates the user by their Google account, logs them in.

### F. Logout  (`POST /logout` or `GET /logout`)
- Ends the session and redirects to home/login.

### G. "Who is logged in?" helper
- A function any other feature can call to get the current logged-in user (or know that no one is logged in).

### H. "Login required" guard
- A way to protect pages (like checkout) so only logged-in users can open them; otherwise redirect to login.

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Successful signup
- **Given** a visitor on the signup page with a new email
- **When** they submit a valid name, email, and matching passwords
- **Then** a new user is created with a hashed password, they are logged in, and sent to the home page.

### AC-2: Duplicate email blocked
- **Given** an email that already has an account
- **When** someone tries to sign up with that same email
- **Then** signup is rejected with a clear "email already registered" message and no duplicate user is created.

### AC-3: Password rules enforced
- **Given** the signup form
- **When** the password is too short or the two passwords don't match
- **Then** the account is NOT created and a clear validation message is shown.

### AC-4: Successful login
- **Given** a registered email/password user
- **When** they enter the correct email and password
- **Then** they are logged in and redirected to the home page.

### AC-5: Wrong credentials rejected
- **Given** the login form
- **When** the email or password is wrong
- **Then** login fails with a generic "invalid email or password" message (not revealing which field was wrong).

### AC-6: Passwords never stored as plain text
- **Given** any user created with a password
- **When** you inspect the database
- **Then** the stored value is a hash, never the readable password.

### AC-7: Session persists across pages
- **Given** a logged-in user
- **When** they navigate to different pages
- **Then** they stay logged in without re-entering credentials.

### AC-8: "Remember me" behaviour
- **Given** the login form
- **When** the user checks "Remember me"
- **Then** the session persists after the browser is closed; when unchecked, closing the browser logs them out.

### AC-9: Logout works
- **Given** a logged-in user
- **When** they click logout
- **Then** their session ends and protected pages are no longer accessible.

### AC-10: Login required guard
- **Given** a NOT-logged-in user
- **When** they try to open a protected page (e.g. checkout)
- **Then** they are redirected to the login page, and sent back to that page after logging in.

### AC-11: Google login — new user
- **Given** a visitor who has never signed up
- **When** they click "Continue with Google" and approve
- **Then** a new user account is created from their Google profile and they are logged in.

### AC-12: Google login — returning user
- **Given** a user who previously signed up with Google
- **When** they click "Continue with Google" again
- **Then** they are logged into their existing account (no duplicate account is created).

---

## 7. Files to Change

- The `users` table definition / database helper → add `google_id`, make `password_hash` nullable (done safely, without breaking existing data).
- Main app/routes file → register the new auth routes.

## 8. Files to Create

- An authentication module (signup, login, logout, Google login logic, the "current user" helper and the "login required" guard).
- Page templates/components for signup and login.

---

## 9. Dependencies

- A password-hashing helper (already available from feature 01).
- A library/helper to handle Google login (OAuth). This needs **Google credentials** (a Client ID and Secret) created in a free Google Cloud account — the plan should explain where these go and how to keep them secret (not committed to GitHub).

---

## 10. Rules for Implementation

- **Passwords always hashed**, never plain text.
- **Login errors stay generic** ("invalid email or password") — never reveal whether the email exists.
- **Google Client ID/Secret must NEVER be committed to GitHub** — keep them in a local environment file that `.gitignore` excludes.
- Use **parameterized queries only**.
- A user can be valid with a password OR a Google id (or both) — never require both.
- Protect sensitive pages with the "login required" guard.
- Sessions must be handled securely (use the framework's built-in secure session handling).

---

## 11. Error Handling Expectations

- Duplicate email on signup → clear, friendly message, no crash.
- Wrong password → generic invalid-credentials message.
- Google login cancelled or failed → return the user to the login page with a friendly message, no crash.
- Trying to access a protected page while logged out → smooth redirect to login (not an error screen).

---

## 12. Out of Scope (handled later / other features)

- Password reset / "forgot password" email flow → future feature.
- Email verification (confirming the email is real) → future feature.
- User profile editing → future feature.
- Roles/permissions (admin vs normal user) → handled in the Admin Dashboard feature.
- This feature only handles signing up, logging in/out, and knowing who is logged in.

---

## 13. Definition of Done

- [ ] A user can sign up with name, email, and password.
- [ ] Duplicate email is rejected with a clear message.
- [ ] Password rules (length, match) are enforced.
- [ ] Passwords are stored hashed, never plain text.
- [ ] A user can log in with correct email + password.
- [ ] Wrong credentials show a generic error message.
- [ ] The user stays logged in while browsing pages.
- [ ] "Remember me" controls whether the session survives closing the browser.
- [ ] Logout ends the session.
- [ ] Protected pages redirect logged-out users to login, then back.
- [ ] "Continue with Google" creates a new account for first-time users.
- [ ] "Continue with Google" logs returning Google users into their existing account (no duplicates).
- [ ] Google Client ID/Secret are NOT committed to GitHub.