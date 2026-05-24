import os
import json
from groq import Groq
from dotenv import load_dotenv
from docx import Document

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def safe_json_parse(text):
    text = text.strip()

    start = text.find("[")
    end = text.rfind("]")

    if start == -1 or end == -1:
        raise ValueError("No JSON list found")

    json_text = text[start:end + 1]
    return json.loads(json_text)

def read_transcript(file_path):
    doc = Document(file_path)

    full_text = []

    for para in doc.paragraphs:
        text = para.text.strip()
        if text:
            full_text.append(text)

    return "\n".join(full_text)


def split_text_into_chunks(text, max_chars=3500):
    lines = text.split("\n")

    chunks = []
    current_chunk = ""

    for line in lines:
        if len(current_chunk) + len(line) < max_chars:
            current_chunk += line + "\n"
        else:
            chunks.append(current_chunk)
            current_chunk = line + "\n"

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def extract_signals_from_chunk(chunk_text, conversation_id, chunk_number):
    prompt = f"""
You are extracting structured commercial signals from a B2C sales call transcript chunk.

Context:
- This is an outbound retail sales/admission call.
- The customer is an individual person.
- Extract only what is actually said or clearly implied.
- Do NOT guess.
- Do NOT extract greetings, fillers, small talk, or repeated "okay/hmm/hello".

Allowed categories:
1. people
2. products
3. locations
4. process_step
5. objection
6. pain_point
7. commitment
8. next_step
9. budget_pricing
10. timeline
11. authority_decision
12. competition_status_quo
13. requirement_constraint
14. product_intent
15. risk_cue
16. intent_signal
17. rapport_item

Category meanings:
- people: any person mentioned, such as prospect, counsellor, friend, brother, parent, faculty.
- products: any program, app, platform, service, course, exam, stock, tool, or financial product mentioned.
- locations: any city, school, campus, market, exchange, or geographic place.
- process_step: any step in admission/onboarding/sales process, such as form, KYC, test, video essay, interview, activation.
- objection: hesitation, doubt, pushback, concern, or resistance.
- pain_point: personal problem or frustration.
- commitment: something the customer or rep agrees to do.
- next_step: concrete future action with owner/due date if available.
- budget_pricing: fee, scholarship, budget, charges, investment capacity, price sensitivity.
- timeline: when something will happen or when customer will decide.
- authority_decision: who makes the decision or whether customer needs to consult someone.
- competition_status_quo: competitor, alternative option, current way of doing things.
- requirement_constraint: condition, limitation, eligibility, dependency, or constraint.
- product_intent: interest, curiosity, like/dislike toward a feature, course, service, return, or process.
- risk_cue: signal that deal may not close.
- intent_signal: positive, negative, or neutral buying/admission intent.
- rapport_item: personal useful detail about the customer.

Return ONLY a valid JSON list.
No explanation.
No markdown.

Each JSON object must have exactly these fields:
- conversation_id
- speaker
- category
- source_text
- confidence
- payload
- status
- chunk_number

Rules:
- source_text must be exact text from transcript chunk.
- confidence must be between 0 and 1.
- status should be "active".
- payload must be an object.
- If unsure, do not extract.
- Prefer fewer but high-quality signals.
- Do not create duplicate signals from the same source_text.
- Keep source_text short and exact.

Payload guidance by category:
- people: {{"name_or_role": "", "side": "rep-side/customer-side/unknown"}}
- products: {{"name": "", "type": ""}}
- locations: {{"place": "", "type": ""}}
- process_step: {{"step": "", "stage": ""}}
- objection: {{"objection_type": "", "severity": "low/medium/high", "status": "open/resolved/reopened"}}
- pain_point: {{"pain_type": "", "customer_agreed": "yes/no/unclear"}}
- commitment: {{"owner": "", "commitment_type": "", "hardness": "soft/hard", "conditional": "yes/no"}}
- next_step: {{"owner": "", "action": "", "due_date": "", "dependency": "", "status": "open/done"}}
- budget_pricing: {{"pricing_type": "", "amount": "", "sensitivity": "low/medium/high/unknown"}}
- timeline: {{"time_reference": "", "urgency": "low/medium/high"}}
- authority_decision: {{"decision_maker": "", "needs_consultation": "yes/no/unclear"}}
- competition_status_quo: {{"alternative": "", "type": "competitor/status_quo"}}
- requirement_constraint: {{"constraint_type": "", "description": ""}}
- product_intent: {{"type": "feature/process/program/service", "intent": "curious/like/dislike", "confidence_type": "definitive/hedged/speculative"}}
- risk_cue: {{"risk_area": "", "severity": "low/medium/high"}}
- intent_signal: {{"polarity": "positive/negative/neutral", "strength": "weak/moderate/strong"}}
- rapport_item: {{"detail": "", "usefulness": ""}}

conversation_id: {conversation_id}
chunk_number: {chunk_number}

Transcript chunk:
{chunk_text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    result = response.choices[0].message.content.strip()

    return safe_json_parse(result)

def extract_signals_from_text(transcript_text, conversation_id):
    chunks = split_text_into_chunks(transcript_text, max_chars=2000)

    all_signals = []

    print(f"Total chunks created: {len(chunks)}")

    for i, chunk in enumerate(chunks, start=1):
        print(f"Extracting chunk {i}/{len(chunks)}")

        try:
            signals = extract_signals_from_chunk(
                chunk_text=chunk,
                conversation_id=conversation_id,
                chunk_number=i
            )

            all_signals.extend(signals)

        except Exception as e:
            print(f"Chunk {i} failed:", e)

    return all_signals


def extract_from_file(file_path, conversation_id):
    transcript_text = read_transcript(file_path)
    signals = extract_signals_from_text(transcript_text, conversation_id)
    return signals