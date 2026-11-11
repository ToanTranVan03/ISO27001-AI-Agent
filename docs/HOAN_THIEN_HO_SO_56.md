# Hoàn thiện hồ sơ và nguồn đối chiếu đánh giá

Cập nhật 11/11/2026. Phạm vi 56 control, không tự chuyển phê duyệt hoặc nhãn người chấm thành hoàn tất.

## Các chức năng bổ sung

### Nguồn live nối với hồ sơ 56

Admin mở lượt A.8 live đã hoàn tất → **Nhập nguồn live vào hồ sơ 56**. Chức năng chỉ nhập artifacts, metadata, hash và phạm vi tiêu chí đại diện; không nhập kết luận Agent, đáp án, nhãn hay facts dẫn xuất làm đáp án.

- Nguồn giữ `is_synthetic=true`, origin `a8-live-capture-v1`; không đổi thành tài liệu production.
- Kiểm tra report/artifact hash, cùng assessment, control hợp lệ và khóa các control trước khi nhập. Control đang chạy thì từ chối toàn giao dịch.
- Nhập lại cùng gói sử dụng lại evidence ID, không thêm bản trùng hoặc event trùng.
- Chế độ đánh giá nguồn đã thu nhận bản capture này một cách tường minh. Preset doanh nghiệp tự sinh vẫn bị loại khỏi chế độ này.
- Toàn phạm vi dùng rubric riêng; chỉ có nguồn lab đại diện không đủ xác nhận **Compliant** toàn bộ control. Nguồn này không tự thay kết quả đợt hoặc thẩm định của người thật.
- Timestamp quan sát là thời điểm bản thu gốc, không phải cam kết trạng thái hệ thống ở mọi lần xem lại.

Đã nhập 18 bản thu của lượt `67d38694…` vào đợt hiện tại và kiểm tra nhập lặp không trùng. Số control có bằng chứng tăng **15 → 29/56**; 18 có bản thu lab rõ nguồn, nguồn nộp ngoài preset vẫn là 1. Các số này không phải số control đạt.

Đã chạy Agent riêng trên 18 nguồn nhập theo rubric hồ sơ toàn phạm vi: **9 thiếu bằng chứng, 8 một phần, 1 không đạt**; 18 job cuối đều thành công. Đây khác lượt thử đại diện có 18 kết luận một phần vì rubric/phạm vi đánh giá khác nhau. Không lấy trạng thái ca thử làm kết luận toàn control. [Kết quả và audit trail](a8-results/dossier-capture-evaluations.json).

Hiện 19/56 control có nguồn được cho phép dùng ở chế độ không lấy preset (18 capture lab và 1 control có hồ sơ nộp). Danh sách bàn giao ghi 37 control còn cần nguồn tương ứng, không coi preset tự sinh là hồ sơ đã cung cấp đầy đủ.

Đã xuất [SoA 56 hiện tại — Markdown](a8-results/SOA_56_HIEN_TAI.md) và [JSON](a8-results/soa56-current-draft.json), giữ đủ 56 dòng và trạng thái dự thảo. Những quyết định chưa có vẫn để chưa xác định, không tự tạo lý do áp dụng/phê duyệt.

### Khai báo nguồn hỗ trợ khi chấm

Mỗi nhãn mới có hai khai báo: tự chấm/AI hỗ trợ/thảo luận/chưa khai báo và đã xem kết luận Agent/đáp án hay chưa. Nhãn có hỗ trợ hoặc chưa khai báo được giữ trong tiến độ và bảng riêng, không tính vào đối chiếu độc lập. Không mặc định nhãn cũ là độc lập chỉ vì dùng tài khoản khác.

Khai báo là thông tin do người nộp tự xác nhận, không chứng minh năng lực chuyên gia hoặc độc lập ngoài nhóm. Nếu dùng hướng dẫn AI thì chọn đúng **Có AI hỗ trợ**. Hai nhãn cũ của Khoa giữ nguyên, hiện chưa có các khai báo này; không sửa lịch sử thay người chấm.

Phê duyệt báo cáo con A.8 yêu cầu một bộ nhãn đủ 18/18 được khai báo phù hợp với đối chiếu độc lập và rubric đã duyệt. Đây là điều kiện nghiên cứu của ứng dụng; không được tạo nhãn giả để vượt điều kiện. Hồ sơ SoA tổng thể 56 vẫn có luồng thẩm định riêng.

### Màn hình nguồn dễ đọc và danh sách bàn giao

- Người chấm đọc danh sách điều kiện/nguồn, mở từng artifact để xem nội dung và hash; JSON gốc có thể mở rộng/thu gọn. Không tự chọn sẵn **Compliant**.
- Phạm vi 56 có **Việc còn thiếu để bàn giao** theo bước và vai trò; nhấn control để mở hồ sơ, xuất JSON/Markdown để giao việc.
- [Danh sách theo dữ liệu hiện tại](VIEC_CAN_HOAN_THIEN_56.json) là snapshot; xuất lại từ ứng dụng sau khi dữ liệu đổi. Không dùng số việc làm tỷ lệ tuân thủ.

## Kiểm chứng và giới hạn

- Test phần mềm kiểm tra tách nhãn hỗ trợ, chặn duyệt sai, không lộ báo cáo trước khi nộp đủ, nhập nguồn idempotent và khóa công việc.
- Kiểm tra PostgreSQL thật phát hiện lỗi bind ký tự `%` ở truy vấn nguồn mới trong lần tích hợp đầu. Đã sửa thành tham số, thêm hồi quy, giữ lịch sử các job lỗi riêng. Lỗi này xảy ra trước gọi model, không tính thành số đo suy luận LLM.
- Bộ điều khiển trình duyệt/native vẫn không kết nối trong phiên này; không đánh dấu hoàn tất việc bấm toàn bộ UI bằng kết quả API/build.
- 202 test Python, 5 test JavaScript, lint và build đạt; còn 3 cảnh báo thư viện Python. Không thay thế đánh giá chuyên môn.

## Phần cần người phụ trách thực hiện

1. Rà rubric/phạm vi và nguồn được chấp nhận; ghi quyết định áp dụng 56 control cùng kế hoạch.
2. Bổ sung nguồn cho các control chưa có; rà chất lượng nguồn đã có, nhất là hồ sơ A.6/A.7 và ngữ cảnh/rủi ro ngoài phép thử lab.
3. Người đánh giá thực sự đọc nguồn, khai báo mức hỗ trợ và nộp căn cứ; không lấy bản chấm AI làm nhãn người thật.
4. Cung cấp bộ kiểm định chưa dùng phát triển, xác nhận mức độc lập và chốt nhãn trước khi đo.
5. Kiểm tra UI có đăng nhập, xuất báo cáo và duyệt SoA khi đủ điều kiện.
