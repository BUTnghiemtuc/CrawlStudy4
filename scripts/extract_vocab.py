import re
from pathlib import Path
from collections import Counter

import pandas as pd


DETAIL_DIR = Path("data/details")
OUTPUT_PATH = Path("data/vocab_basic.csv")

STOPWORDS = {
    "the", "a", "an", "to", "of", "in", "on", "at", "for", "from",
    "and", "or", "but", "is", "are", "was", "were", "be", "been",
    "by", "with", "as", "that", "this", "these", "those", "it",
    "its", "you", "your", "we", "they", "he", "she", "his", "her",
    "their", "our", "not", "no", "yes", "do", "does", "did",
    "have", "has", "had", "will", "would", "can", "could", "should",
    "may", "might", "must", "if", "then", "than", "because",
    "question", "answer", "correct", "incorrect", "part", "detail",
    "study", "study4", "toeic", "test", "result", "results",
    "chi", "tiết", "đáp", "án", "câu", "hỏi",
}


def clean_text(text: str):
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_words_from_text(text: str):
    words = re.findall(r"\b[a-zA-Z][a-zA-Z\-]{2,}\b", text.lower())

    filtered = []
    for word in words:
        if word in STOPWORDS:
            continue
        if len(word) < 4:
            continue
        filtered.append(word)

    return filtered


def main():
    if not DETAIL_DIR.exists():
        print("Chưa có thư mục data/details. Hãy chạy scripts/crawl_result.py trước.")
        return

    txt_files = sorted(DETAIL_DIR.glob("question_*.txt"))

    if not txt_files:
        print("Không có file chi tiết câu sai nào trong data/details.")
        return

    all_words = []
    word_sources = {}

    for txt_file in txt_files:
        qid_match = re.search(r"question_(\d+)\.txt", txt_file.name)
        qid = qid_match.group(1) if qid_match else ""

        text = txt_file.read_text(encoding="utf-8")
        text = clean_text(text)

        words = extract_words_from_text(text)
        all_words.extend(words)

        for word in set(words):
            word_sources.setdefault(word, set()).add(qid)

    counter = Counter(all_words)

    rows = []
    for word, freq in counter.most_common():
        rows.append(
            {
                "word": word,
                "frequency": freq,
                "question_ids": ", ".join(sorted(word_sources.get(word, []))),
                "meaning_vi": "",
                "part_of_speech": "",
                "note": "",
                "priority": "",
            }
        )

    df = pd.DataFrame(rows)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Đã lọc {len(df)} từ từ {len(txt_files)} câu sai.")
    print(f"Đã lưu vào: {OUTPUT_PATH}")
    print(df.head(30))


if __name__ == "__main__":
    main()