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

def insert_graph_entity(entity):
    query = """
    MERGE (c:Conversation {id: $conversation_id})
    SET c.source_file = $source_file

    MERGE (sp:Speaker {label: $speaker})
    SET sp.name = $speaker_name,
        sp.role = $speaker_role,
        sp.source_file = $source_file

    MERGE (e:Entity {id: $id})
    SET e.entity_category = $entity_category,
        e.entity_text = $entity_text,
        e.normalized_value = $normalized_value,
        e.context = $context,
        e.attributes = $attributes,
        e.confidence = $confidence,
        e.status = $status,
        e.chunk_number = $chunk_number,
        e.source_file = $source_file,
        e.speaker_label = $speaker,
        e.speaker_name = $speaker_name,
        e.speaker_role = $speaker_role

    MERGE (sp)-[:MENTIONED]->(e)
    MERGE (e)-[:FROM_CONVERSATION]->(c)
    """

    with driver.session() as session:
        session.run(
            query,
            id=entity["id"],
            conversation_id=entity["conversation_id"],
            speaker=entity.get("speaker"),
            speaker_name=entity.get("speaker_name"),
            speaker_role=entity.get("speaker_role"),
            entity_category=entity["entity_category"],
            entity_text=entity["entity_text"],
            normalized_value=entity.get("normalized_value"),
            context=entity.get("context"),
            attributes=str(entity.get("attributes", {})),
            confidence=entity.get("confidence"),
            status=entity.get("status", "active"),
            chunk_number=entity.get("chunk_number"),
            source_file=entity.get("source_file")
        )

    print("Entity inserted into Neo4j graph")

def close_driver():
    driver.close()