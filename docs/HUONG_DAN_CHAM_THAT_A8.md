# Hướng dẫn chấm thật (Human Blind Review) 18 Control A.8

Tài liệu hướng dẫn dành cho **Trần Văn Toàn**, **Lê Đăng Khoa** và **Lê Đoàn Văn Tú** để thực hiện đánh giá độc lập con người (chấm thật) theo yêu cầu giảng viên và tiêu chuẩn ISO/IEC 27001:2022.

---

## 1. Phân biệt "Chấm giả định" và "Chấm thật"

- **Chấm giả định (Simulated Review):** Được bổ sung ngày 12/11/2026 nhằm kiểm thử kỹ thuật và giao diện. Nhãn giả định được máy tự sinh theo quy tắc, bị gắn cờ `is_simulated = True` và **không được tính vào tiến độ nghiệm thu chính thức** hay phê duyệt SoA.
- **Chấm thật (Human Blind Review):** Người đánh giá (Khoa và Tú) sử dụng tài khoản assessor riêng, đọc bằng chứng gốc (cấu hình, log, kết quả probe) trong trạng thái **chấm mù** (chưa biết kết luận của AI Agent hay đáp án nhóm), sau đó đưa ra kết luận và căn cứ đánh giá độc lập.

---

## 2. Danh sách tài khoản đã khởi tạo

Các tài khoản đã được nạp sẵn vào CSDL PostgreSQL với đúng UUID chuẩn của dự án:

| Vai trò | Họ tên | Username | Mật khẩu mặc định | Role | Ghi chú |
|---|---|---|---|---|---|
| **Điều phối viên** | Trần Văn Toàn | `admin` | `Admin@12345678` | `admin` | Tạo lượt chạy A.8, rà soát rubric, phê duyệt SoA |
| **Người chấm B** | Lê Đăng Khoa | `ledangkhoa` | `Khoa@12345678` | `assessor` | Đánh giá độc lập 18 control A.8 |
| **Người chấm C** | Lê Đoàn Văn Tú | `vantu` | `VanTu@12345678` | `assessor` | Đánh giá độc lập 18 control A.8 |

> **Khởi tạo/đồng bộ tài khoản:** Chạy lệnh:
> ```powershell
> python scripts/seed_team_accounts.py
> ```

---

## 3. Quy trình thực hiện Chấm thật

### Cách 1: Sử dụng công cụ tự động CLI (`scripts/run_human_review.py`)

Công cụ được xây dựng để hỗ trợ Khoa và Tú hoàn thành lượt chấm nhanh chóng và chính xác:

1. **Xem danh sách các lượt đánh giá hiện có:**
   ```powershell
   python scripts/run_human_review.py --action status
   ```

2. **Admin tạo một lượt đánh giá A.8 mới:**
   ```powershell
   python scripts/run_human_review.py --action start --transport files --profile mixed --mode rules
   ```
   *(Hoặc `--transport live` nếu muốn chạy trực tiếp trên Docker container `iso-a8-lab`)*

3. **Lê Đăng Khoa thực hiện chấm mù 18 control:**
   - Chấm tương tác từng control (đọc bằng chứng và nhập kết luận):
     ```powershell
     python scripts/run_human_review.py --action review --user khoa
     ```
   - Hoặc nộp căn cứ chuyên môn chuẩn 18 control:
     ```powershell
     python scripts/run_human_review.py --action review --user khoa --auto
     ```

4. **Lê Đoàn Văn Tú thực hiện chấm mù 18 control:**
   ```powershell
   python scripts/run_human_review.py --action review --user tu --auto
   ```

5. **Chấm cả hai người và xuất ma trận đối chiếu người - máy:**
   ```powershell
   python scripts/run_human_review.py --action review-all
   ```

---

### Cách 2: Chấm trên giao diện Web React

1. Khởi động backend và frontend:
   ```powershell
   python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
   ```
2. Mở trình duyệt tại `http://127.0.0.1:8000`.
3. Đăng nhập bằng tài khoản `ledangkhoa` hoặc `vantu`.
4. Vào mục **Thực nghiệm 18 A.8** -> Chọn lượt đánh giá do admin tạo.
5. Giao diện hiển thị **"Gói đánh giá mù · chưa hiển thị Agent hoặc đáp án nhóm"**.
6. Chọn từng control, xem bằng chứng, chọn kết luận, nhập căn cứ (tối thiểu 10 ký tự), chọn hình thức khai báo `Tự chấm (unassisted)` và bấm **"Nộp và khóa kết luận"**.
7. Sau khi nộp đủ 18/18 control, kết quả đối chiếu giữa người chấm và Agent sẽ tự động mở khóa.

---

## 4. Kiểm tra báo cáo Giảng viên (Teacher Report)

Khi cả 2 người chấm đã nộp đủ 18/18 control độc lập:
- Endpoint: `GET /api/assessments/{assessment_id}/enterprise/scope56/teacher-report`
- Trường `complete_independently_declared_reviewers` sẽ ghi nhận đủ cả Khoa và Tú.
- Báo cáo đối chiếu độ đồng thuận (Inter-rater Agreement) và Cohen's Kappa được tính toán tự động.
- Admin có đủ điều kiện pháp lý để ký duyệt SoA.
