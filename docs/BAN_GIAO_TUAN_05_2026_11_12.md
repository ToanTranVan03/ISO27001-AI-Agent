# Hoàn thiện bàn giao tuần 5 — 12/11/2026

Phạm vi giữ nguyên 56 control, ưu tiên thực nghiệm 18 A.8. Bản cập nhật này bổ sung công cụ hoàn thiện hồ sơ; không xác nhận đã nghiệm thu chuyên môn.

## Đã triển khai và kiểm tra

- Gói bàn giao lấy trực tiếp từ snapshot đợt, đủ 56 control / 113 tiêu chí dự án. Có yêu cầu nguồn cho từng tiêu chí, vai trò đề nghị, loại nguồn cần rà, ID/hash nguồn hiện có và trạng thái thẩm định.
- Gợi ý xử lý tách khỏi kế hoạch đã ghi: người nhận, hạn và phê duyệt vẫn để trống cho người phụ trách xác nhận. Không tự ghi quyết định áp dụng, kết luận người chấm hay chữ ký.
- Chỉ thẩm định hiện hành được hiển thị trong phần tiêu chí đã kiểm chứng. Kết luận máy hoặc có đúng loại tài liệu không tự biến thành tiêu chí đã đạt. Snapshot thay đổi làm gói/hash và thẩm định tương ứng thay đổi.
- Xuất JSON/Markdown tại **Phạm vi 56 → Gói bàn giao**; bấm control để mở hồ sơ và điền thẩm định theo luồng hiện có.
- Sửa hướng dẫn bước tiếp theo khi chỉ có preset: yêu cầu thu nguồn thay vì hướng dẫn chạy Agent.
- API thật trả đủ 56 dòng, 113 tiêu chí; không tạo nhãn, hồ sơ hoặc phê duyệt giả trong database.

[Gói snapshot JSON xuất ngày 12/11](a8-results/week5-handoff-2026-11-12.json) là bản đọc tại thời điểm xuất; lấy lại từ ứng dụng khi hồ sơ thay đổi. Hash chỉ kiểm tra nhất quán nội dung, không chứng minh tính đúng hay độc lập của nguồn.

## Trạng thái thực tế và cách đóng các vướng mắc

| Việc | Hiện trạng | Đầu vào cần có để hoàn tất |
|---|---|---|
| Nguồn toàn phạm vi | 29 có bằng chứng; 19 có nguồn ngoài preset, gồm 18 capture lab | Chủ hồ sơ cung cấp nguồn có nội dung cho 37 control còn thiếu; rà cả nguồn đã có theo từng tiêu chí |
| Rubric | Chưa được người phụ trách xác nhận | Rà 113 tiêu chí dự án, mức bao phủ và nguồn được chấp nhận; ghi xác nhận đúng hash |
| Tính áp dụng | 0/56 quyết định | Người phụ trách ghi lý do và kế hoạch; không tự loại trừ control chỉ vì thiếu nguồn |
| Thẩm định hồ sơ | 0 thẩm định hiện hành | Người đánh giá đọc nguồn, viện dẫn từng tiêu chí, giữ unknown khi không đủ căn cứ |
| Đối chiếu người đánh giá | Chưa có bộ nhãn độc lập hoàn tất | Xác nhận tư cách người chấm với giảng viên, chấm trên cùng snapshot và khai đúng mức hỗ trợ/tiếp xúc đáp án |
| Tập kiểm định | Có công cụ chốt/dò trùng, chưa có tập mới được xác nhận | Nhóm cung cấp nguồn chưa dùng phát triển và nhãn thật; không tái đặt tên fixture làm tập độc lập |
| UI | API/build/test đạt; Computer Use không kết nối native pipe | Người thao tác kiểm tra đăng nhập, chọn control, đọc/nộp nguồn, đánh giá, chấm, xuất và các trường hợp chặn duyệt |
| SoA | Dự thảo, chưa duyệt | Chốt quyết định/thẩm định/rubric hiện hành, kế hoạch xử lý rồi người có trách nhiệm phê duyệt |

18 probe live chỉ là phép thử đại diện của lab. Nguồn này không chứng minh đầy đủ 18 control ISO hoặc toàn bộ 56 control. Các trường chưa có người thật xác nhận được giữ nguyên, không đánh dấu hoàn tất để đẩy tiến độ.

## Thứ tự thao tác ngay trên ứng dụng

1. Mở Phạm vi 56, xuất gói bàn giao và phân nguồn cho Nhân sự, Hành chính/an ninh vật lý, IT/ATTT theo vai trò đề nghị.
2. Với từng control, đọc các yêu cầu tiêu chí; thu tài liệu/cấu hình/log gốc, ghi chủ sở hữu, thời điểm, đối tượng và giới hạn mẫu. Mẫu yêu cầu không phải bằng chứng.
3. Thu gói, chạy đánh giá không dùng preset; kiểm tra lỗi và phần còn thiếu trước khi thẩm định.
4. Chính người đánh giá ghi từng tiêu chí và căn cứ. Chấm mù A.8 là luồng riêng, không dùng kế hoạch/gói này để chấm thay người thật.
5. Rà tính áp dụng, kế hoạch, xuất SoA; duyệt khi đủ điều kiện. Control không đạt vẫn có thể nằm trong SoA với trạng thái và kế hoạch trung thực.

Kiểm chứng phiên này: 207 test Python, 5 test JavaScript, lint/build đạt. Có 3 cảnh báo deprecation từ thư viện. Không coi các kiểm chứng phần mềm là độ đúng so với người đánh giá, kiểm định độc lập hoặc chứng nhận ISO.
