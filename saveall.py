import hashlib

from extractor.extraction import extract_from_file
from ingestion.ingest import ingest


files = [
    (r"D:\Transcrpit\sales_brain\transcripts\Finideas_0171_transcript8.docx", "Finideas_0171"),
    (r"D:\Transcrpit\sales_brain\transcripts\Finideas_1319_transcript4.docx", "Finideas_1319"),
    (r"D:\Transcrpit\sales_brain\transcripts\Finideas_3060_transcript5.docx", "Finideas_3060"),
]


for file_path, conversation_id in files:
    print("\n====================================")
    print("STARTING FILE:", conversation_id)
    print("====================================")

    try:
        signals = extract_from_file(file_path, conversation_id)
        print("Extracted signals:", len(signals))

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

                signal["id"] = hashlib.md5(raw.encode()).hexdigest()

                print(f"Inserting {idx}/{len(signals)}:", signal["category"])
                ingest(signal)

            except Exception as e:
                print("Signal failed:", e)
                continue

        print("FINISHED FILE:", conversation_id)

    except Exception as e:
        print("FILE FAILED:", conversation_id)
        print("ERROR:", e)
        continue

print("\nALL FILES DONE")