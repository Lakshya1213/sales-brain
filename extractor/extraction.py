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
# CUSTOMER-CENTRIC CATEGORIES
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
# SAFE JSON PARSER
# ─────────────────────────────────────────────

def _safe_parse(text):
    text = text.strip()
    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError(f"No JSON list found. Raw output:\n{text[:300]}")

    return json.loads(text[start:end + 1])



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

            # Avoid common non-name words from transcript noise
            if name.lower() in {"hello", "okay", "right", "correct", "yes", "no", "good", "morning"}:
                continue

            # Assign addressed name to the other speaker if there are exactly 2 speakers
            if len(speakers) == 2:
                other_speaker = speakers[0] if speakers[1] == current_speaker else speakers[1]

                if metadata.get(other_speaker, {}).get("speaker_name") is None:
                    metadata[other_speaker]["speaker_name"] = name

    return metadata


# ─────────────────────────────────────────────
# LLM SPEAKER METADATA EXTRACTION
# No NER. No entity model.
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
# SIGNAL EXTRACTION
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
# POST PROCESSING
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
# MAIN EXTRACTION FROM TEXT
# ─────────────────────────────────────────────

def extract_signals_from_text(transcript_text, conversation_id, source_file):
    speaker_metadata = extract_speaker_metadata(
        transcript_text=transcript_text,
        source_file=source_file
    )

    chunks = split_into_chunks(transcript_text, max_chars=3500)

    all_signals = []

    print(f"[{conversation_id}] Source file: {source_file}")
    print(f"[{conversation_id}] Speaker metadata:")
    print(json.dumps(speaker_metadata, indent=2, ensure_ascii=False))
    print(f"[{conversation_id}] {len(chunks)} chunks")

    for i, chunk in enumerate(chunks, 1):
        print(f"  chunk {i}/{len(chunks)} ...", end=" ")

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
            print(f"FAILED: {e}")

        time.sleep(1)

    final = post_process(
        signals=all_signals,
        speaker_metadata=speaker_metadata,
        source_file=source_file
    )

    print(f"  → {len(final)} signals after cleanup")

    return final


# ─────────────────────────────────────────────
# MAIN EXTRACTION FROM FILE
# ─────────────────────────────────────────────

def extract_from_file(file_path, conversation_id):
    transcript_text = read_transcript(file_path)

    source_file = os.path.basename(file_path)

    return extract_signals_from_text(
        transcript_text=transcript_text,
        conversation_id=conversation_id,
        source_file=source_file
    )