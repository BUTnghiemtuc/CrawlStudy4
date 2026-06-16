import json
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


USER_DATA_DIR = "study4_browser_profile"
BASE_URL = "https://study4.com"

DATA_DIR = Path("data")
DETAIL_DIR = DATA_DIR / "details"

RAW_HTML_PATH = DATA_DIR / "raw_result.html"
RAW_TEXT_PATH = DATA_DIR / "raw_result.txt"

ANSWER_LIST_JSON = DATA_DIR / "answer_list.json"
QUESTIONS_CSV = DATA_DIR / "questions_basic.csv"
WRONG_CSV = DATA_DIR / "wrong_questions.csv"


def ensure_dirs():
    DATA_DIR.mkdir(exist_ok=True)
    DETAIL_DIR.mkdir(exist_ok=True)


def save_page(page):
    html = page.content()
    text = page.locator("body").inner_text()

    RAW_HTML_PATH.write_text(html, encoding="utf-8")
    RAW_TEXT_PATH.write_text(text, encoding="utf-8")

    print(f"Đã lưu: {RAW_HTML_PATH}")
    print(f"Đã lưu: {RAW_TEXT_PATH}")

    return html, text


def parse_answers_from_html(html: str):
    """
    Parse danh sách câu hỏi từ raw_result.html.

    Format STUDY4:
    <div class="result-answers-item">
        <span class="question-number"><strong>104</strong></span>
        <span class="text-answerkey">B</span>:
        <i class="text-line-through mr-1">D</i>
        <span class="text-wrong ..."></span>
        <a class="result-answer-detail" data-href="/tests/.../q/.../?view=embed">[Chi tiết]</a>
    </div>
    """

    soup = BeautifulSoup(html, "lxml")
    rows = []

    current_part = None

    # Duyệt theo thứ tự các node để biết câu thuộc Part nào
    content = soup.select_one(".contentblock") or soup

    for node in content.find_all(["h5", "div"], recursive=True):
        if node.name == "h5":
            title = node.get_text(" ", strip=True)
            if title.startswith("Part"):
                current_part = title

        if node.name == "div":
            classes = node.get("class", [])
            if "result-answers-item" not in classes:
                continue

            qid_el = node.select_one(".question-number strong")
            correct_el = node.select_one(".text-answerkey")
            user_el = node.select_one("i")
            detail_el = node.select_one("a.result-answer-detail")

            if not qid_el or not correct_el or not user_el:
                continue

            question_id = qid_el.get_text(strip=True)
            correct_answer = correct_el.get_text(strip=True)
            user_answer = user_el.get_text(strip=True)

            is_wrong = node.select_one(".text-wrong") is not None
            is_correct = not is_wrong

            detail_href = ""
            detail_url = ""

            if detail_el:
                detail_href = detail_el.get("data-href", "")
                detail_url = urljoin(BASE_URL, detail_href)

            rows.append(
                {
                    "question_id": question_id,
                    "part": current_part or "",
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "is_wrong": is_wrong,
                    "detail_href": detail_href,
                    "detail_url": detail_url,
                }
            )

    # Khử trùng lặp theo question_id
    unique = {}
    for row in rows:
        unique[row["question_id"]] = row

    return list(unique.values())


def save_answers_json(answers):
    ANSWER_LIST_JSON.write_text(
        json.dumps(answers, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Đã lưu danh sách đáp án: {ANSWER_LIST_JSON}")


def save_answers_csv(answers):
    import pandas as pd

    df = pd.DataFrame(answers)
    df.to_csv(QUESTIONS_CSV, index=False, encoding="utf-8-sig")

    wrong_df = df[df["is_wrong"] == True]
    wrong_df.to_csv(WRONG_CSV, index=False, encoding="utf-8-sig")

    print(f"Đã lưu toàn bộ câu hỏi: {QUESTIONS_CSV}")
    print(f"Đã lưu câu sai: {WRONG_CSV}")
    print(f"Tổng số câu: {len(df)}")
    print(f"Số câu sai: {len(wrong_df)}")


def click_explanation_button(page):
    """
    Trong trang chi tiết câu hỏi, bấm nút 'Giải thích chi tiết đáp án'
    để mở phần giải thích nếu có.
    """
    try:
        page.get_by_text("Giải thích chi tiết đáp án", exact=False).click(timeout=5000)
        page.wait_for_timeout(1500)
        print("Đã bấm nút Giải thích chi tiết đáp án.")
    except Exception:
        print("Không tìm thấy hoặc không cần bấm nút Giải thích chi tiết đáp án.")


def crawl_wrong_details(page, answers):
    wrong_answers = [item for item in answers if item["is_wrong"]]

    if not wrong_answers:
        print("Không có câu sai nào để crawl chi tiết.")
        return

    print(f"\nBắt đầu crawl chi tiết {len(wrong_answers)} câu sai...")

    for item in wrong_answers:
        qid = item["question_id"]
        detail_url = item["detail_url"]

        if not detail_url:
            print(f"Bỏ qua câu {qid}: không có detail_url.")
            continue

        print(f"\nĐang mở chi tiết câu {qid}: {detail_url}")

        try:
            page.goto(detail_url, wait_until="networkidle")
            page.wait_for_timeout(1500)

            # Bấm mở phần giải thích chi tiết
            click_explanation_button(page)

            html = page.content()
            text = page.locator("body").inner_text()

            html_path = DETAIL_DIR / f"question_{qid}.html"
            txt_path = DETAIL_DIR / f"question_{qid}.txt"

            html_path.write_text(html, encoding="utf-8")
            txt_path.write_text(text, encoding="utf-8")

            print(f"Đã lưu HTML: {html_path}")
            print(f"Đã lưu TXT: {txt_path}")

        except Exception as e:
            print(f"Lỗi khi crawl câu {qid}: {e}")

def main():
    ensure_dirs()

    result_url = input("Nhập link kết quả STUDY4: ").strip()

    if not result_url:
        print("Bạn chưa nhập link kết quả.")
        return

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = context.new_page()

        print("Đang mở trang kết quả...")
        page.goto(result_url, wait_until="networkidle")
        page.wait_for_timeout(3000)

        html, _ = save_page(page)

        answers = parse_answers_from_html(html)

        if not answers:
            print("Không parse được câu hỏi nào.")
            print("Hãy kiểm tra lại data/raw_result.html.")
            context.close()
            return

        save_answers_json(answers)
        save_answers_csv(answers)

        crawl_wrong_details(page, answers)

        context.close()

    print("\nHoàn tất crawl kết quả + chi tiết câu sai.")


if __name__ == "__main__":
    main()