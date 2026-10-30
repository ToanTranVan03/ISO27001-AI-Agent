# Nâng cấp học thuật HiveFive

- [x] Hồ sơ sự việc: trước/sau, bằng chứng, thiếu dữ liệu, khắc phục và tái kiểm tra.
- [x] Agent: kiểm tra sâu dữ liệu thiếu; số đo thời gian và quyết định công cụ.
- [x] Thực nghiệm: ca tổng hợp có nhãn riêng, ba chế độ, báo cáo kết quả có thể tái lập.
- [x] Kiểm tra Python/JS, trình duyệt và tài liệu nghiên cứu.

Minh chứng: 40 test Python, 3 test tìm đường; Ollama thật 3 ca; UI HF-042
thiếu bằng chứng revision 5 → khắc phục revision 6 → AI xác minh và đóng việc.
Đây là hoàn tất phần nâng cấp kỹ thuật đã lên kế hoạch. Thẩm định chuyên gia,
dữ liệu doanh nghiệp thật, nghiên cứu người dùng vẫn là giới hạn học thuật.

## Đào sâu nghiệp vụ và so sánh công bằng
- [x] Đào tạo hết hạn, nguồn LMS mâu thuẫn, chuyển vai trò và ngoại lệ giữ tài khoản có phê duyệt/thời hạn.
- [x] Agent kiểm tra ngữ cảnh nghiệp vụ và giải thích căn cứ xử lý.
- [x] Thực nghiệm ba chế độ cùng tập ca, lặp nhiều lần; báo cáo độ phân tán và lỗi.
- [x] UI thao tác/căn cứ mới, kiểm thử và tài liệu bảo vệ/khảo sát người dùng.

Kiểm chứng: 47 test Python, 3 test tìm đường; 72 lượt thực nghiệm Ollama/luật/
workflow cùng 8 ca, 3 lần lặp. UI mâu thuẫn nguồn và rà soát vai trò đã xác minh.
Chưa nạp hai sửa logic cuối vào server đang chạy vì lệnh khởi động lại bị
automatic policy chặn. Chi tiết ở docs/VALIDATION.md; không coi runtime đã cập nhật đủ.
