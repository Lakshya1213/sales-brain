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


def count_temporal_signals_by_category():
    query = """
    MATCH (t:TemporalSignal)
    RETURN t.category AS category, count(t) AS count
    ORDER BY count DESC
    """
    run_query("Bi-temporal Signals by Category", query)


def show_temporal_fields():
    query = """
    MATCH (t:TemporalSignal)
    RETURN
        t.category AS category,
        t.source_text AS text,
        t.valid_from AS valid_from,
        t.valid_to AS valid_to,
        t.recorded_at AS recorded_at,
        t.invalidated_at AS invalidated_at,
        t.status AS status
    LIMIT 20
    """
    run_query("Temporal Fields", query)


def active_temporal_signals():
    query = """
    MATCH (t:TemporalSignal)
    WHERE t.status = 'active'
    RETURN
        t.category AS category,
        t.source_text AS text,
        t.valid_from AS valid_from,
        t.recorded_at AS recorded_at
    LIMIT 30
    """
    run_query("Currently Active Temporal Signals", query)


def temporal_objections():
    query = """
    MATCH (t:TemporalSignal)
    WHERE t.category = 'objection'
    RETURN
        t.source_text AS objection,
        t.valid_from AS valid_from,
        t.status AS status
    """
    run_query("Temporal Objections", query)


def temporal_risk_cues():
    query = """
    MATCH (t:TemporalSignal)
    WHERE t.category = 'risk_cue'
    RETURN
        t.source_text AS risk_text,
        t.valid_from AS valid_from,
        t.status AS status
    """
    run_query("Temporal Risk Cues", query)


def invalidated_signals():
    query = """
    MATCH (t:TemporalSignal)
    WHERE t.invalidated_at IS NOT NULL
    RETURN
        t.category AS category,
        t.source_text AS text,
        t.invalidated_at AS invalidated_at
    """
    run_query("Invalidated Signals", query)


def closed_old_facts():
    query = """
    MATCH (t:TemporalSignal)
    WHERE t.valid_to IS NOT NULL
    RETURN
        t.category AS category,
        t.source_text AS text,
        t.valid_from AS valid_from,
        t.valid_to AS valid_to
    """
    run_query("Closed Old Facts / World Changed", query)


if __name__ == "__main__":
    count_temporal_signals_by_category()
    show_temporal_fields()
    active_temporal_signals()
    temporal_objections()
    temporal_risk_cues()
    invalidated_signals()
    closed_old_facts()

    driver.close()