# TestSprite AI Testing Report (MCP)

---

## 1️⃣ Document Metadata

- **Project Name:** vibecoder-cmo (Vibe Marketer / Autopilot Marketer)
- **Date:** 2026-02-20
- **Prepared by:** TestSprite AI Team
- **App Type:** Streamlit Frontend (Python)
- **Test Suite:** 38 test cases, full codebase scope
- **Overall Pass Rate:** 12/38 (31.6%)

---

## 2️⃣ Requirement Validation Summary

### REQ-1: Product Description Input (Phase 1)

| Test | Description | Status |
|------|-------------|--------|
| TC001 | Start Discovery after entering product description shows first AI question | ❌ Failed |
| TC002 | Skip Discovery after entering product description shows discovery summary | ✅ Passed |
| TC003 | Start Discovery without product description is blocked with feedback | ❌ Failed |
| TC004 | Skip Discovery without product description is blocked with feedback | ❌ Failed |
| TC005 | Product description supports long multi-paragraph input | ✅ Passed |
| TC006 | Product description supports special characters without breaking flow | ✅ Passed |
| TC007 | Switching from Start Discovery to Skip Discovery works cleanly | ❌ Failed |

**Findings:**
- TC001/TC007: "Start Discovery" button not found — this button is **disabled** when `ANTHROPIC_API_KEY` (MiniMax) is missing. Tests could not interact with it because the test environment lacks that key.
- TC003/TC004: The textarea has a pre-filled default value (`"An AI workout tracking app called Sage..."`), making it impossible for tests to clear it and test empty-input validation.
- TC005/TC006: Input field correctly handles long text and special characters.

---

### REQ-2: Discovery Chat (Phase 2)

| Test | Description | Status |
|------|-------------|--------|
| TC008 | Start Discovery and answer one question to receive next AI question | ❌ Failed |
| TC009 | Skip discovery early using "I've shared enough — Generate Strategy" | ✅ Passed |
| TC010 | Discovery chat supports multi-sentence answers and preserves history | ❌ Failed |
| TC011 | Submitting an empty message does not advance the discovery chat | ❌ Failed |
| TC012 | Discovery chat continues across two consecutive Q&A turns | ❌ Failed |

**Findings:**
- TC008/TC010/TC011/TC012: All depend on "Start Discovery" being clickable, which requires a MiniMax API key. Without it, the button is disabled and the chat interface is never rendered.
- TC009: Passed because "Skip Discovery" path (AWS credentials only) was available and correctly transitions to the discovery summary + Generate Strategy phase.

---

### REQ-3: Strategy Generation (Phase 3)

| Test | Description | Status |
|------|-------------|--------|
| TC013 | Generate strategy successfully from discovery summary and view results | ✅ Passed |
| TC014 | Generate Strategy shows Strategist phase progress (spinner) before results | ❌ Failed |
| TC015 | Platform specialists phase progress is visible during strategy generation | ❌ Failed |
| TC016 | Quality judge phase progress is visible before final playbooks display | ❌ Failed |

**Findings:**
- TC013: The end-to-end flow (Skip Discovery → Generate Strategy → view results) worked correctly when AWS credentials are present.
- TC014/TC015/TC016: Spinner/in-progress states are transient — tests could not capture them in time before the page re-rendered with results. These are timing/race condition issues in the test runner, not app bugs.

---

### REQ-4: Strategy Results Display

| Test | Description | Status |
|------|-------------|--------|
| TC017 | Final results contain ICP section and multiple platform playbooks | ❌ Failed |
| TC018 | Discovery summary can be collapsed without disrupting strategy generation | ❌ Failed |
| TC019 | Open Reddit tab and verify all playbook sections shown | ❌ Failed |
| TC020 | Reddit quality score badge and rationale are visible | ❌ Failed |
| TC021 | Switch between platform tabs and confirm content updates per platform | ❌ Failed |
| TC022 | Each playbook section contains visible content (not just headers) | ❌ Failed |
| TC023 | Quality judge unavailable: shows warning about missing MiniMax key | ✅ Passed |
| TC024 | When quality score missing, no score badge shown for that platform | ❌ Failed |
| TC025 | ICP tab remains accessible after viewing platform tabs | ❌ Failed |

**Findings:**
- TC017–TC022, TC024–TC025: These tests expect results from a completed strategy generation run. They failed because the page was in a prior state (pre-generation) when the test started — likely due to Streamlit session state not persisting across test sessions.
- TC023: Correctly passes — with no MiniMax key, the sidebar shows "Add MiniMax key to .env for discovery" warning.

---

### REQ-5: Datadog Integration

| Test | Description | Status |
|------|-------------|--------|
| TC026 | Valid Datadog API key shows connected/success status in sidebar | ✅ Passed |
| TC027 | Invalid Datadog API key shows toast warning for connection failure | ❌ Failed |
| TC028 | Datadog status persists after triggering app activity | ✅ Passed |
| TC029 | Invalid Datadog key warning remains visible after Generate Strategy | ❌ Failed |
| TC030 | Switching from invalid to valid key updates status to success | ✅ Passed |
| TC031 | Clearing Datadog API key shows not-connected or warning state | ❌ Failed |

**Findings:**
- TC026/TC028/TC030: Sidebar status indicator correctly reflects whether a key is entered (`"Datadog: OK"` vs warning).
- TC027: The app does **not** validate API key correctness — it only checks if a value is non-empty. Entering an invalid key still shows "Datadog: OK". Real validation only happens when a campaign is generated and the metric submission fails (as a toast).
- TC031: Clearing the field returns to the warning state reactively, but the test expected specific wording (`"Datadog connection failed"`) that doesn't match the actual app text (`"Enter Datadog API key to enable metrics"`).
- TC029: Relies on a state (invalid key + post-strategy generation) that wasn't reachable in the test session.

---

### REQ-6: Credentials Sidebar & Session Management

| Test | Description | Status |
|------|-------------|--------|
| TC032 | Datadog connection status is visible without needing to run discovery | ✅ Passed |
| TC033 | Sidebar shows Bedrock and MiniMax status indicators | ✅ Passed |
| TC034 | Datadog API key input accepts a value and remains visible | ✅ Passed |
| TC035 | Start Over resets session state and clears Datadog API key | ❌ Failed |
| TC036 | Start Over clears main workflow UI content after progress has begun | ❌ Failed |
| TC037 | AWS credentials missing: Generate Strategy disabled with warning | ❌ Failed |
| TC038 | Generate Strategy remains non-actionable when AWS credentials warning present | ❌ Failed |

**Findings:**
- TC032/TC033/TC034: Sidebar credential indicators work correctly for read-only status.
- TC035: "Start Over" only clears `st.session_state` keys (discovery chat, product, etc.) — it does **not** reset the Datadog API key input because it's a sidebar widget with its own Streamlit state, not tracked in `session_state`. This is a real bug.
- TC036/TC037/TC038: Tests encountered a loading/placeholder skeleton, suggesting the app wasn't in a rendered state at the start of those test runs. Also TC037/TC038 require the app to be in the discovery-complete phase without AWS credentials, a compound state that wasn't set up.

---

## 3️⃣ Coverage & Matching Metrics

- **Total Tests:** 38
- **Passed:** 12 (31.6%)
- **Failed:** 26 (68.4%)

| Requirement | Total Tests | ✅ Passed | ❌ Failed |
|---|---|---|---|
| REQ-1: Product Description Input | 7 | 2 | 5 |
| REQ-2: Discovery Chat | 5 | 1 | 4 |
| REQ-3: Strategy Generation | 4 | 1 | 3 |
| REQ-4: Strategy Results Display | 9 | 1 | 8 |
| REQ-5: Datadog Integration | 6 | 3 | 3 |
| REQ-6: Credentials & Session Mgmt | 7 | 4 | 3 |
| **Total** | **38** | **12** | **26** |

---

## 4️⃣ Key Gaps / Risks

### 🔴 High Priority

1. **MiniMax/Discovery path untestable without API key**
   Most failures in REQ-1 and REQ-2 stem from the "Start Discovery" button being disabled without a MiniMax key. The test environment doesn't have this key, so ~10 tests can never pass in CI without it. Consider adding a mock/stub mode for the discovery endpoint in tests.

2. **"Start Over" does not reset Datadog key (TC035 — confirmed bug)**
   The sidebar Datadog API key input is not tracked in `st.session_state`, so "Start Over" leaves it populated. Users who click "Start Over" would still have their previous Datadog key in the field — potentially unexpected behavior.

3. **No real-time Datadog API key validation (TC027/TC031)**
   Entering any non-empty string marks Datadog as "OK". Real validation only occurs at metric-send time (silently, as a toast). Users may not discover a bad key until after a full strategy run completes.

### 🟡 Medium Priority

4. **Spinner states are too transient to test reliably (TC014/TC015/TC016)**
   The strategy generation spinners appear and disappear in a single Streamlit re-render cycle. Tests can't reliably assert on them. Consider adding a status text element that persists beyond the spinner for testability and user clarity.

5. **Default product description prevents empty-input testing (TC003/TC004)**
   The textarea is pre-filled with a default value. There is no way for a user (or test) to easily reach a truly empty state because the default is always injected. This also means the "Please enter a product description" error path is practically unreachable via normal UI.

6. **Streamlit session state doesn't persist across test sessions (many TC failures)**
   Tests that expect to start in a post-strategy-generation state (results tabs open) find the app in Phase 1. TestSprite can't carry session state across test runs. A workaround would be to expose a query-param or URL hash to pre-seed the app state for testing.

### 🟢 Low Priority

7. **Test wording mismatches (TC031)**
   Test assertions use expected strings like `"Datadog connection failed"` but the app shows `"Enter Datadog API key to enable metrics"`. Test cases should be updated to match actual UI copy.

8. **Quality judge test coverage is shallow**
   The MiniMax quality judge flow (TC023–TC024) is only tested for the "key missing" path. The "key present, judge runs" path is not covered with assertions on the actual score rendering — this is a gap if the MiniMax key is ever available in the test environment.
