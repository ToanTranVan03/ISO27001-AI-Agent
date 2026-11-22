# Kiểm tra tệp trước khi nộp bằng chứng

Đây là kiểm tra kỹ thuật, không nhập database, không giữ bản gốc, không chạy Agent và không tạo xác nhận chuyên môn. Không cần mở API hoặc có tài khoản để dùng CLI trên tệp mà bạn được phép đọc.

```powershell
.venv\Scripts\python.exe scripts/check_source_before_intake.py --file "DUONG_DAN_TEP_GOC" --assessment-id 7f7c009b-bdcd-5b33-934e-15251ad2c976 --control-id A.6.2 --evidence-type EVID_PPL_CONTRACT_NDA --origin "DON_VI_CUNG_CAP_THUC_TE" --output work/ket-qua-kiem-tra-moi.json
```

Ví dụ dùng loại nguồn hợp đồng/NDA của A.6.2 trong catalog hiện tại. Khi đổi control, chọn đúng `evidence_type` từ danh sách loại nguồn của control trên giao diện. Có thể thêm `--observed-at` với thời điểm ISO có múi giờ và `--note` mô tả phạm vi/mẫu. Không điền thông tin giả chỉ để qua bộ lọc.

- `passed: false`: đọc `issues`, sửa đầu vào hoặc yêu cầu lại bản gốc; chương trình trả mã thoát 1. Không sửa tài liệu để biến kết luận không đạt thành đạt.
- `passed: true`: chỉ qua định dạng, kích thước, trích xuất và ngưỡng nội dung. `coverage_verified` và `provenance_verified` vẫn false. Trường `proposed_evidence_id` chưa phải bằng chứng được lưu.
- Báo cáo không chép văn bản nguồn; giữ hash, số byte và kết quả kiểm tra. Nếu thiếu thời điểm quan sát sẽ có cảnh báo, không tự bịa ngày.
- Công cụ chặn ghi đè báo cáo cũ. Khi thay nguồn hoặc metadata, xuất sang tên mới rồi đối chiếu; không thay kết quả cũ.
- Sau kiểm tra, đọc tiêu chí và đối chiếu bản gốc. Nộp nguồn qua web/connector hiện có; Agent đánh giá lại và người đánh giá thẩm định. CLI không xác nhận độc lập hoặc thay bước phê duyệt.

Minh chứng ngày 22/11: [chạy CLI bằng fixture lab có sẵn](a8-results/release-2026-11-22-source-preflight-example.json), [387 test Python](a8-results/release-2026-11-22-preflight-python.xml). Ví dụ là phép thử phần mềm bằng dữ liệu đã biết, không phải nguồn doanh nghiệp mới. Tệp JSON thiết bị qua kiểm tra định dạng không tự chứng minh tiêu chí bảo vệ endpoint; vẫn phải rà nội dung theo rubric.
