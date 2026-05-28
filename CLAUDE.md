# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Status

This is a new e-commerce website project. No application code exists yet. The tech stack (backend language, database) has not been decided and will be chosen during the `01-database-setup` spec/plan phase.

## Development Methodology

This project uses **Spec-Driven Development (SDD)**. The full workflow is documented in `.claude/SDD-Instructions-Ecommerce.md`. Key points:

- Every feature follows a **16-step loop**: spec → plan → implement → validate → commit → PR → merge.
- **Never implement before a spec and plan exist** for that feature.
- Specs live in `.claude/specs/NN-feature-name.md`; plans live in `.claude/plans/NN-feature-name.md`. Both are committed.
- Each feature gets its own branch: `feature/{feature-name}`. Never work directly on `main`.
- Merge to `main` only after the feature is fully validated against its spec.

## Planned Feature Order

| NN | Branch | What it builds |
|----|--------|----------------|
| 01 | `database-setup` | Database schema — users, products, orders tables |
| 02 | `user-auth` | Signup, login, logout, password security |
| 03 | `product-catalog` | Product list + detail page |
| 04 | `search-filter` | Search bar, category filters, pagination |
| 05 | `shopping-cart` | Add/remove items, quantity update |
| 06 | `checkout-flow` | Address, order summary, confirm order |
| 07 | `payment` | Razorpay / Stripe integration |
| 08 | `order-management` | Order history, status tracking |
| 09 | `admin-dashboard` | Manage products and orders |
| 10 | `reviews-ratings` | Product reviews and star ratings |

## Commands

Commands will be added here once the tech stack is decided in feature `01-database-setup`.
