import os
import json
import hashlib
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


def create_tables():
    conn = get_pg_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS signals (
        id TEXT PRIMARY KEY,
        conversation_id TEXT NOT NULL,
        speaker TEXT,
        category TEXT NOT NULL,
        source_text TEXT NOT NULL,
        confidence FLOAT,
        payload JSONB,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS audit_log (
        id SERIAL PRIMARY KEY,
        signal_id TEXT,
        store_name TEXT,
        action TEXT,
        status TEXT,
        error_message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
    print("PostgreSQL tables created")


def generate_signal_id(signal):
    raw = (
        signal["conversation_id"]
        + signal["speaker"]
        + signal["category"]
        + signal["source_text"]
    )
    return hashlib.md5(raw.encode()).hexdigest()


def insert_signal(signal):
    conn = get_pg_connection()
    cur = conn.cursor()

    signal_id = signal.get("id") or generate_signal_id(signal)

    try:
        cur.execute("""
        INSERT INTO signals
        (id, conversation_id, speaker, category, source_text, confidence, payload, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """, (
            signal_id,
            signal["conversation_id"],
            signal["speaker"],
            signal["category"],
            signal["source_text"],
            signal["confidence"],
            json.dumps(signal.get("payload", {})),
            signal.get("status", "active")
        ))

        cur.execute("""
        INSERT INTO audit_log (signal_id, store_name, action, status, error_message)
        VALUES (%s, %s, %s, %s, %s);
        """, (
            signal_id,
            "postgres",
            "insert_signal",
            "success",
            None
        ))

        conn.commit()
        print("Signal inserted into PostgreSQL")

    except Exception as e:
        conn.rollback()

        cur.execute("""
        INSERT INTO audit_log (signal_id, store_name, action, status, error_message)
        VALUES (%s, %s, %s, %s, %s);
        """, (
            signal_id,
            "postgres",
            "insert_signal",
            "failed",
            str(e)
        ))

        conn.commit()
        print("PostgreSQL insert failed:", e)

    finally:
        cur.close()
        conn.close()