# ĐỀ CƯƠNG NỘI DUNG SLIDE BẢO VỆ ĐỒ ÁN (18 SLIDE)

**Tên đề tài:** Hệ thống AI Agent hỗ trợ đánh giá và tư vấn khắc phục tuân thủ an toàn thông tin theo tiêu chuẩn ISO/IEC 27001:2022  
**Thời lượng trình bày dự kiến:** 12–15 phút thuyết trình Slide + 15 phút Demo trực tiếp & Hỏi đáp.

> **Nguyên tắc thiết kế Slide:** Mỗi slide chỉ dùng 3–5 gạch đầu dòng ngắn gọn (dưới 40 từ/slide), ưu tiên sơ đồ trực quan và ảnh chụp màn hình thật từ hệ thống, tuyệt đối không chép cả đoạn văn dài lên slide.

---

### Slide 1: Trang bìa
- **Tiêu đề:** HỆ THỐNG AI AGENT HỖ TRỢ ĐÁNH GIÁ VÀ TƯ VẤN KHẮC PHỤC TUÂN THỦ ISO/IEC 27001:2022
- **Nội dung ngắn gọn:**
  - Thông tin nhóm sinh viên thực hiện & Giảng viên hướng dẫn.
  - Phạm vi: 56 Control (A.6, A.7, A.8) · Thực nghiệm sâu 18 A.8 · Vòng đời Tư vấn & Khắc phục khép kín.
- **Hình ảnh / Sơ đồ cần sử dụng:** Logo trường/khoa + Ảnh chụp màn hình giao diện tổng quan hệ thống (`Scope56`).
- **Nội dung thuyết trình (Speaker Notes):** Kính chào Hội đồng. Nhóm xin trình bày đề tài xây dựng Hệ thống AI Agent hỗ trợ đánh giá và tư vấn khắc phục tuân thủ an toàn thông tin theo tiêu chuẩn ISO/IEC 27001:2022.

---

### Slide 2: Đặt vấn đề & Động lực nghiên cứu
- **Tiêu đề:** Bài toán Đánh giá & Khắc phục ISO/IEC 27001 thực tế
- **Nội dung ngắn gọn:**
  - Quản lý bằng chứng thủ công rời rạc, khó kiểm chứng tính toàn vẹn.
  - Nhiều công cụ chỉ dừng ở chấm *"Đạt / Không đạt"*, thiếu quy trình khắc phục & xác minh sau đánh giá.
  - Chatbot AI thông thường dễ *"ảo giác"* (hallucination), tự suy diễn tuân thủ khi thiếu bằng chứng.
- **Hình ảnh / Sơ đồ cần sử dụng:** Sơ đồ so sánh 2 cột: *Công cụ chấm điểm truyền thống / Chatbot tự do* vs. *Nền tảng AI Agent gắn kết bằng chứng & quy trình khắc phục*.
- **Nội dung thuyết trình:** Trong thực tế tư vấn ISO 27001, việc tìm ra điểm chưa đạt mới chỉ là bước đầu. Thách thức lớn nhất là chỉ rõ cho doanh nghiệp biết họ bị sai ở đâu, thiếu hồ sơ gì, giao cho ai sửa, nộp bằng chứng nào để người độc lập xác minh lại. Đồng thời, nếu ứng dụng AI, hệ thống phải kiểm soát được hiện tượng AI tự bịa bằng chứng.

---

### Slide 3: Mục tiêu & Phạm vi của hệ thống
- **Tiêu đề:** Mục tiêu & Phạm vi 56 Control ISO/IEC 27001:2022
- **Nội dung ngắn gọn:**
  - **Quản lý 56 Control:** 8 A.6 (Con người) · 14 A.7 (Vật lý) · 34 A.8 (Kỹ thuật).
  - **Thực nghiệm chuyên sâu 18 Control A.8:** 108 ca Raw Replay & 18 Probe Live v2.
  - **Quy trình 12 bước khép kín:** Từ tiếp nhận khách hàng → Đánh giá → Phát hiện GAP → AI Tư vấn → Giao việc → Xác minh độc lập → Báo cáo Trước/Sau.
  - **Nguyên tắc cốt lõi:** AI chỉ hỗ trợ dự thảo; con người giữ quyền thẩm định và phê duyệt cuối cùng.
- **Hình ảnh / Sơ đồ cần sử dụng:** Biểu đồ phân bổ 56 Control (8 A.6 / 14 A.7 / 34 A.8) và sơ đồ chuỗi 12 bước nghiệp vụ.
- **Nội dung thuyết trình:** Hệ thống quản lý 56 control thuộc 3 trụ cột Con người, Vật lý và Kỹ thuật, ưu tiên thực nghiệm sâu 18 control A.8 theo góp ý của giảng viên, đồng thời hoàn thiện trọn vẹn quy trình tư vấn khắc phục đa khách hàng.

---

### Slide 4: Kiến trúc tổng thể hệ thống
- **Tiêu đề:** Kiến trúc 4 tầng của Hệ thống ISO27001-AI-Agent
- **Nội dung ngắn gọn:**
  - **Frontend:** React 19 + Vite + TailwindCSS (4 phân hệ, đồng bộ ngữ cảnh URL Hash).
  - **Backend:** FastAPI + Pydantic v2 (REST API, RBAC, Background Workers).
  - **AI Engine:** LangGraph + Ollama `qwen2.5:7b` (vận hành local, bảo mật dữ liệu nội bộ).
  - **Lưu trữ:** PostgreSQL 16 (ACID, khóa CAS/FOR UPDATE) + Kho bản gốc SHA-256.
- **Hình ảnh / Sơ đồ cần sử dụng:** Sơ đồ kiến trúc tổng thể từ `docs/defense/ARCHITECTURE_PRESENTATION.md`.
- **Nội dung thuyết trình:** Hệ thống được thiết kế theo kiến trúc 4 tầng. Toàn bộ mô hình ngôn ngữ lớn Qwen2.5:7b chạy cục bộ qua Ollama, giúp dữ liệu bằng chứng nhạy cảm của doanh nghiệp không bị gửi ra ngoài Internet.

---

### Slide 5: Tiếp nhận & Kiểm định Toàn vẹn Nguồn Bằng chứng
- **Tiêu đề:** Kiểm soát Chất lượng & Toàn vẹn Bằng chứng (SHA-256)
- **Nội dung ngắn gọn:**
  - Hỗ trợ đa định dạng: PDF, DOCX, TXT, JSON, CSV, CONF, LOG (<= 15MB).
  - **Kiểm tra trước (Preflight):** Lọc tệp rỗng, quá ngắn, lặp ký tự rác, lỗi cú pháp JSON trước khi lưu.
  - **Kho bản gốc bất biến:** Lưu file nhị phân theo mã băm `SHA-256`, chống nạp trùng và phát hiện sửa đổi.
- **Hình ảnh / Sơ đồ cần sử dụng:** Ảnh chụp màn hình khung *Nộp hồ sơ, log hoặc cấu hình gốc* (`SourceIntake.jsx`) hiển thị kết quả Preflight & mã SHA-256.
- **Nội dung thuyết trình:** Trước khi AI được phép chạy, mọi nguồn bằng chứng đều phải qua cổng kiểm định chất lượng và toàn vẹn. Ví dụ nguồn A.6.2 chỉ có 1 ký tự sẽ bị hệ thống chặn lại, không đưa vào model để tránh kết luận sai.

---

### Slide 6: Đồ thị Trạng thái AI Agent Đánh giá (LangGraph)
- **Tiêu đề:** Luồng suy luận 4 nút của AI Agent & Guardrail chống ảo giác
- **Nội dung ngắn gọn:**
  - `node_plan`: Chọn chế độ nguồn (`user_evidence_only` cho khách hàng thật).
  - `node_collect`: Thu nguồn đã qua cổng kiểm tra toàn vẹn SHA-256.
  - `node_evaluate`: Kiểm tra ngân sách token (`16.384`), chống prompt injection, gọi `qwen2.5:7b` theo Rubric.
  - `node_verify` (**Guardrail**): Đối chiếu `evidence_ids` viện dẫn; tự động bác bỏ nếu AI bịa mã bằng chứng.
- **Hình ảnh / Sơ đồ cần sử dụng:** Sơ đồ `node_plan → node_collect → node_evaluate → node_verify`.
- **Nội dung thuyết trình:** Điểm khác biệt cốt lõi giữa AI Agent của nhóm với Chatbot là nút `node_verify`. AI bắt buộc phải trích dẫn mã `evidence_id` có thật trong gói bằng chứng. Nếu AI bịa ra mã không tồn tại hoặc kết luận đạt mà không có viện dẫn, guardrail sẽ tự động hạ kết luận về *Thiếu bằng chứng*.

---

### Slide 7: Thực nghiệm Chuyên sâu 18 Control A.8 & Chấm mù
- **Tiêu đề:** Thực nghiệm 18 Control A.8 (Raw Replay & Live Container v2)
- **Nội dung ngắn gọn:**
  - **Raw Replay:** 18 Control × 6 Profile = 108 kịch bản cấu hình/log.
  - **Live A.8 v2:** Container `iso-a8-lab` cô lập với 18 Probe (5 quan sát tài nguyên, 13 phép thử chủ động TCP/TLS/Auth/Crypto).
  - **Chấm mù (`blind-v3`):** Tách người điều phối và người chấm, che đáp án thiết kế, lưu sổ xử lý bất đồng.
- **Hình ảnh / Sơ đồ cần sử dụng:** Ảnh chụp màn hình phân hệ *Thực nghiệm A.8* và phiếu rà sai khác tiêu chí.
- **Nội dung thuyết trình:** Đối với 18 control kỹ thuật A.8, ngoài việc đọc tài liệu, hệ thống còn có container lab cô lập để chạy 18 probe kiểm tra trực tiếp cấu hình TLS, xác thực, mã hóa và sao lưu, kèm quy trình chấm mù để đối chiếu với con người.

---

### Slide 8: Quản lý Đa khách hàng & Cách ly Dữ liệu (Multi-Tenant)
- **Tiêu đề:** Mô hình Tư vấn Nhiều Doanh nghiệp & Nhiều Đợt Đánh giá
- **Nội dung ngắn gọn:**
  - Tạo/cập nhật hồ sơ nhiều khách hàng có đánh số phiên bản (`v1`, `v2`...).
  - Mỗi khách hàng có nhiều đợt đánh giá độc lập (`inventory_mode = 'client'`).
  - **Đợt mới bắt đầu rỗng:** Không tự nạp nhân sự/tài sản mẫu của phòng lab.
  - **Khai báo danh mục:** Nhân viên, Tài khoản, Tài sản gắn mã `snapshot_hash` và audit trước/sau.
- **Hình ảnh / Sơ đồ cần sử dụng:** Ảnh chụp màn hình *Khách hàng tư vấn* (`ClientManagement.jsx`) và *Khai báo danh mục doanh nghiệp* (`ClientInventoryEditor.jsx`).
- **Nội dung thuyết trình:** Để sử dụng trong tư vấn thực tế, hệ thống hỗ trợ quản lý nhiều doanh nghiệp khách hàng. Khi tạo một khách hàng mới, đợt đánh giá bắt đầu hoàn toàn rỗng và chỉ sử dụng nguồn bằng chứng do chính doanh nghiệp đó nộp lên.

---

### Slide 9: Phát hiện GAP &AI Tư vấn Phương án Khắc phục
- **Tiêu đề:** Từ Phát hiện Khoảng cách (GAP) đến AI Tư vấn có cấu trúc
- **Nội dung ngắn gọn:**
  - **Khóa Baseline ban đầu:** Lưu cứng kết luận, `review_token`, bằng chứng và tiêu chí tại thời điểm phát hiện.
  - **AI Tư vấn (`Advice` Schema — 15 trường):**
    - *Bị sai / thiếu gì:* Vấn đề, Nguyên nhân cần xác minh, Câu hỏi làm rõ (`clarification_questions`).
    - *Phải làm gì, ở đâu:* Mục tiêu, Lý do, Vị trí, Bộ phận, Nguồn lực, Thời gian dự kiến, Checklist bước con (`tasks`).
    - *Phải nộp gì mới đạt chuẩn:* Bằng chứng cần cung cấp, Điều kiện nghiệm thu, Cách kiểm tra lại.
- **Hình ảnh / Sơ đồ cần sử dụng:** Ảnh chụp màn hình khung *Phân tích tư vấn / thông tin cần xác minh* trên thẻ Hành động khắc phục.
- **Nội dung thuyết trình:** Khi một control chưa đạt, AI Tư vấn sẽ đọc bối cảnh doanh nghiệp, tiêu chí rubric và trích đoạn bằng chứng đang thiếu để sinh ra phương án khắc phục gồm 15 trường chi tiết: chỉ rõ bị sai ở đâu, cần làm những bước nào, phải nộp thêm tài liệu gì và kiểm tra lại ra sao mới đạt chuẩn.

---

### Slide 10: Duyệt Kế hoạch, Giao việc Phối hợp & Phân công Bước con
- **Tiêu đề:** Chuyên viên Duyệt, Giao việc & Theo dõi Tiến độ Tuần tự
- **Nội dung ngắn gọn:**
  - Đề xuất của AI luôn ở trạng thái **`Chờ duyệt` (`PENDING_APPROVAL`)**.
  - Chuyên viên chỉnh sửa phương án, duyệt và giao cho **Người chính (`assignee`)** + **Người phối hợp (`collaborator_ids`)** + **Thời hạn**.
  - Phân công chi tiết tới từng bước công việc con (`assign_task`).
  - Các bước con thực hiện theo **thứ tự phụ thuộc tuần tự**.
- **Hình ảnh / Sơ đồ cần sử dụng:** Ảnh chụp màn hình giao diện *Duyệt và giao thực hiện* cùng danh sách checkbox bước con.
- **Nội dung thuyết trình:** AI không bao giờ được tự động giao việc hay phê duyệt. Chuyên viên tư vấn là người rà soát, chỉnh sửa phương án của AI rồi mới duyệt giao cho nhân sự phụ trách chính và người phối hợp bên phía doanh nghiệp.

---

### Slide 11: Xác minh Độc lập, Đánh giá lại & Phê duyệt SoA
- **Tiêu đề:** Nguyên tắc Phân tách Nhiệm vụ & Xác minh Độc lập
- **Nội dung ngắn gọn:**
  - Doanh nghiệp phải đính kèm **bằng chứng mới nộp sau baseline** trước khi gửi xác minh.
  - **Chặn tự xác minh:** Người thực hiện chính và người phối hợp bị chặn `403` nếu tự xác minh công việc của mình.
  - **4 kết quả xác minh:** *Xác minh đạt* · *Cải thiện một phần* · *Trả làm lại* · *Yêu cầu bổ sung*.
  - Chỉ được *Xác minh đạt* khi người xác minh độc lập đã ký thẩm định tiêu chí hiện hành (`Compliant`) viện dẫn nguồn mới.
- **Hình ảnh / Sơ đồ cần sử dụng:** Sơ đồ State Machine khắc phục và ảnh chụp màn hình 2 cột *Trước khắc phục — giữ nguyên* vs. *Hiện tại — cần thẩm định*.
- **Nội dung thuyết trình:** Hệ thống áp dụng nghiêm ngặt nguyên tắc phân tách nhiệm vụ của kiểm toán ISO: người thực hiện không thể tự xác minh công việc của mình, và việc hoàn thành checklist công việc không tự động biến control thành tuân thủ nếu chưa có bằng chứng mới được người xác minh độc lập thẩm định.

---

### Slide 12: Sổ Rủi ro (5×5), Sổ Yêu cầu & Hộp thư Thông báo
- **Tiêu đề:** Quản trị Rủi ro, Danh mục Yêu cầu & Thông báo Nhắc hạn
- **Nội dung ngắn gọn:**
  - **Sổ rủi ro 5×5:** Liên kết tài sản, kịch bản, điểm rủi ro ban đầu/còn lại, phương án xử lý với Control & Phát hiện.
  - **Sổ yêu cầu có nguồn:** Lưu tham chiếu tiêu chuẩn/pháp lý/hợp đồng, phiên bản và căn cứ quyền sử dụng.
  - **Chống tự duyệt sổ:** Người tạo/sửa mục sổ không được tự rà soát mục sổ đó.
  - **Hộp thư thông báo:** Thông báo giao việc, giao bước con, gửi xác minh, kết quả xác minh, nhắc sắp đến hạn (3 ngày) và quá hạn.
- **Hình ảnh / Sơ đồ cần sử dụng:** Ảnh chụp màn hình *Sổ rủi ro & danh mục yêu cầu có nguồn* và *Thông báo khắc phục*.
- **Nội dung thuyết trình:** Bên cạnh luồng khắc phục, hệ thống tích hợp Sổ rủi ro 5x5 và Sổ yêu cầu có nguồn. Các mục sổ đã được người thứ hai rà soát sẽ được tự động đưa vào ngữ cảnh để AI Tư vấn tham khảo khi lập kế hoạch khắc phục.

---

### Slide 13: Dashboard 3 Góc nhìn & Báo cáo Trước–Sau 5 Định dạng
- **Tiêu đề:** Dashboard Theo Vai trò & Xuất Báo cáo Đa định dạng
- **Nội dung ngắn gọn:**
  - **3 góc nhìn Dashboard:** *Chuyên viên* (rủi ro, việc khẩn cấp) · *Doanh nghiệp* (tiến độ, tiêu chí chưa đáp ứng) · *Lãnh đạo* (mức độ đáp ứng, nguồn lực, quyết định chờ).
  - **Bộ lọc 9 trạng thái của 56 Control** kèm danh sách việc cụ thể (`required_tasks`).
  - **Xuất báo cáo Trước–Sau:** PDF Tiếng Việt Unicode, Excel XLSX (8 sheet), CSV, HTML bản in, JSON.
- **Hình ảnh / Sơ đồ cần sử dụng:** Ảnh chụp màn hình *Dashboard tư vấn và khắc phục* + Ảnh chụp file PDF và Excel 8 sheet xuất ra từ hệ thống.
- **Nội dung thuyết trình:** Toàn bộ dữ liệu được tổng hợp theo thời gian thực trên Dashboard 3 góc nhìn và xuất ra 5 định dạng báo cáo chuyên nghiệp, hỗ trợ đầy đủ font tiếng Việt Unicode và chống chèn mã độc CSV/Excel.

---

### Slide 14: Phân quyền RBAC & Bảo mật Hệ thống
- **Tiêu đề:** Kiểm soát Truy cập, Concurrency & An toàn Ứng dụng
- **Nội dung ngắn gọn:**
  - **Cách ly đa khách hàng:** Kiểm tra `assessment_members` trên mọi API, chặn `403` khi truy cập chéo ID.
  - **Chống ghi đè đồng thời:** Khóa dòng `SELECT ... FOR UPDATE`, `pg_advisory_xact_lock` và kiểm tra `expected_version` / `snapshot_hash` (`409 Conflict`).
  - **Bảo mật:** PBKDF2-SHA256 (310k vòng), khóa brute-force 15 phút, chống SQLi, XSS, Formula Injection và Path Traversal.
- **Hình ảnh / Sơ đồ cần sử dụng:** Bảng ma trận phân quyền 4 vai trò (`consultant`, `verifier`, `business_admin`, `operator`).
- **Nội dung thuyết trình:** Mọi quy tắc phân quyền đều được cưỡng chế ở tầng Backend và Database chứ không chỉ ẩn nút ở giao diện. Hệ thống sử dụng khóa giao dịch PostgreSQL để đảm bảo hai người thao tác cùng lúc không ghi đè mất dữ liệu của nhau.

---

### Slide 15: Kết quả Thực nghiệm AI & Kiểm thử Hệ thống
- **Tiêu đề:** Kết quả Thực nghiệm & Kiểm thử Toàn diện
- **Nội dung ngắn gọn:**
  - **Thực nghiệm 18 A.8 Raw v2:** Khớp khóa thiết kế nhóm 206/216 lượt (95,37%); chạy thành công 18/18 Probe Live v2.
  - **Tập mở rộng 38 hồ sơ mô phỏng:** Khớp khóa thiết kế phát triển 23/38 ca (60,53%), giữ nguyên 15 ca lệch để phân tích chuyên môn.
  - **Kiểm thử phần mềm:** **442/442 test Python PASS** · **14/14 test JS PASS** · **17/17 kịch bản UI Edge PASS**.
  - **E2E Real-Write & Restart:** Chạy xuyên suốt trên PostgreSQL thật + Qwen2.5:7b thật, bảo toàn 100% dữ liệu sau khi khởi động lại.
- **Hình ảnh / Sơ đồ cần sử dụng:** Bảng tổng hợp kết quả test từ `docs/FINAL_ACCEPTANCE_2026.md`.
- **Nội dung thuyết trình:** Nhóm báo cáo trung thực các con số thực nghiệm: giữ nguyên cả các ca AI lệch khóa thiết kế để phân tích, đồng thời đạt 442 bài kiểm thử Python, 14 bài kiểm thử JS và kiểm thử xuyên suốt ghi thật qua khởi động lại.

---

### Slide 16: Phân định rõ Phần mềm đã hoàn tất & Việc cần Con người thực hiện
- **Tiêu đề:** Tính Trung thực Học thuật & Giới hạn Tự động hóa
- **Nội dung ngắn gọn:**
  - **Phần mềm đã hoàn tất 100%:** Luồng đánh giá 56 control, thực nghiệm 18 A.8, đa khách hàng, AI tư vấn, giao việc, xác minh độc lập, dashboard, báo cáo.
  - **Phần chờ dữ liệu & quyết định con người trong đợt chính:**
    - Bổ sung nguồn bằng chứng thật cho 37 control còn thiếu & thay nguồn `A.6.2` (1 ký tự).
    - Chuyên gia xác nhận rubric, chấm độc lập trên tập mới, ghi 56 quyết định áp dụng và ký duyệt SoA.
- **Hình ảnh / Sơ đồ cần sử dụng:** Ảnh chụp màn hình *Bảng điều kiện sẵn sàng phê duyệt SoA 56 control* (`SoAReadiness.jsx`).
- **Nội dung thuyết trình:** Hệ thống tuân thủ nguyên tắc không làm giả dữ liệu để báo cáo đẹp: những control chưa có hồ sơ thật được hiển thị rõ là đang thiếu nguồn, và chức năng phê duyệt SoA sẽ khóa cho đến khi con người cung cấp đủ quyết định và thẩm định.

---

### Slide 17: Demo Trực tiếp Hệ thống (Live Demo)
- **Tiêu đề:** Trình diễn Trực tiếp Quy trình Khép kín (Live Demo)
- **Nội dung ngắn gọn:**
  1. Tạo khách hàng & đợt đánh giá mới (bắt đầu rỗng) + Khai báo nhân sự/tài sản.
  2. Kiểm tra trước (Preflight) & nộp bằng chứng ban đầu cho `A.8.13` → AI Agent đánh giá (`Partially Compliant`).
  3. Tạo Phát hiện GAP → AI `qwen2.5:7b` tư vấn phương án khắc phục 15 trường.
  4. Chuyên viên duyệt & giao việc → Doanh nghiệp làm từng bước & nộp biên bản Restore Test mới.
  5. Người xác minh độc lập thẩm định & xác minh đạt → Xem Dashboard 3 góc nhìn & Xuất PDF/Excel Trước–Sau.
- **Hình ảnh / Sơ đồ cần sử dụng:** Sơ đồ luồng Demo 5 chặng cho Control `A.8.13` (Sao lưu thông tin).
- **Nội dung thuyết trình:** Tiếp theo, nhóm xin chuyển sang màn hình ứng dụng đang chạy thực tế để demo trực tiếp quy trình từ lúc tiếp nhận khách hàng mới đến khi xuất báo cáo nghiệm thu PDF và Excel.

---

### Slide 18: Kết luận & Hướng phát triển
- **Tiêu đề:** Kết luận & Hướng phát triển Tiếp theo
- **Nội dung ngắn gọn:**
  - **Kết quả đạt được:** Chuyển hóa thành công công cụ đánh giá thành nền tảng quản lý tư vấn & khắc phục ISO/IEC 27001:2022 có kiểm soát bằng chứng.
  - **Hướng phát triển:**
    - Mở rộng từ 56 Control lên toàn bộ 93 Control Annex A và các điều khoản 4–10.
    - Tách worker sang hàng đợi phân tán (Celery/Redis) và tích hợp chữ ký số cho biên bản thẩm định.
    - Thực hiện đánh giá đối chứng độc lập với kiểm toán viên ISO 27001 trên doanh nghiệp thực tế.
- **Hình ảnh / Sơ đồ cần sử dụng:** Sơ đồ lộ trình phát triển (56 Control MVP → 93 Control Full ISMS → Enterprise Cloud Deployment).
- **Nội dung thuyết trình:** Nhóm xin chân thành cảm ơn sự hướng dẫn của Giảng viên và sự lắng nghe của Hội đồng. Nhóm rất mong nhận được các câu hỏi và ý kiến đóng góp của các thầy cô.
