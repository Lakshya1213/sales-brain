from storage.relational import insert_signal
from storage.graph import insert_graph_signal
from storage.bitemporal import insert_bitemporal_signal


def ingest(signal):

    try:
        insert_signal(signal)

    except Exception as e:
        print("PostgreSQL failed:", e)

    try:
        insert_graph_signal(signal)

    except Exception as e:
        print("Neo4j graph failed:", e)

    try:
        insert_bitemporal_signal(signal)

    except Exception as e:
        print("Bi-temporal graph failed:", e)

    print("Ingestion completed")