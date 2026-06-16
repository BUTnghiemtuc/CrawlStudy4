from pathlib import Path
import csv
import re
import socket
from playwright.sync_api import sync_playwright


QUIZLET_IMPORT_FILE = Path("data/quizlet_import.txt")
FINAL_TXT_FILE = Path("data/final.txt")
FLASHCARD_LINK_CSV = Path("data/flashcard_link.csv")
BROWSER_PROFILE_DIR = Path("browser_profile")

CREATE_SET_URL = "https://quizlet.com/create-set"
DEFAULT_TITLE = "TOEIC Vocabulary - Auto Generated"


# =========================
# ĐỌC FILE
# =========================

def read_flashcards_text() -> str:
    if not QUIZLET_IMPORT_FILE.exists():
        raise FileNotFoundError(
            f"Chưa có file {QUIZLET_IMPORT_FILE}. "
            "Hãy chạy scripts/make_quizlet_import.py trước."
        )

    content = QUIZLET_IMPORT_FILE.read_text(encoding="utf-8").strip()

    if not content:
        raise ValueError(f"File {QUIZLET_IMPORT_FILE} đang rỗng.")

    return content


def extract_test_name() -> str:
    if not FINAL_TXT_FILE.exists():
        return DEFAULT_TITLE

    try:
        lines = [
            line.strip()
            for line in FINAL_TXT_FILE.read_text(encoding="utf-8").splitlines()
        ]

        for idx, line in enumerate(lines):
            if line.startswith("Đáp án chi tiết"):
                for next_line in lines[idx + 1:]:
                    if next_line:
                        return next_line

    except Exception as e:
        print(f"[Warning] Lỗi khi đọc tên bài test từ {FINAL_TXT_FILE}: {e}")

    return DEFAULT_TITLE


# =========================
# HELPER
# =========================

def wait_manual_checkpoint(page, message: str) -> None:
    print("\n" + "=" * 70)
    print(message)
    print("URL hiện tại:", page.url)
    print("=" * 70)
    input("Xử lý xong trên trình duyệt thì quay lại terminal và nhấn Enter...")


def browser_debug_port_is_open(host: str = "localhost", port: int = 9222) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host, port)) == 0


def safe_click(page, selectors, timeout=3000, label="") -> bool:
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.click(timeout=timeout)
            print(f"Đã click {label}: {selector}")
            return True
        except Exception:
            continue

    return False


def click_button_by_text(page, texts, timeout=3000) -> bool:
    for text in texts:
        try:
            btn = page.get_by_role("button", name=re.compile(re.escape(text), re.I)).first
            btn.wait_for(state="visible", timeout=timeout)
            btn.click(timeout=timeout)
            print(f"Đã click button: {text}")
            return True
        except Exception:
            continue

    return False


def click_text_exact(page, texts, timeout=3000) -> bool:
    for text in texts:
        try:
            locator = page.get_by_text(text, exact=True).first
            locator.wait_for(state="visible", timeout=timeout)
            locator.click(timeout=timeout)
            print(f"Đã click text: {text}")
            return True
        except Exception:
            continue

    return False


def clear_and_type_active(page, value: str) -> None:
    """
    Dùng cho các ô kiểu contenteditable của Quizlet.
    Click vào ô trước, rồi gọi hàm này.
    """
    page.keyboard.press("Control+A")
    page.keyboard.press("Backspace")
    page.keyboard.insert_text(value)


# =========================
# LOGIC QUIZLET
# =========================

def open_create_set_page(page) -> None:
    print("Đang mở trang tạo học phần Quizlet...")

    page.goto(CREATE_SET_URL, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    # Nếu bị login / Cloudflare thì cho xử lý tay
    if "login" in page.url.lower():
        wait_manual_checkpoint(
            page,
            "Quizlet yêu cầu đăng nhập. Bạn hãy đăng nhập thủ công."
        )
        page.goto(CREATE_SET_URL, wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

    # Kiểm tra đã vào đúng trang chưa
    if not page.get_by_text("Tạo một học phần mới").first.is_visible(timeout=5000):
        wait_manual_checkpoint(
            page,
            "Nếu đang gặp Cloudflare hoặc chưa vào trang tạo học phần, hãy xử lý thủ công rồi nhấn Enter."
        )


def handle_draft_popup(page) -> None:
    print("Kiểm tra popup bản nháp...")

    page.wait_for_timeout(1500)

    # 1. Kiểm tra popup toast ở góc dưới trái (Chúng tôi đã khôi phục bản nháp...)
    try:
        discard_draft_btn = page.locator("button:has-text('Tạo học phần mới'), button:has-text('Create new set')").first
        if discard_draft_btn.is_visible():
            discard_draft_btn.click()
            print("Đã click 'Tạo học phần mới' / 'Create new set' (xóa bản nháp cũ để nhập mới)")
            page.wait_for_timeout(1000)
            return
    except Exception:
        pass

    # 2. Kiểm tra popup modal đè giữa màn hình
    click_button_by_text(
        page,
        [
            "Xóa bản nháp",
            "Discard draft",
            "Bắt đầu lại",
            "Start over",
            "Tạo học phần mới",
        ],
        timeout=1200,
    )


def fill_title(page, title: str) -> None:
    """
    Điền đúng ô Tiêu đề.
    Không click vào label 'Tiêu đề' nữa vì label bị input che pointer event.
    """
    print("Đang điền đúng ô Tiêu đề...")

    selectors = [
        "input[aria-label='Tiêu đề']",
        "input[aria-label*='Tiêu đề']",
        "input[placeholder*='Nhập tiêu đề']",
        "input[placeholder*='tiêu đề' i]",
        "input[aria-label='Title']",
        "input[aria-label*='Title']",
        "input[placeholder*='title' i]",
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=5000)
            locator.fill(title, timeout=5000)
            print(f"Đã điền tiêu đề bằng selector: {selector}")
            return
        except Exception:
            continue

    wait_manual_checkpoint(
        page,
        "Không tự điền được tiêu đề. Bạn hãy tự nhập vào ô Tiêu đề."
    )


def fill_description(page, description: str) -> None:
    """
    Điền đúng ô Thêm mô tả.
    """
    if not description:
        return

    print("Đang điền đúng ô Thêm mô tả...")

    selectors = [
        "textarea[placeholder='Thêm mô tả...']",
        "textarea[placeholder*='Thêm mô tả']",
        "textarea[aria-label*='Thêm mô tả']",
        "textarea[placeholder*='description' i]",
        "textarea[aria-label*='description' i]",
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=5000)
            locator.fill(description, timeout=5000)
            print(f"Đã điền mô tả bằng selector: {selector}")
            return
        except Exception:
            continue

    print("[Warning] Không tự điền được mô tả. Bỏ qua vì mô tả không bắt buộc.")

def open_import_page_or_dialog(page) -> None:
    """
    Bấm đúng nút + Nhập ở khu vực thêm nội dung.
    Không dùng get_by_role quá rộng vì có thể bắt nhầm nút Nhập khác.
    """
    print("Đang bấm nút + Nhập...")

    selectors = [
        "button:has-text('+ Nhập')",
        "button:has-text('Nhập')",
        "button:has-text('+ Import')",
        "button:has-text('Import')",
        "button[aria-label='Nhập']",
        "button[aria-label='Import']",
        "button[aria-label*='Nhập']",
        "button[aria-label*='Import']",
        "text=+ Nhập",
        "text=+ Import",
    ]

    for selector in selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=5000)
            locator.click(timeout=5000)
            print(f"Đã click nút + Nhập bằng selector: {selector}")
            page.wait_for_timeout(4000)
            return
        except Exception:
            continue

    wait_manual_checkpoint(
        page,
        "Không tự bấm được nút + Nhập. Bạn hãy tự bấm nút + Nhập trên Quizlet."
    )

    page.wait_for_timeout(4000)


def paste_flashcards_to_import_area(page, flashcards_text: str) -> None:
    """
    Màn hình Import của Quizlet có 1 ô textarea lớn.
    Cần click/focus vào ô đó trước, sau đó mới paste dữ liệu.
    """
    print("Đang paste nội dung flashcards vào ô Nhập dữ liệu...")

    page.wait_for_timeout(2000)

    # Selector đúng với màn hình trong ảnh của bạn
    selectors = [
        ".ReactModalPortal textarea",
        "textarea[placeholder*='Từ 1']",
        "textarea[placeholder*='Định nghĩa']",
        ".ReactModalPortal [role='textbox']",
        ".ReactModalPortal [contenteditable='true']",
    ]

    # Cách 1: click textarea lớn rồi fill trực tiếp
    for selector in selectors:
        try:
            box = page.locator(selector).first
            box.wait_for(state="visible", timeout=5000)

            # Quan trọng: click vào ô trước
            box.click(timeout=5000)
            page.wait_for_timeout(500)

            # Xóa nội dung mẫu nếu có
            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.wait_for_timeout(300)

            # Paste nội dung
            box.fill(flashcards_text, timeout=10000)

            # Bắn input/change để Quizlet cập nhật phần xem trước
            box.evaluate(
                """
                el => {
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));
                }
                """
            )

            page.wait_for_timeout(1500)
            print(f"Đã paste flashcards vào ô import bằng selector: {selector}")
            return

        except Exception as e:
            print(f"[Debug] Không paste được bằng selector {selector}: {e}")
            continue

    # Cách 2: nếu fill không ăn, dùng keyboard.insert_text sau khi click
    for selector in selectors:
        try:
            box = page.locator(selector).first
            box.wait_for(state="visible", timeout=5000)

            box.click(timeout=5000)
            page.wait_for_timeout(500)

            page.keyboard.press("Control+A")
            page.keyboard.press("Backspace")
            page.wait_for_timeout(300)

            page.keyboard.insert_text(flashcards_text)
            page.wait_for_timeout(1500)

            print(f"Đã paste flashcards bằng keyboard vào selector: {selector}")
            return

        except Exception as e:
            print(f"[Debug] Không paste keyboard được bằng selector {selector}: {e}")
            continue

    # Cách 3: ép bằng JavaScript nếu Playwright không fill được
    try:
        success = page.evaluate(
            """
            (text) => {
                const textareas = Array.from(document.querySelectorAll('textarea'));

                if (textareas.length === 0) {
                    return false;
                }

                // Chọn textarea lớn nhất trên màn hình
                textareas.sort((a, b) => {
                    const ra = a.getBoundingClientRect();
                    const rb = b.getBoundingClientRect();
                    return (rb.width * rb.height) - (ra.width * ra.height);
                });

                const el = textareas[0];
                el.focus();
                el.click();

                const nativeSetter = Object.getOwnPropertyDescriptor(
                    window.HTMLTextAreaElement.prototype,
                    'value'
                ).set;

                nativeSetter.call(el, text);

                el.dispatchEvent(new Event('input', { bubbles: true }));
                el.dispatchEvent(new Event('change', { bubbles: true }));

                return true;
            }
            """,
            flashcards_text,
        )

        if success:
            print("Đã paste flashcards bằng JavaScript vào textarea lớn.")
            page.wait_for_timeout(1500)
            return

    except Exception as e:
        print(f"[Debug] JavaScript paste thất bại: {e}")

    wait_manual_checkpoint(
        page,
        "Không tự paste được. Bạn hãy click vào ô Nhập dữ liệu rồi paste nội dung trong data/quizlet_import.txt."
    )


def choose_import_separators(page) -> None:
    """
    Bắt buộc chọn đúng:
    - Giữa thuật ngữ và định nghĩa: Tab
    - Giữa các thẻ: Dòng mới

    Đây là bước quan trọng để Quizlet hiểu mỗi dòng là 1 flashcard:
    word<TAB>meaning
    word<TAB>meaning
    """

    print("Đang chọn dấu phân cách: Tab và Dòng mới...")

    page.wait_for_timeout(1000)

    # 1. Chọn Tab cho: Giữa thuật ngữ và định nghĩa
    tab_selectors = [
        "label:has-text('Tab')",
        "text=Tab",
    ]

    tab_ok = False

    for selector in tab_selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=3000)
            locator.click(timeout=3000)
            print("Đã chọn: Giữa thuật ngữ và định nghĩa = Tab")
            tab_ok = True
            break
        except Exception as e:
            print(f"[Debug] Chưa chọn được Tab bằng {selector}: {e}")

    # 2. Chọn Dòng mới cho: Giữa các thẻ
    newline_selectors = [
        "label:has-text('Dòng mới')",
        "text=Dòng mới",
        "label:has-text('New line')",
        "text=New line",
        "label:has-text('Newline')",
        "text=Newline",
    ]

    newline_ok = False

    for selector in newline_selectors:
        try:
            locator = page.locator(selector).first
            locator.wait_for(state="visible", timeout=3000)
            locator.click(timeout=3000)
            print("Đã chọn: Giữa các thẻ = Dòng mới")
            newline_ok = True
            break
        except Exception as e:
            print(f"[Debug] Chưa chọn được Dòng mới bằng {selector}: {e}")

    if not tab_ok:
        print("[Warning] Không tự chọn được Tab. Bạn hãy kiểm tra radio Tab đã được tích chưa.")

    if not newline_ok:
        print("[Warning] Không tự chọn được Dòng mới. Bạn hãy kiểm tra radio Dòng mới đã được tích chưa.")

    page.wait_for_timeout(1000)


def click_import_confirm(page) -> None:
    """
    Bấm nút Nhập ở góc dưới bên phải của màn hình Import.
    """
    print("Đang bấm nút Nhập để xác nhận import...")

    page.wait_for_timeout(2000)

    selectors = [
        ".ReactModalPortal button[data-testid='assembly-button-primary']",
        "[role='dialog'] button[data-testid='assembly-button-primary']",
        ".ReactModalPortal button:has-text('Nhập')",
        ".ReactModalPortal button:has-text('Import')",
        "[role='dialog'] button:has-text('Nhập')",
        "[role='dialog'] button:has-text('Import')",
    ]

    for selector in selectors:
        try:
            button = page.locator(selector).first
            
            # Đợi button xuất hiện và visible
            button.wait_for(state="visible", timeout=5000)
            
            # Đợi button được enable (tối đa 15 giây vì parse danh sách dài có thể lâu)
            for i in range(15):
                if button.is_enabled():
                    break
                print(f"[Debug] Nút Nhập đang disabled (đang xử lý dữ liệu), đợi 1 giây... ({i+1}/15)")
                page.wait_for_timeout(1000)

            button.click(timeout=5000)
            print(f"Đã bấm nút Nhập bằng selector: {selector}")
            page.wait_for_timeout(4000)
            return

        except Exception as e:
            print(f"[Debug] Chưa bấm được {selector}: {e}")
            continue

    wait_manual_checkpoint(
        page,
        "Không tự bấm được nút Nhập. Bạn hãy bấm nút Nhập ở góc dưới bên phải."
    )

    page.wait_for_timeout(4000)

def scroll_to_bottom(page) -> None:
    print("Đang kéo xuống cuối trang...")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)


def click_create_final(page) -> None:
    """
    Sau khi import xong, kéo xuống cuối rồi bấm Tạo / Tạo và ôn luyện.
    Trên ảnh của bạn nút ở góc phải trên là 'Tạo' hoặc 'Tạo và ôn luyện'.
    """
    print("Đang bấm nút Tạo cuối cùng...")

    scroll_to_bottom(page)

    if click_button_by_text(
        page,
        [
            "Tạo và ôn luyện",
            "Tạo học phần",
            "Tạo",
            "Create and practice",
            "Create set",
            "Create",
        ],
        timeout=6000,
    ):
        page.wait_for_timeout(3000)
        return

    # Nếu kéo xuống làm mất nút sticky, thử kéo lên đầu và bấm nút trên góc phải
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)

    if click_button_by_text(
        page,
        [
            "Tạo và ôn luyện",
            "Tạo học phần",
            "Tạo",
            "Create and practice",
            "Create set",
            "Create",
        ],
        timeout=6000,
    ):
        page.wait_for_timeout(3000)
        return

    wait_manual_checkpoint(
        page,
        "Không tự bấm được nút Tạo. Bạn hãy kéo xuống cuối hoặc lên góc phải và bấm Tạo thủ công."
    )


def get_and_save_flashcard_link(page) -> str:
    print("Đang chờ Quizlet tạo xong học phần...")

    FLASHCARD_LINK_CSV.parent.mkdir(parents=True, exist_ok=True)

    new_url = ""

    for _ in range(60):
        current_url = page.url

        if "quizlet.com" in current_url and "create-set" not in current_url:
            new_url = current_url
            break

        page.wait_for_timeout(1000)

    if not new_url:
        wait_manual_checkpoint(
            page,
            "Nếu học phần đã được tạo, hãy mở đúng trang học phần mới rồi nhấn Enter."
        )
        new_url = page.url

    with FLASHCARD_LINK_CSV.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["link_flashcard"])
        writer.writerow([new_url])

    print(f"Link học phần mới: {new_url}")
    print(f"Đã lưu link vào: {FLASHCARD_LINK_CSV}")

    return new_url


# =========================
# MAIN FLOW
# =========================

def create_quizlet_set(title: str, description: str = "") -> str:
    flashcards_text = read_flashcards_text()

    BROWSER_PROFILE_DIR.mkdir(exist_ok=True)

    use_cdp = browser_debug_port_is_open()

    with sync_playwright() as p:
        if use_cdp:
            print("[CDP Mode] Đang kết nối Chrome debugging ở cổng 9222...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()

        else:
            print("[Normal Mode] Đang mở Chrome với profile riêng...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=str(BROWSER_PROFILE_DIR),
                channel="chrome",
                headless=False,
                slow_mo=120,
                viewport={
                    "width": 1400,
                    "height": 900,
                },
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                ],
            )

            context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
            )

            page = context.new_page()

        try:
            # 1. Mở trang tạo học phần
            open_create_set_page(page)

            # 2. Nếu có popup bản nháp thì xử lý
            handle_draft_popup(page)

            # 3. Điền đúng ô tiêu đề
            fill_title(page, title)

            # 4. Điền đúng ô thêm mô tả
            fill_description(page, description)

            # 5. Bấm + Nhập
            open_import_page_or_dialog(page)

            # 6. Paste nội dung quizlet_import.txt
            paste_flashcards_to_import_area(page, flashcards_text)

            # 7. Chọn dấu phân cách nếu có
            choose_import_separators(page)

            # 8. Bấm Nhập để import, quay về trang tạo học phần
            click_import_confirm(page)

            # 9. Kéo xuống cuối và bấm Tạo / Tạo và ôn luyện
            click_create_final(page)

            # 10. Lưu link
            link = get_and_save_flashcard_link(page)

            print("\nHoàn tất.")
            return link

        finally:
            if use_cdp:
                print("CDP Mode: không tự đóng Chrome của bạn.")
            else:
                input("Nhấn Enter để đóng trình duyệt...")
                context.close()


if __name__ == "__main__":
    test_name = extract_test_name()

    print(f"Tiêu đề học phần: {test_name}")

    create_quizlet_set(
        title=test_name,
        description=f"Generated automatically for {test_name}",
    )