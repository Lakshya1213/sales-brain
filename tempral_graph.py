import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


def count_temporal_signals_by_category():
    query = """
    MATCH (t:TemporalSignal)
    RETURN t.category AS category, count(t) AS count
    ORDER BY count DESC
    """

    with driver.session() as session:
        result = session.run(query)

        print("\nBi-temporal signals by category:\n")
        for record in result:
            print(record["category"], record["count"])


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
    LIMIT 10
    """

    with driver.session() as session:
        result = session.run(query)

        print("\nTemporal signals with time fields:\n")
        for record in result:
            print("Category:", record["category"])
            print("Text:", record["text"])
            print("valid_from:", record["valid_from"])
            print("valid_to:", record["valid_to"])
            print("recorded_at:", record["recorded_at"])
            print("invalidated_at:", record["invalidated_at"])
            print("status:", record["status"])
            print("-" * 50)


def active_temporal_signals():
    query = """
    MATCH (t:TemporalSignal)
    WHERE t.valid_to IS NULL 
      AND t.invalidated_at IS NULL
      AND t.status = 'active'
    RETURN t.category AS category, t.source_text AS text
    LIMIT 20
    """

    with driver.session() as session:
        result = session.run(query)

        print("\nCurrently active temporal signals:\n")
        for record in result:
            print(record["category"], ":", record["text"])


def invalidated_signals():
    query = """
    MATCH (t:TemporalSignal)
    WHERE t.invalidated_at IS NOT NULL
    RETURN 
        t.category AS category,
        t.source_text AS text,
        t.invalidated_at AS invalidated_at
    """

    with driver.session() as session:
        result = session.run(query)

        print("\nInvalidated signals:\n")
        found = False
        for record in result:
            found = True
            print(record["category"], ":", record["text"])
            print("invalidated_at:", record["invalidated_at"])

        if not found:
            print("No invalidated signals found yet.")


if __name__ == "__main__":
    count_temporal_signals_by_category()
    show_temporal_fields()
    active_temporal_signals()
    invalidated_signals()

    driver.close()