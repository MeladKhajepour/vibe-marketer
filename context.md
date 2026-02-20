# Vibe Marketer — Project Context

## Overview

**Project name:** Vibe Marketer
**Repo:** https://github.com/MeladKhajepour/vibe-marketer
**Goal:** AI CMO for vibe coders — product description in, full distribution playbook out.

---

## What It Does

Vibe Marketer takes a product description, runs a short discovery chat to extract key audience insights, then generates a complete platform-by-platform go-to-market playbook with no manual work required.

---

## Agent Pipeline

```
Phase 1 — Discovery (MiniMax M2.5)
  Up to 3 rounds of targeted questions to extract:
  - Trigger: the painful event that drives someone to look for this solution
  - Hack: what they currently use as a workaround
  - Win: the specific outcome they want

Phase 2 — Strategy (Amazon Bedrock / Claude Sonnet 4.6)
  Agent 1: The Strategist
    Input: product description + discovery conversation
    Output: ICP, Trigger, Hack, Win, top 3 platforms with justifications

Phase 3 — Platform Playbooks (Amazon Bedrock / Claude Sonnet 4.6) [PARALLEL]
  One Platform Specialist per platform, running concurrently
  Each specialist has deep expertise in that platform AND the product category
  Output per platform (4 sections):
    - WHERE TO GO: 3–5 specific communities (subreddits, hashtags, Discord servers, etc.)
    - WHAT TO TALK ABOUT: 3 content angles tied directly to Trigger/Hack/Win
    - WHAT TO SAY: 2 ready-to-use posts (Gary Halbert Problem-Solution Lead framework,
                   wrapped in code blocks for one-click copy)
    - HOW TO ENGAGE: step-by-step execution (before posting, responding, DMs, red flags)

Phase 4 — Quality Judging (MiniMax M2.5) [PARALLEL]
  One Quality Judge per platform, running concurrently
  Cross-model evaluation (MiniMax judges Claude's output — avoids self-grading bias)
  Scored on: Platform Fit (30pts) + Copy Strength (30pts) + ICP Precision (25pts) + Actionability (15pts)
  Output: SCORE (0–100) + one-line RATIONALE
  Score displayed as colour-coded badge in UI (green ≥70, orange ≥50, red <50)
```

**Total Bedrock calls:** 4 (1 Strategist + 3 Specialists)
**Total MiniMax calls:** 3 discovery (M2.5) + 3 judges (M2.5)
**Wall time:** ~13s (specialists and judges each run in parallel via ThreadPoolExecutor)

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Strategy + Playbooks | Amazon Bedrock (Claude Sonnet 4.6 — `us.anthropic.claude-sonnet-4-6`) |
| Discovery + Quality Judging | MiniMax M2.5 via Anthropic-compatible API |
| Metrics | Datadog API v2 (`datadog-api-client`) |
| LLM Observability Logs | Datadog Logs (`requests` → `http-intake.logs.datadoghq.com`) |
| Parallelism | `concurrent.futures.ThreadPoolExecutor` |

---

## Datadog Integration

### Metrics (sent per platform after each generation)
- `autopilot.campaigns.generated` — COUNT, tagged `platform:<name>`
- `autopilot.campaigns.predicted_ctr` — GAUGE (score/100), tagged `platform:<name>`

### Logs (LLM Observability)
Sent to Datadog Log Explorer per platform. Each log entry contains:
- `platform`, `product_description`, `trigger`, `hack`, `win`
- `generated_playbook` — full Claude output
- `quality_score` — MiniMax's cross-model evaluation score

Auth: API key only (`DD-API-KEY` header / `configuration.api_key["apiKeyAuth"]`). No app key required.

---

## Key Files

| File | Purpose |
|---|---|
| `app.py` | Entire application (prompts, agents, UI, Datadog) |
| `.env` | Local secrets — never committed |
| `.env.example` | Template for required env vars |
| `requirements.txt` | Python dependencies |

---

## Environment Variables

```
AWS_ACCESS_KEY_ID          Bedrock IAM credentials
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION         Default: us-east-1
ANTHROPIC_API_KEY          MiniMax API key (discovery + quality judging)
DD_API_KEY                 Datadog API key (metrics + logs)
```

---

## Prompt Architecture

| Constant | Model | Role |
|---|---|---|
| `DISCOVERY_SYSTEM_PROMPT` | MiniMax M2.5 | Extracts Trigger/Hack/Win via 1–3 questions |
| `PROMPT_TEMPLATE` | Claude Sonnet 4.6 | Strategist — ICP + top 3 platforms |
| `PLATFORM_SPECIALIST_PROMPT` | Claude Sonnet 4.6 | Full playbook per platform (4 sections) |
| `QUALITY_JUDGE_PROMPT` | MiniMax M2.5 | Cross-model quality scorer (0–100) |
