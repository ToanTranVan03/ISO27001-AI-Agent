# KỊCH BẢN DEMO BẢO VỆ ĐỒ ÁN 15 PHÚT & BỘ DỮ LIỆU DEMO MẪU

Tài liệu này cung cấp kịch bản trình diễn trực tiếp trên hệ thống trong **15 phút** trước hội đồng/giảng viên, kèm theo **bộ dữ liệu doanh nghiệp mẫu nhất quán** để copy-paste nhanh khi demo mà **không làm bẩn đợt đánh giá chính từ trước**.

---

## PHẦN A: BỘ DỮ LIỆU DEMO NHẤT QUÁN (DÙNG ĐỂ COPY-PASTE KHI TRÌNH DIỄN)

> **Phân biệt rõ dữ liệu:** Đây là bộ dữ liệu minh họa cho một khách hàng giả định (*Công ty Cổ phần Dịch vụ Số Minh Việt*) dùng để thao tác tạo mới trực tiếp trước hội đồng. Khi tạo khách hàng này qua giao diện **Khách hàng tư vấn**, toàn bộ dữ liệu nằm trong một đợt đánh giá riêng (`inventory_mode = 'client'`), hoàn toàn tách biệt với đợt nghiên cứu chính (`ISO Enterprise Lab — Đánh giá nhóm 11`).

### 1. Thông tin Khách hàng & Đợt đánh giá Demo
- **Tên khách hàng:** `Công ty Cổ phần Dịch vụ Số Minh Việt (DEMO)`
- **Lĩnh vực khách hàng:** `Thương mại điện tử và Dịch vụ đám mây`
- **Người liên hệ khách hàng:** `Nguyễn Minh Quân — Trưởng ban ATTT (quan.nm@minhviet-demo.vn)`
- **Địa điểm khách hàng:** `Tầng 8, Tòa nhà Công nghệ, Quận Cầu Giấy, Hà Nội`
- **Tên đợt đầu tiên:** `Đánh giá & Khắc phục ISO 27001 — Quý 4/2026 (DEMO)`
- **Phạm vi ISMS của đợt:** `Hệ thống cổng thanh toán, cụm máy chủ cơ sở dữ liệu khách hàng và đội ngũ vận hành hạ tầng CNTT tại trụ sở Hà Nội.`

### 2. Danh mục Doanh nghiệp Demo (Khai báo trực tiếp trên UI)
- **Nhân viên:**
  - Mã danh mục: `EMP-001`
  - Họ tên nhân viên: `Lê Hoàng Nam`
  - Phòng ban: `Vận hành Hạ tầng CNTT`
  - Chức danh: `Kỹ sư Quản trị Hệ thống & Sao lưu`
  - Lý do tạo/sửa danh mục: `Khai báo nhân sự phụ trách vận hành máy chủ sao lưu trong phạm vi ISMS demo.`
- **Tài khoản:**
  - Mã danh mục: `ACC-BACKUP-01`
  - Tên hệ thống tài khoản: `Hệ thống Quản trị Sao lưu Veeam/PostgreSQL`
  - Phòng ban: `Vận hành Hạ tầng CNTT`
  - Nhân viên liên quan: `EMP-001 · Lê Hoàng Nam`
  - Trạng thái: `Đang hoạt động`
  - Lý do tạo/sửa: `Khai báo tài khoản quản trị sao lưu phục vụ rà soát A.8.13.`
- **Tài sản:**
  - Mã danh mục: `SRV-BK-01`
  - Tên tài sản: `Máy chủ Lưu trữ Bản sao lưu Dự phòng`
  - Phòng ban: `Vận hành Hạ tầng CNTT`
  - Nhân viên liên quan: `EMP-001 · Lê Hoàng Nam`
  - Loại tài sản: `Phần cứng`
  - Lý do tạo/sửa: `Khai báo máy chủ lưu trữ bản sao lưu trong phạm vi đánh giá.`

### 3. Hai tệp Bằng chứng Mẫu cho Control `A.8.13` (Sao lưu thông tin)

Bạn có thể tạo sẵn 2 file `.txt` ngoài Desktop để chọn tải lên trong lúc demo:

- **Tệp 1 — Trước khắc phục (`A813_truoc_khac_phuc.txt`):** *(Có log sao lưu nhưng thiếu biên bản kiểm thử khôi phục)*
  ```text
  [NHẬT KÝ HỆ THỐNG SAO LƯU — MINH VIỆT DEMO]
  Hệ thống: Cụm cơ sở dữ liệu PostgreSQL & Máy chủ SRV-BK-01
  Ngày ghi nhận: 20/11/2026
  1. Trạng thái job sao lưu tự động hàng đêm (02:00 UTC+7): THÀNH CÔNG (Full Backup 420GB, SHA256: 8f9a2b...c104).
  2. Tần suất sao lưu: Hàng ngày (Incremental) và Chủ nhật hàng tuần (Full).
  3. Ghi chú vận hành: Trong 6 tháng qua nhóm vận hành chỉ kiểm tra trạng thái job báo xanh trên màn hình. Chưa từng thực hiện diễn tập khôi phục dữ liệu (restore test) ra máy chủ độc lập và chưa có biên bản nghiệm thu khôi phục dữ liệu.
  ```
- **Tệp 2 — Sau khắc phục (`A813_sau_khac_phuc_restore_test.txt`):** *(Đã bổ sung biên bản diễn tập khôi phục thành công)*
  ```text
  [BIÊN BẢN NGHIỆM THU DIỄN TẬP KHÔI PHỤC DỮ LIỆU (RESTORE TEST) — MINH VIỆT DEMO]
  Mã biên bản: BB-RESTORE-2026-Q4 | Ngày thực hiện: 24/11/2026
  Hệ thống nguồn: Máy chủ sao lưu SRV-BK-01 | Môi trường khôi phục: Máy chủ cô lập SRV-RESTORE-LAB
  Người thực hiện: EMP-001 (Lê Hoàng Nam) | Người giám sát: Nguyễn Minh Quân
  1. Bản sao lưu được kiểm thử: Full Backup ngày 23/11/2026 (422GB).
  2. Kết quả khôi phục: Khôi phục thành công 100% bảng giao dịch và cấu hình trong 38 phút (đạt mục tiêu RTO < 60 phút).
  3. Đối chiếu toàn vẹn: Mã băm SHA-256 của dữ liệu sau khôi phục khớp hoàn toàn với bản gốc trước sao lưu.
  4. Kết luận: Đạt yêu cầu cả hai tiêu chí (có log sao lưu thành công gần nhất và có biên bản test khôi phục dữ liệu).
  ```

---

## PHẦN B: KỊCH BẢN DEMO 15 PHÚT (12 BƯỚC TRÌNH TỰ & ĐIỂM NHẤN)

### Bước 1: Giới thiệu hệ thống (01 phút — Phút 00:00 đến 01:00)
- **Trang cần mở:** Màn hình Đăng nhập (`http://127.0.0.1:8000`) → Đăng nhập tài khoản `admin`.
- **Nút cần thao tác:** Điền tài khoản `admin`, bấm **`ĐĂNG NHẬP HỆ THỐNG`**.
- **Nội dung cần trình bày:** Giới thiệu thanh điều hướng 4 phân hệ (*Tổng quan 56 control*, *Thực nghiệm A.8*, *Doanh nghiệp*, *Hồ sơ ISO*) và mục tiêu đồ án: chuyển từ công cụ chấm đạt/không đạt đơn thuần sang nền tảng quản lý trọn vẹn vòng đời đánh giá – phát hiện GAP – AI tư vấn khắc phục – giao việc – xác minh độc lập – báo cáo trước/sau.
- **Điểm nhấn trước giảng viên:** Hệ thống tách biệt rõ kết quả gợi ý của AI với thẩm định chuyên môn của con người; mọi thay đổi đều gắn mã băm SHA-256 và phiên bản trong PostgreSQL.

### Bước 2: Tạo khách hàng tư vấn (01 phút — Phút 01:00 đến 02:00)
- **Trang cần mở:** Tab **`Doanh nghiệp`** → Mở khung **`▸ Khách hàng tư vấn · doanh nghiệp và các đợt riêng`**.
- **Nút cần thao tác:** Điền thông tin *Công ty Cổ phần Dịch vụ Số Minh Việt (DEMO)*, lĩnh vực, người liên hệ, tên đợt đầu tiên và phạm vi ISMS → Bấm **`Lưu khách hàng`**.
- **Nội dung cần trình bày:** Hệ thống cho phép đơn vị tư vấn quản lý nhiều doanh nghiệp khách hàng độc lập, mỗi hồ sơ khách hàng đều được đánh số phiên bản (`v1`, `v2`...) và lưu lịch sử chỉnh sửa.
- **Điểm nhấn trước giảng viên:** Dữ liệu giữa các khách hàng được cách ly ở tầng API backend (`403 Forbidden` nếu truy cập chéo), không chỉ ẩn trên giao diện.

### Bước 3: Chọn đợt đánh giá mới & Khai báo danh mục doanh nghiệp (01 phút 30 giây — Phút 02:00 đến 03:30)
- **Trang cần mở:** Trên thanh Header trên cùng, ở ô **`Đợt đang làm`**, chọn đợt **`Đánh giá & Khắc phục ISO 27001 — Quý 4/2026 (DEMO)`** vừa tạo.
- **Nút cần thao tác:**
  1. Chỉ vào 3 ô thống kê: `Nhân viên: 0`, `Tài khoản: 0`, `Thiết bị: 0`.
  2. Mở **`▸ Khai báo / sửa danh mục doanh nghiệp — không tự tạo bằng chứng`**, nhập nhanh nhân viên `EMP-001` (*Lê Hoàng Nam*) → Bấm **`Lưu danh mục theo snapshot hiện tại`**.
  3. Mở **`▸ Cấp thành viên đúng đợt`** trong khung Khách hàng tư vấn để cấp tài khoản `operator` (người thực hiện) cho đợt này.
- **Nội dung cần trình bày:** Đợt khách hàng mới bắt đầu hoàn toàn rỗng (`inventory_mode = 'client'`), không tự nạp dữ liệu mẫu của phòng lab.
- **Điểm nhấn trước giảng viên:** Việc khai báo tên nhân viên hay thiết bị chỉ tạo bối cảnh danh mục và mã `snapshot_hash`, **hệ thống không tự suy diễn nhân viên đó đã học ATTT hay thiết bị đã bật mã hóa**.

### Bước 4: Nộp hồ sơ bằng chứng ban đầu & Kiểm tra trước (01 phút 30 giây — Phút 03:30 đến 05:00)
- **Trang cần mở:** Tab **`Tổng quan 56 control`** → Tìm và chọn Control **`A.8.13 · Sao lưu thông tin`**.
- **Nút cần thao tác:**
  1. Trong mục **`01 · Đọc tiêu chí & bổ sung bằng chứng`**, chọn loại bằng chứng `EVID_TECH_BACKUP_LOG`, nhập xuất xứ `Trích xuất log hệ thống sao lưu SRV-BK-01`, chọn file `A813_truoc_khac_phuc.txt`.
  2. Bấm **`Kiểm tra trước — chưa lưu`** (Preflight).
  3. Sau khi thấy hộp thông báo SHA-256 và số ký tự hợp lệ, bấm **`Lưu nguồn và bản gốc`**.
- **Nội dung cần trình bày:** Hệ thống kiểm tra chất lượng văn bản trước khi cho phép lưu vào DB, đồng thời lưu giữ bản gốc nhị phân theo mã băm SHA-256 để chống sửa đổi.
- **Điểm nhấn trước giảng viên:** Trước khi nộp nguồn, nút chạy AI Agent bị khóa kèm lời giải thích rõ lý do; hệ thống không chạy AI khi không có đầu vào.

### Bước 5: AI Agent đánh giá hiện trạng (01 phút 30 giây — Phút 05:00 đến 06:30)
- **Trang cần mở:** Vẫn tại thẻ chi tiết Control **`A.8.13`**.
- **Nút cần thao tác:** Bấm nút **`Agent đánh giá hồ sơ đã thu (không dùng preset)`**.
- **Nội dung cần trình bày:** LangGraph điều phối 4 bước (`Plan → Collect → Evaluate → Verify`), gọi model `qwen2.5:7b` cục bộ qua Ollama để đối chiếu tệp `A813_truoc_khac_phuc.txt` với 2 tiêu chí của `A.8.13` (*Có log sao lưu gần nhất* và *Có biên bản test khôi phục dữ liệu*).
- **Điểm nhấn trước giảng viên:** Vì tệp ban đầu chỉ có log sao lưu mà chưa có biên bản diễn tập khôi phục, AI kết luận **`Partially Compliant` (Tuân thủ một phần)**, chỉ rõ lý do thiếu biên bản restore test và viện dẫn đúng mã bằng chứng `WEB-...` vừa nộp.

### Bước 6: Phát hiện GAP & Khóa Baseline (01 phút — Phút 06:30 đến 07:30)
- **Trang cần mở:** Cuộn lên đầu trang **`Tổng quan 56 control`** → Mở khung **`▸ Tư vấn & khắc phục · từ phát hiện đến xác minh`**.
- **Nút cần thao tác:** Bấm nút **`Tạo phát hiện ứng viên từ nguồn đã đánh giá`** (hoặc tạo trong *Ghi nhận phát hiện trên snapshot hiện tại* cho `A.8.13`).
- **Nội dung cần trình bày:** Hệ thống tự động phát hiện Control `A.8.13` chưa đạt toàn diện và tạo thẻ **Phát hiện (GAP)** bên dưới, đồng thời đóng băng cột **`Trước khắc phục — giữ nguyên`** (gồm kết luận ban đầu, `review_token` và mã SHA-256 của bằng chứng ban đầu).
- **Điểm nhấn trước giảng viên:** Baseline ban đầu được khóa bất biến để cuối quy trình có thể đối chiếu trung thực "Trước và Sau khắc phục".

### Bước 7: AI Tư vấn phương án khắc phục chi tiết (02 phút — Phút 07:30 đến 09:30)
- **Trang cần mở:** Trên thẻ Phát hiện `A.8.13` trong khung **Tư vấn & khắc phục**.
- **Nút cần thao tác:** Mở **`▸ Đề xuất kế hoạch cho phát hiện này`** → Bấm nút **`AI đề xuất có cấu trúc — chờ tư vấn duyệt`**.
- **Nội dung cần trình bày:** Khi AI chạy xong, chỉ vào khung **`Phân tích tư vấn / thông tin cần xác minh`** đã mở sẵn trên thẻ hành động:
  - *Bị sai / thiếu gì:* `Vấn đề cần xử lý` & `Nguyên nhân có thể — cần xác minh`.
  - *Phải làm gì, ở đâu:* `Mục tiêu khắc phục`, `Vì sao cần thực hiện`, `Vị trí / hệ thống cần xử lý`, danh sách checkbox các bước công việc con.
  - *Phải nộp thêm gì mới đạt chuẩn:* `Bằng chứng nghiệm thu cần cung cấp`, `Điều kiện nghiệm thu` và `Cách kiểm tra lại`.
  - *Câu hỏi làm rõ:* `Câu hỏi / thông tin AI yêu cầu bổ sung`.
- **Điểm nhấn trước giảng viên:** AI không chỉ sinh văn bản chung chung mà trả về cấu trúc 15 trường gắn chặt với tiêu chí Control và trích đoạn bằng chứng; đặc biệt trạng thái luôn là **`Chờ duyệt kế hoạch` (`PENDING_APPROVAL`)** — AI không được quyền tự giao việc hay tự duyệt.

### Bước 8: Chuyên viên sửa, duyệt và giao việc / phân công bước con (01 phút 30 giây — Phút 09:30 đến 11:00)
- **Trang cần mở:** Ngay trên thẻ Hành động khắc phục vừa được AI sinh ra.
- **Nút cần thao tác:**
  1. (Tuỳ chọn) Mở **`▸ Sửa kế hoạch trước phê duyệt`** để chỉnh sửa nội dung AI gợi ý.
  2. Nhập *Ghi chú thao tác* (`Phê duyệt kế hoạch diễn tập khôi phục sao lưu Q4`), chọn *Người thực hiện*, *Người phối hợp*, *Hạn hoàn thành* → Bấm **`Duyệt và giao thực hiện`**.
  3. Ở danh sách bước con, chọn dropdown **`Người phụ trách bước...`** để phân công bước cụ thể cho thành viên.
- **Nội dung cần trình bày:** Chuyên viên kiểm soát hoàn toàn phương án trước khi giao xuống doanh nghiệp, hỗ trợ phối hợp nhiều người và phân công tới từng bước nhỏ.
- **Điểm nhấn trước giảng viên:** Hệ thống tự động bắn thông báo vào hộp thư **Thông báo khắc phục** của người thực hiện, người phối hợp và quản lý doanh nghiệp.

### Bước 9: Doanh nghiệp thực hiện & Nộp bằng chứng sau khắc phục (01 phút 30 giây — Phút 11:00 đến 12:30)
- **Trang cần mở:** Đăng nhập (hoặc chuyển sang cửa sổ ẩn danh) của tài khoản **Người thực hiện (`operator`)** đã được giao việc.
- **Nút cần thao tác:**
  1. Ở thẻ Hành động `A.8.13`, nhập ghi chú, tích hoàn thành lần lượt từng checkbox công việc con từ bước 1 đến bước cuối.
  2. Xuống thẻ Control `A.8.13`, tải lên tệp **`A813_sau_khac_phuc_restore_test.txt`** (Biên bản diễn tập khôi phục thành công).
  3. Quay lên thẻ Hành động khắc phục, ở dropdown **`Bằng chứng sau thực hiện đã lưu vào control`**, chọn nguồn mới vừa tải lên → Bấm **`Gắn nguồn vào hành động`** → Bấm **`Gửi xác minh — chưa kết luận đạt`**.
- **Nội dung cần trình bày:** Các bước con bắt buộc thực hiện theo đúng thứ tự phụ thuộc; hệ thống chỉ cho phép chọn nguồn mới nộp sau thời điểm baseline (chặn đính kèm lại nguồn cũ).
- **Điểm nhấn trước giảng viên:** Chỉ người chịu trách nhiệm chính mới bấm được nút *Gửi xác minh*, và khi gửi xong cũng không thấy nút *Xác minh đạt* (ngăn chặn tuyệt đối việc tự nghiệm thu công việc của chính mình).

### Bước 10: Xác minh độc lập & Đánh giá lại Control (01 phút — Phút 12:30 đến 13:30)
- **Trang cần mở:** Quay lại cửa sổ của **Chuyên viên / Người xác minh (`admin` / `verifier`)**.
- **Nút cần thao tác:**
  1. Tại thẻ Control `A.8.13`, bấm **`Agent đánh giá hồ sơ đã thu`** để AI đánh giá lại khi đã có thêm biên bản restore test.
  2. Mở mục **`02 · Thẩm định kết luận trên nguồn hiện hành`**, tích đạt 2 tiêu chí, chọn **`Tuân thủ` (`Compliant`)**, ghi căn cứ thẩm định → Bấm **`Người đánh giá xác nhận`**.
  3. Lên thẻ Hành động khắc phục `A.8.13`, nhập ghi chú xác minh → Bấm **`Xác minh đạt`** → Bấm **`Đóng hành động đã xác minh`**.
- **Nội dung cần trình bày:** Hệ thống hiển thị song song 2 ô: **`Trước khắc phục — giữ nguyên`** (`Partially Compliant`) và **`Hiện tại — cần thẩm định`** (`Compliant`).
- **Điểm nhấn trước giảng viên:** Backend chỉ cho phép bấm *Xác minh đạt* khi chính người xác minh độc lập đã ký thẩm định tiêu chí hiện hành và viện dẫn trực tiếp bằng chứng mới sau khắc phục.

### Bước 11: Dashboard 3 góc nhìn & Quản lý 56 Control (01 phút — Phút 13:30 đến 14:30)
- **Trang cần mở:** Khung **`Dashboard tư vấn và khắc phục`** ngay trong khu vực Tư vấn & khắc phục.
- **Nút cần thao tác:**
  1. Chuyển dropdown **`Góc nhìn báo cáo`** qua lại giữa 3 chế độ: **`Chuyên viên`**, **`Doanh nghiệp`** và **`Lãnh đạo`**.
  2. Chuyển dropdown **`Danh sách công việc theo control`** để lọc theo *Thiếu nguồn*, *Chưa thẩm định hiện hành*, *Có hành động đã xác minh*.
- **Nội dung cần trình bày:** Mỗi góc nhìn phục vụ đúng đối tượng: Chuyên viên xem phân loại rủi ro & việc khẩn cấp; Doanh nghiệp xem tiến độ & các tiêu chí chưa đáp ứng; Lãnh đạo xem mức độ đáp ứng, nguồn lực kế hoạch và các quyết định còn chờ.
- **Điểm nhấn trước giảng viên:** Mọi con số thống kê đều truy vấn trực tiếp từ PostgreSQL, không dùng số liệu giả lập và ghi rõ *tỷ lệ hoàn thành công việc không phải là tỷ lệ chứng nhận ISO*.

### Bước 12: Xuất báo cáo Trước–Sau (PDF / Excel / HTML / CSV) (30 giây — Phút 14:30 đến 15:00)
- **Trang cần mở:** Hàng nút công cụ trên cùng của khung **Tư vấn & khắc phục**.
- **Nút cần thao tác:** Bấm **`Tải PDF`**, **`Tải Excel XLSX`** và **`Tải bản in HTML`**, mở file vừa tải về lên màn hình.
- **Nội dung cần trình bày:** Trình chiếu file PDF tiếng Việt và file Excel 8 sheet chứa đầy đủ: Tổng quan lãnh đạo, Danh sách việc 56 Control, Sổ rủi ro, Tình trạng trước khắc phục, Kế hoạch tư vấn của AI, Bằng chứng sau khắc phục kèm SHA-256 và Chữ ký xác minh độc lập.
- **Điểm nhấn kết thúc:** Khẳng định hệ thống đã nối thông suốt từ khâu đánh giá bằng chứng kỹ thuật tới quản trị tư vấn khắc phục thực tế, đảm bảo tính toàn vẹn, truy vết kiểm toán (audit trail) và phân quyền nghiêm ngặt.
