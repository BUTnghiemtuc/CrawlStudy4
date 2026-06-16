import json
from pathlib import Path

import pandas as pd


ANSWER_LIST_JSON = Path("data/answer_list.json")
QUESTIONS_CSV = Path("data/questions_basic.csv")


def main():
    if not ANSWER_LIST_JSON.exists():
        print("Chưa có data/answer_list.json. Hãy chạy scripts/crawl_result.py trước.")
        return

    answers = json.loads(ANSWER_LIST_JSON.read_text(encoding="utf-8"))

    if not answers:
        print("answer_list.json rỗng.")
        return

    df = pd.DataFrame(answers)
    df.to_csv(QUESTIONS_CSV, index=False, encoding="utf-8-sig")

    print(f"Đã lưu {len(df)} câu vào: {QUESTIONS_CSV}")
    print(df[["question_id", "part", "user_answer", "correct_answer", "is_correct"]].head(20))


if __name__ == "__main__":
    main()