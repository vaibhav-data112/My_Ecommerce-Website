Run a complete pre-launch QA inspection of the Karvii Spices website using the `launch-checker` agent.

The launch-checker will:
1. Run ALL automated test files (test_auth, test_contact, test_coupon_system, test_order_management, etc.)
2. Check Flask backend health — imports, blueprints, DB migrations, no debug prints
3. Verify frontend dist build exists and is complete
4. Security audit — no hardcoded secrets, admin routes protected, SQL injection check
5. Feature completeness check — all 17+ features working
6. Environment variables audit — which .env vars are set vs missing
7. Code quality scan — TODOs, console.logs, ESLint errors
8. Responsive design check — breakpoints, layout grids collapse on mobile, tables wrapped, no inline styles, hamburger nav, page wrappers

Final output:
- 🟢 GREEN SIGNAL: "Website ready hai — deploy kar sakte ho!"
- 🔴 RED SIGNAL: "Pehle ye X cheezein theek karo"

Also saves full report to `.claude/reports/launch-check-[date].md`

CRITICAL: Do NOT edit any source code. Only inspect, test, and report.
