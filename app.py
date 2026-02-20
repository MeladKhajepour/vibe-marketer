"""
Autopilot Marketer — AI CMO for vibe coders.
Takes a product description and generates ICP, communities, and platform-native marketing copy.
Uses Amazon Bedrock (Claude) for strategy generation; MiniMax (sponsor) for alternative copy variations.
"""

from dotenv import load_dotenv
load_dotenv()

import os
import re
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

import streamlit as st
import boto3
from botocore.config import Config
import anthropic

# Optional Datadog integration
try:
    from datetime import datetime
    from datadog_api_client import ApiClient, Configuration
    from datadog_api_client.v2.api.metrics_api import MetricsApi
    from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
    from datadog_api_client.v2.model.metric_payload import MetricPayload
    from datadog_api_client.v2.model.metric_point import MetricPoint
    from datadog_api_client.v2.model.metric_resource import MetricResource
    from datadog_api_client.v2.model.metric_series import MetricSeries

    DATADOG_AVAILABLE = True
except ImportError:
    DATADOG_AVAILABLE = False

BEDROCK_MODEL_ID = "us.anthropic.claude-sonnet-4-6"
MINIMAX_MODEL_ID = "MiniMax-M2.5"
MINIMAX_DISCOVERY_MODEL_ID = "MiniMax-M2.5"
MINIMAX_BASE_URL = "https://api.minimax.io/anthropic"
DEFAULT_PRODUCT = "An AI workout tracking app called Sage that tracks progressive overload"
MAX_DISCOVERY_ROUNDS = 3

DISCOVERY_SYSTEM_PROMPT = """You are an elite, no-nonsense AI Growth Marketer for "vibe coders" and solo developers. Your goal is to gather just enough info to identify their Ideal Customer Profile (ICP) and find where that ICP hangs out online.

You need to understand three vectors:
1. THE TRIGGER: What specific, painful event forces someone to look for this solution?
2. THE HACK: How is the target user currently duct-taping this problem together?
3. THE WIN: What specific metric or outcome improves if this product works perfectly?

RULES:
- Analyze what the user has told you so far. Identify which vectors are CLEAR vs MISSING.
- If you're missing info on any vector, ask ONE question to fill the most critical gap. Be casual, direct, developer-friendly.
- If you have enough context to understand all 3 vectors clearly, respond with exactly: READY
- Never ask more than one question per turn.
- Never repeat a question the user already answered.
- Keep it brief. No fluff.

Respond with ONLY your question OR the word READY. Nothing else."""

PROMPT_TEMPLATE = """You are an expert CMO and strategist. Given the product description and discovery conversation below, extract the key insights and identify the top distribution platforms.

Product: {product}

Discovery conversation:
{conversation}

Respond with EXACTLY this markdown structure:

## Ideal Customer Profile
[Describe the ICP: demographics, pain points, goals. Be specific based on the discovery.]

## Trigger
[One clear sentence: the exact painful event that forces someone to look for this solution]

## Hack
[One clear sentence: what the ICP is currently using to solve this problem]

## Win
[One clear sentence: the specific outcome or metric that improves when this product works perfectly]

## Platform 1: [Platform Name]
[One sentence: why this platform is where the ICP spends time and why it is the top choice for this product]

## Platform 2: [Platform Name]
[One sentence: why this platform is where the ICP spends time and why it is a strong choice for this product]

## Platform 3: [Platform Name]
[One sentence: why this platform is where the ICP spends time and why it rounds out the distribution strategy]

Choose the top 3 platforms by ICP fit and organic reach (e.g., Reddit, Twitter/X, Instagram, TikTok, LinkedIn, Discord, Hacker News, YouTube). Rank them by priority for this specific ICP and product category."""

PLATFORM_SPECIALIST_PROMPT = """You are a world-class {platform} content strategist and community expert with deep insider knowledge of {platform}'s culture, unwritten rules, what gets upvoted vs. flagged, and what makes someone look like a credible community member vs. a spammer.

You also specialize in marketing products like the one described below — you know exactly how this type of product is talked about, shared, and discovered by the people who need it most.

Your job: write a complete, step-by-step execution playbook for this product on {platform}. The person reading this is a solo developer who will follow your instructions exactly. Zero guesswork. Make every step so specific they can open {platform} right now and start.

Context:
- Product: {product_desc}
- ICP: {icp}
- Trigger (why they go looking): {the_trigger}
- Current Hack (what they use now): {the_hack}
- The Win (dream outcome): {the_win}

Respond with EXACTLY this structure:

## WHERE TO GO
List 3-5 specific communities on {platform} where this ICP actually hangs out (exact subreddit names, hashtags, Discord server names, account types, etc.). For each:
- **[Community name]**: One sentence on why this community, plus one key tip for fitting in here.

## WHAT TO TALK ABOUT
3 specific content angles that will resonate in these communities. These must directly connect the Trigger or Hack to the product — not generic topic ideas. For each angle, write one punchy sentence describing the exact approach.

## WHAT TO SAY
Two ready-to-use posts for {platform}. Each post must:
- Follow the Problem-Solution Lead framework: Hook (agitate the Trigger) → Empathy (acknowledge the Hack sucks) → Pivot (introduce the product as the fix) → CTA (one low-friction next step)
- Sound like a fellow community member sharing a discovery, not a brand announcement
- Use short sentences with line breaks between them. No jargon. No hype words.
- Focus on ONE emotion and ONE promise. No feature lists.
- Match the exact length, tone, and format of {platform}

Wrap each post in a code block so it can be copied directly. Label them **Post A** and **Post B**.

## HOW TO ENGAGE
Exact step-by-step instructions:
1. **Before you post**: What to do first (e.g., read community rules, comment on 5 threads, build karma)
2. **When someone comments**: Exactly how to respond to build trust and keep the thread alive
3. **DM playbook**: When and how to take conversations to DMs (only include if relevant to {platform})
4. **3 things that will get you ignored or banned**: Specific red flags for these communities"""

QUALITY_JUDGE_PROMPT = """You are a ruthless, expert advertising quality evaluator who specializes in {platform}. You have spent years studying what makes content succeed or fail on {platform} — you know its culture, its moderation patterns, what its users upvote vs. downvote, and exactly what separates a post that gets traction from one that gets ignored or flagged.

You also have deep expertise in direct response copywriting: you know a strong hook from a weak one, a compelling Problem-Solution lead from generic feature-listing, and a clear CTA from a vague one.

You are evaluating a marketing playbook written for {platform} for the following product and audience:
- Product: {product_desc}
- ICP: {icp}
- Trigger (why they go looking): {the_trigger}
- Current Hack (what they use now): {the_hack}
- The Win (dream outcome): {the_win}

Playbook to evaluate:
{playbook}

Score this playbook on four criteria. Be critical — a score above 80 must be genuinely earned:

1. Platform Fit (0-30 pts): Does this feel completely native to {platform}? Would a real community member recognize the posts as authentic, or do they read like ads? Are the recommended communities real and accurately described?
2. Copy Strength (0-30 pts): Are the posts emotionally resonant? Is the hook specific and painful (not generic)? Does it follow Problem-Solution structure? Is the CTA clear and low-friction?
3. ICP Precision (0-25 pts): Does the copy speak directly to this specific ICP's Trigger and Hack — or does it feel like it could be for anyone?
4. Actionability (0-15 pts): Can a solo developer follow the engagement instructions right now without googling anything or making judgment calls?

Respond with EXACTLY this format (two lines, nothing else):
SCORE: [0-100]
RATIONALE: [One blunt sentence identifying the single biggest strength or weakness]"""




def get_bedrock_client(access_key: str | None, secret_key: str | None, region: str | None):
    """Create Bedrock runtime client, using sidebar overrides if provided."""
    log.info("Creating Bedrock client (region=%s)", region)
    kwargs = {}
    if access_key and secret_key:
        kwargs["aws_access_key_id"] = access_key
        kwargs["aws_secret_access_key"] = secret_key
        log.info("Using IAM credentials from .env")
    else:
        log.info("Using default credential chain (env/BearerToken/profile)")
    if region:
        kwargs["region_name"] = region
    config = Config(retries={"max_attempts": 2, "mode": "standard"})
    return boto3.client("bedrock-runtime", config=config, **kwargs)


def invoke_bedrock(client, prompt: str) -> str:
    """Call Bedrock Converse API with Claude Sonnet 4.6."""
    log.info("Calling Bedrock (model=%s)...", BEDROCK_MODEL_ID)
    response = client.converse(
        modelId=BEDROCK_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 4096, "temperature": 0.7},
    )
    text = response["output"]["message"]["content"][0]["text"]
    log.info("Bedrock response received (%d chars)", len(text))
    return text


def invoke_minimax(api_key: str, prompt: str, system: str = "You are an expert advertising quality evaluator.") -> str:
    """Call MiniMax API via Anthropic-compatible endpoint."""
    log.info("Calling MiniMax API...")
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=MINIMAX_BASE_URL,
    )
    message = client.messages.create(
        model=MINIMAX_MODEL_ID,
        max_tokens=5000,
        system=system,
        messages=[{"role": "user", "content": prompt}],
    )
    text_parts = []
    for block in message.content:
        if hasattr(block, "text") and block.text:
            text_parts.append(block.text)
    result = "\n".join(text_parts)
    log.info("MiniMax response received (%d chars)", len(result))
    return result


def invoke_minimax_discovery(api_key: str, messages: list[dict]) -> str:
    """Call MiniMax M2.5 for discovery chat (multi-turn)."""
    log.info("Calling MiniMax Discovery (model=%s, messages=%d)...", MINIMAX_DISCOVERY_MODEL_ID, len(messages))
    client = anthropic.Anthropic(
        api_key=api_key,
        base_url=MINIMAX_BASE_URL,
    )
    message = client.messages.create(
        model=MINIMAX_DISCOVERY_MODEL_ID,
        max_tokens=10000,
        system=DISCOVERY_SYSTEM_PROMPT,
        messages=messages,
    )
    text_parts = []
    for block in message.content:
        if hasattr(block, "text") and block.text:
            text_parts.append(block.text)
    result = "\n".join(text_parts).strip()
    log.info("MiniMax Discovery response (stop=%s): %s",
             message.stop_reason, result)
    return result


def parse_strategy_output(text: str) -> tuple[str, list[tuple[str, str]], str, str, str]:
    """Parse Strategist output into ICP, platforms (name + justification), trigger, hack, win."""
    log.info("Parsing strategy output...")
    sections = re.split(r"\n##\s+", text, flags=re.IGNORECASE)
    icp = ""
    platforms: list[tuple[str, str]] = []
    trigger = ""
    hack = ""
    win = ""

    for section in sections:
        section = section.strip()
        if not section:
            continue
        lines = section.split("\n", 1)
        header = lines[0].strip().rstrip(":")
        body = lines[1].strip() if len(lines) > 1 else ""

        if "Ideal Customer Profile" in header or header == "ICP":
            icp = body
        elif header == "Trigger":
            trigger = body
        elif header == "Hack":
            hack = body
        elif header == "Win":
            win = body
        elif re.match(r"^Platform \d+:", header, re.IGNORECASE):
            name = re.sub(r"^Platform \d+:\s*", "", header, flags=re.IGNORECASE).strip()
            if name:
                platforms.append((name, body))

    log.info("Parsed: ICP + %d platforms, trigger=%s", len(platforms), bool(trigger))
    return icp, platforms, trigger, hack, win


def parse_quality_score(text: str) -> tuple[int, str]:
    """Extract SCORE and RATIONALE from MiniMax judge response."""
    log.info("MiniMax judge raw response: %s", text[:300])
    score = None
    rationale = ""
    for line in text.strip().splitlines():
        line = line.strip()
        if re.search(r"score", line, re.IGNORECASE):
            m = re.search(r"\b(\d{1,3})\b", line)
            if m:
                try:
                    score = int(m.group(1))
                    score = max(0, min(100, score))
                except ValueError:
                    pass
        if re.search(r"rationale", line, re.IGNORECASE) and ":" in line:
            rationale = line.split(":", 1)[1].strip()
    if score is None:
        # Last resort: grab first standalone number in the whole response
        m = re.search(r"\b(\d{1,3})\b", text)
        if m:
            score = max(0, min(100, int(m.group(1))))
            log.warning("Score extracted via fallback regex: %d", score)
        else:
            score = 50
            log.warning("Could not parse score from MiniMax response — defaulting to 50")
    log.info("Quality score parsed: %d — %s", score, rationale[:80])
    return score, rationale


def send_datadog_metric(api_key: str | None, platform: str | None = None, quality_score: int | None = None):
    """Send metrics to Datadog using API key auth only.

    Always sends the autopilot.campaigns.generated counter.
    When platform and quality_score are provided, also sends autopilot.campaigns.predicted_ctr
    gauge tagged with the platform name.
    """
    if not DATADOG_AVAILABLE:
        log.warning("Datadog client not available (import failed)")
        return
    if not api_key:
        log.warning("Datadog API key not set — skipping metric")
        return
    try:
        configuration = Configuration()
        configuration.api_key["apiKeyAuth"] = api_key
        ts = int(datetime.now().timestamp())
        platform_tag = platform.lower().replace("/", "_").replace(" ", "_") if platform else "unknown"
        series = [
            MetricSeries(
                metric="autopilot.campaigns.generated",
                type=MetricIntakeType.COUNT,
                points=[MetricPoint(timestamp=ts, value=1)],
                tags=[f"platform:{platform_tag}"],
                resources=[MetricResource(name="autopilot-marketer", type="service")],
            ),
        ]
        if quality_score is not None:
            series.append(
                MetricSeries(
                    metric="autopilot.campaigns.predicted_ctr",
                    type=MetricIntakeType.GAUGE,
                    points=[MetricPoint(timestamp=ts, value=quality_score / 100)],
                    tags=[f"platform:{platform_tag}"],
                    resources=[MetricResource(name="autopilot-marketer", type="service")],
                )
            )
        with ApiClient(configuration) as api_client:
            MetricsApi(api_client).submit_metrics(body=MetricPayload(series=series))
        log.info("Datadog metrics sent: platform=%s score=%s", platform_tag, quality_score)
    except Exception as e:
        log.warning("Datadog metric failed: %s", e)
        raise


def send_datadog_log(api_key: str | None, platform: str, product_desc: str,
                     playbook: str, quality_score: int | None,
                     trigger: str, hack: str, win: str):
    """Send generated playbook to Datadog Logs for LLM observability."""
    if not api_key:
        return
    payload = [{
        "ddsource": "python",
        "service": "vibe-marketer",
        "message": "Campaign Generated",
        "platform": platform,
        "product_description": product_desc,
        "trigger": trigger,
        "hack": hack,
        "win": win,
        "generated_playbook": playbook,
        "quality_score": quality_score,
    }]
    try:
        resp = requests.post(
            "https://http-intake.logs.datadoghq.com/api/v2/logs",
            headers={"DD-API-KEY": api_key, "Content-Type": "application/json"},
            json=payload,
            timeout=5,
        )
        resp.raise_for_status()
        log.info("Datadog log sent for platform=%s (status=%s)", platform, resp.status_code)
    except Exception as e:
        log.warning("Datadog log failed for %s: %s", platform, e)
        raise


def format_discovery_for_prompt(product: str, chat: list[dict]) -> str:
    """Format the discovery chat as context for the strategy prompt."""
    lines = []
    for msg in chat:
        role = "User" if msg["role"] == "user" else "Agent"
        lines.append(f"{role}: {msg['content']}")
    return "\n".join(lines) if lines else "(No discovery conversation)"


def main():
    st.set_page_config(page_title="Vibe Marketer", layout="wide")
    st.title("Vibe Marketer")
    st.caption("AI CMO for vibe coders — product in, ICP + communities + native copy out")

    # Credentials from .env (loaded at startup)
    access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") or "us-east-1"
    minimax_api_key = os.environ.get("ANTHROPIC_API_KEY")
    bedrock_token = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
    dd_api_key_env = os.environ.get("DD_API_KEY", "")

    log.info("App loaded. Bedrock=%s, MiniMax=%s",
             "ok" if ((access_key and secret_key) or bedrock_token) else "missing",
             "ok" if minimax_api_key else "not set")

    # Initialize session state
    if "discovery_chat" not in st.session_state:
        st.session_state["discovery_chat"] = []
    if "discovery_round" not in st.session_state:
        st.session_state["discovery_round"] = 0
    if "discovery_complete" not in st.session_state:
        st.session_state["discovery_complete"] = False
    if "discovery_started" not in st.session_state:
        st.session_state["discovery_started"] = False
    if "product" not in st.session_state:
        st.session_state["product"] = ""
    if "trigger" not in st.session_state:
        st.session_state["trigger"] = ""
    if "hack" not in st.session_state:
        st.session_state["hack"] = ""
    if "win" not in st.session_state:
        st.session_state["win"] = ""
    if "datadog_sent" not in st.session_state:
        st.session_state["datadog_sent"] = False

    # Sidebar: status + credentials
    with st.sidebar:
        st.subheader("Credentials")
        if access_key and secret_key:
            st.success("Bedrock: OK")
        elif bedrock_token:
            st.success("Bedrock: OK (API key)")
        else:
            st.warning("Add Bedrock keys to .env")
        if minimax_api_key:
            st.success("MiniMax: OK")
        else:
            st.warning("Add MiniMax key to .env for discovery")

        st.divider()
        st.subheader("Datadog")
        dd_api_key = st.text_input(
            "Datadog API Key",
            value=dd_api_key_env,
            type="password",
        )
        if dd_api_key:
            st.success("Datadog: OK")
        else:
            st.warning("Enter Datadog API key to enable metrics")

        st.divider()
        if st.button("Start Over"):
            for key in ["discovery_chat", "discovery_round", "discovery_complete",
                        "discovery_started", "product", "strategy",
                        "trigger", "hack", "win", "datadog_sent"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

    # ========== PHASE 1: Product Input ==========
    if not st.session_state["discovery_started"]:
        st.subheader("1. Describe your product")
        product = st.text_area(
            "What are you building?",
            value=DEFAULT_PRODUCT,
            height=120,
            placeholder="Describe your product...",
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start Discovery", type="primary", disabled=not minimax_api_key):
                if not product.strip():
                    st.error("Please enter a product description.")
                else:
                    st.session_state["product"] = product.strip()
                    st.session_state["discovery_started"] = True
                    st.session_state["discovery_chat"] = []
                    st.session_state["discovery_round"] = 0
                    st.session_state["discovery_complete"] = False
                    # Kick off first question
                    try:
                        initial_msg = f"I'm building: {product.strip()}"
                        messages = [{"role": "user", "content": initial_msg}]
                        response = invoke_minimax_discovery(minimax_api_key, messages)
                        st.session_state["discovery_chat"] = [
                            {"role": "user", "content": initial_msg},
                            {"role": "assistant", "content": response},
                        ]
                        st.session_state["discovery_round"] = 1
                        if response.strip().upper() == "READY":
                            st.session_state["discovery_complete"] = True
                        st.rerun()
                    except Exception as e:
                        log.exception("Discovery start error")
                        st.error(f"MiniMax error: {e}")
        with col2:
            if st.button("Skip Discovery", disabled=not ((access_key and secret_key) or bedrock_token)):
                if not product.strip():
                    st.error("Please enter a product description.")
                else:
                    st.session_state["product"] = product.strip()
                    st.session_state["discovery_started"] = True
                    st.session_state["discovery_complete"] = True
                    st.rerun()
        
        if not minimax_api_key:
            st.caption("Add ANTHROPIC_API_KEY to .env to enable discovery chat.")
        return

    # ========== PHASE 2: Discovery Chat ==========
    if not st.session_state["discovery_complete"]:
        st.subheader("2. Quick Discovery")
        st.caption(f"Round {st.session_state['discovery_round']} of {MAX_DISCOVERY_ROUNDS}")
        
        # Display chat history
        for msg in st.session_state["discovery_chat"]:
            if msg["role"] == "user" and msg["content"].startswith("I'm building:"):
                continue  # Skip the initial context message in display
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Chat input
        user_input = st.chat_input("Your answer...")
        if user_input:
            # Add user message
            st.session_state["discovery_chat"].append({"role": "user", "content": user_input})
            st.session_state["discovery_round"] += 1
            
            # Check if we've hit max rounds
            if st.session_state["discovery_round"] > MAX_DISCOVERY_ROUNDS:
                st.session_state["discovery_complete"] = True
                st.rerun()
            
            # Get next question from MiniMax
            try:
                response = invoke_minimax_discovery(
                    minimax_api_key, 
                    st.session_state["discovery_chat"]
                )
                st.session_state["discovery_chat"].append({"role": "assistant", "content": response})
                
                if response.strip().upper() == "READY":
                    st.session_state["discovery_complete"] = True
                st.rerun()
            except Exception as e:
                log.exception("Discovery error")
                st.error(f"MiniMax error: {e}")
        
        # Option to skip remaining questions
        if st.session_state["discovery_round"] >= 1:
            if st.button("I've shared enough — Generate Strategy"):
                st.session_state["discovery_complete"] = True
                st.rerun()
        return

    # ========== PHASE 3: Strategy Generation ==========
    st.subheader("3. Generate Strategy")
    st.info("✅ Discovery session complete! The agent has gathered enough context about your product. Click **Generate Strategy** below to create your go-to-market strategy.")

    # Show discovery summary
    if st.session_state["discovery_chat"]:
        with st.expander("Discovery conversation", expanded=False):
            for msg in st.session_state["discovery_chat"]:
                role = "You" if msg["role"] == "user" else "Agent"
                st.write(f"**{role}:** {msg['content']}")
    
    # Strategy results
    if "strategy" in st.session_state:
        icp, platforms = st.session_state["strategy"]
        st.success("Strategy generated successfully!")
        if st.session_state.get("datadog_sent"):
            st.success("📊 Metric successfully sent to Datadog!")
        tab_names = ["ICP"] + [p[0] for p in platforms]
        tabs = st.tabs(tab_names)
        with tabs[0]:
            st.markdown(icp)
        for i, (name, justification, playbook_text, quality_score, rationale) in enumerate(platforms):
            with tabs[i + 1]:
                if justification:
                    st.caption(justification)
                if quality_score is not None:
                    score_color = "green" if quality_score >= 70 else "orange" if quality_score >= 50 else "red"
                    score_label = f":{score_color}[**Quality Score: {quality_score}/100**]"
                    if rationale:
                        st.markdown(f"{score_label} — {rationale}")
                    else:
                        st.markdown(score_label)
                st.markdown(playbook_text)
    else:
        # Generate button
        has_bedrock = (access_key and secret_key) or bedrock_token
        if not has_bedrock:
            st.error("Add AWS keys to .env to generate strategy.")
            return

        if st.button("Generate Strategy", type="primary"):
            client = get_bedrock_client(access_key, secret_key, region)
            try:
                product = st.session_state["product"]
                conversation = format_discovery_for_prompt(product, st.session_state["discovery_chat"])

                # --- Agent 1: Strategist ---
                with st.spinner("Agent 1 — The Strategist: Mapping ICP and platforms..."):
                    prompt = PROMPT_TEMPLATE.format(product=product, conversation=conversation)
                    raw = invoke_bedrock(client, prompt)
                    icp, platform_list, trigger, hack, win = parse_strategy_output(raw)
                    if not icp and not platform_list:
                        icp = raw
                        platform_list = []
                    st.session_state["trigger"] = trigger
                    st.session_state["hack"] = hack
                    st.session_state["win"] = win

                # Show identified platforms so the user has context before specialists run
                platform_names_str = " · ".join(f"**{n}**" for n, _ in platform_list)
                st.info(f"Platforms identified: {platform_names_str}")

                # --- Agents 2–N: Platform Specialists (parallel) ---
                def run_specialist(args):
                    pname, pjust = args
                    try:
                        local_client = get_bedrock_client(access_key, secret_key, region)
                        sp = PLATFORM_SPECIALIST_PROMPT.format(
                            platform=pname,
                            product_desc=product,
                            icp=icp,
                            the_trigger=trigger or product,
                            the_hack=hack or "their current workaround",
                            the_win=win or "their goal",
                        )
                        playbook = invoke_bedrock(local_client, sp)
                        return pname, pjust, playbook.strip(), None
                    except Exception as e:
                        log.exception("Specialist failed for %s", pname)
                        return pname, pjust, "", e

                n = len(platform_list)
                with st.spinner(f"Running {n} Platform Specialists in parallel..."):
                    with ThreadPoolExecutor(max_workers=n) as pool:
                        specialist_results = list(pool.map(run_specialist, platform_list))

                for pname, _, _, err in specialist_results:
                    if err:
                        st.toast(f"⚠️ Specialist failed for {pname}: {err}", icon="⚠️")

                successful = [(pname, pjust, pb) for pname, pjust, pb, err in specialist_results if not err]

                # --- Quality Judges (parallel, only if MiniMax key available) ---
                judge_results: dict[str, tuple[int | None, str]] = {pname: (None, "") for pname, _, _ in successful}

                if minimax_api_key and successful:
                    def run_judge(args):
                        pname, pjust, playbook = args
                        try:
                            jp = QUALITY_JUDGE_PROMPT.format(
                                platform=pname,
                                product_desc=product,
                                icp=icp,
                                the_trigger=trigger or product,
                                the_hack=hack or "their current workaround",
                                the_win=win or "their goal",
                                playbook=playbook,
                            )
                            raw_j = invoke_minimax(minimax_api_key, jp)
                            score, rationale = parse_quality_score(raw_j)
                            return pname, score, rationale, None
                        except Exception as e:
                            log.warning("Judge failed for %s: %s", pname, e)
                            return pname, None, "", e

                    with st.spinner(f"Judging {len(successful)} playbooks in parallel..."):
                        with ThreadPoolExecutor(max_workers=len(successful)) as pool:
                            judge_list = list(pool.map(run_judge, successful))

                    for pname, score, rationale, err in judge_list:
                        if err:
                            st.toast(f"⚠️ Quality judge failed for {pname}: {err}", icon="⚠️")
                        judge_results[pname] = (score, rationale)

                # --- Datadog metrics + assemble final platform list ---
                platforms = []
                for pname, pjust, playbook in successful:
                    score, rationale = judge_results[pname]
                    try:
                        send_datadog_metric(dd_api_key, platform=pname, quality_score=score)
                        send_datadog_log(
                            dd_api_key,
                            platform=pname,
                            product_desc=product,
                            playbook=playbook,
                            quality_score=score,
                            trigger=trigger,
                            hack=hack,
                            win=win,
                        )
                        st.session_state["datadog_sent"] = True
                    except Exception as dd_err:
                        log.warning("Datadog metric failed for %s: %s", pname, dd_err)
                        st.toast(f"⚠️ Datadog metric failed for {pname}: {dd_err}", icon="⚠️")
                    platforms.append((pname, pjust, playbook, score, rationale))

                st.session_state["strategy"] = (icp, platforms)
                st.rerun()
            except Exception as e:
                log.exception("Bedrock error")
                st.error(f"Error: {e}")


if __name__ == "__main__":
    log.info("Starting Autopilot Marketer...")
    main()
