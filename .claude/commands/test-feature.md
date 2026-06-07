Run the full testing pipeline for the feature that was just implemented on the current git branch.

## Steps (run in this exact order — do not skip any)

### Step 1 — Test Writer
Use the `test-writer` subagent to:
1. Read the feature spec from `.claude/specs/`
2. Read the actual implementation code
3. Write comprehensive pytest tests in `tests/test_<feature_name>.py`
4. Update `tests/conftest.py` if needed

Wait for test-writer to fully complete before moving to Step 2.

### Step 2 — Test Runner  
Use the `test-runner` subagent to:
1. Run the tests that test-writer just created
2. Diagnose every failure (real bug vs test issue vs environment)
3. Give quality assessment
4. Output the Final Summary with VERDICT

## Final Output
After both agents complete, give me:

```
✅ Tests written: X tests in tests/test_<feature>.py
✅ Tests run: X passed, X failed

VERDICT: <PUSH KAR SAKTE HO / PEHLE THEEK KARO / MAT PUSH KARO>

Agar failures hain:
❌ [test name] — [plain Hindi mein kya toota aur kya fix karna hai]

Manual browser checks baaki:
⚠️  [jo auto-test nahi ho saka]
```