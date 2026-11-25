# ĐỀ CƯƠNG BÁO CÁO ĐỒ ÁN TỐT NGHIỆP / ĐỒ ÁN CHUYÊN NGÀNH

**Tên đề tài:**  
**HỆ THỐNG AI AGENT HỖ TRỢ ĐÁNH GIÁ VÀ TƯ VẤN KHẮC PHỤC TUÂN THỦ AN TOÀN THÔNG TIN THEO TIÊU CHUẨN ISO/IEC 27001:2022**

*(Đề cương này được thiết kế bám sát 100% kiến trúc, mã nguồn, cơ sở dữ liệu và kết quả thực nghiệm thực tế trong repository `ISO27001-AI-Agent`)*

---

## MỤC LỤC CHI TIẾT DỰ KIẾN

### LỜI CAM ĐOAN, LỜI CẢM ƠN, DANH MỤC HÌNH VẼ, DANH MỤC BẢNG BIỂU, DANH MỤC TỪ VIẾT TẮT

---

### CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI
- **1.1. Đặt vấn đề và tính cấp thiết của đề tài**
  - Nhu cầu đánh giá và duy trì Hệ thống Quản lý An toàn Thông tin (ISMS) theo tiêu chuẩn ISO/IEC 27001:2022 tại các doanh nghiệp.
  - Khoảng trống của các phương pháp truyền thống: quản lý bằng bảng tính rời rạc, khó kiểm chứng tính toàn vẹn của bằng chứng gốc, và dừng lại ở việc chấm "Đạt / Không đạt" mà thiếu quy trình tư vấn khắc phục – giao việc – xác minh độc lập.
  - Rủi ro khi sử dụng các công cụ AI/Chatbot thông thường trong kiểm toán ATTT: hiện tượng ảo giác (hallucination), tự suy diễn tuân thủ khi thiếu bằng chứng, và thiếu cơ chế truy vết kiểm toán (audit trail).
- **1.2. Mục tiêu của đề tài**
  - *Mục tiêu tổng quát:* Xây dựng nền tảng quản lý quy trình đánh giá và tư vấn khắc phục ISO/IEC 27001:2022 kết hợp AI Agent có kiểm soát bằng chứng (Evidence-bound AI Agent).
  - *Mục tiêu cụ thể:*
    1. Quản lý phạm vi **56 biện pháp kiểm soát (Controls)** thuộc 3 nhóm: Con người (`A.6`, 8 control), Vật lý (`A.7`, 14 control), Kỹ thuật (`A.8`, 34 control).
    2. Thực nghiệm chuyên sâu **18 Control A.8** với bộ 108 kịch bản Raw Replay và 18 Probe Live v2 trên container cô lập.
    3. Xây dựng vòng đời tư vấn và khắc phục khép kín cho nhiều doanh nghiệp khách hàng: *Phát hiện GAP → AI Tư vấn phương án → Chuyên viên duyệt & Giao việc/Bước con → Doanh nghiệp thực hiện & Nộp bằng chứng sau → Người xác minh độc lập kiểm tra → Đánh giá lại → Xuất báo cáo Trước/Sau*.
- **1.3. Đối tượng và phạm vi nghiên cứu**
  - Đối tượng: 56 Control thuộc Phụ lục A (ISO/IEC 27001:2022) và quy trình phối hợp hai bên (Đơn vị tư vấn/đánh giá & Doanh nghiệp khách hàng).
  - Giới hạn phạm vi và nguyên tắc đạo đức/học thuật: Hệ thống là công cụ hỗ trợ kỹ thuật, không bao gồm toàn văn bản quyền tiêu chuẩn, không tự động tuyên bố đạt chứng nhận ISO và không tự phê duyệt Tuyên bố tính áp dụng (SoA) thay con người.
- **1.4. Phương pháp nghiên cứu và bố cục báo cáo**
  - Phương pháp: Nghiên cứu tiêu chuẩn, thiết kế kiến trúc hướng trạng thái (LangGraph StateGraph), thực nghiệm đối chứng với baseline luật (Rule-based) và chấm mù (Blind Review).

---

### CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ
- **2.1. Tiêu chuẩn ISO/IEC 27001:2022 và Phụ lục A (Annex A)**
  - Cấu trúc 4 nhóm kiểm soát mới trong phiên bản 2022 (Organizational, People, Physical, Technological) và cập nhật Amd 1:2024.
  - Khái niệm Bằng chứng kiểm toán (Audit Evidence), Tiêu chí đạt (Pass Criteria / Rubric), Phát hiện khoảng cách (GAP / Finding), Kế hoạch xử lý rủi ro (Risk Treatment Plan) và Tuyên bố tính áp dụng (Statement of Applicability – SoA).
  - Nguyên tắc phân tách nhiệm vụ (Separation of Duties) trong kiểm toán và xác minh khắc phục.
- **2.2. Kiến trúc AI Agent và Mô hình Ngôn ngữ Lớn cục bộ (Local LLM)**
  - Sự khác biệt giữa Chatbot hội thoại tự do và AI Agent hướng trạng thái có ràng buộc công cụ & guardrail (`LangGraph`).
  - Mô hình `Qwen2.5:7b` vận hành cục bộ qua `Ollama` đảm bảo quyền riêng tư dữ liệu doanh nghiệp (Data Privacy – không gửi tài liệu nội bộ lên đám mây bên thứ ba).
  - Kỹ thuật ép cấu trúc đầu ra (Structured Output / JSON Schema) và kiểm soát ngân sách ngữ cảnh (`Context Window Budgeting`).
- **2.3. Các công nghệ nền tảng trong hệ thống**
  - Backend: FastAPI, Pydantic v2, PostgreSQL 16 (giao dịch ACID, khóa bi quan `FOR UPDATE`, khóa lạc quan theo `version`/`hash` và `pg_advisory_xact_lock`).
  - Frontend: React 19, Vite, TailwindCSS, đồng bộ trạng thái điều hướng qua URL Hash.
  - Bảo mật và xuất bản tài liệu: Băm mật khẩu PBKDF2-HMAC-SHA256, kiểm toàn vẹn tệp bằng SHA-256, xuất báo cáo PDF Unicode (`ReportLab`) và Excel đa trang tính (`OpenPyXL`).

---

### CHƯƠNG 3: PHÂN TÍCH YÊU CẦU VÀ THIẾT KẾ HỆ THỐNG
- **3.1. Phân tích yêu cầu hệ thống**
  - *Yêu cầu chức năng:* Quản lý đa khách hàng và đợt đánh giá; khai báo danh mục nhân sự/tài khoản/tài sản; tiếp nhận và kiểm tra trước (preflight) bằng chứng; AI đánh giá 56 Control; quản lý Sổ rủi ro (5×5) và Sổ yêu cầu; phát hiện GAP và khóa baseline; AI tư vấn khắc phục; giao việc/phối hợp/bước con; xác minh độc lập; Dashboard 3 góc nhìn; hộp thư thông báo; xuất báo cáo 5 định dạng.
  - *Yêu cầu phi chức năng:* Cách ly dữ liệu đa khách hàng (Multi-tenant Isolation), chống tự xác minh, chống giả mạo bằng chứng, bảo toàn dữ liệu qua khởi động lại (Restart Persistence), chống SQL Injection / XSS / CSV Formula Injection.
- **3.2. Thiết kế phân quyền (RBAC) và Mô hình phối hợp hai bên**
  - Quyền hệ thống (`admin`, `assessor`) và 4 vai trò theo từng đợt đánh giá (`consultant`, `verifier`, `business_admin`, `operator`).
  - Ma trận phân quyền chi tiết ở tầng Backend API (ai được tạo khách hàng, sửa danh mục, tạo phát hiện, duyệt kế hoạch, thực hiện bước con, gửi xác minh, xác minh đạt và phê duyệt SoA).
- **3.3. Thiết kế kiến trúc tổng thể và luồng dữ liệu**
  - Sơ đồ kiến trúc 4 tầng: Giao diện React → FastAPI Application → LangGraph AI & Evidence Collectors → PostgreSQL & Kho bản gốc SHA-256.
  - Thiết kế đồ thị trạng thái AI Agent (`node_plan` → `node_collect` → `node_evaluate` → `node_verify`).
  - Thiết kế máy trạng thái (State Machine) vòng đời hành động khắc phục (`PENDING_APPROVAL` → `NOT_STARTED` → `IN_PROGRESS` → `AWAITING_VERIFICATION` → `REWORK` / `NEEDS_INFORMATION` → `VERIFIED` → `CLOSED`).
- **3.4. Thiết kế Cơ sở dữ liệu PostgreSQL**
  - Sơ đồ thực thể liên kết (ERD) của 17 bảng dữ liệu chính:
    - Nhóm Quản trị & Đa khách hàng: `team_users`, `team_sessions`, `login_attempts`, `consulting_clients`, `consulting_campaigns`, `assessment_campaigns`, `assessment_members`.
    - Nhóm Danh mục & Đánh giá 56 Control: `controls`, `compliance_rubrics`, `evidence`, `evaluations`, `control_progress`, `agent_jobs`, `source_evaluation_batches`, `assessment_events`, `enterprise_company`, `enterprise_sim_people`, `enterprise_company_accounts`, `enterprise_sim_assets`.
    - Nhóm Tư vấn, Khắc phục & Quản trị rủi ro: `remediation_roles`, `remediation_records`, `governance_records`, `remediation_notifications`.

---

### CHƯƠNG 4: XÂY DỰNG VÀ TRIỂN KHAI HỆ THỐNG
- **4.1. Xây dựng phân hệ Quản lý Đa khách hàng, Đợt đánh giá và Danh mục doanh nghiệp**
  - Cơ chế tách `inventory_mode` (`client` so với `lab`): đợt khách hàng bắt đầu rỗng, không tự nạp dữ liệu giả lập.
  - Khai báo nhân viên, tài khoản, tài sản có kiểm tra `expected_snapshot_hash` và ghi lịch sử trước/sau (`ClientManagement.jsx`, `ClientInventoryEditor.jsx`).
- **4.2. Xây dựng phân hệ Tiếp nhận, Kiểm định toàn vẹn Nguồn và Đánh giá 56 Control**
  - Bộ lọc chất lượng văn bản (`source_quality.py`), kiểm tra trước không ghi DB (`validate`) và kho lưu bản gốc theo SHA-256 (`source_intake.py`).
  - Thực thi đánh giá đơn lẻ và đánh giá theo lô trên server (`batch_work.py`), cơ chế tự phục hồi và mở khóa khi dịch vụ khởi động lại.
- **4.3. Xây dựng phân hệ Thực nghiệm chuyên sâu 18 Control A.8**
  - Thiết kế container `iso-a8-lab` không kết nối mạng ngoài với 18 Probe Live v2 (5 quan sát tài nguyên, 13 phép thử chủ động TCP/TLS/Auth/Crypto) và 108 ca Raw Replay.
  - Giao thức chấm mù (`blind-v3-coordinator-only`) và sổ theo dõi xử lý bất đồng (`disagreement_ledger.py`).
- **4.4. Xây dựng phân hệ Phát hiện GAP, AI Tư vấn khắc phục và Giao việc phối hợp**
  - Khóa `baseline` phát hiện và quét ứng viên GAP từ kết quả đánh giá hiện hành.
  - Xây dựng prompt và schema `Advice` (15 trường cấu trúc + `clarification_questions`), trích xuất nội dung bằng chứng thực tế đưa vào `qwen2.5:7b` và xử lý lưu lỗi khi model trả sai định dạng.
  - Luồng chuyên viên sửa/duyệt, giao người chính, người phối hợp, phân công từng bước con (`assign_task`) và kiểm soát thứ tự hoàn thành bước.
- **4.5. Xây dựng phân hệ Xác minh độc lập, Thẩm định tiêu chí và Phê duyệt SoA**
  - Ràng buộc đính kèm bằng chứng mới sau baseline, chặn người thực hiện tự xác minh, luồng trả bổ sung (`more_information` / `rework`) và gửi xác minh lại.
  - Liên kết xác minh đạt với chữ ký thẩm định từng tiêu chí hiện hành (`ControlCriteriaReview.jsx`) và bảng điều kiện sẵn sàng phê duyệt SoA 56 dòng (`SoAReadiness.jsx`).
- **4.6. Xây dựng Dashboard 3 góc nhìn, Thông báo và Xuất báo cáo 5 định dạng**
  - Dashboard theo góc nhìn *Chuyên viên*, *Doanh nghiệp*, *Lãnh đạo* và bộ lọc 9 trạng thái công việc của 56 Control (`ConsultingDashboard.jsx`).
  - Hộp thư thông báo trong ứng dụng, worker quét nhắc hạn 3 ngày và tích hợp tùy chọn SMTP an toàn qua biến môi trường.
  - Xuất báo cáo PDF tiếng Việt Unicode, Excel 8 sheet, CSV, HTML bản in và JSON.

---

### CHƯƠNG 5: THỰC NGHIỆM, KIỂM THỬ VÀ ĐÁNH GIÁ KẾT QUẢ
- **5.1. Môi trường thực nghiệm và phương pháp kiểm thử**
  - Cấu hình phần cứng/phần mềm: Docker PostgreSQL 16 (cổng 5433), Container `iso-a8-lab`, Ollama `qwen2.5:7b`, FastAPI, React/Playwright Edge.
  - Phân tách rõ 4 lớp kiểm thử: Unit/Contract Test, UI Mocked Form Test, Isolated Real-Write E2E Test (trên DB tạm) và Nghiệm thu hồ sơ chuyên môn.
- **5.2. Kết quả thực nghiệm AI Agent trên 18 Control A.8 và 38 Hồ sơ mô phỏng**
  - Kết quả trên 108 ca Raw v2 (206/216 lượt khớp đáp án thiết kế nhóm – 95,37%) và 18 Probe Live v2.
  - Kết quả trên 38 hồ sơ doanh nghiệp mô phỏng mở rộng ngoài nhóm 18 A.8 (khớp khóa thiết kế phát triển 23/38 ca – 60,53%; phân tích chi tiết 15 ca lệch kết luận tổng và 19 tiêu chí lệch để người đánh giá rà soát).
  - Đánh giá hiệu quả của Guardrail `node_verify` và bộ lọc chất lượng nguồn (ví dụ: chặn nguồn `A.6.2` chỉ có 1 ký tự).
- **5.3. Kết quả kiểm thử toàn diện hệ thống phần mềm**
  - Kết quả **442/442 test Python đạt** và **14/14 test JavaScript đạt** (0 lỗi, 0 cảnh báo linter).
  - Kết quả **17/17 kịch bản giao diện Playwright Edge đạt**.
  - Kết quả **Kiểm thử xuyên suốt ghi thật (End-to-End Real-Write) và Restart Persistence**: Tạo 2 khách hàng độc lập, kiểm tra chặn truy cập chéo `403`, nộp nguồn trước/sau, gọi `qwen2.5:7b` tư vấn khắc phục, giao việc phối hợp, xác minh độc lập, xuất PDF/XLSX và giữ nguyên 100% dữ liệu sau khi khởi động lại dịch vụ.
- **5.4. Thảo luận về giới hạn hiện tại và các điều kiện nghiệm thu thực tế**
  - Phân tích rõ 37 Control còn chờ doanh nghiệp/nhóm bổ sung nguồn thực tế và các bước bắt buộc cần quyết định của con người (xác nhận rubric, chấm độc lập trên bộ kiểm định mới, quyết định tính áp dụng và phê duyệt SoA).

---

### CHƯƠNG 6: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN
- **6.1. Kết luận các kết quả đạt được**
  - Hoàn thành nền tảng phần mềm tích hợp trọn vẹn từ đánh giá bằng chứng 56 Control tới tư vấn, giao việc, xác minh khắc phục và báo cáo trước/sau.
  - Đảm bảo tính trung thực, toàn vẹn bằng chứng (SHA-256), phân quyền RBAC đa khách hàng và kiểm soát chặt chẽ giới hạn của AI.
- **6.2. Hạn chế của đồ án**
  - Phạm vi hiện tại tập trung vào 56 Control Phụ lục A (chưa bao phủ các điều khoản quản trị 4–10 và nhóm A.5); worker đánh giá chạy chung tiến trình API; chưa xử lý OCR hình ảnh/video tự động.
- **6.3. Hướng phát triển tiếp theo**
  - Mở rộng đủ 93 Control của Annex A và các điều khoản 4–10 của ISO/IEC 27001:2022.
  - Tách hàng đợi tác vụ phân tán (Celery / Redis) và triển khai hạ tầng Production (TLS Reverse Proxy, sao lưu tự động, chữ ký số cho biên bản thẩm định).
  - Tổ chức đánh giá đối chứng độc lập với chuyên gia kiểm toán ISO 27001 trên dữ liệu doanh nghiệp thực tế.

---

### TÀI LIỆU THAM KHẢO & PHỤ LỤC
- **Phụ lục A:** Danh mục 56 Control và ma trận loại bằng chứng (`docs/MA_TRAN_56_CONTROL.md`).
- **Phụ lục B:** Cấu trúc JSON Schema của AI Đánh giá (`ControlEvaluationOutput`) và AI Tư vấn Khắc phục (`Advice`).
- **Phụ lục C:** Minh chứng kết quả kiểm thử tự động và biên nhận kiểm thử ghi thật (`docs/FINAL_ACCEPTANCE_2026.md`).
