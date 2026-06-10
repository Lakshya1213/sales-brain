# Sales Brain: Multi-Database Transcript Intelligence Pipeline

## Overview

Sales Brain is an LLM-powered transcript intelligence system that extracts structured business signals from unstructured sales call transcripts.

The system processes conversation transcripts, identifies commercially relevant signals, and stores them across multiple databases for analytics, relationship discovery, and temporal tracking.

---

## Problem Statement

Sales conversations contain valuable customer insights such as:

* Objections
* Pain Points
* Commitments
* Buying Intent
* Pricing Discussions
* Risk Signals
* Next Steps

These signals are typically hidden inside unstructured conversation text and are difficult to analyze at scale.

Sales Brain converts raw transcripts into structured business intelligence.

---

## Solution Architecture

Transcript (.docx)

↓

Transcript Chunking

↓

Groq LLM Signal Extraction

↓

Ingestion Pipeline

↓

PostgreSQL | Neo4j Graph | Bi-Temporal Neo4j

↓

Analytics & Query Layer

---

## Features

### Transcript Processing

* Reads DOCX transcripts
* Splits large transcripts into manageable chunks
* Handles long conversations exceeding LLM context limits

### Signal Extraction

* LLM-powered commercial signal extraction
* Confidence scoring
* Duplicate signal prevention
* Structured JSON output

### PostgreSQL Storage

Stores structured signals including:

* Conversation ID
* Speaker
* Category
* Source Text
* Confidence Score
* Metadata Payload

### Neo4j Graph Storage

Models relationships:

Speaker → Signal → Conversation

Useful for relationship-based analytics.

### Bi-Temporal Neo4j Storage

Tracks:

* When information became valid
* When information was recorded
* Historical signal changes
* Active vs inactive facts

---

## Signal Categories

The system extracts categories such as:

* Objection
* Pain Point
* Commitment
* Next Step
* Budget & Pricing
* Intent Signal
* Risk Cue
* Product Interest
* Requirement / Constraint
* Authority / Decision Process
* Competition / Status Quo
* Rapport Information

---

## Tech Stack

* Python
* PostgreSQL
* Neo4j
* Groq API
* SQL
* Cypher
* JSON
* python-docx

---

## Project Structure

```text
sales_brain/

├── transcripts/
├── extractor/
├── storage/
│   ├── relational.py
│   ├── graph.py
│   └── bitemporal.py
├── ingestion/
│   └── ingest.py
├── queries/
│   ├── pg_queries.py
│   ├── graph_queries.py
│   └── bitemporal_queries.py
├── saveall.py
├── requirements.txt
└── README.md
```

## Example Business Questions

* What objections are most common across calls?
* What customer pain points occur repeatedly?
* Which customers show strong buying intent?
* What pricing concerns are frequently raised?
* What next-step actions are pending?
* Which conversations contain risk signals?
* How do customer concerns evolve over time?

---

## Future Improvements

* Retrieval-Augmented Generation (RAG)
* Real-time call intelligence
* LangGraph orchestration
* Streamlit dashboard
* Sales performance analytics
* Automated insight generation

---

## Author

Lakshya Rishi

B.Tech, IIT Indore
