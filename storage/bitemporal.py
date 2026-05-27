import os
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()


driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


def insert_bitemporal_signal(signal):

    now = datetime.utcnow().isoformat()

    query = """
    MERGE (c:Conversation {id: $conversation_id})
    MERGE (sp:Speaker {name: $speaker})

    MERGE (ts:TemporalSignal {id: $id})

    SET ts.category = $category,
        ts.source_text = $source_text,
        ts.confidence = $confidence,
        ts.payload = $payload,
        ts.status = $status,

        ts.valid_from = $valid_from,
        ts.valid_to = $valid_to,

        ts.recorded_at = $recorded_at,
        ts.invalidated_at = $invalidated_at

    MERGE (sp)-[:SAID_TEMPORAL]->(ts)
    MERGE (ts)-[:FROM_CONVERSATION_TEMPORAL]->(c)
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
            status=signal.get("status", "active"),

            valid_from=now,
            valid_to=None,

            recorded_at=now,
            invalidated_at=None
        )

    print("Signal inserted into Bi-Temporal Neo4j")


def invalidate_signal(signal_id):

    now = datetime.utcnow().isoformat()

    query = """
    MATCH (ts:TemporalSignal {id: $signal_id})

    SET ts.invalidated_at = $now,
        ts.status = 'invalidated'
    """

    with driver.session() as session:
        session.run(
            query,
            signal_id=signal_id,
            now=now
        )

    print("Signal invalidated")


def close_old_fact_and_insert_new(old_signal_id, new_signal):

    now = datetime.utcnow().isoformat()

    close_query = """
    MATCH (ts:TemporalSignal {id: $old_signal_id})

    SET ts.valid_to = $now
    """

    insert_query = """
    MERGE (c:Conversation {id: $conversation_id})
    MERGE (sp:Speaker {name: $speaker})

    CREATE (ts:TemporalSignal {
        id: $id,
        category: $category,
        source_text: $source_text,
        confidence: $confidence,
        payload: $payload,
        status: $status,

        valid_from: $valid_from,
        valid_to: null,

        recorded_at: $recorded_at,
        invalidated_at: null
    })

    MERGE (sp)-[:SAID_TEMPORAL]->(ts)
    MERGE (ts)-[:FROM_CONVERSATION_TEMPORAL]->(c)
    """

    with driver.session() as session:

        session.run(
            close_query,
            old_signal_id=old_signal_id,
            now=now
        )

        session.run(
            insert_query,

            id=new_signal["id"],
            conversation_id=new_signal["conversation_id"],
            speaker=new_signal["speaker"],
            category=new_signal["category"],
            source_text=new_signal["source_text"],
            confidence=new_signal["confidence"],
            payload=str(new_signal.get("payload", {})),
            status=new_signal.get("status", "active"),

            valid_from=now,
            recorded_at=now
        )

    print("Old fact closed and new fact inserted")



def insert_bitemporal_entity(entity):

    now = datetime.utcnow().isoformat()

    query = """
    MERGE (c:Conversation {id: $conversation_id})
    MERGE (sp:Speaker {name: $speaker})

    MERGE (te:TemporalEntity {id: $id})

    SET te.entity_category = $entity_category,
        te.entity_text = $entity_text,
        te.normalized_value = $normalized_value,
        te.context = $context,
        te.attributes = $attributes,
        te.confidence = $confidence,
        te.status = $status,
        te.source_file = $source_file,
        te.chunk_number = $chunk_number,

        te.valid_from = $valid_from,
        te.valid_to = $valid_to,

        te.recorded_at = $recorded_at,
        te.invalidated_at = $invalidated_at

    MERGE (sp)-[:MENTIONED_TEMPORAL]->(te)
    MERGE (te)-[:FROM_CONVERSATION_TEMPORAL]->(c)
    """

    with driver.session() as session:
        session.run(
            query,
            id=entity["id"],
            conversation_id=entity["conversation_id"],
            speaker=entity.get("speaker"),
            entity_category=entity["entity_category"],
            entity_text=entity["entity_text"],
            normalized_value=entity.get("normalized_value"),
            context=entity.get("context"),
            attributes=str(entity.get("attributes", {})),
            confidence=entity.get("confidence"),
            status=entity.get("status", "active"),
            source_file=entity.get("source_file"),
            chunk_number=entity.get("chunk_number"),
            valid_from=now,
            valid_to=None,
            recorded_at=now,
            invalidated_at=None
        )

    print("Entity inserted into Bi-Temporal Neo4j")

def close_driver():
    driver.close()