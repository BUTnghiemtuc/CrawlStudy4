# STUDY4 Mistake Crawler & Quizlet Flashcard Pipeline

Hệ thống crawl kết quả làm bài, tải chi tiết các câu làm sai, sử dụng AI (GPT-4o-mini/DeepSeek) để tự động lọc và dịch từ vựng, cuối cùng tự động tạo học phần Flashcard trên Quizlet.

---

## 📌 Các Tính Năng Chính
1. **Quản lý đăng nhập tự động**: Lưu session đăng nhập bằng Chrome Profile thực tế thông qua Playwright, hạn chế việc bị chặn/hỏi captcha của STUDY4 và Quizlet.
2. **Crawl kết quả tổng quan**: Tải toàn bộ đáp án của bài làm, phân loại theo Part.
3. **Crawl chi tiết câu hỏi**:
   - Truy cập trang chi tiết từng câu làm sai.
   - Tự động click nút **"Giải thích chi tiết đáp án"** để lấy phần nội dung giải thích đầy đủ.
   - Lưu lại cả file dạng `.html` và `.txt` cho từng câu phục vụ lưu trữ ngoại tuyến.
4. **Trích xuất từ vựng bằng AI (`extract_vocab`)**:
   - Quét qua toàn bộ nội dung câu để tìm từ vựng tiềm năng.
   - Sử dụng LLM (mặc định là `gpt-4o-mini` hoặc `deepseek-v4-flash` qua OpenRouter) để lọc ra tối đa 3 cụm từ/collocation/từ vựng business đáng học nhất trong mỗi câu và dịch nghĩa tiếng Việt sát ngữ cảnh nhất.
   - Xuất kết quả ra file `data/vocabulary.csv`.
5. **Đồng bộ hóa & Tạo dữ liệu nhập**: Tự động chuẩn bị file `data/quizlet_import.txt` phân tách bằng tab.
6. **Tự động hóa Quizlet (`quizlet_auto`)**:
   - Sử dụng Playwright điều khiển Chrome thật để đăng nhập và truy cập trang tạo học phần Quizlet.
   - Tự động xóa bản nháp cũ để bắt đầu sạch sẽ.
   - Điền Tiêu đề và Mô tả học phần.
   - Mở giao diện nhập liệu dạng văn bản, paste toàn bộ danh sách từ vựng đã trích xuất, cấu hình dấu phân cách (Tab và Dòng mới).
   - Tự động chờ Quizlet phân tích cú pháp dữ liệu thành công rồi nhấn **Tạo và ôn luyện**.
   - Lưu link học phần Quizlet đã tạo vào `data/flashcard_link.csv`.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
CRAWL_STUDY4/
├── main.py                     # Script chạy toàn bộ pipeline tự động từ đầu đến cuối
├── requierments.txt            # Danh sách thư viện cần cài đặt
├── study4_browser_profile/     # Thư mục lưu session đăng nhập STUDY4 (tự sinh ra)
├── data/                       # Thư mục chứa dữ liệu kết quả (tự sinh ra)
│   ├── details/                # Chứa chi tiết HTML/TXT từng câu sai
│   ├── raw_result.html         # HTML trang kết quả tổng quan
│   ├── raw_result.txt          # Văn bản trang kết quả tổng quan
│   ├── answer_list.json        # Dữ liệu đáp án dạng JSON
│   ├── questions_basic.csv     # Bảng tổng hợp tất cả câu hỏi
│   ├── wrong_questions.csv     # Bảng tổng hợp các câu làm sai
│   ├── vocabulary.csv          # Từ vựng & dịch nghĩa do AI trích xuất
│   ├── quizlet_import.txt      # Định dạng text dạng tab để import vào Quizlet
│   ├── flashcard_link.csv      # Lưu URL học phần Quizlet đã tạo thành công
│   └── final.txt               # File tổng hợp giải thích tất cả câu sai
└── scripts/                    # Các script thực thi theo từng bước
    ├── auth.py                 # Lưu session đăng nhập STUDY4
    ├── crawl_result.py         # Crawl kết quả & chi tiết câu hỏi
    ├── extract_result.py       # Chuyển đổi kết quả thô sang định dạng bảng
    ├── filter_wrong.py         # Lọc danh sách câu làm sai
    ├── extract_vocab.py        # Dùng AI để trích xuất từ vựng từ câu sai
    ├── make_quizlet_import.py  # Tạo file txt định dạng tab để import
    └── quizlet_auto.py         # Tự động hóa tạo học phần trên Quizlet
```

---

## 🛠️ Yêu Cầu Hệ Thống & Cài Đặt

### 1. Tạo môi trường ảo và kích hoạt
Mở terminal tại thư mục dự án và chạy lệnh:
```bash
python3 -m venv .crawlStudy4
source .crawlStudy4/bin/activate
```

### 2. Cài đặt các thư viện cần thiết
```bash
pip install -r requierments.txt
```

### 3. Cài đặt driver cho Playwright
Hệ thống sử dụng Playwright để điều khiển trình duyệt Chrome thực tế:
```bash
playwright install chrome chromium
```

### 4. Cấu hình khóa API cho AI
Tạo file `.env` tại thư mục gốc của dự án và điền khóa API của bạn:
```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

---

## 🚀 Hướng Dẫn Sử Dụng Chi Tiết

### Bước 1: Đăng nhập STUDY4 & Quizlet (Chỉ cần làm lần đầu)
1. **Đăng nhập STUDY4:** Chạy lệnh sau để bật trình duyệt lên và đăng nhập vào tài khoản STUDY4 của bạn:
   ```bash
   python scripts/auth.py
   ```
   Sau khi đăng nhập xong trên giao diện Chrome và thấy ảnh đại diện của bạn, hãy quay lại terminal nhấn **Enter** để lưu session.

2. **Đăng nhập Quizlet:** Chạy lệnh sau để mở trình duyệt lưu session Quizlet:
   ```bash
   python scripts/quizlet_auto.py
   ```
   *Lưu ý:* Khi trình duyệt bật lên, hãy đăng nhập tài khoản Quizlet của bạn. Sau khi đăng nhập hoàn tất và thấy trang chủ Quizlet, bạn có thể tắt trình duyệt. Bước này giúp lưu cookie đăng nhập Quizlet vào profile Chrome dùng chung.

### Bước 2: Chạy toàn bộ quy trình tự động
Chạy file điều phối chính:
```bash
python main.py
```

Khi Terminal hiển thị yêu cầu:
```text
Nhập link kết quả STUDY4: 
```
Hãy dán link kết quả bài thi của bạn trên STUDY4 (Ví dụ: `https://study4.com/tests/results/34915569/`) và nhấn **Enter**.

Hệ thống sẽ chạy liên mạch toàn bộ pipeline:
1. Crawl trang kết quả & lời giải chi tiết của từng câu sai.
2. Trích xuất từ vựng và dịch nghĩa bằng mô hình AI.
3. Chuyển đổi dữ liệu và tự động khởi động Chrome để nhập liệu, cấu hình phân tách và bấm **Tạo học phần** trên Quizlet.
4. Lưu link học phần mới tạo và hoàn tất.

---

## 📊 Mô Tả Các File Kết Quả Đầu Ra (Thư mục `data/`)

| File / Thư mục | Định dạng | Mô tả chi tiết |
| :--- | :--- | :--- |
| `data/flashcard_link.csv` | CSV | Lưu link học phần Quizlet đã được tạo thành công trực tiếp (ví dụ: `https://quizlet.com/1189847919/learn`). |
| `data/quizlet_import.txt` | Văn bản | Định dạng dữ liệu được phân tách bằng dấu `Tab` và `Dòng mới` để sẵn sàng import vào Quizlet. |
| `data/vocabulary.csv` | CSV | Chứa danh sách từ vựng do AI trích xuất kèm dịch nghĩa tiếng Việt (`meaning_vi`), phân loại (`type`), lý do chọn (`reason`), và câu chứa từ đó (`source_sentence`). |
| `data/final.txt` | Văn bản | File tổng hợp toàn bộ phần dịch và giải thích chi tiết của các câu làm sai. Thích hợp để đọc ôn tập nhanh. |
| `data/wrong_questions.csv` | CSV | Danh sách tất cả câu làm sai gồm Part, đáp án của bạn, đáp án đúng và link chi tiết câu hỏi. |
| `data/questions_basic.csv` | CSV | Danh sách toàn bộ các câu hỏi trong đề cùng trạng thái Đúng/Sai. |

---

## ⚠️ Lưu ý khi sử dụng
- **Profile đăng nhập:** Profile đăng nhập được lưu tại `study4_browser_profile`. Tránh xóa thư mục này trừ khi bạn muốn đăng nhập lại tài khoản khác.
- **Tránh can thiệp khi chạy:** Trong lúc `quizlet_auto.py` đang điều khiển trình duyệt để tạo học phần, bạn vui lòng không tắt trình duyệt đó hoặc can thiệp click chuột cho đến khi terminal in ra thông báo `Hoàn tất. Nhấn Enter để đóng trình duyệt...`.
- **Nếu Google Block:** Nếu đăng nhập bằng Google bị chặn, hãy thiết lập mật khẩu trực tiếp cho tài khoản STUDY4/Quizlet để đăng nhập thủ công bằng email & password trong trình duyệt tự động của bước setup đầu tiên.
