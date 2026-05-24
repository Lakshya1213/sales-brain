from extraction import extract_from_file
signals = extract_from_file(
    r"D:\Transcrpit\sales_brain\transcripts\020_MU_transcript.docx",
    "020"
)

for signal in signals:
    print(signal)