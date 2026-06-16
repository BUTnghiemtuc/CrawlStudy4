import subprocess
import sys
from pathlib import Path


LOGIN_PROFILE = Path("study4_browser_profile")
DATA_DIR = Path("data")


def run_script(script_path: str):
    print("\n" + "=" * 70)
    print(f"Đang chạy: {script_path}")
    print("=" * 70)

    result = subprocess.run([sys.executable, script_path])

    if result.returncode != 0:
        print(f"\nScript bị lỗi: {script_path}")
        print("Pipeline đã dừng.")
        sys.exit(result.returncode)


def check_project_structure():
    required_files = [
        "scripts/auth.py",
        "scripts/crawl_result.py",
        "scripts/extract_result.py",
        "scripts/filter_wrong.py",
        "scripts/extract_vocab.py",
    ]

    missing_files = []

    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("Thiếu các file sau:")
        for file_path in missing_files:
            print(f"- {file_path}")
        sys.exit(1)


def merge_detail_txt_files():
    details_dir = Path("data/details")
    final_file = Path("data/final.txt")

    if not details_dir.exists():
        print("\nThư mục data/details không tồn tại.")
        return

    import re
    def get_question_number(path: Path):
        match = re.search(r"question_(\d+)\.txt", path.name)
        return int(match.group(1)) if match else 999999

    txt_files = sorted(details_dir.glob("question_*.txt"), key=get_question_number)

    if not txt_files:
        print("\nKhông tìm thấy file .txt nào trong data/details để gộp.")
        return

    print(f"\nĐang gộp {len(txt_files)} file .txt thành {final_file}...")

    with open(final_file, "w", encoding="utf-8") as outfile:
        for i, filepath in enumerate(txt_files):
            try:
                content = filepath.read_text(encoding="utf-8")
                outfile.write(content)
                if i < len(txt_files) - 1:
                    outfile.write("\n\n" + "="*80 + "\n\n")
            except Exception as e:
                print(f"Lỗi khi đọc file {filepath.name}: {e}")

    print(f"Đã gộp xong vào: {final_file}")


def main():
    print("STUDY4 Mistake Crawler Pipeline")

    check_project_structure()
    DATA_DIR.mkdir(exist_ok=True)

    if not LOGIN_PROFILE.exists():
        print("\nChưa có profile đăng nhập STUDY4.")
        print("Cần đăng nhập STUDY4 trước.")
        run_script("scripts/auth.py")
    else:
        print(f"\nĐã tìm thấy profile đăng nhập: {LOGIN_PROFILE}")

    run_script("scripts/crawl_result.py")
    run_script("scripts/extract_result.py")
    run_script("scripts/filter_wrong.py")
    run_script("scripts/extract_vocab.py")

    merge_detail_txt_files()

    print("\n" + "=" * 70)
    print("Pipeline hoàn tất.")
    print("=" * 70)

    print("\nCác file kết quả:")
    print("- data/raw_result.html")
    print("- data/raw_result.txt")
    print("- data/answer_list.json")
    print("- data/questions_basic.csv")
    print("- data/wrong_questions.csv")
    print("- data/details/question_*.txt")
    print("- data/details/question_*.html")
    print("- data/vocab_basic.csv")
    print("- data/final.txt (Đã gộp từ details/*.txt)")


if __name__ == "__main__":
    main()