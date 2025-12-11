import sys
from pathlib import Path
from Self_Improvement import rag_index

def chunk_text(text, chunk_paragraphs=2):
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []
    for i in range(0, len(paragraphs), chunk_paragraphs):
        chunk = '\n\n'.join(paragraphs[i:i+chunk_paragraphs]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def main():
    if len(sys.argv) < 2:
        print("Usage: python index_rag_reference.py path/to/file.txt [source_name]")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"File not found: {file_path}")
        sys.exit(1)

    source_name = sys.argv[2] if len(sys.argv) > 2 else file_path.stem

    text = file_path.read_text(encoding='utf-8')
    chunks = chunk_text(text, chunk_paragraphs=2)

    for idx, chunk in enumerate(chunks, start=1):
        doc_id = f"{source_name}_p{idx}"
        # rag_index.add_document expects (doc_id, text)
        rag_index.add_document(doc_id, chunk)
        print(f"Indexed: {doc_id}")

    try:
        current = len(rag_index.load_documents())
    except Exception:
        current = "unknown"
    print('Indexing complete. Current index size:', current)


if __name__ == "__main__":
    main()
