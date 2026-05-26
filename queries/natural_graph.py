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

Correct graph pattern is always:

MATCH (sp:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)

Nodes:
- Speaker(name)
- Signal(category, source_text, confidence, payload, status)
- Conversation(id)

Rules:
- Always use this relationship direction:
  (Speaker)-[:SAID]->(Signal)-[:FROM_CONVERSATION]->(Conversation)

- Always use:
  toLower(sig.source_text) CONTAINS "keyword"

- Never use regex =~

- Never use COUNT unless user asks "how many"

- Always return:
    sig.source_text AS source_text,
    sp.name AS speaker,
    sig.category AS category,
    c.id AS conversation_id

Important Search Rules:

1. Scholarship Questions
Search for:
- scholarship
- scholarships
- percent
- percentage
- sat
- jee
- musat
- mu-sat
- msat
- 20%
- 25%
- 50%
- 80%
OR category = "budget_pricing"

2. Fee / Cost / Pricing Questions
Search for:
- fee
- fees
- tuition
- cost
- pricing
- budget
- lakhs
- ₹
OR category = "budget_pricing"

3. AI / Data Science Questions
Search for:
- ai
- artificial intelligence
- data science
- machine learning
- ml
- deep learning

4. Masters Union Questions
Search for:
- masters union
- master's union
- mu

5. Illinois Tech / Dual Degree Questions
Search for:
- illinois
- illinois tech
- chicago
- dual degree
- global track

6. MU-SAT Questions
Search for:
- mu-sat
- musat
- msat
- entrance exam
- mock test
- 45 marks

7. Internship / Placement / Career Questions
Search for:
- internship
- internships
- placement
- placements
- pre-placement
- offer
- offers
- ppo
- career

8. University Questions
Search for:
- university
- harvard
- stanford
- cornell
- nyu
- seattle
- illinois
- chicago
- delhi university
- ugc

9. Curriculum / Company Questions
Search for:
- google
- microsoft
- ola
- physics wallah
- curriculum
- collaboration
- experts

10. Faculty Questions
Search for:
- faculty
- professor
- harvard
- stanford
- cornell
- nasa
- nyu
- dr.

11. Admission Process Questions
Search for:
- admission
- process
- application
- video essay
- mu-sat
- interview
- group discussion
- personal interview
- form

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
You are answering questions using Neo4j query results only.

Rules:
- If context contains rows, answer from the rows.
- Never say "I don't know" if rows exist.
- Summarize clearly and naturally.
- Mention speaker names if available.
- Mention important percentages, fees, universities, scholarships etc.
- Keep answer concise but informative.
- Do not add information outside the context.

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

# =========================
# Chain
# =========================

chain = GraphCypherQAChain.from_llm(
    llm=llm,
    graph=graph,
    verbose=True,
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
    print("RAW DATABASE OUTPUT")
    print("=" * 80)

    if "intermediate_steps" in response:
        for step in response["intermediate_steps"]:
            print(step)
    else:
        print("No raw output found")

    print("\n" + "=" * 80)
    print("READABLE LLM ANSWER")
    print("=" * 80)
    print(response["result"])

    return response


# =========================
# Questions
# =========================

questions = [

   
    "Who discussed Relax Plan and why was it suggested for retirement planning?"
]

# =========================
# Run Questions
# =========================

for q in questions:
    ask_question(q)

# =========================
# Optional Interactive Mode
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

# import os
# from dotenv import load_dotenv

# from langchain_neo4j import Neo4jGraph, GraphCypherQAChain
# from langchain_groq import ChatGroq
# from langchain_core.prompts import PromptTemplate

# load_dotenv()

# # =========================
# # Neo4j Connection
# # =========================

# graph = Neo4jGraph(
#     url=os.getenv("NEO4J_URI"),
#     username=os.getenv("NEO4J_USERNAME"),
#     password=os.getenv("NEO4J_PASSWORD")
# )

# # =========================
# # LLM
# # =========================

# llm = ChatGroq(
#     model="llama-3.3-70b-versatile",
#     temperature=0
# )

# # =========================
# # Cypher Prompt
# # =========================

# CYPHER_GENERATION_TEMPLATE = """
# You are an expert Neo4j Cypher query generator.

# Use only this schema:
# {schema}

# Correct graph pattern is always:

# MATCH (sp:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)

# Nodes:
# - Speaker(name)
# - Signal(category, source_text, confidence, payload, status)
# - Conversation(id)

# Rules:
# - Always use this relationship direction:
#   (Speaker)-[:SAID]->(Signal)-[:FROM_CONVERSATION]->(Conversation)

# - Always use:
#   toLower(sig.source_text) CONTAINS "keyword"

# - Never use regex =~

# - Never use COUNT unless user asks "how many"

# - Always return:
#     sig.source_text AS source_text,
#     sp.name AS speaker,
#     sig.category AS category,
#     c.id AS conversation_id

# Important Search Rules:

# 1. Scholarship Questions
# Search for:
# - scholarship
# - scholarships
# - percent
# - percentage
# - sat
# - jee
# - musat
# - mu-sat
# - msat
# - 20%
# - 25%
# - 50%
# - 80%
# OR category = "budget_pricing"

# 2. Fee / Cost / Pricing Questions
# Search for:
# - fee
# - fees
# - tuition
# - cost
# - pricing
# - budget
# - lakhs
# - ₹
# OR category = "budget_pricing"

# 3. AI / Data Science Questions
# Search for:
# - ai
# - artificial intelligence
# - data science
# - machine learning
# - ml
# - deep learning

# 4. Masters Union Questions
# Search for:
# - masters union
# - master's union
# - mu

# 5. Illinois Tech / Dual Degree Questions
# Search for:
# - illinois
# - illinois tech
# - chicago
# - dual degree
# - global track

# 6. MU-SAT Questions
# Search for:
# - mu-sat
# - musat
# - msat
# - entrance exam
# - mock test
# - 45 marks

# 7. Internship / Placement / Career Questions
# Search for:
# - internship
# - internships
# - placement
# - placements
# - pre-placement
# - offer
# - offers
# - ppo
# - career

# 8. University Questions
# Search for:
# - university
# - harvard
# - stanford
# - cornell
# - nyu
# - seattle
# - illinois
# - chicago
# - delhi university
# - ugc

# 9. Curriculum / Company Questions
# Search for:
# - google
# - microsoft
# - ola
# - physics wallah
# - curriculum
# - collaboration
# - experts

# 10. Faculty Questions
# Search for:
# - faculty
# - professor
# - harvard
# - stanford
# - cornell
# - nasa
# - nyu
# - dr.

# 11. Admission Process Questions
# Search for:
# - admission
# - process
# - application
# - video essay
# - mu-sat
# - interview
# - group discussion
# - personal interview
# - form

# Question:
# {question}

# Cypher Query:
# """

# cypher_prompt = PromptTemplate(
#     input_variables=["schema", "question"],
#     template=CYPHER_GENERATION_TEMPLATE
# )

# # =========================
# # QA Prompt
# # =========================

# QA_TEMPLATE = """
# You are answering questions using Neo4j query results only.

# Rules:
# - If context contains rows, answer from the rows.
# - Never say "I don't know" if rows exist.
# - Summarize clearly and naturally.
# - Mention speaker names if available.
# - Mention important percentages, fees, universities, scholarships etc.
# - Keep answer concise but informative.

# Context:
# {context}

# Question:
# {question}

# Answer:
# """

# qa_prompt = PromptTemplate(
#     input_variables=["context", "question"],
#     template=QA_TEMPLATE
# )

# # =========================
# # Chain
# # =========================

# chain = GraphCypherQAChain.from_llm(
#     llm=llm,
#     graph=graph,
#     verbose=True,
#     allow_dangerous_requests=True,
#     cypher_prompt=cypher_prompt,
#     qa_prompt=qa_prompt
# )

# # =========================
# # Questions
# # =========================

# questions = [

#     "Show me all speakers who discussed scholarships and what they said.",

#     "Show all discussions related to fees or tuition costs.",

#     "Which conversations talked about AI or Data Science?",

#     "Who talked about Masters Union?",

#     "Show all scholarship percentages mentioned in the conversation.",

#     "Show discussions related to internships or placement offers.",

#     "Which universities were mentioned in the conversation?",

#     "Who discussed the Illinois Tech dual degree?",

#     "Show all discussions about MU-SAT.",

#     "Which speaker mentioned internships?",

#     "What companies helped design the curriculum?",

#     "Who talked about Harvard or Stanford faculty?",

#     "Find all discussions related to placements."

# ]

# # =========================
# # Run Questions
# # =========================

# for q in questions:

#     print("\n" + "=" * 80)
#     print("QUESTION:", q)
#     print("=" * 80)

#     response = chain.invoke({
#         "query": q
#     })

#     print("\nANSWER:")
#     print(response["result"])

# # =========================
# # Close Driver
# # =========================

# graph._driver.close()