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

Correct graph pattern:

MATCH (sp:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)

Nodes:
- Speaker(name)
- Signal(category, source_text, confidence, payload, status)
- Conversation(id)

Rules:

1. Always use this relationship direction:
(Speaker)-[:SAID]->(Signal)-[:FROM_CONVERSATION]->(Conversation)

2. Always search using source_text, category, and payload.

Use this pattern:

WHERE toLower(sig.source_text) CONTAINS "keyword"
   OR toLower(sig.category) CONTAINS "keyword"
   OR toLower(toString(sig.payload)) CONTAINS "keyword"

3. Never use regex =~.

4. Never use COUNT unless user explicitly asks:
- how many
- count
- total number

5. Always return:

sig.source_text AS source_text,
sp.name AS speaker,
sig.category AS category,
sig.payload AS payload,
c.id AS conversation_id

6. Use LIMIT 20 unless user asks for all records.

7. Do NOT assume any specific domain.
8. Do NOT hardcode company/product names.
9. Extract important keywords from the user's question.
10. Use OR between related keywords for broader retrieval.
11. Do NOT force all keywords using AND unless user explicitly asks strict filtering.
12. Different information may exist in different Signal rows.
13. Retrieve broader context first, then let QA summarize.

Customer-centric mapping rules:

If user asks about pricing concern, search:
pricing, price, fee, fees, charge, charges, cost, amount, expensive, budget, ticket

If user asks about advisory fee, search:
advisory, fee, fees, charge, charges

If user asks about minimum ticket size, search:
minimum, ticket, amount, investment, capital

If user asks about drop-off, search:
drop, hesitate, hesitation, delay, not interested, later, think, inactive, concern

If user asks about risk concern, search:
risk, loss, downside, protection, guarantee, guaranteed, safety, safe

If user asks about unresolved query, search:
clarify, confusion, repeated, question, doubt, unresolved, not clear

If user asks about buying intent, search:
interested, proceed, yes, commit, investment, ready, positive

If user asks about salesperson performance, search:
resolved, explanation, clarify, objection, answer, response

For reasoning questions like:
- why
- explain
- compare
- discuss
- summarize
- suitable
- related to
- difference between

Use OR-based retrieval.

Never invent properties or relationships outside schema.

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
- Never hallucinate or invent facts.
- If rows exist, summarize them naturally.
- Mention speaker names when available.
- Mention conversation IDs when useful.
- Mention category and payload details when helpful.
- Mention important numbers, percentages, fees, dates, amounts, or statistics if present.
- Keep answers concise but informative.
- Combine related rows into one readable explanation.
- If multiple speakers discuss the same topic, summarize all perspectives.
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