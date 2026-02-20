# Autopilot Marketer — Project Context

## Overview

**Project name:** Autopilot Marketer  
**Scope:** 5-hour hackathon MVP  
**Goal:** Build an AI CMO for vibe coders.

## What It Does

Autopilot Marketer takes a product description, runs a quick discovery chat to understand the ICP deeply, then produces a full go-to-market strategy:

1. **Discovery chat (MiniMax M2.5)** — 1–3 questions to extract Trigger, Hack, and Win vectors
2. **Ideal Customer Profile (ICP)** — Who is the perfect customer, based on discovery insights
3. **Community identification** — The top 2–3 specific online communities where that ICP hangs out
4. **Platform-native marketing copy** — Tailored content for each platform

## Flow

```
Product description → Discovery chat (max 3 rounds) → ICP definition → Communities → Native copy
```

## Tech Stack

- **Python** — Application language
- **Streamlit** — Web UI
- **boto3** — AWS SDK for Amazon Bedrock (Claude) — *required* for strategy generation
- **anthropic** — MiniMax API (Anthropic-compatible; hackathon sponsor) — *optional*, for "Generate alternative" per platform
- **datadog-api-client** — Observability (custom metrics)

## Datadog Note

The hackathon requires use of Datadog MCP. For the MVP, we use `datadog-api-client` to send custom metrics (e.g. `autopilot_marketer.strategy.created`) when a strategy is generated. Datadog MCP can also be used in Cursor for dev-time observability.
