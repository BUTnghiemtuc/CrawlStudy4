import csv
from pathlib import Path

INPUT_FILE = Path("data/vocabulary.csv")
OUTPUT_FILE = Path("data/quizlet_import.txt")


def main():
    if not INPUT_FILE.exists():
        print(f"Không tìm thấy file: {INPUT_FILE}")
        return

    flashcards = []
    seen = set()

    with open(INPUT_FILE, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        
        # Đảm bảo CSV có cột item và meaning_vi
        if not reader.fieldnames or "item" not in reader.fieldnames or "meaning_vi" not in reader.fieldnames:
            print(f"File CSV không đúng định dạng. Cần có cột 'item' và 'meaning_vi'. Cột hiện tại: {reader.fieldnames}")
            return
            
        for row in reader:
            term = row["item"].strip()
            definition = row["meaning_vi"].strip()
            
            if not term or not definition:
                continue
                
            key = term.lower()
            if key in seen:
                continue
                
            seen.add(key)
            flashcards.append((term, definition))

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        for term, definition in flashcards:
            f.write(f"{term}\t{definition}\n")

    print(f"Đã tạo: {OUTPUT_FILE}")
    print(f"Số flashcards: {len(flashcards)}")


if __name__ == "__main__":
    main()