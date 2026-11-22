# Hướng dẫn sử dụng hệ thống đánh giá tuân thủ

Khởi động và đăng nhập theo [CHAY_LOCAL.md](CHAY_LOCAL.md). Giao diện chính: http://127.0.0.1:5173.

## Phạm vi 56 control

1. Xem tiêu chí, nguồn và bước cần làm tiếp của từng control.
2. Thu gói hồ sơ hoặc nộp PDF/DOCX phù hợp, đọc nội dung/nguồn/hash đã thu.
3. Chạy **Agent đánh giá hồ sơ đã thu**; kiểm tra kết luận, viện dẫn và phần thiếu.
4. Người đánh giá thẩm định có căn cứ; người phụ trách xác định tính áp dụng và kế hoạch xử lý.
5. Xuất SoA 56 và chỉ phê duyệt khi đủ điều kiện. Thay đổi nguồn/tiêu chí làm thẩm định cũ không còn hiện hành.

Chi tiết: [thu hồ sơ và thẩm định](docs/THU_HO_SO_VA_THAM_DINH_56.md).

## Thực nghiệm 18 A.8

Admin chọn nguồn raw replay hoặc live, profile và engine rồi tạo lượt. Assessor khác tài khoản mở lượt mới để chấm mù. Lượt cũ trước giao thức `blind-v3-coordinator-only` giữ làm lịch sử, cần admin tạo lại để chấm theo giao thức mới.

- Raw: 18 control, 108 ca cấu hình/log mô phỏng.
- Live v2: 18 probe đại diện (5 quan sát tài nguyên, 13 phép thử chủ động trên thành phần ứng dụng lab).
- Baseline là đối chứng luật, không phải AI. Không có nhãn người thật thì chưa có độ đúng so với con người.

Chi tiết: [quy trình nghiệm thu](docs/QUY_TRINH_NGHIEM_THU_A8.md), [giới hạn hiện tại](docs/HOAN_THIEN_THEO_GOP_Y_GIANG_VIEN.md).

## Doanh nghiệp, Khách hàng tư vấn và Hồ sơ ISO

- **Quản lý nhiều khách hàng & đợt đánh giá:** Trong màn hình **Doanh nghiệp → Khách hàng tư vấn**, quản trị viên tạo hồ sơ khách hàng có phiên bản, mở đợt đánh giá mới (`inventory_mode = 'client'`, bắt đầu rỗng, không nạp dữ liệu lab) và cấp quyền thành viên (`consultant`, `verifier`, `business_admin`, `operator`). Chọn đợt đang làm việc trên thanh điều hướng.
- **Khai báo danh mục doanh nghiệp:** Thêm/sửa nhân viên (`EMP-001`...), tài khoản, tài sản kèm snapshot và lịch sử trước/sau. Danh bạ, tài khoản và thiết bị đọc từ PostgreSQL theo đợt; khai báo danh mục không tự tạo bằng chứng tuân thủ.
- **Tư vấn & khắc phục (Remediation):** Trong **Tổng quan 56 control → Tư vấn & khắc phục**, thực hiện luồng: tạo phát hiện từ kết quả đánh giá hoặc thủ công → AI (`qwen2.5:7b`) đề xuất phương án khắc phục có cấu trúc (hoặc lập thủ công) → chuyên viên sửa/duyệt và giao người thực hiện chính, người phối hợp, phân công từng bước con, đặt thời hạn → doanh nghiệp thực hiện từng bước, nộp bằng chứng mới sau khắc phục và gửi xác minh → người xác minh độc lập thẩm định tiêu chí hiện hành, xác minh đạt/một phần/trả làm lại/yêu cầu bổ sung → đóng hành động và xuất báo cáo trước–sau (PDF, Excel XLSX, CSV, HTML, JSON).
- **Dashboard & Sổ quản trị:** Xem Dashboard theo 3 góc nhìn (Chuyên viên / Doanh nghiệp / Lãnh đạo), hộp thư thông báo trong ứng dụng và quản lý Sổ rủi ro (5×5) / Sổ yêu cầu có nguồn.
- Chi tiết: [hướng dẫn hoàn thiện theo s.txt](docs/HOAN_THIEN_THEO_S_TXT_2026_11_22.md) và [nghiệm thu cuối cùng](docs/FINAL_ACCEPTANCE_2026.md).
