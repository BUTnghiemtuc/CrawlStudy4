import os
import re
import json
import time
import pandas as pd
from tqdm import tqdm
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)


INPUT_PATH = "data/final.txt"
OUTPUT_PATH = "data/vocabulary.csv"


def split_questions(text: str) -> list[str]:
    """
    Tách file thành từng block câu hỏi dựa vào 'Đáp án chi tiết #'.
    """
    blocks = re.split(r"(?=Đáp án chi tiết #\d+)", text)
    return [b.strip() for b in blocks if b.strip().startswith("Đáp án chi tiết #")]


def extract_question_id(block: str) -> int | None:
    match = re.search(r"Đáp án chi tiết #(\d+)", block)
    return int(match.group(1)) if match else None


def extract_correct_answer_letter(block: str) -> str | None:
    """
    Ưu tiên lấy dòng 'Đáp án đúng:X'.
    Nếu không có, thử tìm trong giải thích kiểu: 'Đáp án đúng là C'.
    """
    match = re.search(r"Đáp án đúng\s*:\s*([A-D])", block)
    if match:
        return match.group(1)

    match = re.search(r"Đáp án đúng là\s+([A-D])", block, re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r"đáp án đúng là\s+([A-D])", block, re.IGNORECASE)
    if match:
        return match.group(1)

    match = re.search(r"chọn\s+([A-D])", block, re.IGNORECASE)
    if match:
        return match.group(1)

    return None


def extract_choices(block: str) -> dict:
    """
    Lấy các lựa chọn A/B/C/D.
    """
    choices = {}
    for letter in ["A", "B", "C", "D"]:
        pattern = rf"^{letter}\.\s*(.+)$"
        match = re.search(pattern, block, re.MULTILINE)
        if match:
            choices[letter] = match.group(1).strip()
    return choices


def extract_question_sentence(block: str, question_id: int | None) -> str | None:
    """
    Lấy câu hỏi chính sau dòng số câu.
    Ví dụ:
    112
    The Master Gardeners Club had to _____ its monthly meeting...
    """
    if question_id is None:
        return None

    lines = [line.strip() for line in block.splitlines() if line.strip()]

    for i, line in enumerate(lines):
        if line == str(question_id):
            # dòng sau số câu thường là câu hỏi
            if i + 1 < len(lines):
                return lines[i + 1]

    return None


def extract_tags(block: str) -> str:
    """
    Lấy dòng tag chứa [Grammar], [Part 5], [Câu hỏi từ vựng]...
    """
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    tag_lines = [line for line in lines if "[" in line and "]" in line]
    return " ".join(tag_lines[:2])


def build_clean_question(block: str) -> dict | None:
    question_id = extract_question_id(block)
    question = extract_question_sentence(block, question_id)
    choices = extract_choices(block)
    correct_letter = extract_correct_answer_letter(block)
    tags = extract_tags(block)

    if not question_id or not question or not choices:
        return None

    correct_word = choices.get(correct_letter) if correct_letter else None

    filled_sentence = question
    if correct_word:
        filled_sentence = question.replace("_____", correct_word)

    return {
        "question_id": question_id,
        "tags": tags,
        "question": question,
        "choices": choices,
        "correct_answer": correct_letter,
        "correct_word": correct_word,
        "filled_sentence": filled_sentence,
    }


def batch_items(items: list[dict], batch_size: int = 8):
    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]


VOCAB_SCHEMA = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "question_id": {"type": "integer"},
                    "item": {"type": "string"},
                    "meaning_vi": {"type": "string"},
                    "type": {
                        "type": "string",
                        "enum": [
                            "vocabulary",
                            "collocation",
                            "word_family",
                            "grammar_pattern"
                        ]
                    },
                    "reason": {"type": "string"},
                    "source_sentence": {"type": "string"}
                },
                "required": [
                    "question_id",
                    "item",
                    "meaning_vi",
                    "type",
                    "reason",
                    "source_sentence"
                ],
                "additionalProperties": False
            }
        }
    },
    "required": ["items"],
    "additionalProperties": False
}


def clean_and_parse_json(text: str) -> dict:
    text = text.strip()
    # Thử tìm phần JSON nằm giữa ```json và ``` hoặc ``` và ```
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    
    # Nếu không tìm thấy markdown block, cố gắng lấy phần nằm giữa { và } ngoài cùng
    if not (text.startswith("{") or text.startswith("[")):
        match = re.search(r"(\{.*\})", text, re.DOTALL | re.MULTILINE)
        if match:
            text = match.group(1).strip()
            
    # Xóa chú thích dạng // ... trong chuỗi JSON (ngoại trừ khi nằm trong URL)
    text = re.sub(r'(?<!:)\/\/.*$', '', text, flags=re.MULTILINE)

    # Xóa dấu phẩy thừa ở cuối phần tử trước dấu đóng ngoặc } hoặc ]
    text = re.sub(r',\s*([\]}])', r'\1', text)
            
    return json.loads(text)


def extract_vocab_with_llm(batch: list[dict]) -> list[dict]:
    system_prompt = """
Bạn là hệ thống lọc và dịch nghĩa từ vựng TOEIC sang tiếng Việt.

Nhiệm vụ:
Từ mỗi câu hỏi TOEIC trong danh sách được cung cấp, hãy chọn tối đa 3 mục đáng học nhất (từ vựng, collocation, cụm từ cố định, hoặc cấu trúc ngữ pháp).
Với mỗi mục được chọn, hãy dịch nghĩa sang tiếng Việt sát nhất với nghĩa của từ/cụm từ đó trong ngữ cảnh của câu.

Ưu tiên lựa chọn:
1. Collocation TOEIC: verb+noun, adj+noun, adv+adj, noun+prep (Ví dụ: "make a decision", "fully operational").
2. Cụm cố định: free of charge, out of stock, according to...
3. Word family nếu câu hỏi kiểm tra từ loại.
4. Grammar pattern nếu câu hỏi kiểm tra ngữ pháp (Ví dụ: "capable of completing").
5. Từ vựng business/workplace hay gặp trong TOEIC.

Quy định lọc và định dạng giá trị:
- KHÔNG chọn từ quá dễ hoặc quá thông dụng đứng riêng lẻ (như "day", "week", "take", "make").
- KHÔNG chọn tên riêng.
- KHÔNG chọn quá 3 mục cho mỗi câu hỏi.
- "question_id" BẮT BUỘC phải là KIỂU SỐ NGUYÊN (ví dụ: 101), trùng khớp hoàn toàn với question_id của câu hỏi gốc. KHÔNG được để dạng chuỗi "question_id: 101".
- "item" BẮT BUỘC chỉ chứa từ hoặc cụm từ tiếng Anh được lọc ra (ví dụ: "accounting files"). KHÔNG được chèn nghĩa tiếng Việt hay dấu hai chấm vào trường này.
- "meaning_vi" BẮT BUỘC chỉ chứa nghĩa tiếng Việt của từ/cụm từ đó (ví dụ: "hồ sơ kế toán").
- KHÔNG viết thêm các chú thích bằng ký hiệu `//` hay bất kỳ ký tự nào ngoài JSON trong chuỗi JSON trả về.

Bạn phải trả về một đối tượng JSON duy nhất theo đúng cấu trúc mẫu sau (không kèm giải thích hay ký tự thừa nào ngoài JSON):
{
  "items": [
    {
      "question_id": 101,
      "item": "accounting files",
      "meaning_vi": "hồ sơ kế toán",
      "type": "collocation",
      "reason": "Business terminology",
      "source_sentence": "With the help of one of the IT technicians, the missing accounting files have been recovered."
    }
  ]
}
""".strip()

    user_prompt = json.dumps(batch, ensure_ascii=False, indent=2)

    try:
        # Sử dụng Chat Completions tiêu chuẩn của OpenAI SDK (tương thích 100% với OpenRouter và các LLM khác)
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "toeic_vocab_items",
                    "strict": True,
                    "schema": VOCAB_SCHEMA
                }
            }
        )
    except Exception as e:
        print(f"\n[Warning] API call with strict json_schema failed: {e}. Retrying with json_object format...")
        response = client.chat.completions.create(
            model="google/gemma-4-31b-it:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )

    result_text = response.choices[0].message.content
    if not result_text:
        print("\n[Warning] API returned empty content.")
        return []

    try:
        result_json = clean_and_parse_json(result_text)
    except Exception as e:
        print(f"\n[Warning] Failed to parse JSON response: {e}")
        print("--- RAW RESPONSE START ---")
        print(result_text)
        print("--- RAW RESPONSE END ---")
        return []

    if not isinstance(result_json, dict) or "items" not in result_json:
        print("\n[Warning] JSON response is not in the expected format (missing 'items' key).")
        return []

    return result_json["items"]


def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        text = f.read()

    blocks = split_questions(text)

    parsed_questions = []
    for block in blocks:
        item = build_clean_question(block)
        if item:
            parsed_questions.append(item)

    print(f"Parsed questions: {len(parsed_questions)}")

    all_vocab = []

    for batch in tqdm(list(batch_items(parsed_questions, batch_size=8))):
        try:
            vocab_items = extract_vocab_with_llm(batch)
            all_vocab.extend(vocab_items)
            time.sleep(0.5)
        except Exception as e:
            print("Error in batch:")
            print(e)
            continue

    df = pd.DataFrame(all_vocab)
    df.drop_duplicates(subset=["question_id", "item"], inplace=True)
    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"Saved to {OUTPUT_PATH}")
    print(df.head(20))


if __name__ == "__main__":
    main()