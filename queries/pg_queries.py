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


def run_query(title, query):

    conn = get_pg_connection()
    cur = conn.cursor()

    print(f"\n{'=' * 50}")
    print(title)
    print(f"{'=' * 50}\n")

    cur.execute(query)

    rows = cur.fetchall()

    if not rows:
        print("No data found")

    for row in rows:
        print(row)

    cur.close()
    conn.close()


def count_signals_by_category():

    query = """
    SELECT category, COUNT(*)
    FROM signals
    GROUP BY category
    ORDER BY COUNT(*) DESC;
    """

    run_query("Signals by Category", query)


def get_objections():

    query = """
    SELECT conversation_id, speaker, source_text
    FROM signals
    WHERE category = 'objection';
    """

    run_query("Customer Objections", query)


def get_pain_points():

    query = """
    SELECT conversation_id, source_text
    FROM signals
    WHERE category = 'pain_point';
    """

    run_query("Pain Points", query)


def get_commitments():

    query = """
    SELECT conversation_id, speaker, source_text
    FROM signals
    WHERE category = 'commitment';
    """

    run_query("Commitments", query)


def get_next_steps():

    query = """
    SELECT conversation_id, speaker, source_text
    FROM signals
    WHERE category = 'next_step';
    """

    run_query("Next Steps", query)


def get_risk_cues():

    query = """
    SELECT conversation_id, source_text
    FROM signals
    WHERE category = 'risk_cue';
    """

    run_query("Risk Cues", query)


def get_intent_signals():

    query = """
    SELECT conversation_id, source_text
    FROM signals
    WHERE category = 'intent_signal';
    """

    run_query("Intent Signals", query)


def get_budget_pricing():

    query = """
    SELECT conversation_id, source_text
    FROM signals
    WHERE category = 'budget_pricing';
    """

    run_query("Budget & Pricing Signals", query)


def get_product_interest():

    query = """
    SELECT conversation_id, source_text
    FROM signals
    WHERE category = 'product_intent';
    """

    run_query("Product Intent", query)

def count_signals_by_conversation():

    query = """
    SELECT conversation_id, COUNT(*)
    FROM signals
    GROUP BY conversation_id
    ORDER BY COUNT(*) DESC;
    """

    run_query("Signals by Conversation", query)


def category_count_per_conversation():

    query = """
    SELECT conversation_id, category, COUNT(*)
    FROM signals
    GROUP BY conversation_id, category
    ORDER BY conversation_id, COUNT(*) DESC;
    """

    run_query("Category Count per Conversation", query)
    
if __name__ == "__main__":

    count_signals_by_conversation()

    category_count_per_conversation()

    count_signals_by_category()

    get_objections()

    get_pain_points()

    get_commitments()

    get_next_steps()

    get_risk_cues()

    get_intent_signals()

    get_budget_pricing()

    get_product_interest()