from storage.relational import insert_signal, insert_entity
from storage.graph import insert_graph_signal, insert_graph_entity
from storage.bitemporal import insert_bitemporal_signal, insert_bitemporal_entity


def ingest_signal(signal):

    try:
        insert_signal(signal)
    except Exception as e:
        print("PostgreSQL signal failed:", e)

    try:
        insert_graph_signal(signal)
    except Exception as e:
        print("Neo4j graph signal failed:", e)

    try:
        insert_bitemporal_signal(signal)
    except Exception as e:
        print("Bi-temporal signal failed:", e)

    print("Signal ingestion completed")


def ingest_entity(entity):

    try:
        insert_entity(entity)
    except Exception as e:
        print("PostgreSQL entity failed:", e)

    try:
        insert_graph_entity(entity)
    except Exception as e:
        print("Neo4j graph entity failed:", e)

    try:
        insert_bitemporal_entity(entity)
    except Exception as e:
        print("Bi-temporal entity failed:", e)

    print("Entity ingestion completed")


def ingest_output(output):

    for signal in output["signals"]:
        ingest_signal(signal)

    for entity in output["entities"]:
        ingest_entity(entity)

    print("Full ingestion completed")