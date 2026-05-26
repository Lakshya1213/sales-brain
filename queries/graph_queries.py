import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


def run_query(title, query):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)

    with driver.session() as session:
        result = session.run(query)

        found = False
        for record in result:
            found = True
            print(dict(record))

        if not found:
            print("No data found")


def count_signals_by_category():
    query = """
    MATCH (sig:Signal)
    RETURN sig.category AS category, count(sig) AS count
    ORDER BY count DESC
    """

    run_query("Neo4j Signals by Category", query)


def speaker_signal_paths():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)
    RETURN 
        s.name AS speaker,
        sig.category AS category,
        sig.source_text AS text,
        c.id AS conversation_id
    LIMIT 30
    """

    run_query("Speaker → Signal → Conversation Paths", query)


def get_objections():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)
    WHERE sig.category = 'objection'
    RETURN c.id AS conversation_id, s.name AS speaker, sig.source_text AS text
    """

    run_query("Objections from Graph", query)


def get_pain_points():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)
    WHERE sig.category = 'pain_point'
    RETURN c.id AS conversation_id, s.name AS speaker, sig.source_text AS text
    """

    run_query("Pain Points from Graph", query)


def get_next_steps():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)
    WHERE sig.category = 'next_step'
    RETURN c.id AS conversation_id, s.name AS speaker, sig.source_text AS text
    """

    run_query("Next Steps from Graph", query)


def get_risk_cues():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)
    WHERE sig.category = 'risk_cue'
    RETURN c.id AS conversation_id, s.name AS speaker, sig.source_text AS text
    """

    run_query("Risk Cues from Graph", query)


def get_intent_signals():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)
    WHERE sig.category = 'intent_signal'
    RETURN c.id AS conversation_id, s.name AS speaker, sig.source_text AS text
    """

    run_query("Intent Signals from Graph", query)


def get_budget_pricing():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)
    WHERE sig.category = 'budget_pricing'
    RETURN c.id AS conversation_id, s.name AS speaker, sig.source_text AS text
    """

    run_query("Budget/Pricing Signals from Graph", query)


def show_visual_graph_sample():
    query = """
    MATCH (s:Speaker)-[r1:SAID]->(sig:Signal)-[r2:FROM_CONVERSATION]->(c:Conversation)
    RETURN s, r1, sig, r2, c
    LIMIT 25
    """

    run_query("Visual Graph Sample", query)


if __name__ == "__main__":
    count_signals_by_category()
    speaker_signal_paths()
    get_objections()
    get_pain_points()
    get_next_steps()
    get_risk_cues()
    get_intent_signals()
    get_budget_pricing()
    show_visual_graph_sample()

    driver.close()