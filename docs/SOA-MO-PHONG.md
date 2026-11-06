# Phạm vi, rủi ro và SoA mô phỏng cho HiveFive

Đây là mẫu diễn giải 8 kiểm soát con người phục vụ đồ án, không phải SoA
đầy đủ theo ISO/IEC 27001. Danh mục chuẩn có 93 kiểm soát; phải đánh giá rủi
ro, yêu cầu pháp lý/hợp đồng và đối chiếu bản tiêu chuẩn hợp pháp trước khi
quyết định áp dụng thực tế. Tất cả tám kiểm soát dưới đây được chọn trong
phạm vi mô phỏng, không có nghĩa toàn bộ yêu cầu của từng kiểm soát đã đáp ứng.

| ID | Rủi ro / lý do chọn | Biện pháp và bằng chứng của đồ án | Phụ trách | Phần chưa đánh giá |
|---|---|---|---|---|
| A.6.1 | Tuyển người chưa được thẩm tra phù hợp | Trường screened và hồ sơ HR | HR | Mức độ thẩm tra theo vai trò, pháp luật |
| A.6.2 | Trách nhiệm bảo mật không rõ | Cam kết lao động | HR/Pháp chế | Nội dung, hiệu lực và cập nhật hợp đồng |
| A.6.3 | Hành vi thiếu nhận thức, bằng chứng đào tạo lỗi thời | Hoàn tất, đạt kiểm tra, thời hạn, đối soát HR/LMS | HR/Quản lý | Hiệu quả hành vi lâu dài, chương trình theo vai trò |
| A.6.4 | Xử lý vi phạm thiếu nhất quán | Chính sách và phổ biến quy trình | HR | Quy trình thực tế, công bằng và quyền khiếu nại |
| A.6.5 | Quyền cũ còn tồn tại khi nghỉ/đổi việc | Tài khoản, thiết bị, rà soát vai trò, ngoại lệ có hạn | HR/IT | IAM thật, chi tiết từng quyền, SLA và phê duyệt xác thực |
| A.6.6 | Lộ thông tin do nghĩa vụ bảo mật chưa rõ | NDA | HR/Pháp chế | Hiệu lực, phạm vi, rà soát và bên thứ ba |
| A.6.7 | Thiết bị/kết nối từ xa thiếu bảo vệ | Chính sách, mã hóa laptop, VPN MFA | IT/Quản lý | Môi trường vật lý, giám sát, thiết bị ngoài quản lý |
| A.6.8 | Sự kiện không được báo cáo/xử lý kịp | Đào tạo, kênh báo cáo, sự kiện giả lập | SecOps/Quản lý | Thời gian báo cáo, chất lượng và xử lý sự cố thật |

## Chính sách ngoại lệ của mô phỏng

Một tài khoản HR được giữ tạm khi nghỉ việc để đối chiếu bàn giao nếu có:
mã tài khoản trùng khớp, scope offboarding-retention, approved=true kiểu
boolean, người duyệt, lý do và expires_on còn hạn (bao gồm ngày hết hạn).
Các tài khoản khác không được miễn kiểm tra nhờ ngoại lệ này. Thiết bị vẫn
phải được bàn giao. Quy tắc này là quyết định chính sách của dự án, không
phải kết luận ISO cho phép giữ tài khoản cá nhân sau nghỉ việc trong mọi trường hợp.
Trong doanh nghiệp thật cần cân nhắc lưu trữ hồ sơ hoặc tài khoản bàn giao
được ủy quyền thay cho tiếp tục truy cập bằng tài khoản người đã nghỉ.

Người vận hành ghi nhận phê duyệt giả lập bằng nghiệp vụ riêng. Agent chỉ
kiểm tra điều kiện, không tự phê duyệt và không cấp/thu hồi quyền thật.
UI hiển thị rõ ngoại lệ có điều kiện; không coi cảnh báo biến mất là chấp
nhận rủi ro hoặc chứng nhận. Dùng Chuyển ngày mô phỏng hai lần sau khi đề
nghị/duyệt để quan sát quyền giữ tạm hết hạn và cảnh báo tự xuất hiện.

Ngày tham chiếu được lưu trong snapshot; nguồn cũ mặc định 2026-10-30.
Không dùng đồng hồ thực để thay đổi âm thầm kết quả của cùng một snapshot.
Đây là thời gian mô phỏng, chưa có scheduler tự chuyển ngày trong vận hành thật.
