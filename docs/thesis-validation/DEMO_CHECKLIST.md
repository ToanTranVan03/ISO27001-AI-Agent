# DANH MỤC KIỂM TRA TRƯỚC KHI DEMO BẢO VỆ ĐỒ ÁN (DEMO CHECKLIST)

Tài liệu này giúp nhóm kiểm tra nhanh toàn bộ hạ tầng, dữ liệu mẫu và kịch bản thao tác trong vòng **10 phút trước khi bước vào phòng bảo vệ**.

---

## 1. Kiểm tra Hạ tầng & Dịch vụ Kỹ thuật (5 phút trước giờ bảo vệ)

- [ ] **Docker Desktop & Container:**
  ```powershell
  docker compose -f docker-compose.enterprise-lab.yml up -d postgres
  docker compose -f docker-compose.a8.yml up -d
  docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
  ```
  - Xác nhận `iso27001-postgres` đang `Up (healthy)` ở cổng `5433`.
  - Xác nhận `iso-a8-lab` đang `Up (healthy)`.
- [ ] **Ollama Local LLM (`qwen2.5:7b`):**
  ```powershell
  Invoke-RestMethod http://127.0.0.1:11434/api/tags
  ```
  - Xác nhận model `qwen2.5:7b` có trong danh sách và Ollama đang lắng nghe tại `127.0.0.1:11434`.
- [ ] **Backend FastAPI & Health Check:**
  ```powershell
  .\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
  Invoke-RestMethod http://127.0.0.1:8000/api/health
  ```
  - Kết quả trả về phải là: `{"status": "ok", "database": "connected", "frontend_build": true}`.
- [ ] **Giao diện Trình duyệt:**
  - Mở `http://127.0.0.1:8000` (hoặc `http://127.0.0.1:5173`).
  - Mở thêm 1 cửa sổ ẩn danh (Incognito/InPrivate) để đóng vai **Người thực hiện (`operator`)** khi demo phối hợp 2 vai trò.

---

## 2. Chuẩn bị Tệp Bằng chứng Mẫu ngoài Desktop

Chuẩn bị sẵn thư mục `Desktop\ISO27001_Demo_Files\` gồm 3 tệp sau để thao tác upload trực tiếp:

- [ ] **Tệp 1 (`A813_truoc_khac_phuc.txt`):** Log sao lưu hàng đêm thành công nhưng ghi rõ chưa có biên bản diễn tập khôi phục (dùng ở Bước 4 của kịch bản demo → AI đánh giá `Partially Compliant`).
- [ ] **Tệp 2 (`A813_sau_khac_phuc_restore_test.txt`):** Biên bản diễn tập khôi phục dữ liệu thành công trên máy chủ cô lập kèm đối chiếu mã SHA-256 (dùng ở Bước 9 của kịch bản demo → Đính kèm bằng chứng sau khắc phục & Xác minh đạt).
- [ ] **Tệp 3 (`file_loi_1_ky_tu.txt`):** Chỉ chứa 1 chữ `x` (dùng nếu giảng viên yêu cầu demo tính năng chặn tệp rác / không đủ chất lượng ở bước Preflight).

---

## 3. Checklist 12 Điểm Nhấn Nghiệp vụ Cần Trình diễn Trước Hội đồng

- [ ] **Điểm 1 — Tạo khách hàng & đợt đánh giá mới (`Doanh nghiệp → Khách hàng tư vấn`):** Chỉ rõ đợt mới bắt đầu hoàn toàn rỗng (`0` nhân viên, `0` tài khoản, `0` thiết bị), không bị trộn dữ liệu mẫu của phòng lab.
- [ ] **Điểm 2 — Khai báo danh mục doanh nghiệp:** Tạo nhân viên `EMP-001`, chỉ rõ hệ thống cập nhật `snapshot_hash` và ghi lịch sử trước/sau nhưng không tự suy diễn nhân sự đã đạt tuân thủ.
- [ ] **Điểm 3 — Kiểm tra trước nguồn (Preflight) & Bảo toàn bản gốc SHA-256:** Bấm *"Kiểm tra trước — chưa lưu"* trên `A.8.13`, sau đó bấm *"Lưu nguồn và bản gốc"* và tải lại bản gốc để chứng minh toàn vẹn SHA-256.
- [ ] **Điểm 4 — AI Agent đánh giá dựa trên bằng chứng (`LangGraph + Qwen2.5:7b`):** Bấm *"Agent đánh giá hồ sơ đã thu"*, chỉ rõ kết luận `Partially Compliant`, lý do bằng tiếng Việt và mã bằng chứng `WEB-...` được viện dẫn.
- [ ] **Điểm 5 — Phát hiện GAP & Khóa Baseline:** Mở khung *"Tư vấn & khắc phục"*, tạo phát hiện trên `A.8.13`, chỉ rõ cột *"Trước khắc phục — giữ nguyên"* đã khóa cứng `review_token` và bằng chứng ban đầu.
- [ ] **Điểm 6 — AI Tư vấn phương án khắc phục 15 trường:** Bấm *"AI đề xuất có cấu trúc — chờ tư vấn duyệt"*, trình chiếu khung *"Phân tích tư vấn / thông tin cần xác minh"* (Bị sai gì, thiếu gì, các bước checkbox phải làm, bằng chứng phải nộp thêm, cách kiểm tra lại và câu hỏi bổ sung).
- [ ] **Điểm 7 — Chuyên viên sửa, duyệt & giao việc phối hợp:** Chuyên viên duyệt kế hoạch, giao người thực hiện chính + người phối hợp + thời hạn, và phân công bước 1 cho người phối hợp.
- [ ] **Điểm 8 — Hộp thư thông báo trong ứng dụng:** Mở *"Thông báo khắc phục"* trên tài khoản người thực hiện để thấy thông báo giao việc và phân công bước con vừa nhận.
- [ ] **Điểm 9 — Thực hiện tuần tự & Đính kèm bằng chứng mới sau khắc phục:** Thử bấm bước 2 trước khi làm bước 1 (bị khóa), sau đó tích hoàn thành tuần tự, tải lên tệp `A813_sau_khac_phuc_restore_test.txt`, gắn vào hành động và gửi xác minh.
- [ ] **Điểm 10 — Chặn tự xác minh & Xác minh độc lập:** Chỉ rõ người thực hiện không có nút tự xác minh; chuyển sang tài khoản chuyên viên/người xác minh để ký thẩm định tiêu chí hiện hành (`Compliant`) rồi bấm *"Xác minh đạt"* và *"Đóng hành động"*.
- [ ] **Điểm 11 — Dashboard 3 góc nhìn & Sổ rủi ro 5×5:** Chuyển đổi giữa 3 góc nhìn (*Chuyên viên*, *Doanh nghiệp*, *Lãnh đạo*) và bộ lọc 9 trạng thái của 56 Control.
- [ ] **Điểm 12 — Xuất báo cáo Trước–Sau (PDF & Excel 8 Sheet):** Tải trực tiếp file PDF tiếng Việt và file Excel `.xlsx`, mở lên đối chiếu cột Trước khắc phục (`Partially Compliant`) và Sau khắc phục (`Compliant`).
