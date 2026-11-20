# Kiểm tra sẵn sàng bàn giao — 20/11/2026

## Thay đổi đã kiểm chứng

- Báo cáo CLI tách đối chiếu đủ điều kiện khỏi nhãn lịch sử: người chấm phải nộp đủ, tự khai độc lập và không còn căn cứ lỗi/cảnh báo chưa xác nhận. Giữ nguyên nhãn khóa; tự khai không chứng minh chuyên môn.
- Giao diện hiển thị thông báo 409/422 và tên trường lỗi; giữ dữ liệu lỗi có cấu trúc, không đưa giá trị đầu vào nhạy cảm vào thông báo validation.
- Thống nhất chính sách `scope56-approval-v2-followup`: lưu nháp được, trình duyệt control áp dụng cần kế hoạch, người nhận, hạn, cách kiểm tra lại và thẩm định hiện hành.
- Phiếu yêu cầu nguồn v2 tách nguồn thiếu/không dùng được khỏi rà mức bao phủ nguồn đã có. Không tự phân công, đặt hạn hoặc tạo bằng chứng.

## Kết quả kiểm thử

| Kiểm tra | Kết quả |
|---|---|
| Toàn bộ pytest | 316 đạt; 3 cảnh báo deprecation thư viện |
| JavaScript request API | 9 đạt |
| Lint và build frontend | Đạt |
| Edge headless, admin/Khoa/Tú | 3 kịch bản đạt trên ứng dụng local |

Các kịch bản Edge có đăng nhập/đăng xuất thật, điều hướng bốn màn hình, mở danh sách bàn giao, tải và đọc SoA JSON đủ 56 dòng, xác nhận SoA vẫn dự thảo và nút duyệt bị khóa; người chấm không có nút khởi chạy lô. Admin thử nộp tệp một ký tự: API từ chối 422, giao diện hiện lỗi; chọn áp dụng chỉ trên form để kiểm tra nhắc trường còn thiếu, **không nộp quyết định**.

Không nộp nhãn, không chạy model, không nộp nguồn hợp lệ và không tạo phê duyệt trong các kịch bản này. Chưa bao phủ toàn bộ thao tác nộp/khóa nhãn, tiếp nhận nguồn hợp lệ, đổi snapshot và phê duyệt thành công trên trình duyệt; các phần đó không được tích hoàn tất bằng kết quả đọc/xuất này. Computer Use native pipe chưa kết nối; kiểm thử Edge thực hiện bằng Playwright, không coi là kiểm thử thủ công hay người đánh giá độc lập.

## Chạy lại

Backend cổng 8000 và Vite cổng 5173 phải đang chạy. Cài dependency bằng `npm ci` trong `frontend-react`; máy cần Microsoft Edge. Tệp `.env` ở gốc chứa `INITIAL_ADMIN_PASSWORD`; cung cấp `ACCEPTANCE_KHOA_PASSWORD` và `ACCEPTANCE_TU_PASSWORD` qua biến môi trường local, không commit mật khẩu.

```powershell
.venv\Scripts\python.exe -m pytest -q
node --test tests/api_request.test.mjs
cd frontend-react
npm run lint
npm run build
npm run test:ui
```

Nếu thiếu mật khẩu người chấm, kịch bản đó báo skipped, không được tuyên bố đủ ba tài khoản. Có thể đặt `UI_BASE_URL` để kiểm tra một địa chỉ local khác. Kết quả Playwright trong `test-results/` không commit vì có thể chứa ngữ cảnh màn hình; kiểm tra console và số passed/skipped trước khi ghi biên bản mới.

## Trạng thái hồ sơ sau kiểm tra

API hiện trả 19 control có nguồn ngoài preset, 18 qua kiểm tra nội dung tối thiểu, A.6.2 cần thay nguồn; 37 chưa có nguồn ngoài preset. Có 38 yêu cầu cung cấp/thay nguồn và 18 yêu cầu rà mức bao phủ riêng. Chưa có xác nhận rubric, quyết định áp dụng hoặc thẩm định hiện hành; SoA vẫn `DRAFT_NOT_APPROVED`.

Xem [phiếu nguồn hiện hành](YEU_CAU_NGUON_56_HIEN_HANH.md) và [danh sách công việc](VIEC_CAN_HOAN_THIEN_56.md). Đây là snapshot ngày kiểm tra, không tự cập nhật theo dữ liệu mới.

## Điều kiện còn phải có trước nghiệm thu

1. Người phụ trách xác nhận rubric và phạm vi nguồn; thống nhất người chấm/phương pháp với giảng viên.
2. Nhóm cung cấp nguồn có nội dung cho phần thiếu và thay A.6.2; chốt tập kiểm định mới trước dự đoán/chấm.
3. Thu nhãn phù hợp, phân tích bất đồng; không dùng nhãn có AI hỗ trợ làm chấm độc lập.
4. Kiểm tra các thao tác UI còn lại trên đợt thử riêng; ghi người thực hiện, thời gian, kỳ vọng/kết quả và trường hợp bị chặn.
5. Ghi 56 quyết định có căn cứ, thẩm định trên nguồn hiện hành và kế hoạch xử lý; người có trách nhiệm duyệt SoA khi đủ điều kiện.

Không tự tích các bước cần xác nhận thực tế. Phạm vi 56 control của đồ án không phải toàn bộ ISMS hoặc chứng nhận ISO.
