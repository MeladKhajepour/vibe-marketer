# Autopilot Marketer

AI CMO for vibe coders. Runs a quick discovery chat, then generates ICP, community recommendations, and platform-native marketing copy.

## Flow

1. **Describe your product** — Enter what you're building
2. **Discovery chat** — MiniMax M2.5 asks 1–3 questions to understand your ICP (Trigger, Hack, Win)
3. **Generate Strategy** — Bedrock (Claude) creates ICP + communities + native copy

## Quick start

1. **Edit `.env`** — Add your MiniMax and Bedrock keys
2. **Install & run:**
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. **Open** http://localhost:8501
