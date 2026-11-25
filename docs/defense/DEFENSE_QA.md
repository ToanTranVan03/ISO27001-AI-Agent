# BỘ 28 CÂU HỎI PHẢN BIỆN & CÂU TRẢ LỜI MẪU BẢO VỆ ĐỒ ÁN — ISO27001-AI-AGENT

Bộ câu hỏi và câu trả lời dưới đây được biên soạn bám sát **100% mã nguồn, kiến trúc và số liệu thực nghiệm có thật** trong repository `ISO27001-AI-Agent`. Tuyệt đối không phóng đại độ chính xác và không tuyên bố hệ thống thay thế chứng nhận ISO.

---

### Câu 1: Tại sao nhóm lại sử dụng kiến trúc AI Agent (LangGraph) thay vì chỉ gọi API LLM thông thường?
- **Trả lời mẫu:** Nếu chỉ gọi một prompt LLM thông thường, mô hình rất dễ suy diễn tự do, bỏ qua bước kiểm tra chất lượng tài liệu hoặc trích dẫn bằng chứng không tồn tại. Nhóm sử dụng **LangGraph (`StateGraph`)** trong `agent_core/graph_builder.py` để chia quá trình đánh giá thành 4 nút trạng thái độc lập: `node_plan` (xác định chế độ nguồn), `node_collect` (thu thập và lọc toàn vẹn nguồn SHA-256), `node_evaluate` (kiểm tra ngân sách token và suy luận theo Rubric), và `node_verify` (guardrail hậu kiểm đối chiếu mã `evidence_id` thực tế). Nhờ đó, hệ thống kiểm soát được từng bước, lưu lại `audit_trail` rõ ràng và chặn được kết luận sai ngay tại nút hậu kiểm.

### Câu 2: AI Agent trong hệ thống này khác với một Chatbot hỏi-đáp ISO 27001 như thế nào?
- **Trả lời mẫu:** Hệ thống không có cửa sổ chat tự do mà là một **Evidence-bound Workflow Agent (AI gắn chặt với bằng chứng và quy trình)**:
  1. **Đầu vào bị khóa theo snapshot:** AI chỉ được đọc các bằng chứng đã qua kiểm định chất lượng/SHA-256 của đúng đợt đánh giá và đúng Control đó.
  2. **Đầu ra ép kiểu JSON Schema nghiêm ngặt:** Đánh giá trả về `ControlEvaluationOutput` (4 trường cố định), tư vấn khắc phục trả về `Advice` (15 trường cấu trúc + câu hỏi bổ sung).
  3. **Gắn trực tiếp vào máy trạng thái nghiệp vụ:** Kết quả của AI tự động liên kết với bảng tiến độ, tạo bản nháp kế hoạch khắc phục (`PENDING_APPROVAL`) kèm danh sách công việc con để chuyên viên duyệt và giao việc, chứ không chỉ trả lời văn bản rồi biến mất.

### Câu 3: AI dựa vào những nguồn dữ liệu nào để đánh giá một Control?
- **Trả lời mẫu:** Đối với một đợt đánh giá khách hàng thực tế (`inventory_mode = 'client'`), AI chỉ sử dụng:
  1. **Tiêu chí chấm điểm (Rubric):** Định nghĩa trong `docs/compliance_rubrics.json` cho từng Control (`Compliant`, `Partially Compliant`, `Non-Compliant`).
  2. **Bằng chứng do người dùng nộp (`user_evidence_only`):** Các tài liệu chính sách, biên bản, file cấu hình, hoặc log hệ thống đã tải lên cho Control đó và vượt qua bài kiểm tra chất lượng văn bản (`source_quality.py`) cũng như kiểm tra khớp mã băm bản gốc (`source_verification.py`).
  - Riêng trong môi trường phòng lab nghiên cứu (`inventory_mode = 'lab'`), hệ thống hỗ trợ thêm 18 probe thu thập trực tiếp từ container `iso-a8-lab` và dữ liệu mô phỏng để phục vụ thực nghiệm.

### Câu 4: Làm thế nào hệ thống hạn chế hiện tượng AI "ảo giác" (Hallucination)?
- **Trả lời mẫu:** Nhóm áp dụng **5 lớp bảo vệ đa tầng**:
  1. **Chặn trước khi gọi AI (Zero-evidence short-circuit):** Nếu Control chưa có nguồn bằng chứng hợp lệ, `node_evaluate` trả về ngay `Insufficient Evidence` mà không gọi LLM.
  2. **Ép nhiệt độ và Schema:** Đặt `temperature = 0.0` và ép phản hồi qua Pydantic JSON Schema (`extra='forbid'`).
  3. **Kiểm soát ngân sách ngữ cảnh (`validate_budget`):** Đảm bảo tổng đầu vào không vượt ngưỡng 16.384 token của model, tránh việc ngữ cảnh bị cắt cụt âm thầm làm AI mất thông tin.
  4. **Hậu kiểm mã viện dẫn (`node_verify`):** Nếu AI trả về `evidence_ids` không nằm trong tập bằng chứng thực tế của Control đó, hoặc kết luận đạt mà không trích dẫn được `evidence_id` nào, `node_verify` tự động hủy kết luận của AI và đưa về `Insufficient Evidence` (`confidence = 0.0`).
  5. **Bắt buộc đặt câu hỏi khi thiếu dữ liệu trong Tư vấn khắc phục:** Nếu thiếu nội dung nguồn mà AI tư vấn không sinh `clarification_questions`, backend từ chối lưu và báo lỗi.

### Câu 5: AI có thể tự tuyên bố doanh nghiệp đạt chuẩn ISO 27001 hoặc tự phê duyệt kế hoạch không?
- **Trả lời mẫu:** **Tuyệt đối không.** Trong toàn bộ hệ thống:
  - Kết luận của AI chỉ được hiển thị là *"Kết quả máy — chưa thay xác nhận của người phụ trách"*.
  - Mọi phương án khắc phục do AI sinh ra đều mang nhãn `OLLAMA_DRAFT_REQUIRES_REVIEW` ở trạng thái `PENDING_APPROVAL`, không có người nhận (`assignee = None`) và không có hạn (`due_date = None`).
  - Mọi báo cáo xuất ra (JSON, CSV, HTML, XLSX, PDF) đều gắn cứng cờ `certification_claim = False` và dòng cảnh báo rõ: *"Báo cáo hỗ trợ đánh giá và khắc phục; không phải chứng nhận ISO"*.

### Câu 6: Tại sao hệ thống bắt buộc phải có bước "Xác minh độc lập" (Independent Verification)?
- **Trả lời mẫu:** Theo chuẩn mực kiểm toán ISO/IEC 27001 (nguyên tắc khách quan và phân tách nhiệm vụ – Separation of Duties), người trực tiếp thực hiện cấu hình hoặc viết tài liệu không được tự nghiệm thu công việc của chính mình. Trong `backend/remediation.py`, hệ thống kiểm tra ID người dùng ở tầng backend: cả người chịu trách nhiệm chính (`assignee`) lẫn người phối hợp (`collaborator_ids`) đều bị chặn bằng lỗi `PermissionError (403)` nếu gọi lệnh `verify`, `return` hoặc `close`. Phải có một tài khoản khác thuộc vai trò `consultant` hoặc `verifier` kiểm tra bằng chứng mới và xác minh.

### Câu 7: Khi người thực hiện tích hoàn thành 100% các bước công việc khắc phục, Control đó có tự động chuyển sang "Tuân thủ" (Compliant) không?
- **Trả lời mẫu:** **Không.** Đây là một quy tắc thiết kế rất quan trọng của hệ thống: tiến độ công việc (`workflow state`) tách biệt hoàn toàn với trạng thái tuân thủ (`compliance status`). Khi người thực hiện tích xong các task và nộp bằng chứng mới, hành động chỉ chuyển sang `AWAITING_VERIFICATION`. Để xác minh đạt (`VERIFIED`), người xác minh độc lập bắt buộc phải đọc bằng chứng mới, thực hiện **Thẩm định từng tiêu chí hiện hành (`POST /scope56/reviews`)** có viện dẫn mã bằng chứng mới đó và kết luận `Compliant`.

### Câu 8: Vì sao hệ thống phải lưu giữ bản gốc bằng chứng và khóa Baseline ban đầu khi tạo Phát hiện (GAP)?
- **Trả lời mẫu:** Trong quá trình khắc phục kéo dài nhiều tuần, doanh nghiệp sẽ nộp thêm tài liệu mới hoặc chạy đánh giá lại nhiều lần. Nếu không khóa `baseline` (gồm kết luận ban đầu, `review_token`, danh sách mã bằng chứng ban đầu kèm `sha256_hash` và tiêu chí rubric) tại thời điểm phát hiện GAP, hệ thống sẽ mất dấu trạng thái lịch sử và không thể chứng minh được sự cải thiện **"Trước khắc phục vs. Sau khắc phục"**. Nhờ khóa `baseline`, báo cáo nghiệm thu luôn đối chiếu được rõ ràng trước đây thiếu gì và sau khi khắc phục đã bổ sung được bằng chứng nào.

### Câu 9: Mã băm SHA-256 có chứng minh được tài liệu doanh nghiệp nộp lên là "thật" và "đúng sự thật" không?
- **Trả lời mẫu:** **Không.** Hệ thống ghi chú rất rõ trên giao diện và trong code (`provenance_verified = False`): mã băm **SHA-256 chỉ chứng minh tính toàn vẹn kỹ thuật (Integrity)** — tức là tệp bằng chứng không bị sửa đổi, làm hỏng hay tráo đổi kể từ thời điểm được nộp vào hệ thống, đồng thời giúp chống nạp trùng cùng một tệp. Còn việc nội dung bên trong tệp đó có phản ánh đúng thực tế vận hành của doanh nghiệp hay không (Authenticity & Adequacy) bắt buộc phải do chuyên viên đánh giá và người xác minh độc lập đọc và thẩm định.

### Câu 10: Hệ thống xử lý như thế nào nếu doanh nghiệp nộp một file rác (ví dụ file chỉ có 1 ký tự hoặc lặp đi lặp lại một chữ) để qua mặt AI?
- **Trả lời mẫu:** Nhóm đã xây dựng module `evidence_collectors/source_quality.py` và `source_verification.py` dùng chung cho cả cổng nộp web, CLI preflight, đầu vào AI Agent và cổng thẩm định:
  - Chặn các tệp có số ký tự chữ/số quá ít, tỷ lệ ký tự lặp bất thường, chứa byte NUL hoặc JSON sai cú pháp.
  - Ví dụ thực tế trong dự án: nguồn cũ của `A.6.2` trong đợt lab chỉ trích xuất được 1 ký tự đã bị bộ lọc đánh dấu `usable = False`, loại khỏi đầu vào của AI Agent, khóa nút chạy đánh giá và hiển thị cảnh báo yêu cầu nộp lại nguồn.

### Câu 11: AI Tư vấn khắc phục hoạt động như thế nào khi dữ liệu đầu vào chưa đủ?
- **Trả lời mẫu:** Trong `backend/remediation_api.py` (endpoint `POST /findings/{id}/ai-proposal`), schema `Advice` có trường `clarification_questions` (danh sách câu hỏi cần làm rõ) và `possible_causes` (nguyên nhân có thể — cần xác minh). System prompt yêu cầu `qwen2.5:7b` không được bịa nguyên nhân nếu bằng chứng chưa rõ mà phải đặt câu hỏi cụ thể cho doanh nghiệp. Đặc biệt, dòng kiểm tra hậu kiểm bắt buộc: nếu Control đang không có nội dung trích đoạn bằng chứng nào mà model trả về danh sách `clarification_questions` rỗng, backend sẽ raise `ValueError` và từ chối lưu đề xuất đó.

### Câu 12: Khi AI Tư vấn khắc phục được gọi, những thông tin ngữ cảnh nào của doanh nghiệp được truyền vào prompt?
- **Trả lời mẫu:** Trước đó nhóm từng phát hiện lỗi trích đoạn nguồn bị rỗng do API chỉ trả metadata; nhóm đã sửa triệt để trong `backend/remediation_api.py` (dòng 320–340) để truyền đầy đủ 7 nhóm ngữ cảnh thực tế vào `qwen2.5:7b`:
  1. Thông tin phát hiện (`finding`, `location`, `reported_cause_unconfirmed`, `reported_risk_unconfirmed`).
  2. Bối cảnh doanh nghiệp & phạm vi ISMS (`company_context_unverified`, tối đa 1.200 ký tự/trường).
  3. Tiêu chí đạt của Control (`criteria` từ baseline) và loại bằng chứng kỳ vọng (`required_evidence_types`).
  4. Trích đoạn văn bản thực tế từ bảng `evidence` của đợt đó (`source_excerpts_untrusted`: tối đa 6 nguồn khả dụng, mỗi nguồn 1.500 ký tự kèm cờ `truncated`).
  5. Các mục trong **Sổ rủi ro** và **Sổ yêu cầu** đã được rà soát (`status = 'ACKNOWLEDGED'`) liên quan đến Control đó (`reviewed_registers_untrusted`).
  6. Lịch sử tối đa 8 hành động khắc phục trước đó trên cùng phát hiện (`prior_actions`).

### Câu 13: Nếu model Ollama bị tắt hoặc trả về JSON sai cấu trúc thì hệ thống xử lý ra sao? Có dùng mẫu cố định (fallback) để lấp vào không?
- **Trả lời mẫu:** **Không dùng fallback ngầm.** Nguyên tắc của hệ thống là không giả lập AI thành AI thật. Nếu Ollama không phản hồi hoặc `qwen2.5:7b` trả về JSON không khớp Pydantic schema:
  - Ở luồng đánh giá Control: Job được ghi nhận trạng thái `FAILED` kèm thông báo lỗi rõ ràng trong bảng `agent_jobs`, giữ nguyên kết luận cũ và mở khóa Control.
  - Ở luồng AI tư vấn khắc phục: Hệ thống bắt ngoại lệ, ghi một bản ghi `ai_proposal_failed` kèm phản hồi thô (`raw_response`) vào `history` của phát hiện để truy vết lỗi, và trả mã HTTP `502`, tuyệt đối không tự chèn một kế hoạch mẫu giả tạo.

### Câu 14: Độ chính xác của AI trong dự án được đo như thế nào và kết quả thực tế ra sao?
- **Trả lời mẫu:** Nhóm tách biệt rất rõ giữa **độ khớp trên tập phát triển/hồi quy** và **độ chính xác độc lập so với chuyên gia**:
  1. Trên bộ **108 ca Raw v2 của 18 Control A.8**: Model `qwen2.5:7b` khớp **206/216 lượt (95,37%)** so với đáp án thiết kế của nhóm (tính cả các lượt lỗi kỹ thuật trong mẫu số).
  2. Trên bộ **38 hồ sơ mô phỏng mở rộng ngoài nhóm 18 A.8** (8 A.6, 14 A.7, 16 A.8): Model chạy 38/38 ca, khớp khóa thiết kế phát triển **22/38 ca ở lần đầu và 23/38 ca (60,53%) sau khi thử lại lỗi cú pháp JSON**; còn **15 control lệch kết luận tổng và 19 tiêu chí lệch khóa**.
  - Nhóm giữ nguyên toàn bộ 15 ca lệch này trong báo cáo (`docs/RA_SAI_KHAC_TIEU_CHI_LAB_38.md`) chứ không sửa khóa thiết kế để làm đẹp số liệu, đồng thời khẳng định đây là kết quả trên bộ dữ liệu mô phỏng phát triển, chưa phải độ chính xác đo với kiểm toán viên độc lập trên hồ sơ doanh nghiệp thật.

### Câu 15: 56 Control trong hệ thống có đủ để chứng nhận ISO/IEC 27001:2022 không? Tại sao nhóm chọn 56 Control này?
- **Trả lời mẫu:** Tiêu chuẩn ISO/IEC 27001:2022 đầy đủ gồm các điều khoản quản trị từ Điều 4 đến Điều 10 và **93 Control** trong Phụ lục A (37 A.5 Organizational, 8 A.6 People, 14 A.7 Physical, 34 A.8 Technological). Trong phạm vi đồ án, nhóm xây dựng đầy đủ cho **56 Control thuộc 3 nhóm A.6 (8), A.7 (14) và A.8 (34)** — là các nhóm có bằng chứng vận hành, nhân sự, vật lý và kỹ thuật cụ thể, đồng thời ưu tiên thực nghiệm sâu 18 Control A.8 theo định hướng của giảng viên. Do đó, hệ thống quản lý SoA dự thảo trong phạm vi 56 Control của đồ án và luôn ghi rõ cảnh báo không thay thế toàn bộ 93 Control hay các điều khoản 4–10.

### Câu 16: Làm thế nào hệ thống đảm bảo dữ liệu của Doanh nghiệp A không bị Doanh nghiệp B đọc hoặc sửa?
- **Trả lời mẫu:** Hệ thống kiểm soát cách ly đa khách hàng (Multi-tenant Isolation) ngay tại tầng Backend và Database:
  1. Mỗi khách hàng (`consulting_clients`) liên kết với các đợt đánh giá riêng thông qua bảng `consulting_campaigns`.
  2. Quyền truy cập vào đợt đánh giá được kiểm soát bởi bảng `assessment_members(assessment_id, user_id)`.
  3. Mọi API đều có dependency `require_campaign(assessment_id, user)` hoặc `require_client(cur, client_id, user)`. Nếu người dùng của Doanh nghiệp A thay UUID trên URL sang `assessment_id` của Doanh nghiệp B, backend từ chối ngay với mã `403 Forbidden`. Điều này đã được kiểm thử tự động trên 7 nhóm endpoint khác nhau trong `live-zz-clients.spec.js`.

### Câu 17: Tại sao khi tạo một khách hàng mới, đợt đánh giá của họ lại không có sẵn nhân viên hay bằng chứng như đợt Lab?
- **Trả lời mẫu:** Trước đây hệ thống có cơ chế tự seed danh bạ nhân viên và thiết bị giả lập vào mọi đợt. Tuy nhiên, đối với khách hàng tư vấn thực tế, việc tự động chèn nhân viên giả hoặc gọi collector giả lập sẽ làm sai lệch hoàn toàn hồ sơ kiểm toán. Vì vậy, nhóm đã bổ sung cột `inventory_mode` (`'lab'` vs `'client'`) trong bảng `assessment_campaigns`. Khi tạo đợt cho khách hàng mới (`inventory_mode = 'client'`), danh mục bắt đầu hoàn toàn rỗng (`0` nhân viên, `0` tài khoản, `0` thiết bị) và AI Agent chỉ chạy ở chế độ `user_evidence_only`.

### Câu 18: Khi khai báo một nhân viên hoặc thiết bị vào danh mục doanh nghiệp, hệ thống có tự đánh giá nhân viên/thiết bị đó đạt chuẩn không?
- **Trả lời mẫu:** **Không.** Khi khai báo qua `ClientInventoryEditor.jsx` (`PUT /enterprise/company/inventory/{kind}/{id}`), hệ thống gán cứng cờ `origin = 'user_declared_not_verified'`, trạng thái `mfa = None`, `encrypted = None`. Việc khai báo chỉ giúp xác lập danh mục tài sản/nhân sự và mã `snapshot_hash` của đợt; để kết luận tuân thủ, doanh nghiệp vẫn phải nộp tài liệu/log bằng chứng gốc cho các Control tương ứng.

### Câu 19: Hệ thống xử lý bài toán hai người cùng lúc sửa một phát hiện hoặc cùng lúc bấm chạy đánh giá một Control (Race Condition) như thế nào?
- **Trả lời mẫu:** Mọi quyết định đồng thời đều được giải quyết trong **PostgreSQL** chứ không nằm ở biến nhớ trên trình duyệt:
  1. **Khi bấm chạy đánh giá Control (`claim_job`):** Dùng câu lệnh nguyên tử `UPDATE control_progress SET workflow_status='RUNNING' ... WHERE assessment_id=%s AND control_id=%s AND workflow_status <> 'RUNNING' RETURNING control_id`. Chỉ 1 request đầu tiên chiếm được quyền chạy, request thứ hai nhận ngay mã `409 Conflict`.
  2. **Khi cập nhật hồ sơ khách hàng, danh mục, bối cảnh, phát hiện hoặc sổ rủi ro:** Kết hợp `SELECT ... FOR UPDATE` (khóa dòng trong transaction) và kiểm tra `expected_version` / `expected_snapshot_hash` (Optimistic Concurrency Control). Nếu phiên bản đã thay đổi, API trả `409 Conflict` yêu cầu tải lại bản mới nhất.
  3. **Khi khởi tạo bản ghi lần đầu (`context`, `discover`, `governance_records`):** Dùng `SELECT pg_advisory_xact_lock(hashtext(...))` để chống hai luồng tạo trùng cùng lúc.

### Câu 20: Nếu đang chạy đánh giá hoặc sau khi đã hoàn tất khắc phục mà máy chủ Backend bị tắt đột ngột rồi khởi động lại (Restart) thì dữ liệu có mất không?
- **Trả lời mẫu:** Toàn bộ dữ liệu nghiệp vụ được lưu bền vững trong PostgreSQL và kho tệp SHA-256 trên đĩa. Khi FastAPI khởi động lại (`lifespan` trong `backend/main.py`):
  - Các dữ liệu khách hàng, đợt đánh giá, danh mục, bằng chứng, phát hiện, kế hoạch khắc phục, xác minh và thông báo được giữ nguyên 100%.
  - Riêng các job đánh giá luồng (`agent_jobs`) đang ở trạng thái `RUNNING` tại thời điểm server bị ngắt sẽ được hàm `init_teamwork()` và `recover_interrupted()` tự động chuyển sang `INTERRUPTED` / `FAILED` và giải phóng khóa trên `control_progress`, đảm bảo không có Control nào bị treo khóa vĩnh viễn sau khi restart. Tính năng này đã được kiểm chứng tự động trong `run_isolated_acceptance.py`.

### Câu 21: Sự khác biệt giữa "Người thực hiện chính" (`assignee`) và "Người phối hợp" (`collaborator_ids`) trong hệ thống là gì?
- **Trả lời mẫu:** Trong một hành động khắc phục:
  - **Người phối hợp (`collaborator_ids`):** Được quyền xem hành động, bắt đầu công việc (`start`), đánh dấu hoàn thành các bước công việc con (`task`) được giao cho mình và đính kèm bằng chứng mới (`attach`). Tuy nhiên, người phối hợp **không được gửi hồ sơ xác minh (`submit` → chặn `403`)**.
  - **Người chịu trách nhiệm chính (`assignee`):** Có quyền điều phối tất cả các bước con và là **người duy nhất được bấm gửi yêu cầu xác minh (`submit`)** khi toàn bộ bước con đã hoàn tất và đã có bằng chứng mới.
  - Cả hai đều bị chặn không được tự xác minh (`verify`).

### Câu 22: Hệ thống bảo vệ chống các lỗ hổng bảo mật web phổ biến (SQL Injection, XSS, CSV/Excel Formula Injection, Path Traversal) như thế nào?
- **Trả lời mẫu:**
  - **SQL Injection:** 100% câu lệnh SQL dùng truy vấn tham số hóa (`%s`) của thư viện `psycopg`, không nối chuỗi trực tiếp từ input người dùng.
  - **XSS:** Giao diện React tự động escape JSX; báo cáo bản in HTML và luồng tạo PDF dùng `html.escape()` trước khi render.
  - **CSV & Excel Formula Injection:** Khi xuất `.csv` và `.xlsx`, mọi giá trị chuỗi bắt đầu bằng `=`, `+`, `-`, `@` (kể cả sau ký tự khoảng trắng hoặc BOM) đều được tự động thêm dấu nháy đơn `'` ở đầu để Excel không thực thi công thức độc hại.
  - **Path Traversal:** Hàm `source_intake.prepare()` và `original_path()` chặn mọi ký tự `/`, `\`, `..`, byte NUL, kiểm tra định dạng UUID của đợt và đối chiếu `path.resolve()` phải nằm đúng trong thư mục `data/evidence-originals/`.

### Câu 23: Hệ thống thông báo và nhắc hạn hoạt động ra sao? Có làm lộ mật khẩu email (SMTP) trong code không?
- **Trả lời mẫu:**
  - Hệ thống ưu tiên **Hộp thư thông báo trong ứng dụng (`remediation_notifications`)**, gắn khóa chống trùng `UNIQUE(assessment_id, user_id, dedupe_key)`. Một luồng nền (`remediation-due-reminders`) quét định kỳ mỗi 5 phút để tạo thông báo cho các công việc sắp đến hạn (trong vòng 3 ngày) và quá hạn, gửi tới người chính, người phối hợp và quản lý doanh nghiệp (`business_admin`).
  - Đối với Email, module `remediation_notifications.py` hỗ trợ gửi qua SMTP tùy chọn **chỉ khi** quản trị viên cấu hình biến môi trường `REMEDIATION_SMTP_ENABLED=1` cùng `REMEDIATION_SMTP_HOST`, `REMEDIATION_SMTP_FROM`, `REMEDIATION_SMTP_USER`, `REMEDIATION_SMTP_PASSWORD`. Trong mã nguồn và Git tuyệt đối không có bất kỳ thông tin SMTP hay mật khẩu hardcode nào.

### Câu 24: Tại sao trên Dashboard Lãnh đạo, mục "Chi phí dự kiến" lại hiển thị là "Chưa có dữ liệu số tiền"?
- **Trả lời mẫu:** Yêu cầu của dự án là **không hiển thị số liệu giả (no invented metrics)**. Hiện tại trong schema kế hoạch khắc phục, hệ thống lưu trữ trường văn bản `resources` (nguồn lực dự kiến: thiết bị, nhân sự) và `estimated_effort` (thời gian dự kiến), chưa có bảng hạch toán tiền tệ đã được kiểm toán. Vì vậy, `remediation.dashboard()` trả về `estimated_cost = None`, hiển thị tổng hợp các nguồn lực/thời gian từ kế hoạch đã lập (`planned_resources`) và ghi rõ *"Chưa có dữ liệu số tiền; xem nguồn lực trong kế hoạch"*.

### Câu 25: Làm sao phân biệt được các bài kiểm thử dùng dữ liệu giả lập (Mock/Synthetic) với dữ liệu thực tế của dự án?
- **Trả lời mẫu:** Nhóm phân tách nghiêm ngặt thành 3 cơ chế:
  1. **UI Form Tests (`frontend-react/tests/*.spec.js`):** Sử dụng `page.route()` để chặn và mô phỏng phản hồi API khi kiểm thử tương tác form trên trình duyệt, không ghi bất kỳ dòng nào vào database chính.
  2. **Isolated Real-Write E2E Tests (`run_isolated_acceptance.py` & `live-zz-clients.spec.js`):** Tự động tạo một database PostgreSQL tạm thời có tên ngẫu nhiên `iso_acceptance_<12_hex>`, chạy toàn bộ API thật, gọi Ollama `qwen2.5:7b` thật, kiểm tra restart thật, xuất biên nhận JSON ghi rõ `"origin": "SYNTHETIC_DISPOSABLE_DATABASE_ONLY"`, `"human_assessment": false`, sau đó `DROP DATABASE` tạm và kiểm tra số dòng các bảng trong database chính giữ nguyên không đổi (`main_table_counts_unchanged: true`).
  3. **Database chính:** Giữ nguyên hiện trạng thực tế (19/56 control có nguồn, 37 control thiếu nguồn, 0 phê duyệt giả).

### Câu 26: Hạn chế lớn nhất của hệ thống hiện tại là gì?
- **Trả lời mẫu:** Có 4 hạn chế thực tế mà nhóm đã ghi nhận thẳng thắn trong tài liệu nghiệm thu:
  1. **Về phạm vi tiêu chuẩn:** Mới bao phủ 56/93 Control của Phụ lục A (nhóm A.6, A.7, A.8), chưa bao gồm 37 Control nhóm A.5 và các điều khoản quản trị 4–10.
  2. **Về xử lý đa phương thức:** Mới trích xuất văn bản từ PDF/DOCX/TXT/JSON/CSV/LOG/CONF; chưa tích hợp OCR cho ảnh chụp màn hình hoặc phân tích video camera giám sát.
  3. **Về kiến trúc thực thi nền:** Worker chạy đánh giá lô và worker quét nhắc hạn hiện vẫn chạy bằng `ThreadPoolExecutor` / daemon thread bên trong tiến trình Uvicorn, nên mới phù hợp cho triển khai một tiến trình (single-worker), chưa phải hàng đợi phân tán High Availability (như Celery/Redis).
  4. **Về dữ liệu nghiệm thu đợt chính:** Đợt đánh giá chính của nhóm vẫn còn 37 Control chờ bổ sung hồ sơ thực tế và chờ giảng viên/người đánh giá độc lập ký thẩm định.

### Câu 27: Hệ thống hiện tại đã có thể đem đi triển khai sử dụng thực tế cho một đơn vị tư vấn ISO 27001 chưa?
- **Trả lời mẫu:**
  - **Ở quy mô triển khai nội bộ (On-Premise / Intranet LAN cho một nhóm tư vấn và khách hàng):** Hệ thống **đã hoàn toàn sử dụng được ngay** vì toàn bộ luồng tạo khách hàng, tách đợt, nộp bằng chứng, AI đánh giá & tư vấn local, giao việc, xác minh độc lập và xuất báo cáo PDF/Excel đều hoạt động trên PostgreSQL thật và LLM thật.
  - **Để đưa lên môi trường Internet công cộng (Public SaaS):** Cần bổ sung thêm lớp Reverse Proxy có chứng chỉ TLS/HTTPS (Nginx/Caddy), tách worker sang hàng đợi riêng (Redis/Celery), thiết lập chính sách backup/restore PostgreSQL tự động hàng ngày và cấu hình tường lửa mạng.

### Câu 28: Nếu có thêm thời gian, hướng phát triển tiếp theo của nhóm là gì?
- **Trả lời mẫu:** Nhóm định hướng 4 bước phát triển tiếp theo:
  1. Mở rộng danh mục lên đủ **93 Control của Annex A** và các điều khoản **4–10** của ISO/IEC 27001:2022.
  2. Bổ sung pipeline **OCR tiếng Việt** có kiểm chứng để trích xuất bằng chứng từ ảnh chụp cấu hình và biên bản scan dạng ảnh.
  3. Nâng cấp kiến trúc thực thi nền sang **hàng đợi phân tán (Celery + Redis)** và tích hợp **chữ ký số** cho các bước thẩm định tiêu chí và phê duyệt SoA.
  4. Phối hợp với chuyên gia/kiểm toán viên ISO 27001 để thực hiện một đợt đánh giá và chấm đối chứng độc lập hoàn chỉnh trên doanh nghiệp thực tế.
