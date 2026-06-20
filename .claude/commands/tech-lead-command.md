Run a full project health check and provide strategic guidance using the `tech-lead` subagent.

The tech-lead will:
1. Check git status, branches, recent commits
2. Read CLAUDE.md, skills, specs, and scan all source files
3. Test if Flask backend starts, run existing tests
4. Find broken features, TODOs, debug prints, hardcoded values
5. Check frontend-backend API sync
6. Generate a full Health Report (working / broken / not built)
7. Recommend what to fix first and what to build next
8. Check responsive status and security concerns
9. Update the Launch Readiness checklist

CRITICAL: Do NOT auto-edit any source code. Only read, diagnose, and recommend. Ask user before making any changes.

Output the full Health Report, then ask: "NEXT STEP: [action]. Kya main ye karun? [Y/N]"