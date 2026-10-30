# KỊCH BẢN BẢO VỆ ĐỒ ÁN / KHÓA LUẬN TỐT NGHIỆP TRƯỚC HỘI ĐỒNG

**Đề tài:** HỆ THỐNG AI AGENT GIÁM SÁT TUÂN THỦ ISO/IEC 27001 THEO MÔ HÌNH 3 TRỤ CỘT (CON NGƯỜI - PHẦN MỀM - PHẦN CỨNG)  
**Thời lượng chuẩn:** 25 phút (10 phút Thuyết trình + 5 phút Live Demo + 10 phút Trả lời phản biện)

---

## PHẦN 1: PHÂN BỔ THỜI GIAN & CHIẾN LƯỢC BẢO VỆ

* **Phút 00 - 02:** Mở đầu, lý do chọn đề tài và bối cảnh rủi ro an toàn thông tin bắt nguồn từ con người.
* **Phút 02 - 05:** Kiến trúc 3 Trụ cột (Security Triad), chuỗi lan truyền rủi ro chéo và công thức định lượng rủi ro CIA.
* **Phút 05 - 08:** Cơ chế AI Agent, bộ công cụ hữu hạn (Bounded Tools), Dynamic RAG và NLP Parser xử lý văn bản phi cấu trúc.
* **Phút 08 - 10:** Kết quả thực nghiệm khoa học: Paired Benchmark và Khảo sát người dùng RQ3 (Thang đo SUS 90.0).
* **Phút 10 - 15:** **LIVE DEMO THỰC CHIẾN:** Thao tác trên Web 3D và Terminal VS Code.
* **Phút 15 - 25:** Trả lời câu hỏi phản biện của Hội đồng.

---

## PHẦN 2: LỜI THOẠI THUYẾT TRÌNH TỪNG SLIDE (SPOKEN SCRIPT)

### Slide 1 - Mở đầu
> *"Kính thưa Quý Thầy/Cô Chủ tịch Hội đồng, Thầy/Cô Phản biện và toàn thể các Thầy/Cô trong Hội đồng chấm khóa luận tốt nghiệp. Em tên là [Họ và tên], sinh viên lớp [Tên lớp]. Hôm nay, em xin phép được báo cáo kết quả nghiên cứu đề tài: 'Hệ thống AI Agent Giám sát Tuân thủ ISO/IEC 27001 theo Mô hình 3 Trụ cột: Con người, Phần mềm và Phần cứng'."*

### Slide 2 & 3 - Đặt vấn đề & Câu hỏi nghiên cứu
> *"Kính thưa Thầy/Cô, trong kỷ nguyên số, dữ liệu là tài sản quý giá nhất, nhưng con người lại là mắt xích yếu nhất trong chuỗi bảo mật. Báo cáo Verizon DBIR chỉ ra hơn 74% sự cố rò rỉ dữ liệu xuất phát từ yếu tố con người. Tuy nhiên, các hệ thống giám sát tuân thủ hiện nay thường kiểm tra riêng rẽ, thụ động và làm cán bộ an ninh bị quá tải thông tin dạng bảng biểu. Đề tài của em giải quyết bài toán này bằng cách đặt ra 3 câu hỏi nghiên cứu: Thứ nhất, làm sao để AI Agent tự trị điều phối kiểm tra toàn diện? Thứ hai, hiệu năng so với hệ thống quy tắc truyền thống thế nào? Và thứ ba, việc đưa không gian 3D và mô hình 3 trụ cột vào có thực sự giúp giảm tải nhận thức và rút ngắn thời gian phát hiện rủi ro hay không."*

### Slide 4, 5 & 6 - Kiến trúc 3 Trụ cột & Lan truyền rủi ro
> *"Để giải quyết, em xây dựng mô hình Tam giác An toàn thông tin (Security Triad), lấy Con người (A.6 People Controls) làm trọng tâm. Từ một sự kiện nhân sự như thôi việc (Offboarding) hay làm việc từ xa (Remote working), rủi ro không dừng lại ở phòng HR mà lập tức lan truyền sang Phần mềm (tài khoản SaaS, VPN chưa khóa theo A.8.2) và Phần cứng (laptop chưa thu hồi theo A.7.9, thiếu BitLocker theo A.8.1). Em đã lượng hóa rủi ro này bằng công thức toán học bám sát tiêu chuẩn ISO 27005: Điểm rủi ro bằng Tích số giữa Khả năng xảy ra, Tác động bảo mật theo bộ ba CIA và Trọng số nhạy cảm của phòng ban."*

### Slide 7, 8 & 9 - AI Agent, Dữ liệu phi cấu trúc & Dynamic RAG
> *"Về mặt công nghệ, hệ thống áp dụng kiến trúc Bounded Tool-Using Agent để đảm bảo an toàn, không để LLM tự do can thiệp cơ sở dữ liệu. Đặc biệt, để trả lời câu hỏi cốt lõi: 'Tại sao cần AI thay vì Rule-based engine?', em đã phát triển bộ phân tích văn bản phi cấu trúc (Unstructured Evidence Parser). Trong thực tế, bằng chứng kiểm toán không nằm ở các trường boolean sạch, mà nằm trong email bàn giao, ticket xin gia hạn quyền, ghi chú viết tay. Thử nghiệm cho thấy Rule Engine thất bại hoàn toàn trên văn bản tự nhiên, trong khi AI Agent đạt 100% độ chính xác trong việc trích xuất thực thể và nhận diện vi phạm. Đồng thời, module Dynamic ISO RAG tự động truy xuất điều khoản ISO 27002:2022 để sinh khuyến nghị khắc phục chuẩn quốc tế."*

### Slide 10, 11 & 12 - Trực quan hóa 3D & Kết quả khảo sát RQ3
> *"Để giải bài toán công thái học cho chuyên viên SOC, em xây dựng bản đồ văn phòng 3D bằng Three.js. Khi có sự cố, nhân viên vi phạm lập tức chuyển sang áo đỏ và ghim nhãn cảnh báo trực quan. Thử nghiệm Crossover đối chứng trên 16 người dùng cho thấy: Mô hình 3D giúp rút ngắn thời gian phát hiện rủi ro tới 42.3% (từ 76.6 giây xuống 44.2 giây), giảm 85.7% lỗi bỏ sót rủi ro chéo, và đạt điểm khả dụng SUS lên tới 90.0/100, thuộc nhóm Xuất sắc (Grade A)."*

---

## PHẦN 3: KỊCH BẢN LIVE DEMO (5 PHÚT THỰC CHIẾN)

### Bước 1: Trình diễn giao diện Web Đang vận hành (3D Campus & 2D Triad)
* Mở trình duyệt tại địa chỉ: `http://127.0.0.1:8000`
* **Lời thuyết minh:**
  > *"Thưa Thầy/Cô, đây là giao diện giám sát thời gian thực của HiveFive. Ở nửa trên là mặt bằng văn phòng 3D chia theo 4 phòng ban. Ở nửa dưới là Trạm giám sát với ma trận 3 Trụ cột: Con người, Phần mềm và Phần cứng."*

### Bước 2: Kích hoạt sự cố Offboarding nhân viên HF-010
* Tại mục **Cập nhật hồ sơ doanh nghiệp**:
  * Chọn nhân sự: `HF-010 · Trần Văn Bình`
  * Chọn thao tác: `Ghi nhận nghỉ việc`
  * Bấm nút **Ghi nhận sự kiện**.
* **Quan sát và thuyết minh:**
  > *"Ngay khi em ghi nhận nghỉ việc cho nhân viên HF-010 (thuộc phòng Kế toán):*
  > *1. Trong không gian 3D: Nhân vật HF-010 lập tức đổi sang áo đỏ và hiện nhãn `NGHỈ VIỆC · CHƯA BÀN GIAO`.*
  > *2. Tại bảng Triad bên dưới: Hệ thống lập tức kích hoạt phát hiện chuỗi rủi ro lan truyền chéo:*
  > *   - Nguồn từ Con người: Đã nghỉ việc (A.6.5).*
  > *   - Lan sang Phần mềm: 4 tài khoản (HR, MISA, Email, VPN) vẫn đang mở $\rightarrow$ Rủi ro Critical 22.5/25.*
  > *   - Lan sang Phần cứng: Chưa thu hồi laptop LT-010 $\rightarrow$ Rủi ro Critical 22.5/25.*
  > *3. Module Dynamic RAG tự động trích dẫn căn cứ pháp lý ISO 27002:2022 điều khoản A.6.5 và đưa ra các bước hành động cụ thể cho IT Admin."*

### Bước 3: Trình diễn Agent CLI & Phân tích văn bản phi cấu trúc
* Chuyển sang màn hình VS Code Terminal.
* Chạy lệnh kiểm tra văn bản phi cấu trúc:
  ```powershell
  py -3.11 run_agent_cli.py --unstructured
  ```
* **Thuyết minh:**
  > *"Đây là minh chứng rõ nhất cho giá trị của AI: Khi phân tích email bàn giao của nhân viên HF-010 xin giữ lại tài khoản kế toán 5 ngày mà không có chữ ký CISO, Rule engine hoàn toàn bất lực vì không có trường boolean, nhưng AI Agent đã đọc hiểu văn bản, trích xuất chính xác tên nhân viên, phát hiện việc thiếu chữ ký CISO và gắn đúng vi phạm A.6.5 và A.8.2."*

### Bước 4: Chạy Agent giải quyết và thu hồi tài sản
* Chạy lệnh Agent tuần tra:
  ```powershell
  py -3.11 run_agent_cli.py
  ```
* Cho Hội đồng thấy Agent tự động điều phối 8 công cụ tuần tự, tính toán lại điểm rủi ro và tạo ra danh sách công việc cần xử lý lưu vào SQLite.

---

## PHẦN 4: BỘ CÂU HỎI PHẢN BIỆN THƯỜNG GẶP CỦA HỘI ĐỒNG (VÀ CÁCH TRẢ LỜI)

### Câu hỏi 1: "Tại sao em lại tập trung vào kiểm soát Con người (People) thay vì mạng hay tường lửa?"
* **Trả lời:**
  > *"Thưa Thầy/Cô, kỹ thuật tường lửa hay mã hóa mạng đã có các công cụ IDS/IPS làm rất tốt. Tuy nhiên, hơn 74% rò rỉ dữ liệu trong thực tế lại xảy ra ở lớp con người và quy trình: nhân viên nghỉ việc mang theo laptop, làm việc từ xa qua mạng Wi-Fi quán cafe không bảo mật, hoặc cấp quyền trước khi ký hợp đồng. Nhóm kiểm soát A.6 trong ISO 27002:2022 là chốt chặn đầu tiên nhưng thường bị các giải pháp kỹ thuật bỏ trống. Đề tài của em chọn con người làm tâm điểm để theo dõi cách rủi ro nhân sự lan tỏa sang phần mềm và phần cứng."*

### Câu hỏi 2: "Workflow chạy mất 2ms, AI Agent chạy mất 2.5s. Vậy tại sao doanh nghiệp lại cần AI Agent?"
* **Trả lời:**
  > *"Thưa Thầy/Cô, em rất thẳng thắn thừa nhận giới hạn này trong phần báo cáo khoa học (RQ2). Với dữ liệu có cấu trúc và luật định trước, Workflow chạy nhanh hơn 1000 lần và là lựa chọn tối ưu. Tuy nhiên, AI Agent giải quyết 2 bài toán mà Workflow không làm được:*
  > *1. Xử lý dữ liệu phi cấu trúc: Đọc các email xin ngoại lệ, ticket hỗ trợ tự do và phát hiện các rủi ro tiềm ẩn (như em vừa demo).*
  > *2. Đóng vai trò là trợ lý ảo (Copilot) giải thích ngữ cảnh và tư vấn chính sách: AI Agent sử dụng Dynamic RAG để sinh giải trình tuân thủ phù hợp với từng bối cảnh cụ thể mà không thể viết luật tĩnh cho mọi trường hợp."*

### Câu hỏi 3: "Công thức tính điểm rủi ro $Likelihood \times Impact \times W_{dept}$ có được công nhận không?"
* **Trả lời:**
  > *"Thưa Thầy/Cô, công thức này được em xây dựng bám sát khung hướng dẫn quản lý rủi ro an toàn thông tin **ISO/IEC 27005**. Trong đó, Impact được lượng hóa từ 3 giá trị CIA (Bảo mật, Toàn vẹn, Khả dụng) quy định trong tiêu chuẩn ISO 27002. Trọng số phòng ban $W_{dept}$ thể hiện nguyên lý kiểm soát theo rủi ro (Risk-based approach): cùng một sự cố mất laptop, nhưng nếu xảy ra ở phòng IT Admin hoặc Kế toán thì mức độ đe dọa đến tài sản dữ liệu lớn hơn nhiều so với phòng ban ít tiếp cận thông tin nhạy cảm."*

### Câu hỏi 4: "Mô hình 3D có phải chỉ để cho đẹp mắt không? Thực tế chuyên viên SOC có dùng không?"
* **Trả lời:**
  > *"Dạ thưa Thầy/Cô, đây cũng chính là câu hỏi nghiên cứu RQ3 của đề tài. Em không đưa 3D vào chỉ để trang trí, mà đã thực hiện khảo sát thực nghiệm Crossover trên 16 người dùng. Kết quả thực nghiệm cho thấy trực quan hóa không gian giúp giảm 42.3% thời gian phát hiện rủi ro và giảm 85.7% lỗi bỏ sót liên kết chéo. Nhờ việc mã hóa màu sắc (áo đỏ) và nhãn không gian, chuyên viên an ninh chỉ mất vài giây để nhận diện điểm nóng rủi ro thay vì phải dò tìm thủ công qua hàng trăm dòng Excel."*

### Câu hỏi 5: "Dữ liệu hiện tại là thật hay giả lập? Nếu áp dụng vào doanh nghiệp thật thì cần làm gì?"
* **Trả lời:**
  > *"Thưa Thầy/Cô, vì lý do bảo mật thông tin nhân sự và dữ liệu cá nhân, đề tài hiện đang thử nghiệm trên tập dữ liệu mô phỏng doanh nghiệp HiveFive gồm 50 nhân sự, 200 tài khoản và 50 thiết bị. Để triển khai trên môi trường thật, hệ thống cần bổ sung các API Collector kết nối trực tiếp với Microsoft Entra ID (Azure AD), Google Workspace MDM và hệ thống Jira Service Management. Kiến trúc hướng sự kiện (Event-driven) của đồ án đã được thiết kế mở, sẵn sàng tích hợp các nguồn dữ liệu này qua Webhook."*
