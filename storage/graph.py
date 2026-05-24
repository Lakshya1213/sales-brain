import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


def insert_graph_signal(signal):
    query = """
    MERGE (c:Conversation {id: $conversation_id})
    MERGE (sp:Speaker {name: $speaker})

    MERGE (sig:Signal {id: $id})
    SET sig.category = $category,
        sig.source_text = $source_text,
        sig.confidence = $confidence,
        sig.payload = $payload,
        sig.status = $status

    MERGE (sp)-[:SAID]->(sig)
    MERGE (sig)-[:FROM_CONVERSATION]->(c)
    """

    with driver.session() as session:
        session.run(
            query,
            id=signal["id"],
            conversation_id=signal["conversation_id"],
            speaker=signal["speaker"],
            category=signal["category"],
            source_text=signal["source_text"],
            confidence=signal["confidence"],
            payload=str(signal.get("payload", {})),
            status=signal.get("status", "active")
        )

    print("Signal inserted into Neo4j graph")


def close_driver():
    driver.close()