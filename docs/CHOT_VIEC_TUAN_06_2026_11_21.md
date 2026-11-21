# Việc còn cần hoàn tất — đối chiếu hồ sơ ngày 21/11/2026

Nguồn: API của đợt `7f7c009b-bdcd-5b33-934e-15251ad2c976`, chỉ đọc; [snapshot JSON](a8-results/week6-handoff-2026-11-21.json) lưu thời điểm, hash rubric, fingerprint SoA và phiếu theo từng control. Đây là danh sách việc, không phải bằng chứng hoặc xác nhận đã giao việc.

## Trạng thái xác minh lại

| Mục | Hồ sơ hiện hành | Cần làm để đóng |
|---|---|---|
| Nguồn | 19 control có nguồn ngoài preset, 18 qua ngưỡng nội dung; 37 thiếu nguồn, A.6.2 cần thay | Chủ nguồn nộp artifact/hồ sơ có nội dung đúng tiêu chí, đối tượng và kỳ kiểm tra; người phụ trách rà mức bao phủ |
| Rubric | Chưa xác nhận phiên bản hiện hành | Người phụ trách/giảng viên xác nhận phạm vi và tiêu chí, lưu căn cứ thật |
| Tính áp dụng | 0/56 quyết định được ghi | Người phụ trách ghi từng quyết định có lý do; áp dụng thì có kế hoạch, người nhận, hạn và cách kiểm tra lại |
| Thẩm định | 0/56 thẩm định hiện hành | Người đánh giá đọc nguồn, thẩm định từng tiêu chí và viện dẫn đúng phiên bản |
| Đối chiếu nghiên cứu | Chưa có bộ kiểm định mới và nhãn đủ điều kiện được xác nhận | Chốt nguồn trước khi chạy, xác minh lịch sử sử dụng; hai người đọc/chấm cùng run ID, khai đúng mức hỗ trợ |
| SoA | Dự thảo, chưa đủ điều kiện duyệt | Hoàn thiện hồ sơ theo bảng chặn; người có trách nhiệm đọc và phê duyệt fingerprint hiện hành |

## Hồ sơ giao nhóm đã chuẩn bị

- [Nhóm Hành chính / an ninh vật lý](week6-handoff-2026-11-21/NHOM_01.md): 14 yêu cầu nguồn A.7.
- [Nhóm IT / vận hành / ATTT](week6-handoff-2026-11-21/NHOM_02.md): 16 yêu cầu nguồn A.8 và rà mức bao phủ nguồn đã có.
- [Nhóm Nhân sự / người phụ trách ATTT](week6-handoff-2026-11-21/NHOM_03.md): 8 yêu cầu A.6, gồm thay nguồn A.6.2.

Mỗi phiếu có tiêu chí, loại nguồn và checklist. Ô người nhận/hạn để trống đến khi nhóm thống nhất. Dùng tên vai trò thay vì tự xác nhận Toàn/Khoa/Tú đã nhận hoặc thực hiện.

## Thao tác theo thứ tự

1. **Toàn cùng người phụ trách:** mở rubric, đối chiếu yêu cầu thầy về phạm vi 56 và nhóm thử nghiệm sâu 18 A.8. Ghi người/ngày xác nhận, phiên bản rubric, nguồn chấp nhận và phương pháp/người chấm được đồng ý. Chỉ sau trao đổi thật mới ghi phê duyệt rubric trong ứng dụng.
2. **Người giữ hồ sơ:** làm từng phiếu nguồn ở ba nhóm trên. A.6.2 phải thay tài liệu một ký tự bằng nguồn đọc được; mẫu phiếu yêu cầu hoặc nội dung trợ lý tự viết không thay được hồ sơ cần xác minh. Các hồ sơ lab mô phỏng được dùng nếu phạm vi đó đã được thống nhất, nhưng phải ghi nguồn gốc và giới hạn.
3. **Admin:** nộp nguồn tại đúng control → đọc lại nội dung và hash → chạy Agent. Ở Hồ sơ ISO có thể chạy lô hữu hạn, tải lại trang để theo dõi hoặc dừng sau việc hiện tại. Kết thúc lô không đồng nghĩa đạt control.
4. **Người chuẩn bị kiểm định:** cung cấp thư mục cấu hình/log mới cùng lịch sử ai đã xem và có dùng chỉnh code/prompt chưa. Chuẩn bị gói bằng CLI theo [hướng dẫn](HUONG_DAN_CHOT_VIEC_TUAN_06.md), rồi vào Thực nghiệm A.8 → Tổng hợp nghiên cứu → Nhập gói nguồn. Đọc phiếu kiểm tra/hash/tiêu chí chưa rõ và xuất phiếu trước khi chạy. Đổi engine thì kiểm tra lại. Không có dấu trùng vẫn chưa chứng minh độc lập.
5. **Người chấm được chấp nhận:** tự đọc cùng run ID và gói bằng chứng, nộp đủ control; khai đúng hỗ trợ/tiếp xúc. Nếu trợ lý cung cấp kết luận/căn cứ thì ghi có AI hỗ trợ. Nhãn cũ giữ khóa; bất đồng và lỗi căn cứ được xử lý bằng biên bản riêng, không sửa lịch sử để tăng điểm.
6. **Người đánh giá và người phụ trách:** thẩm định từng tiêu chí trên nguồn hiện hành; ghi tính áp dụng/kế hoạch và người nhận thực tế. Mục chưa rõ có thể giữ chưa rõ với kế hoạch thu bổ sung. Cuối cùng đọc bảng chặn SoA rồi duyệt khi đủ điều kiện.

## Phần kỹ thuật bổ sung trong đợt này

- Quét bản sao fixture nhận biết thêm thay đổi định dạng JSON, xuống dòng và khoảng trắng cuối dòng trong cấu hình/log/inventory. Byte và hash gốc vẫn giữ nguyên; không coi quét trùng là xác minh độc lập. Gói ứng viên cũ cần chuẩn bị lại theo `cosmetic-text-v2`.
- Phiếu kiểm tra gói hiển thị hash, số artifact và tiêu chí chưa rõ; xuất JSON để bàn giao. Chặn chạy nếu phiếu không khớp gói hoặc engine/đợt đã đổi.
- Khi dừng lô, giao diện chọn đúng lô vừa yêu cầu dừng. Kiểm thử trạng thái chờ dừng, giữ kết quả đã làm, tải lại, lỗi nguồn cũ và xuất lượt.
- Các POST trong kiểm thử UI bổ sung đều được chặn bằng phản hồi mô phỏng; không tạo nguồn, nhãn, job hoặc phê duyệt thử trong đợt chính. Kiểm thử ghi thật trước đó vẫn dùng database riêng.
- Kiểm tra kiểu snapshot/evidence/facts/artifact trước khi đọc nội dung; gói sai kiểu trả 422, không làm lỗi server. API đang chạy đã xác nhận từ chối snapshot rỗng và bản sao fixture dù người gửi tự xóa khai báo trùng.

Kiểm chứng: **339 test Python, 14 test JavaScript, 8 kịch bản Edge, lint/build đạt**. [Báo cáo Edge](a8-results/week6-ui-2026-11-21.json) không có bài bỏ qua; [API gói lỗi](a8-results/week6-preflight-api-2026-11-21.json) giữ nguyên danh sách lượt và fingerprint SoA. Các kiểm thử này không tạo đánh giá độc lập hoặc phê duyệt thật.

Các mục nguồn, thống nhất với thầy, chấm thật, quyết định và phê duyệt vẫn mở cho đến khi có hồ sơ tương ứng. Báo cáo kiểm thử phần mềm không đóng thay các mục đó.
