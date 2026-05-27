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

Graph patterns:

For customer signals:
MATCH (sp:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)

For extracted entities:
MATCH (sp:Speaker)-[:MENTIONED]->(e:Entity)-[:FROM_CONVERSATION]->(c:Conversation)

Nodes:

Signal:
- category
- source_text
- confidence
- payload
- status
- source_file
- chunk_number
- speaker_name
- speaker_role

Entity:
- entity_category
- entity_text
- normalized_value
- context
- attributes
- confidence
- status
- source_file
- chunk_number
- speaker_name
- speaker_role

Speaker:
- label
- name
- role

Conversation:
- id
- source_file

Rules:

1. If the user asks about customer psychology, fears, goals, hesitation, objections, buying intent, trust, confusion, use Signal.

2. If the user asks about exact facts like people, products, locations, amount, pricing, broker, plan, KYC, timeline, next steps, use Entity.

3. If the question can need both meaning and exact facts, query both Signal and Entity using UNION.

4. Never use regex =~.

5. Never use COUNT unless user explicitly asks:
- how many
- count
- total number

6. Use LIMIT 20 unless user asks for all records.

7. Do NOT invent properties or relationships outside schema.

Signal search pattern:

WHERE toLower(sig.source_text) CONTAINS "keyword"
   OR toLower(sig.category) CONTAINS "keyword"
   OR toLower(toString(sig.payload)) CONTAINS "keyword"

Entity search pattern:

WHERE toLower(e.entity_text) CONTAINS "keyword"
   OR toLower(e.entity_category) CONTAINS "keyword"
   OR toLower(e.normalized_value) CONTAINS "keyword"
   OR toLower(e.context) CONTAINS "keyword"
   OR toLower(toString(e.attributes)) CONTAINS "keyword"

Always return same column names.

For Signal return:
sig.source_text AS source_text,
sp.name AS speaker,
sig.category AS category,
sig.payload AS payload,
c.id AS conversation_id,
"signal" AS record_type

For Entity return:
e.context AS source_text,
sp.name AS speaker,
e.entity_category AS category,
e.attributes AS payload,
c.id AS conversation_id,
"entity" AS record_type

Customer-centric mapping:

Pricing / charges:
pricing, price, fee, fees, charge, charges, cost, amount, budget, ticket

Risk:
risk, loss, downside, protection, guarantee, safety, market crash

Buying intent:
interested, proceed, yes, commit, investment, ready, positive

Timeline:
today, tomorrow, next week, month, year, later, follow up, start

Products:
plan, product, app, platform, broker, demat, SWP, KYC

People:
customer, advisor, RM, research head, founder, friend, family

Question:
{question}

Cypher Query:
"""

cypher_prompt = PromptTemplate(
    input_variables=["schema", "question"],
    template=CYPHER_GENERATION_TEMPLATE
)

QA_TEMPLATE = """
You are answering questions using Neo4j query results only.

Rules:
- Answer ONLY from the provided context.
- Never hallucinate.
- If record_type is signal, explain customer meaning/psychology.
- If record_type is entity, explain exact extracted facts.
- Mention speaker names when available.
- Mention conversation IDs when useful.
- Mention category and payload details when helpful.
- Keep answer concise and readable.
- If no rows exist, say:
"No matching information was found in the graph database."

Context:
{context}

Question:
{question}

Answer:
"""

qa_prompt = PromptTemplate(
    input_variables=["context", "question"],
    template=QA_TEMPLATE
)

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=False,
    allow_dangerous_requests=True,
    cypher_prompt=cypher_prompt,
    qa_prompt=qa_prompt,
    return_intermediate_steps=True
)

def ask_question(question):

    response = chain.invoke({
        "query": question
    })

    print("\n" + "=" * 80)
    print("QUESTION")
    print("=" * 80)
    print(question)

    print("\n" + "=" * 80)
    print("READABLE LLM ANSWER")
    print("=" * 80)
    print(response["result"])

    return response


questions = [
]

for q in questions:
    ask_question(q)

while True:

    user_question = input("\nAsk your own question (or type exit): ")

    if user_question.lower() in ["exit", "quit", "stop"]:
        break

    ask_question(user_question)

graph._driver.close()