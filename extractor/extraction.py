import os
import json
import time
import re
from groq import Groq
from dotenv import load_dotenv
from docx import Document

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ─────────────────────────────────────────────
# TRANSCRIPT READING
# ─────────────────────────────────────────────

def read_transcript(file_path):
    doc = Document(file_path)
    lines = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n".join(lines)


def split_into_chunks(text, max_chars=3500):
    lines = text.split("\n")
    chunks, current = [], ""

    for line in lines:
        if len(current) + len(line) + 1 > max_chars and current:
            chunks.append(current.strip())
            current = line + "\n"
        else:
            current += line + "\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks


# ─────────────────────────────────────────────
# CUSTOMER-CENTRIC SIGNAL CATEGORIES
# ─────────────────────────────────────────────

CUSTOMER_CATEGORIES = """
CUSTOMER LIFE CONTEXT
1. life_goal
2. life_event
3. existing_wealth
4. financial_anxiety
5. family_dependency
6. past_experience

CUSTOMER DECISION SIGNALS
7. buying_signal
8. hesitation_signal
9. hard_objection
10. clarification_ask
11. commitment

CUSTOMER CONSTRAINTS
12. budget_ceiling
13. liquidity_need
14. time_horizon
15. risk_tolerance
16. execution_capacity

CUSTOMER EMOTIONAL STATE
17. trust_signal
18. distrust_signal
19. confusion_signal
20. rapport_item

DO NOT EXTRACT:
- Advisor explanations unless customer reacts
- Greetings
- Text under 6 words
- Pure advisor statements
"""

VALID_CATEGORIES = {
    "life_goal", "life_event", "existing_wealth", "financial_anxiety",
    "family_dependency", "past_experience",
    "buying_signal", "hesitation_signal", "hard_objection",
    "clarification_ask", "commitment",
    "budget_ceiling", "liquidity_need", "time_horizon",
    "risk_tolerance", "execution_capacity",
    "trust_signal", "distrust_signal", "confusion_signal", "rapport_item"
}

INVALID_CATEGORY_HEADINGS = {
    "CUSTOMER LIFE CONTEXT",
    "CUSTOMER DECISION SIGNALS",
    "CUSTOMER CONSTRAINTS",
    "CUSTOMER EMOTIONAL STATE",
    "CUSTOMER GOALS"
}


PAYLOAD_SCHEMA = """
{
  "speaker_role": "customer" | "advisor" | "unknown",
  "customer_emotion": "anxious" | "confident" | "confused" | "resistant" | "interested" | "neutral",
  "decision_stage": "exploring" | "evaluating" | "ready_to_commit" | "pulling_back" | "unknown",
  "life_context_tag": "short phrase",
  "underlying_need": "1 sentence",
  "follow_up_question": "question or null",
  "sentiment": "positive" | "negative" | "neutral",
  "buying_intent": "high" | "medium" | "low" | "blocking",
  "summary": "1 sentence"
}
"""


# ─────────────────────────────────────────────
# B2C ENTITY CATEGORIES
# Added from your entity-definition document
# ─────────────────────────────────────────────

B2C_ENTITY_CATEGORIES = """
Extract factual B2C sales-call entities using these categories:

1. people
Any individual referenced: prospect, rep, colleague, family, friend, RM, research head.
Capture name or role and side.

2. products
Any named product, app, platform, service, financial instrument, plan, stock, screener.

3. locations
Any geographic place, city, region, exchange, market reference.

4. process_step
Any onboarding or sales-flow step:
KYC, e-KYC, demat account opening, activation, app training, API setup, approval, documentation.

5. objection
Any hesitation, doubt, pushback:
pricing, trust, credibility, ROI doubt, timeline, usability, personal consultation, skepticism.

6. pain_point
Customer problem or gap:
lack of time, lack of knowledge, low returns, no expert guidance, risk exposure, income dependency.

7. commitment
Something either party agrees to do:
do KYC, open account, call back, research, meet, deposit funds, provide projections.

8. next_step
Concrete forward-looking task:
owner, due date, dependency, status.

9. budget_pricing_signal
Investment amount, capacity, charges, pricing sensitivity, fees, brokerage, AMC.

10. timeline_signal
When customer wants to decide, start, invest, follow up, or defer.

11. authority_decision_process
Who decides:
self, spouse, family, friend, personal influencer, wants self-verification.

12. competition_status_quo
Current way of doing things:
self-trading, current broker, current app, mutual fund, other advisor, status quo.

13. requirement_constraint
Conditions or limitations:
needs no manual execution, limited time, broker limitation, wants office visit, wants no upfront cost.

14. product_intent
Interest/curiosity/like/dislike toward a product feature, return, process, app, plan.

15. risk_cue
Deal risk:
trust risk, value doubt, price objection, deferral, status quo, no budget, low engagement, competitor.

16. intent_signal
Positive/negative/neutral buying movement:
asking app name, agreeing to proceed, saying later, repeated no, asking details.

17. rapport_item
Personal non-transactional details:
job, family, availability, preferences, life circumstances.
"""

VALID_ENTITY_CATEGORIES = {
    "people",
    "products",
    "locations",
    "process_step",
    "objection",
    "pain_point",
    "commitment",
    "next_step",
    "budget_pricing_signal",
    "timeline_signal",
    "authority_decision_process",
    "competition_status_quo",
    "requirement_constraint",
    "product_intent",
    "risk_cue",
    "intent_signal",
    "rapport_item"
}


# ─────────────────────────────────────────────
# SAFE JSON PARSER
# ─────────────────────────────────────────────

def _safe_parse(text):
    text = text.strip()
    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON list found. Raw output:\n{text[:300]}")

    return json.loads(text[start:end + 1])


# ─────────────────────────────────────────────
# SPEAKER NAME FALLBACK
# ─────────────────────────────────────────────

def infer_names_from_addressing(transcript_text, metadata):
    """
    Lightweight fallback:
    If one speaker directly addresses a name, assign that name to the other speaker.
    This does not replace LLM output unless speaker_name is missing.
    """

    lines = transcript_text.split("\n")
    current_speaker = None

    address_patterns = [
        r"\b(?:hi|hello|thank you|thanks|alright|okay|ok)\s+([A-Z][a-zA-Z]+)\b",
        r"\b([A-Z][a-zA-Z]+)\s+(?:ma'?am|madam|sir)\b",
    ]

    speakers = list(metadata.keys())

    for line in lines:
        speaker_match = re.match(r"^(Speaker\s+\d+)\s*$", line.strip())
        if speaker_match:
            current_speaker = speaker_match.group(1)
            continue

        if not current_speaker:
            continue

        for pattern in address_patterns:
            match = re.search(pattern, line.strip(), flags=re.IGNORECASE)
            if not match:
                continue

            name = match.group(1).strip()

            if name.lower() in {
                "hello", "okay", "right", "correct",
                "yes", "no", "good", "morning"
            }:
                continue

            if len(speakers) == 2:
                other_speaker = speakers[0] if speakers[1] == current_speaker else speakers[1]

                if metadata.get(other_speaker, {}).get("speaker_name") is None:
                    metadata[other_speaker]["speaker_name"] = name

    return metadata


# ─────────────────────────────────────────────
# LLM SPEAKER METADATA EXTRACTION
# ─────────────────────────────────────────────

def extract_speaker_metadata(transcript_text, source_file):
    prompt = f"""
You are analyzing a financial sales call transcript.

Your task:
Identify speaker roles and speaker names ONLY if clearly available in the transcript.

Return ONLY valid JSON list.

Format:
[
  {{
    "speaker_label": "Speaker 1",
    "speaker_name": "Rahul Sharma",
    "speaker_role": "customer"
  }}
]

Rules:
- speaker_label must exactly match transcript labels like Speaker 1, Speaker 2, Speaker 3.
- speaker_role must be one of: customer, advisor, unknown.
- Detect names from greetings, introductions, and direct addressing.
- If Speaker A says "Hello Phalguni Ma'am", Phalguni is usually Speaker B's name.
- If Speaker A says "Thank you Saloni" or "Alright Saloni", Saloni is usually Speaker B's name.
- If actual name is not clearly present in transcript, use null.
- Do NOT guess or hallucinate names.
- Infer customer/advisor role from conversation behavior.
- Customer usually asks questions, raises doubts, discusses money, risk, goals, family, hesitation.
- Advisor usually explains product, pricing, process, investment plan, hedging, advisory service.
- Return [] only if no speaker labels are found.

Transcript:
{transcript_text[:8000]}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()

    try:
        data = _safe_parse(raw)
        metadata = {}

        for item in data:
            speaker_label = item.get("speaker_label")

            if not speaker_label:
                continue

            metadata[speaker_label] = {
                "speaker_name": item.get("speaker_name"),
                "speaker_role": item.get("speaker_role", "unknown"),
                "source_file": source_file
            }

        metadata = infer_names_from_addressing(transcript_text, metadata)

        return metadata

    except Exception as e:
        print(f"Speaker metadata extraction failed: {e}")
        return {}


# ─────────────────────────────────────────────
# CUSTOMER SIGNAL EXTRACTION
# Your original main extraction prompt kept almost same
# ─────────────────────────────────────────────

def extract_signals_from_chunk(
    chunk_text,
    conversation_id,
    chunk_number,
    speaker_metadata,
    source_file
):
    role_note = "\n".join(
        f"  {speaker}: role={meta.get('speaker_role', 'unknown')}, "
        f"name={meta.get('speaker_name')}"
        for speaker, meta in speaker_metadata.items()
    )

    prompt = f"""
You are a customer insight analyst reviewing a financial sales call transcript.

Your ONLY job is to understand the CUSTOMER:
- fears
- goals
- constraints
- emotional state
- decision readiness
- concerns
- objections
- pricing/advisory fee concerns

You are NOT cataloguing the product pitch.

Speaker metadata:
{role_note}

Source file:
{source_file}

GOLDEN RULE:
Before extracting any signal, ask:
"Does this tell me something meaningful about the customer's situation,
psychology, concern, or decision-making?"

If no, skip it.

If the signal comes from advisor's mouth, only extract it if the customer reacted
to it clearly in the same or immediately next turn.

{CUSTOMER_CATEGORIES}

VERY IMPORTANT CATEGORY RULE:
category must be ONLY one of these exact values:
life_goal, life_event, existing_wealth, financial_anxiety, family_dependency, past_experience,
buying_signal, hesitation_signal, hard_objection, clarification_ask, commitment,
budget_ceiling, liquidity_need, time_horizon, risk_tolerance, execution_capacity,
trust_signal, distrust_signal, confusion_signal, rapport_item

Never use group headings like:
CUSTOMER LIFE CONTEXT, CUSTOMER DECISION SIGNALS, CUSTOMER CONSTRAINTS,
CUSTOMER EMOTIONAL STATE, CUSTOMER GOALS.

PAYLOAD SCHEMA:
{PAYLOAD_SCHEMA}

OUTPUT FORMAT:
Return ONLY valid JSON list. No markdown. No explanation.

Each object must contain:
- id
- conversation_id
- speaker
- speaker_name
- speaker_role
- source_file
- category
- source_text
- confidence
- payload
- status
- chunk_number

Rules:
- id must be unique string
- source_text = exact words from transcript
- source_text minimum 6 words
- Maximum 5 signals per chunk
- Prefer 2-3 high-confidence signals over weak signals
- Confidence below 0.6 = do not include
- For Hindi/English transcript: keep source_text as-is, summary in English
- status must be "active"
- source_file must be "{source_file}"
- If speaker name is unavailable, use null
- Do not invent customer names

conversation_id: {conversation_id}
chunk_number: {chunk_number}

Transcript:
{chunk_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    return _safe_parse(raw)


# ─────────────────────────────────────────────
# B2C ENTITY EXTRACTION
# New support layer. Does not replace signal extraction.
# ─────────────────────────────────────────────

def extract_entities_from_chunk(
    chunk_text,
    conversation_id,
    chunk_number,
    speaker_metadata,
    source_file
):
    role_note = "\n".join(
        f"  {speaker}: role={meta.get('speaker_role', 'unknown')}, "
        f"name={meta.get('speaker_name')}"
        for speaker, meta in speaker_metadata.items()
    )

    prompt = f"""
You are extracting structured B2C entity information from a financial sales call transcript.

This is entity extraction.
Do NOT extract customer psychology here.
Do NOT replace the customer signal extraction.

Context:
Outbound or advisory retail sales call.
Customer is a private individual.
Tag what was actually said or clearly implied.
Do not guess.

Speaker metadata:
{role_note}

Source file:
{source_file}

{B2C_ENTITY_CATEGORIES}

VERY IMPORTANT CATEGORY RULE:
entity_category must be ONLY one of these exact values:
people, products, locations, process_step, objection, pain_point, commitment,
next_step, budget_pricing_signal, timeline_signal, authority_decision_process,
competition_status_quo, requirement_constraint, product_intent, risk_cue,
intent_signal, rapport_item

OUTPUT FORMAT:
Return ONLY valid JSON list. No markdown. No explanation.

Each object must contain:
- id
- conversation_id
- source_file
- chunk_number
- speaker
- speaker_name
- speaker_role
- entity_category
- entity_text
- normalized_value
- context
- attributes
- confidence
- status

Attributes object should include useful fields when available:
- side: "rep-side" | "customer-side" | "unknown"
- subtype
- severity
- owner
- due_date
- dependency
- polarity
- strength
- status
- summary

Rules:
- id must be unique string
- entity_text must be exact words from transcript
- context must be exact short phrase/sentence from transcript
- Do not invent values
- Do not extract greetings
- Do not extract weak/unclear entities
- confidence below 0.6 = do not include
- Keep Hindi/English text as-is
- normalized_value should standardize value if possible, else same as entity_text
- status must be "active"
- source_file must be "{source_file}"

conversation_id: {conversation_id}
chunk_number: {chunk_number}

Transcript:
{chunk_text}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    return _safe_parse(raw)


# ─────────────────────────────────────────────
# SIGNAL POST PROCESSING
# ─────────────────────────────────────────────

def post_process(signals, speaker_metadata, source_file):
    seen = {}
    result = []

    for sig in signals:
        source = sig.get("source_text", "").strip()

        if len(source.split()) < 6:
            continue

        if sig.get("confidence", 0) < 0.6:
            continue

        category = sig.get("category")

        if category in INVALID_CATEGORY_HEADINGS:
            continue

        if category not in VALID_CATEGORIES:
            continue

        speaker = sig.get("speaker")
        meta = speaker_metadata.get(speaker, {})

        speaker_name = sig.get("speaker_name") or meta.get("speaker_name")
        speaker_role = sig.get("speaker_role") or meta.get("speaker_role", "unknown")

        sig["speaker_name"] = speaker_name
        sig["speaker_role"] = speaker_role
        sig["source_file"] = sig.get("source_file") or source_file

        if not sig.get("id"):
            sig["id"] = f'{sig.get("conversation_id")}_{sig.get("chunk_number")}_{abs(hash(source))}'

        payload = sig.setdefault("payload", {})
        payload["speaker_role"] = payload.get("speaker_role") or speaker_role
        payload["speaker_name"] = speaker_name
        payload["source_file"] = sig["source_file"]

        if speaker_role == "advisor":
            customer_reaction_categories = {
                "buying_signal",
                "hesitation_signal",
                "hard_objection",
                "clarification_ask",
                "commitment",
                "trust_signal",
                "distrust_signal",
                "confusion_signal",
            }

            if sig.get("category") not in customer_reaction_categories:
                continue

        key = (
            sig.get("conversation_id"),
            speaker,
            source.lower()
        )

        if key not in seen:
            seen[key] = sig
            result.append(sig)
        else:
            old = seen[key]
            if sig.get("confidence", 0) > old.get("confidence", 0):
                idx = result.index(old)
                result[idx] = sig
                seen[key] = sig

    return result


# ─────────────────────────────────────────────
# ENTITY POST PROCESSING
# ─────────────────────────────────────────────

def post_process_entities(entities, speaker_metadata, source_file):
    seen = {}
    result = []

    for ent in entities:
        entity_text = ent.get("entity_text", "").strip()
        entity_category = ent.get("entity_category", "").strip()

        if not entity_text:
            continue

        if ent.get("confidence", 0) < 0.6:
            continue

        if entity_category not in VALID_ENTITY_CATEGORIES:
            continue

        speaker = ent.get("speaker")
        meta = speaker_metadata.get(speaker, {})

        speaker_name = ent.get("speaker_name") or meta.get("speaker_name")
        speaker_role = ent.get("speaker_role") or meta.get("speaker_role", "unknown")

        ent["speaker_name"] = speaker_name
        ent["speaker_role"] = speaker_role
        ent["source_file"] = ent.get("source_file") or source_file
        ent["status"] = ent.get("status") or "active"

        if not ent.get("normalized_value"):
            ent["normalized_value"] = entity_text

        if not ent.get("attributes") or not isinstance(ent.get("attributes"), dict):
            ent["attributes"] = {}

        ent["attributes"]["speaker_role"] = ent["attributes"].get("speaker_role") or speaker_role
        ent["attributes"]["speaker_name"] = speaker_name
        ent["attributes"]["source_file"] = ent["source_file"]

        if not ent.get("id"):
            ent["id"] = f'{ent.get("conversation_id")}_{ent.get("chunk_number")}_{entity_category}_{abs(hash(entity_text))}'

        key = (
            ent.get("conversation_id"),
            entity_category.lower(),
            entity_text.lower()
        )

        if key not in seen:
            seen[key] = ent
            result.append(ent)
        else:
            old = seen[key]
            if ent.get("confidence", 0) > old.get("confidence", 0):
                idx = result.index(old)
                result[idx] = ent
                seen[key] = ent

    return result


# ─────────────────────────────────────────────
# MAIN EXTRACTION FROM TEXT
# Same function name kept.
# Now returns signals + entities.
# ─────────────────────────────────────────────

def extract_signals_from_text(transcript_text, conversation_id, source_file):
    speaker_metadata = extract_speaker_metadata(
        transcript_text=transcript_text,
        source_file=source_file
    )

    chunks = split_into_chunks(transcript_text, max_chars=3500)

    all_signals = []
    all_entities = []

    print(f"[{conversation_id}] Source file: {source_file}")
    print(f"[{conversation_id}] Speaker metadata:")
    print(json.dumps(speaker_metadata, indent=2, ensure_ascii=False))
    print(f"[{conversation_id}] {len(chunks)} chunks")

    for i, chunk in enumerate(chunks, 1):
        print(f"  chunk {i}/{len(chunks)} signals ...", end=" ")

        try:
            signals = extract_signals_from_chunk(
                chunk_text=chunk,
                conversation_id=conversation_id,
                chunk_number=i,
                speaker_metadata=speaker_metadata,
                source_file=source_file
            )

            print(f"{len(signals)} signals raw")
            all_signals.extend(signals)

        except Exception as e:
            print(f"FAILED SIGNALS: {e}")

        time.sleep(1)

        print(f"  chunk {i}/{len(chunks)} entities ...", end=" ")

        try:
            entities = extract_entities_from_chunk(
                chunk_text=chunk,
                conversation_id=conversation_id,
                chunk_number=i,
                speaker_metadata=speaker_metadata,
                source_file=source_file
            )

            print(f"{len(entities)} entities raw")
            all_entities.extend(entities)

        except Exception as e:
            print(f"FAILED ENTITIES: {e}")

        time.sleep(1)

    final_signals = post_process(
        signals=all_signals,
        speaker_metadata=speaker_metadata,
        source_file=source_file
    )

    final_entities = post_process_entities(
        entities=all_entities,
        speaker_metadata=speaker_metadata,
        source_file=source_file
    )

    print(f"  → {len(final_signals)} signals after cleanup")
    print(f"  → {len(final_entities)} entities after cleanup")

    return {
        "signals": final_signals,
        "entities": final_entities,
        "speaker_metadata": speaker_metadata
    }


# ─────────────────────────────────────────────
# MAIN EXTRACTION FROM FILE
# Same function name kept.
# ─────────────────────────────────────────────

def extract_from_file(file_path, conversation_id):
    transcript_text = read_transcript(file_path)

    source_file = os.path.basename(file_path)

    return extract_signals_from_text(
        transcript_text=transcript_text,
        conversation_id=conversation_id,
        source_file=source_file
    )