from pathlib import Path

import pandas as pd


INPUT_PATH = Path("data/questions_basic.csv")
OUTPUT_PATH = Path("data/wrong_questions.csv")


def main():
    if not INPUT_PATH.exists():
        print("Chưa có data/questions_basic.csv. Hãy chạy extract_result.py trước.")
        return

    df = pd.read_csv(INPUT_PATH)

    if "is_wrong" in df.columns:
        wrong_df = df[df["is_wrong"] == True]
    else:
        wrong_df = df[df["is_correct"] == False]

    wrong_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Đã lưu {len(wrong_df)} câu sai vào: {OUTPUT_PATH}")
    print(wrong_df[["question_id", "part", "user_answer", "correct_answer", "detail_url"]])


if __name__ == "__main__":
    main()