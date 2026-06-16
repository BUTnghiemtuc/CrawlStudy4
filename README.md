# STUDY4 Mistake Crawler Pipeline

Hệ thống crawl kết quả làm bài, chi tiết câu sai và tự động trích xuất từ vựng từ các bài kiểm tra trên hệ thống STUDY4 (đặc biệt là các bài thi thử TOEIC).

---

## 📌 Các Tính Năng Chính
1. **Quản lý đăng nhập tự động**: Lưu session đăng nhập bằng Chrome Profile thực tế thông qua Playwright, hạn chế việc bị chặn/hỏi captcha.
2. **Crawl kết quả tổng quan**: Tải toàn bộ đáp án của bài làm, phân loại theo Part.
3. **Crawl chi tiết câu sai**:
   - Truy cập trang chi tiết từng câu làm sai.
   - Tự động click nút **"Giải thích chi tiết đáp án"** để lấy phần nội dung giải thích đầy đủ.
   - Lưu lại cả file dạng `.html` và `.txt` cho từng câu.
4. **Trích xuất từ vựng tự động (`extract_vocab`)**:
   - Quét qua toàn bộ nội dung câu sai để tìm từ vựng tiếng Anh.
   - Lọc bỏ các từ thông dụng (Stopwords) tiếng Anh và tiếng Việt.
   - Thống kê tần suất xuất hiện và liệt kê danh sách câu hỏi chứa từ đó vào file `vocab_basic.csv`.
5. **Gộp dữ liệu tự động**: Gộp tất cả các file giải thích chi tiết dạng `.txt` thành một file duy nhất `final.txt` theo thứ tự câu hỏi để tiện ôn tập.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
CRAWL_STUDY4/
├── main.py                     # Script chạy toàn bộ pipeline
├── requierments.txt            # Danh sách thư viện cần thiết
├── study4_browser_profile/     # Thư mục lưu session đăng nhập (tự sinh ra)
├── data/                       # Thư mục chứa dữ liệu kết quả (tự sinh ra)
│   ├── details/                # Chứa chi tiết HTML/TXT từng câu sai
│   ├── raw_result.html         # HTML trang kết quả tổng quan
│   ├── raw_result.txt          # Văn bản trang kết quả tổng quan
│   ├── answer_list.json        # Dữ liệu đáp án dạng JSON
│   ├── questions_basic.csv     # Bảng tổng hợp tất cả câu hỏi
│   ├── wrong_questions.csv     # Bảng tổng hợp các câu làm sai
│   ├── vocab_basic.csv         # Danh sách từ vựng trích xuất được
│   └── final.txt               # File tổng hợp giải thích tất cả câu sai
└── scripts/                    # Các script thực thi riêng lẻ
    ├── auth.py                 # Đăng nhập & lưu session
    ├── crawl_result.py         # Crawl kết quả & chi tiết câu sai
    ├── extract_result.py       # Xuất JSON sang CSV
    ├── filter_wrong.py         # Lọc danh sách câu sai
    └── extract_vocab.py        # Trích xuất từ vựng từ câu sai
```

---

## 🛠️ Yêu Cầu Hệ Thống & Cài Đặt

### 1. Cài đặt các thư viện cần thiết
Mở terminal tại thư mục dự án và chạy lệnh:
```bash
pip install -r requierments.txt
```

### 2. Cài đặt driver cho Playwright
Hệ thống sử dụng Playwright để tự động hoá trình duyệt:
```bash
playwright install chromium
```

---

## 🚀 Hướng Dẫn Sử Dụng

### Bước 1: Chạy toàn bộ quy trình qua file `main.py`
Cách đơn giản nhất là chạy trực tiếp file điều phối chính:
```bash
python main.py
```

### Bước 2: Đăng nhập STUDY4 (Chỉ cần làm lần đầu)
Nếu hệ thống chưa tìm thấy thư mục `study4_browser_profile`, trình duyệt Chrome sẽ tự động bật lên.
1. Đăng nhập vào tài khoản STUDY4 của bạn trong cửa sổ trình duyệt đó.
2. Quay lại Terminal và nhấn **Enter** để lưu session. Các lần chạy sau sẽ không cần đăng nhập lại.

### Bước 3: Nhập link kết quả cần crawl
Khi Terminal hiển thị yêu cầu:
```text
Nhập link kết quả STUDY4: 
```
Hãy dán link kết quả bài thi của bạn trên STUDY4 (ví dụ: `https://study4.com/tests/results/.../`) và nhấn **Enter**. 

Hệ thống sẽ tự động thực hiện tất cả các bước:
- Tải trang kết quả chính.
- Duyệt qua từng câu sai và tải chi tiết lời giải giải thích.
- Tạo file CSV thống kê.
- Trích xuất từ vựng tiềm năng.
- Gộp các file chi tiết thành `data/final.txt`.

---

## 📊 Mô Tả Các File Kết Quả Đầu Ra (Thư mục `data/`)

| File / Thư mục | Định dạng | Mô tả chi tiết |
| :--- | :--- | :--- |
| `data/final.txt` | Văn bản | File tổng hợp toàn bộ phần dịch và giải thích chi tiết của các câu làm sai, xếp theo thứ tự từ bé đến lớn. Thích hợp để đọc ôn tập nhanh. |
| `data/vocab_basic.csv` | CSV | Bảng danh sách từ vựng trích xuất từ các câu sai kèm tần suất (`frequency`) và danh sách ID câu hỏi tương ứng (`question_ids`). Có sẵn cột trống để bạn tự điền nghĩa tiếng Việt (`meaning_vi`), từ loại (`part_of_speech`), và ghi chú. |
| `data/wrong_questions.csv` | CSV | Danh sách tất cả câu làm sai gồm Part, đáp án của bạn, đáp án đúng và link chi tiết câu hỏi. |
| `data/questions_basic.csv` | CSV | Danh sách toàn bộ các câu hỏi trong đề cùng trạng thái Đúng/Sai. |
| `data/details/` | Thư mục | Chứa các file `.html` (trang chi tiết nhúng gốc) và `.txt` (văn bản thô chứa giải thích đáp án) của từng câu sai. |
| `data/answer_list.json` | JSON | Dữ liệu cấu trúc gốc thu được sau khi phân tích trang kết quả. |

---

## ⚠️ Lưu ý khi sử dụng
- Hãy giữ nguyên cấu trúc thư mục dự án để các script tìm đúng file trung gian.
- Nếu gặp lỗi đăng nhập bị Google chặn (khi đăng nhập bằng tài khoản Google liên kết), bạn nên cài mật khẩu trực tiếp cho tài khoản STUDY4 để đăng nhập bằng Email/Mật khẩu hoặc quét mã QR.
- Không xoá thư mục `study4_browser_profile` trừ khi bạn muốn đăng nhập lại với một tài khoản khác.
