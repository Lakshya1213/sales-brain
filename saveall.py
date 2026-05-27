import hashlib

from extractor.extraction import extract_from_file
from ingestion.ingest import ingest_signal, ingest_entity


files = [
    (r"D:\Transcrpit\sales_brain\transcripts\Finideas_8508_transcript1 (1).docx","8508_Fin")
    # (r"D:\Transcrpit\sales_brain\transcripts\Finideas_3430_transcript2.docx", "3430_Fin")
    # (r"D:\Transcrpit\sales_brain\transcripts\Finideas_9812_transcript3.docx","9812_Fin")
    # (r"D:\Transcrpit\sales_brain\transcripts\Finideas_1319_transcript4.docx","1319_Fin")
    # (r"D:\Transcrpit\sales_brain\transcripts\Finideas_3060_transcript5.docx","3060_Fin"),
    # (r"D:\Transcrpit\sales_brain\transcripts\Finideas_6101_transcript6.docx","6101_Fin")
    # (r"D:\Transcrpit\sales_brain\transcripts\Finideas_8508_transcript1_newtest.docx","8508_Fin")
    # (r"D:\Transcrpit\sales_brain\transcripts\Finideas_0171_transcript8.docx", "Finideas_0171"),
]


for file_path, conversation_id in files:
    print("\n====================================")
    print("STARTING FILE:", conversation_id)
    print("====================================")

    try:
        output = extract_from_file(file_path, conversation_id)

        signals = output.get("signals", [])
        entities = output.get("entities", [])

        print("Extracted signals:", len(signals))
        print("Extracted entities:", len(entities))

        for idx, signal in enumerate(signals, start=1):
            try:
                required = ["conversation_id", "speaker", "category", "source_text"]

                if not all(k in signal for k in required):
                    print("Skipping bad signal:", signal)
                    continue

                raw = (
                    signal["conversation_id"]
                    + signal["speaker"]
                    + signal["category"]
                    + signal["source_text"]
                )

                signal["id"] = signal.get("id") or hashlib.md5(raw.encode()).hexdigest()

                print(f"Inserting signal {idx}/{len(signals)}:", signal["category"])
                ingest_signal(signal)

            except Exception as e:
                print("Signal failed:", e)
                continue

        for idx, entity in enumerate(entities, start=1):
            try:
                required = ["conversation_id", "speaker", "entity_category", "entity_text"]

                if not all(k in entity for k in required):
                    print("Skipping bad entity:", entity)
                    continue

                raw = (
                    entity["conversation_id"]
                    + entity["speaker"]
                    + entity["entity_category"]
                    + entity["entity_text"]
                )

                entity["id"] = entity.get("id") or hashlib.md5(raw.encode()).hexdigest()

                print(f"Inserting entity {idx}/{len(entities)}:", entity["entity_category"])
                ingest_entity(entity)

            except Exception as e:
                print("Entity failed:", e)
                continue

        print("FINISHED FILE:", conversation_id)

    except Exception as e:
        print("FILE FAILED:", conversation_id)
        print("ERROR:", e)
        continue

print("\nALL FILES DONE")