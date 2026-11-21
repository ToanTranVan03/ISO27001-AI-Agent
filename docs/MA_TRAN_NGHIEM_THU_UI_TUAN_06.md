# Ma trận kiểm thử giao diện — tuần 6

Tổng hợp ngày 21/11/2026 **sau khi thực thi**; đây là ma trận minh chứng kỹ thuật, không phải kế hoạch nghiên cứu đã được giảng viên phê duyệt trước hoặc biên bản nghiệm thu chuyên môn.

Phạm vi chốt: các luồng chính đã nêu trong nhật ký (đọc/thu nguồn, chấm, khóa nhãn, tiến độ, xuất báo cáo, các gate quyền/phiên bản). Không tuyên bố đã kiểm thử mọi lỗi có thể xảy ra.

| Mã | Luồng và điều kiện đạt | Minh chứng | Kết quả |
|---|---|---|---|
| UI01 | Admin/Khoa/Tú đăng nhập, bốn màn hình, đăng xuất; không hiện nút điều phối cho người chấm | `release.spec.js` | Đạt trên tài khoản thật, chỉ đọc/POST mô phỏng |
| UI02 | Lượt lịch sử không có nút nộp; liên kết mở được lượt có thể chấm | `acceptance-closure.spec.js` | Đạt, phản hồi API mô phỏng |
| UI03 | Gói mù không hiện kết quả và không render bảng luyện tập | `isolated-workflow.spec.js`, `acceptance-closure.spec.js` | Đạt, API mô phỏng; hai tài khoản thử cũng đọc cùng gói mù qua API thật |
| UI04 | Căn cứ thử bị từ chối, cảnh báo dán nhầm có xác nhận; sửa căn cứ xóa xác nhận cũ | `acceptance-closure.spec.js` | Đạt, POST mô phỏng; bộ lọc thật có hồi quy Python |
| UI05 | Nộp nhãn, khóa sau nộp, tải lại giữ tiến độ, admin đọc đúng lượt | `live-isolated.spec.js` | Đạt, database riêng: mỗi tài khoản nộp một nhãn qua UI, 17 nhãn còn lại qua API; admin thấy 36 nhãn tổng hợp có hỗ trợ |
| UI06 | Nộp nguồn, tải bản gốc, chặn thẩm định với token cũ | `isolated-workflow.spec.js`, `live-isolated.spec.js` | Đạt, gồm ghi thật trên database riêng |
| UI07 | Thẩm định từng tiêu chí, kế hoạch nháp, nhắc trường còn thiếu | `isolated-workflow.spec.js`, `live-isolated.spec.js` | Đạt, dữ liệu tổng hợp, không phải thẩm định chuyên môn |
| UI08 | Chặn SoA thiếu điều kiện; duyệt thử rồi hết hiệu lực khi nguồn thay đổi | `release.spec.js`, `live-isolated.spec.js` | Đạt; phép duyệt dùng phạm vi giả định trên database riêng |
| UI09 | Nhập quyết định theo lô: xem trước chưa ghi, lưu một lô, chặn fingerprint cũ | `live-isolated.spec.js` | Đạt, 55 quyết định tổng hợp; không nhập vào đợt chính |
| UI10 | Chạy lô, chặn lô trùng, dừng, tải lại và chạy tiếp công việc còn lại | `week6-gaps.spec.js`, `live-orchestration.spec.js` | Đạt, gồm worker/Ollama/PostgreSQL thật trên đợt riêng |
| UI11 | Gói ứng viên lỗi không tạo lượt; xem trước/hash/engine; gói hợp lệ giữ snapshot qua worker | `week6-gaps.spec.js`, `live-orchestration.spec.js` | Đạt, gồm gói 18 bản ghi chạy Qwen thật; nguồn thử không phải kiểm định độc lập |
| UI12 | Xuất JSON/CSV/Markdown đúng run/report hash và đủ control, không lộ khóa designer | `acceptance-closure.spec.js`, `release.spec.js` | Đạt, tải/đọc tệp qua Edge |
| UI13 | Nhân viên → hồ sơ → control → lượt nguồn; Back/F5 giữ ngữ cảnh; F5 không tự cuộn/chạy Agent | `navigation.spec.js` | Đạt, không ghi công việc thật |

## Báo cáo

- [11 kịch bản UI đạt, không bỏ qua](a8-results/ui-acceptance-2026-11-21.json).
- [Ghi thật và kiểm tra toàn vẹn nguồn trên database riêng](a8-results/source-integrity-integration-2026-11-21.json).
- [Phép thử làm lệch bản gốc: kết quả cũ cần đánh giá lại, chặn khởi chạy](a8-results/source-integrity-tamper-2026-11-21.json).
- [Gói Qwen và phục hồi sau ngắt backend thử](a8-results/isolated-llm-restart-2026-11-21-retry.json).

Các lần lỗi trước giữ riêng trong lịch sử; không cộng số bài giữa các lần chạy. Lỗi mạng/đồng thời ngoài các tình huống trên và xác nhận trải nghiệm của người dùng vẫn là giới hạn. Chốt mục kiểm thử kỹ thuật trong phạm vi ma trận này không đóng các mục rubric, nguồn, chấm độc lập hoặc phê duyệt SoA.
