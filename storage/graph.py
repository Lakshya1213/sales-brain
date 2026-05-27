import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD")
    )
)


def insert_graph_signal(signal):
    query = """
    MERGE (c:Conversation {id: $conversation_id})
    SET c.source_file = $source_file

    MERGE (sp:Speaker {label: $speaker})
    SET sp.name = $speaker_name,
        sp.role = $speaker_role,
        sp.source_file = $source_file

    MERGE (sig:Signal {id: $id})
    SET sig.category = $category,
        sig.source_text = $source_text,
        sig.confidence = $confidence,
        sig.payload = $payload,
        sig.status = $status,
        sig.chunk_number = $chunk_number,
        sig.source_file = $source_file,
        sig.speaker_label = $speaker,
        sig.speaker_name = $speaker_name,
        sig.speaker_role = $speaker_role

    MERGE (sp)-[:SAID]->(sig)
    MERGE (sig)-[:FROM_CONVERSATION]->(c)
    """

    with driver.session() as session:
        session.run(
            query,
            id=signal["id"],
            conversation_id=signal["conversation_id"],
            speaker=signal.get("speaker"),
            speaker_name=signal.get("speaker_name"),
            speaker_role=signal.get("speaker_role"),
            category=signal["category"],
            source_text=signal["source_text"],
            confidence=signal["confidence"],
            payload=str(signal.get("payload", {})),
            status=signal.get("status", "active"),
            chunk_number=signal.get("chunk_number"),
            source_file=signal.get("source_file")
        )

    print("Signal inserted into Neo4j graph")


def close_driver():
    driver.close()