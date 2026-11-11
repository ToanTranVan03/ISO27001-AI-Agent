> **Sau đợt dọn mã 11/11/2026:** các mô tả component demo/cảnh báo và số test trước đây là mốc lịch sử. Xem [cấu trúc và kiểm chứng sau dọn](DON_GON_PROJECT.md).

# Rà soát mã nguồn — 11/11/2026

Phạm vi: xác thực/phân quyền, API dùng chung và API tương thích cũ, collector file/Docker/live, graph đánh giá hồ sơ, chấm mù A.8, tiến độ/SoA 56 và frontend React. Kiểm tra tự động bao gồm toàn bộ suite hiện có, cú pháp các module Python trọng tâm, build/lint frontend và tương thích dependency Python. Không coi việc quét/chạy test là đã đọc và chứng minh đúng từng dòng của mọi module lịch sử.

## Những lỗi đã xác định và sửa

| Mức ưu tiên | Vấn đề | Thay đổi và kiểm chứng |
|---|---|---|
| Cao | Thành viên chấm mù có thể tự tạo lượt để tiếp cận đáp án; export sau khi chấm một lượt chứa đáp án cả các profile khác | Chỉ admin điều phối được tạo lượt. Bỏ answer key đầy đủ khỏi phản hồi/export. Giao thức mới `blind-v3-coordinator-only`; lượt cũ giữ lịch sử, không nhận thêm nhãn/duyệt theo giao thức mới. Test quyền assessor và export sau chấm đủ |
| Cao | API đánh giá đồng bộ cũ không claim công việc trước khi gọi model; đường upload cũ có thể bỏ qua khóa control | Dùng cùng `claim_job`/`finish_job` với API chính, giải phóng khi lỗi; upload scoped khóa hàng và trả 409 khi đang chạy. Chuyển handler đánh giá đồng bộ sang threadpool FastAPI để không chặn event loop |
| Cao | Rubric được xác nhận/hash là file hiện tại, nhưng model lấy bản seed database có thể đã cũ | Đọc cùng file rubric chuẩn dùng trong quy trình xác nhận; lỗi đọc/schema không tự chuyển sang rubric khác. Test thay file phiên bản 1 → 2 mà không dùng seed cũ |
| Vừa | Hai tệp gốc khác bytes có thể có cùng văn bản trích xuất và bị nhận là một evidence ID | Thêm SHA256 bytes gốc vào định danh. Test thêm UTF-8 BOM: text không đổi nhưng hash và ID phải đổi. Bản cũ giữ nguyên; lần thu tiếp có thể tạo ID theo định dạng mới |
| Vừa | Confidence thiếu/sai/NaN/vô hạn có thể tự biến thành 0,85 hoặc bị ép vào khoảng | Yêu cầu giá trị có mặt, hợp lệ/hữu hạn; vẫn hỗ trợ phần trăm 0–100 được khai báo. Không tự tạo 85% khi model không cung cấp giá trị hợp lệ |
| Vừa | Graph tổng thể còn giữ kết luận khi model viện dẫn lẫn ID đúng và ID bịa | Hạ về thiếu bằng chứng/confidence 0 khi có ID ngoài gói, giữ audit trail và các ID có thật để điều tra |
| Vừa | Bảng tiến độ coi đánh giá tài liệu là cũ chỉ vì không có snapshot doanh nghiệp mô phỏng | Nhận diện `USER_EVIDENCE_ONLY`; chỉ dữ liệu mô phỏng mới cần kiểm tra snapshot tương ứng. Có nguồn mới sau đánh giá vẫn phải báo cũ; kiểm tra câu SQL trên PostgreSQL thật |
| Vừa | Thư mục control qua junction/symlink có thể trỏ sang đợt khác vẫn nằm dưới root chung | Ràng buộc đường dẫn resolve đúng đợt/control; collector raw cũng ràng buộc đúng profile/control. Test mô phỏng junction giữa hai đợt, không cần quyền tạo link Windows |
| Thấp | Polling Hồ sơ ISO thiếu dependency của hàm khởi chạy | Dùng `useCallback` và dependency đầy đủ; build/lint xác nhận cảnh báo này hết |

## Kiểm chứng

- 278 test Python đạt; 15 test JavaScript đạt.
- Build frontend đạt; compile các module `backend`, `agent_core`, `evidence_collectors`, `lab_a8` đạt.
- `pip check`: không có dependency không thỏa yêu cầu. Đây không phải quét CVE.
- Lint không có lỗi chặn build; còn 5 cảnh báo trong các component doanh nghiệp/bình luận cũ, không được đưa trở lại giao diện chính.
- Truy vấn tiến độ mới trên PostgreSQL thật trả đủ 56 control. Không tạo nhãn chuyên gia hoặc phê duyệt giả để kiểm thử.
- Các test quyền/chấm mù/phê duyệt dùng actor và thư mục tạm; không tính là nghiên cứu người dùng.

## Cách dùng sau sửa

1. Admin tạo **lượt A.8 mới** để dùng giao thức chấm mù đã sửa. Lượt cũ vẫn xem được lịch sử; không sửa nhãn/báo cáo cũ hoặc gộp hai giao thức thành một cohort.
2. Tài khoản assessor mở lượt do admin tạo, đọc bằng chứng và chấm mù. Không cấp tài khoản admin cho người đang làm nhiệm vụ chấm độc lập.
3. Nộp đủ gói được giao mới xem đối chiếu. Việc không lộ đáp án qua API chưa chứng minh độc lập nếu người chấm đọc repo/đáp án hoặc được người khác tiết lộ ngoài hệ thống.
4. Những hồ sơ đã thu trước đây không bị xóa. Khi bytes gốc đổi hoặc dùng định danh mới, kiểm tra lại bằng chứng và thẩm định/SoA có còn hiện hành.

## Giới hạn chưa được giải quyết bằng đợt rà này

- Chưa có hồ sơ thật đầy đủ cho 56 control, người đánh giá độc lập hoàn tất hoặc phê duyệt chuyên môn.
- Nguồn live mới có 5 probe đại diện; 13 control khác trong nhóm 18 chưa có probe live. Bộ replay vẫn là bộ ca kiểm thử của nhóm.
- Lỗi phân loại live A.8.3 của model vẫn tồn tại, đã có guard chặn; không biến test guard thành tuyên bố model đã suy luận đúng.
- Worker A.8 và khóa file/settings vẫn yêu cầu một tiến trình Uvicorn. Chưa hỗ trợ nhiều worker/nhiều máy hoặc hàng đợi bền vững.
- Chưa thực hiện kiểm thử bấm toàn bộ UI có đăng nhập, kiểm thử tải, pentest hay đánh giá chuyên gia. 15 test JS chủ yếu bảo vệ logic lịch sử, không thay thế kiểm thử giao diện 56/A.8.
- Hồ sơ nộp và hash không tự chứng minh nguồn gốc/nội dung đã xác thực; vẫn cần đối chiếu tài liệu gốc và người sở hữu.

Kết luận: đã sửa các lỗi có thể tái hiện và tăng kiểm thử hồi quy. Hệ thống phù hợp tiếp tục thử nghiệm/nghiệm thu theo phạm vi đã nêu; không khẳng định toàn bộ mã hoặc đánh giá ISO đúng 100%.
