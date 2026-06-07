Run the full self code review pipeline for the feature implemented on the current git branch.

## Steps (run in this exact order — do not skip any)

### Step 1 — Security Review
Use the `security-review` subagent to:
1. Run `git diff main...HEAD` to see exactly what changed
2. Check for: auth gaps, SQL injection, XSS, unsafe file uploads, Razorpay tampering, privacy violations, hardcoded secrets
3. Report all findings by severity (HIGH / MEDIUM / LOW)

Wait for security-review to fully complete before moving to Step 2.

### Step 2 — Code Quality Review
Use the `code-quality-review` subagent to:
1. Run `git diff main...HEAD` to see exactly what changed
2. Read CLAUDE.md, db.py patterns, auth.py, and ecommerce-ui-design skill
3. Check for: structure, readability, duplication, error handling, design consistency, dead code
4. Report findings (must-fix vs nice-to-have)

## Final Output
After both agents complete, give a combined summary:

```
╔══════════════════════════════════════════╗
   SELF CODE REVIEW — <Feature Name>
╚══════════════════════════════════════════╝

🔐 SECURITY:
🔴 HIGH:    [issues that must be fixed before push]
🟠 MEDIUM:  [fix soon]
🟡 LOW:     [optional hardening]
✅ Clean:   [what's done correctly]

👨‍💻 CODE QUALITY:
🔧 Must-fix:     [before push]
💡 Nice-to-have: [later]
🎨 Design issues: [ecommerce-ui-design skill mismatch]
🧹 Cleanup:      [dead code etc]

══════════════════════════════════════════
FINAL VERDICT:
✅ CLEAN — push kar sakte ho
⚠️  CHHOTI CHEEZEIN — push kar sakte ho, [items] baad mein fix karo
❌ PEHLE THEEK KARO — [HIGH security ya must-fix quality issues]
══════════════════════════════════════════
```