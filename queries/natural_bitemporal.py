import os
from dotenv import load_dotenv

from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

load_dotenv()


graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)


llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)


CYPHER_GENERATION_TEMPLATE = """
You are an expert Neo4j Cypher query generator.

Use only this schema:
{schema}

Correct graph structure:

(s:Speaker)-[:SAID_TEMPORAL]->(t:TemporalSignal)-[:FROM_CONVERSATION_TEMPORAL]->(c:Conversation)

TemporalSignal properties:
- category
- source_text
- confidence
- payload
- status
- valid_from
- recorded_at
- valid_to
- invalidated_at

Available categories:
- budget_pricing
- product_intent
- process_step
- pain_point
- objection
- risk_cue
- intent_signal
- commitment
- people
- locations
- products

Important category mapping:
- fee, scholarship, budget, pricing, amount, tuition = budget_pricing
- program, BBA, course, degree, Tech and Business Management = product_intent
- admission process, test, interview, simulation, video essay = process_step
- concern, problem, doubt, worried = pain_point
- follow up, share, send, call, brochure, application link = commitment
- person, name, founder, Garima, Pratham Mittal = people
- place, location, Gurgaon, Hyderabad, Bangalore = locations

Rules:
- Use only MATCH queries.
- Never create, delete, update, or modify data.
- Always query TemporalSignal as t.
- Always use AS aliases in RETURN.
- Do not invent categories like fee, scholarship, or program.
- For fee questions, use category budget_pricing OR text search.
- For program questions, use category product_intent OR text search.
- For admission questions, use category process_step OR text search.
- For active/current facts, use t.status = 'active'.
- For invalidated facts, use t.invalidated_at IS NOT NULL.
- For closed old facts, use t.valid_to IS NOT NULL.
- Use toLower(t.source_text) CONTAINS 'keyword' for text search.
- Return only useful fields with aliases:
  t.category AS category,
  t.source_text AS text,
  t.confidence AS confidence,
  t.valid_from AS valid_from,
  t.recorded_at AS recorded_at,
  t.status AS status
- Use LIMIT 10 unless user asks for more.
- Do not count unless user asks how many.

Examples:

Question:
What active fee or scholarship related facts are present?

Cypher:
MATCH (s:Speaker)-[:SAID_TEMPORAL]->(t:TemporalSignal)-[:FROM_CONVERSATION_TEMPORAL]->(c:Conversation)
WHERE t.status = 'active'
AND (
    t.category = 'budget_pricing'
    OR toLower(t.source_text) CONTAINS 'fee'
    OR toLower(t.source_text) CONTAINS 'scholarship'
    OR toLower(t.source_text) CONTAINS 'pricing'
    OR toLower(t.source_text) CONTAINS 'budget'
    OR toLower(t.source_text) CONTAINS 'tuition'
)
RETURN 
    t.category AS category,
    t.source_text AS text,
    t.confidence AS confidence,
    t.valid_from AS valid_from,
    t.recorded_at AS recorded_at,
    t.status AS status
LIMIT 10

Question:
What active program related facts are present?

Cypher:
MATCH (s:Speaker)-[:SAID_TEMPORAL]->(t:TemporalSignal)-[:FROM_CONVERSATION_TEMPORAL]->(c:Conversation)
WHERE t.status = 'active'
AND (
    t.category = 'product_intent'
    OR toLower(t.source_text) CONTAINS 'program'
    OR toLower(t.source_text) CONTAINS 'bba'
    OR toLower(t.source_text) CONTAINS 'degree'
    OR toLower(t.source_text) CONTAINS 'tech and business management'
)
RETURN 
    t.category AS category,
    t.source_text AS text,
    t.confidence AS confidence,
    t.valid_from AS valid_from,
    t.recorded_at AS recorded_at,
    t.status AS status
LIMIT 10

Question:
What admission process steps were explained?

Cypher:
MATCH (s:Speaker)-[:SAID_TEMPORAL]->(t:TemporalSignal)-[:FROM_CONVERSATION_TEMPORAL]->(c:Conversation)
WHERE t.status = 'active'
AND (
    t.category = 'process_step'
    OR toLower(t.source_text) CONTAINS 'admission'
    OR toLower(t.source_text) CONTAINS 'video essay'
    OR toLower(t.source_text) CONTAINS 'aptitude test'
    OR toLower(t.source_text) CONTAINS 'business simulation'
    OR toLower(t.source_text) CONTAINS 'personal interview'
)
RETURN 
    t.category AS category,
    t.source_text AS text,
    t.confidence AS confidence,
    t.valid_from AS valid_from,
    t.recorded_at AS recorded_at,
    t.status AS status
LIMIT 10

Question:
{question}

Cypher Query:
"""


cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

QA_TEMPLATE = """
You are an assistant that answers from Neo4j query results.

Question:
{question}

Neo4j Results:
{context}

Rules:
- Do not show Python list or dictionary format.
- Write answer in clean bullet points.
- Mention category, text, valid_from, recorded_at, and status.
- Ignore irrelevant rows.
- Keep answer clean and readable.

Answer format:

- Category: <category>
  Text: <text>
  Valid From: <valid_from>
  Recorded At: <recorded_at>
  Status: <status>

Answer:
"""

qa_prompt = PromptTemplate(
    input_variables=["question", "context"],
    template=QA_TEMPLATE
)

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
    allow_dangerous_requests=True,
    cypher_prompt=cypher_prompt,
    qa_prompt=qa_prompt
)

questions = [

    "Show all active scholarship-related information currently valid.",

    "Show all information that was recorded today.",

    "Show all outdated or invalidated information.",

    "What scholarship policies were valid on May 25, 2026?",

    "Show me the latest fee structure mentioned in the system.",

    "Show all currently active information related to AI or Data Science courses.",

    "Show the complete history of scholarship-related changes over time.",

    "What was the scholarship policy before it changed?",

    "Show scholarship information along with valid time and recorded time.",

    "Which fee information is currently active?",

    "Show all historical versions of fee structures.",

    "Find all AI-related signals that became invalid.",

    "What information was active during admission round 2?"

]

for q in questions:
    print("\n" + "=" * 80)
    print("QUESTION:", q)
    print("=" * 80)

    response = chain.invoke({"query": q})

    print("\nANSWER:")
    print(response["result"])


graph._driver.close()