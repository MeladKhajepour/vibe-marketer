# Vibe Marketer

**AI CMO for vibe coders.** Describe your product, answer 3 quick questions, and get a complete platform-by-platform distribution playbook — written by specialist AI agents, scored by a cross-model quality judge, and logged to Datadog for full LLM observability.

---

## What It Does

Most vibe coders can ship fast but struggle to market. Vibe Marketer removes that bottleneck entirely. You describe what you built, and a multi-agent AI pipeline does the rest:

1. **Discovery** — A MiniMax agent asks up to 3 targeted questions to extract:
   - **Trigger** — the painful event that drives someone to look for your solution
   - **Hack** — what they currently use as a workaround
   - **Win** — the specific outcome they want

2. **Strategy** — A Strategist agent (Claude via Amazon Bedrock) analyzes your product and discovery answers to define your ICP and identify the top 3 distribution platforms.

3. **Platform Playbooks** — A dedicated Platform Specialist agent runs for each platform *in parallel*, producing a complete step-by-step execution plan:
   - **WHERE TO GO** — 3–5 specific communities (exact subreddits, Discord servers, hashtags)
   - **WHAT TO TALK ABOUT** — 3 content angles tied directly to your audience's Trigger and Hack
   - **WHAT TO SAY** — 2 ready-to-copy posts using direct response copywriting principles (Gary Halbert's Problem-Solution Lead framework)
   - **HOW TO ENGAGE** — exact steps before posting, how to respond to comments, DM strategy, and what will get you banned

4. **Quality Judging** — A MiniMax quality judge evaluates each playbook *in parallel* against platform-specific advertising standards and ICP fit. Scores 0–100 with a one-line critique. Cross-model evaluation (MiniMax judges Claude) avoids self-grading bias.

5. **Datadog Observability** — Every generation sends:
   - Custom metrics (`campaign_generated`, `predicted_ctr`) tagged by platform
   - Full LLM observability logs (inputs + generated playbook + quality score) to Datadog Log Explorer

---

## Agent Architecture

```
MiniMax M2.5          → Discovery (up to 3 rounds)
                              ↓
Claude Sonnet 4.6     → Strategist: ICP + top 3 platforms
                              ↓
Claude Sonnet 4.6 ×3  → Platform Specialists (parallel)
                              ↓
MiniMax M2.1 ×3       → Quality Judges (parallel)
                              ↓
Datadog               → Metrics + LLM observability logs
```

**Wall time:** ~13s for the full pipeline (parallel execution).

---

## Quick Start

### 1. Clone and install
```bash
git clone https://github.com/MeladKhajepour/vibe-marketer.git
cd vibe-marketer
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```
AWS_ACCESS_KEY_ID=         # Bedrock IAM credentials
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
ANTHROPIC_API_KEY=         # MiniMax API key (platform.minimax.io)
DD_API_KEY=                # Datadog API key
```

### 3. Run
```bash
streamlit run app.py
```

Open http://localhost:8501

---

## Tech Stack

| | |
|---|---|
| UI | Streamlit |
| Strategy & Playbooks | Amazon Bedrock (Claude Sonnet 4.6) |
| Discovery & Quality Judging | MiniMax M2.5 / M2.1 |
| Observability | Datadog (metrics + logs) |
| Parallelism | Python `concurrent.futures` |

---

## Environment Variables

| Variable | Required | Purpose |
|---|---|---|
| `AWS_ACCESS_KEY_ID` | Yes | Bedrock access |
| `AWS_SECRET_ACCESS_KEY` | Yes | Bedrock access |
| `AWS_DEFAULT_REGION` | Yes | Bedrock region (default: `us-east-1`) |
| `ANTHROPIC_API_KEY` | Recommended | MiniMax discovery + quality judging |
| `DD_API_KEY` | Recommended | Datadog metrics + logs |
