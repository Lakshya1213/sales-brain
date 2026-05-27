import os
from dotenv import load_dotenv

from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate

load_dotenv()

# =========================
# Neo4j Connection
# =========================

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD")
)

# =========================
# LLM
# =========================

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0
)

# =========================
# Cypher Prompt
# =========================

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

Conversation properties:
- id

Speaker properties:
- name

Rules:
- Use only MATCH queries.
- Never create, delete, update, or modify data.
- Always query TemporalSignal as t.
- Always use this pattern:

MATCH (s:Speaker)-[:SAID_TEMPORAL]->(t:TemporalSignal)-[:FROM_CONVERSATION_TEMPORAL]->(c:Conversation)

- Use toLower(t.source_text) CONTAINS 'keyword' for text search.
- For broad reasoning questions, use OR between related keywords.
- Do NOT force all keywords using AND unless user asks strict filtering.
- Different information may exist in different TemporalSignal rows.
- For current/active facts, use:
  t.status = 'active'

- For invalidated/outdated facts, use:
  t.invalidated_at IS NOT NULL
  OR t.status <> 'active'

- For facts that had an old validity period, use:
  t.valid_to IS NOT NULL

- For recorded-time questions, use:
  t.recorded_at

- For valid-time questions, use:
  t.valid_from and t.valid_to

- Never use COUNT unless user asks "how many", "count", or "total".
- Use LIMIT 20 unless user asks for all records.

Always return:
    t.category AS category,
    t.source_text AS text,
    s.name AS speaker,
    c.id AS conversation_id,
    t.confidence AS confidence,
    t.valid_from AS valid_from,
    t.valid_to AS valid_to,
    t.recorded_at AS recorded_at,
    t.invalidated_at AS invalidated_at,
    t.status AS status

Generic Search Rules:
- Do not assume fixed domain.
- Extract important keywords from the user question.
- Search those keywords in t.source_text.
- Also use category when useful.
- Use OR-based retrieval for explain/why/compare/history/current questions.

Question:
{question}

Cypher Query:
"""

cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

# =========================
# QA Prompt
# =========================

QA_TEMPLATE = """
You are answering using Neo4j bi-temporal query results only.

Question:
{question}

Neo4j Results:
{context}

Rules:
- Answer only from the given context.
- Do not show Python list or dictionary format.
- Write clean bullet points.
- Mention speaker and conversation_id if available.
- Mention category, valid_from, valid_to, recorded_at, invalidated_at, and status.
- Explain the difference between valid time and recorded time when useful.
- Ignore irrelevant rows.
- If context is empty, say:
  "No matching information was found in the bi-temporal graph."

Answer format:

- Speaker: <speaker>
  Conversation: <conversation_id>
  Category: <category>
  Text: <text>
  Valid From: <valid_from>
  Valid To: <valid_to>
  Recorded At: <recorded_at>
  Invalidated At: <invalidated_at>
  Status: <status>

Answer:
"""

qa_prompt = PromptTemplate(
    input_variables=["question", "context"],
    template=QA_TEMPLATE
)

# =========================
# Chain
# =========================

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=False,
    allow_dangerous_requests=True,
    cypher_prompt=cypher_prompt,
    qa_prompt=qa_prompt,
    return_intermediate_steps=True
)

# =========================
# Helper Function
# =========================

def ask_question(question):
    response = chain.invoke({"query": question})

    print("\n" + "=" * 80)
    print("QUESTION")
    print("=" * 80)
    print(question)

    print("\n" + "=" * 80)
    print("GENERATED CYPHER")
    print("=" * 80)

    if "intermediate_steps" in response:
        for step in response["intermediate_steps"]:
            if isinstance(step, dict) and "query" in step:
                print(step["query"])

    print("\n" + "=" * 80)
    print("RAW DATABASE OUTPUT")
    print("=" * 80)

    context_found = False

    if "intermediate_steps" in response:
        for step in response["intermediate_steps"]:
            if isinstance(step, dict) and "context" in step:
                context_found = True
                context = step["context"]

                if len(context) == 0:
                    print("No matching rows found.")
                else:
                    for i, row in enumerate(context, start=1):
                        print(f"\nRow {i}")
                        print("-" * 40)
                        print(row)

    if not context_found:
        print("No context returned.")

    print("\n" + "=" * 80)
    print("READABLE LLM ANSWER")
    print("=" * 80)
    print(response["result"])

    return response


# =========================
# Best Bi-Temporal Questions
# =========================

questions = [

    # "Show all currently active information.",

    # "Show all outdated or invalidated information.",

    # "Show all information with valid time and recorded time.",

    # "Which facts are currently active but were recorded earlier?",

    # "Show all historical versions of fee or pricing information.",

    # "Show all active fee or pricing related information.",

    # "Show all scholarship related information with valid_from and recorded_at.",

    # "What information became invalid over time?",

    # "Show all signals that have valid_to date.",

    # "Show all signals that were invalidated and explain when they were invalidated.",

    # "Show all active product related information.",

    # "Show all admission process related information over time.",

    # "Show information that was recorded today.",

    # "Show complete temporal history of budget or pricing related signals.",

    # "Which conversation contains the latest active facts?"

]

# =========================
# Run Demo Questions
# =========================

for q in questions:
    ask_question(q)

# =========================
# Interactive Mode
# =========================

while True:
    user_question = input("\nAsk your own question or type exit: ")

    if user_question.lower() in ["exit", "quit", "stop"]:
        break

    ask_question(user_question)

# =========================
# Close Driver
# =========================

graph._driver.close()