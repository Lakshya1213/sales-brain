import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_pg_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("POSTGRES_PORT")
    )


def count_signals_by_category():

    conn = get_pg_connection()
    cur = conn.cursor()

    query = """
    SELECT category, COUNT(*)
    FROM signals
    GROUP BY category
    ORDER BY COUNT(*) DESC;
    """

    cur.execute(query)

    rows = cur.fetchall()

    print("\nSignals by category:\n")

    for row in rows:
        print(row)

    cur.close()
    conn.close()


def get_commitments():

    conn = get_pg_connection()
    cur = conn.cursor()

    query = """
    SELECT speaker, source_text
    FROM signals
    WHERE category = 'commitment';
    """

    cur.execute(query)

    rows = cur.fetchall()

    print("\nCommitments:\n")

    for row in rows:
        print(row)

    cur.close()
    conn.close()


def get_questions():

    conn = get_pg_connection()
    cur = conn.cursor()

    query = """
    SELECT speaker, source_text
    FROM signals
    WHERE category = 'question';
    """

    cur.execute(query)

    rows = cur.fetchall()

    print("\nQuestions:\n")

    for row in rows:
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":

    count_signals_by_category()

    get_commitments()

    get_questions()