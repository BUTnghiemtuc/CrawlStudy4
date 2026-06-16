from playwright.sync_api import sync_playwright

USER_DATA_DIR = "study4_browser_profile"


def main():
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",      # dùng Chrome thật, không dùng Chromium mặc định
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
            ],
        )

        page = context.new_page()
        page.goto("https://study4.com/", wait_until="domcontentloaded")

        print("\nHãy đăng nhập STUDY4 trong cửa sổ Chrome vừa mở.")
        print("Nếu Google vẫn chặn, hãy thử đăng nhập bằng email/password STUDY4 nếu có.")
        input("Sau khi đăng nhập xong và thấy avatar/tài khoản trên STUDY4, nhấn Enter...")

        print("Đã lưu profile đăng nhập vào thư mục:", USER_DATA_DIR)
        context.close()


if __name__ == "__main__":
    main()