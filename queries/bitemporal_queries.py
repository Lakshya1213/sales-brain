import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


def count_signals_by_category():
    query = """
    MATCH (sig:Signal)
    RETURN sig.category AS category, count(sig) AS count
    ORDER BY count DESC
    """

    with driver.session() as session:
        result = session.run(query)

        print("\nNeo4j Signals by category:\n")
        for record in result:
            print(record["category"], record["count"])


def speaker_signal_paths():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)-[:FROM_CONVERSATION]->(c:Conversation)
    RETURN s.name AS speaker, sig.category AS category, sig.source_text AS text, c.id AS conversation_id
    LIMIT 20
    """

    with driver.session() as session:
        result = session.run(query)

        print("\nSpeaker → Signal → Conversation paths:\n")
        for record in result:
            print(record["speaker"], "->", record["category"], "->", record["conversation_id"])
            print(record["text"])
            print()


def get_questions_from_graph():
    query = """
    MATCH (s:Speaker)-[:SAID]->(sig:Signal)
    WHERE sig.category = 'question'
    RETURN s.name AS speaker, sig.source_text AS question
    """

    with driver.session() as session:
        result = session.run(query)

        print("\nQuestions from Neo4j:\n")
        for record in result:
            print(record["speaker"], ":", record["question"])


if __name__ == "__main__":
    count_signals_by_category()
    speaker_signal_paths()
    get_questions_from_graph()
    driver.close()