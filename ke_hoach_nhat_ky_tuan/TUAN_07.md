# Tuần 7 — Từ đánh giá đến khắc phục và xác minh

- **Thời gian:** 23/11/2026–29/11/2026 (thứ Hai–Chủ nhật).
- **Trạng thái:** Đang thực hiện. Đã nghiệm thu các ca kỹ thuật chính trên môi trường thử.
- **Cập nhật:** 27/11/2026.

## Mục tiêu và kế hoạch

Giữ phạm vi **56 control** của đồ án (8 A.6 con người, 14 A.7 vật lý, 34 A.8 công nghệ), trong đó **18 A.8** được thực nghiệm sâu. Tập trung trình bày chuỗi **đọc bằng chứng → chỉ ra điểm chưa đạt → duyệt và giao việc → thực hiện → đo lại → thẩm định → xuất báo cáo**. Làm rõ bước nào do Agent, công cụ lab, nhân viên và chuyên viên thực hiện.

## Công việc chuyển tiếp từ tuần 6

- Bổ sung nguồn thực tế cho 37 control còn thiếu và thay nguồn A.6.2 theo mốc bàn giao. Cập nhật số liệu khi rà lại đợt chính. [Nhật ký tuần 6](TUAN_06.md)
- Xác nhận rubric, phạm vi và nguồn. Chuẩn bị tập kiểm định mới, thu nhãn độc lập và hoàn tất thẩm định, quyết định áp dụng, phê duyệt SoA.

## Nhật ký công việc chính

| Ngày | Công việc và kết quả |
|---|---|
| 25/11 | Rà liên kết khách hàng, đợt, control, nguồn, hành động và báo cáo. Sửa lỗi đồng bộ hồ sơ, kết luận thẩm định và thông báo. Kiểm tra ma trận 56 control và 10 tình huống kỹ thuật với Qwen. Chuẩn bị kiến trúc, kịch bản, đề cương báo cáo và câu hỏi bảo vệ. [Kiểm tra liên kết](../docs/INTEGRATION_AUDIT_2026.md) · [Nghiệm thu kỹ thuật](../docs/THESIS_FINAL_VALIDATION.md) · [Hồ sơ bảo vệ](../docs/defense/) |
| 26/11 | Bổ sung nhiều doanh nghiệp và kỳ đánh giá riêng, lưu bản chụp từng kỳ và so sánh theo thời gian. Hỗ trợ nộp nhiều tệp, đọc XLSX, tìm bằng chứng đúng phạm vi quyền và nhập bộ doanh nghiệp mô phỏng. Đo riêng tốc độ tiếp nhận và lập chỉ mục. [Nâng cấp doanh nghiệp](../docs/THESIS_ENTERPRISE_AI_AGENT_UPGRADE.md) |
| 27/11 | Tích hợp chọn lọc từ `Tu/Tuan7`: yêu cầu đánh giá, gợi ý hạn theo ngày làm việc, đào tạo, đọc NDA theo phiên bản, yêu cầu MFA và bàn giao. Gắn tài khoản với đúng nhân viên, phân vai thực hiện và xác minh, giữ lịch sử. [Tích hợp nhánh](../docs/TICH_HOP_CHON_LOC_TU_TUAN7.md) · [Luồng nhân viên](../docs/TICH_HOP_LUONG_NHAN_VIEN_TU_TUAN7.md) |
| 27/11 | **Bàn giao laptop · A.6.5:** mở yêu cầu từ đầu việc được giao, kiểm mã thiết bị, chặn mã sai, tải bản gốc biên nhận và giữ lịch sử trả bổ sung. Chuyên viên xác minh tiêu chí thu hồi. Kết luận A.6.5 vẫn thiếu hồ sơ cắt quyền. [Nghiệm thu bàn giao](../docs/NGHIEM_THU_BAN_GIAO_A65.md) |
| 27/11 | **MFA · A.8.5:** thu nguồn ban đầu từ lab, tạo phát hiện theo tiêu chí, duyệt rồi chạy công cụ. Sau khi bật yêu cầu MFA, lần đo riêng từ chối đăng nhập thiếu yếu tố thứ hai và cho phép khi cung cấp đủ. Lưu nguồn sau vào hồ sơ, thẩm định và xác minh trên React, xuất PDF/Excel. [Demo MFA](../docs/DEMO_MFA_LAB.md) |
| 27/11 | **Cập nhật ứng dụng mẫu · tham chiếu A.8.8:** sau khi duyệt, công cụ cập nhật gói thử từ 1.0.0 lên 1.1.0, khởi chạy lại và kiểm phiên bản, trạng thái, hash. Biên nhận trước–sau có trong hồ sơ và PDF/Excel. Phép thử chỉ áp dụng ứng dụng mẫu trong lab. [Phạm vi và cách chạy](../docs/DOI_CHIEU_HANH_DONG_KHAC_PHUC.md) |
| 27/11 | Làm rõ bốn màn hình chính theo mục đích, người thực hiện và bước tiếp theo. Màn Khắc phục cho thấy người duyệt, trạng thái đầu việc và bằng chứng trước–sau. Hồi quy điều hướng giữ đúng ngữ cảnh đợt, control và nhân viên. |

## Kết quả và minh chứng

**Mốc kiểm chứng mới nhất:** 488 test Python, 14 test JavaScript, lint và build đạt. Ca tích hợp MFA và cập nhật ứng dụng chạy trên Edge, FastAPI và PostgreSQL riêng, giữ biên nhận sau khi khởi động lại API. Đã đối chiếu PDF/Excel.

## Vướng mắc và giới hạn

- Một số thao tác ghi nghiệp vụ vẫn được kiểm qua API.
- Kết quả lab và 10 tình huống Qwen chỉ là minh chứng kỹ thuật. Số đo độ đúng với người chấm độc lập còn chờ.
- Demo cập nhật chỉ xác minh phiên bản và hash của ứng dụng mẫu. Kiểm kê và cập nhật trên các hệ điều hành đích cần lab và quyền phù hợp.

## Việc chuyển tiếp sang tuần 8

- [ ] Chạy diễn tập bảo vệ bằng giao diện và bộ dữ liệu riêng; chốt minh chứng, ảnh giao diện, slide và báo cáo theo kịch bản đã cập nhật.
- [ ] Thu hồ sơ còn thiếu và rà lại mức bao phủ trên đợt chính.
- [ ] Xác nhận rubric, phạm vi và nguồn được chấp nhận; chốt tập kiểm định mới và thu nhãn của người đánh giá đủ điều kiện.
- [ ] Hoàn thiện quyết định áp dụng, thẩm định và trình người phụ trách duyệt SoA. [Điều kiện duyệt SoA](../docs/DIEU_KIEN_DUYET_SOA_56.md)
- [ ] Khi có lab thiết bị và hệ điều hành phù hợp, bổ sung công cụ kiểm kê, cập nhật có phê duyệt và đo lại.

## Đồng bộ GitHub

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 25/11/2026 | 12:03 | Trần Văn Toàn | `main` | Kiểm tra liên kết toàn hệ thống và sửa lỗi đồng bộ (`context`, `human_review_current`, làm mới UI khắc phục); nghiệm thu theo mục tiêu đề tài + 10 tình huống AI độc lập; hồ sơ bảo vệ (`docs/defense/`); test mới nâng lên 449 test Python; cập nhật README và nhật ký tuần 7 |
| 27/11/2026 | 07:20 | Trần Văn Toàn | `ToanTuan7` | Tích hợp chọn lọc Tu/Tuan7: yêu cầu đánh giá, gợi ý hạn; đào tạo/NDA/MFA/bàn giao gắn nguồn và xác minh riêng; kiểm thử và cập nhật hướng dẫn |
| 27/11/2026 | 10:12 | Trần Văn Toàn | `ToanTuan7` | Nghiệm thu MFA và bàn giao; bổ sung cập nhật ứng dụng mẫu có phê duyệt, báo cáo trước–sau và làm rõ bốn màn hình |
| 27/11/2026 | 10:21 | Trần Văn Toàn | `ToanTuan7` | Rút gọn nhật ký tuần 7, sắp theo bố cục tuần 6 và chốt việc chuyển tiếp tuần 8 |
| 27/11/2026 | 10:23 | Trần Văn Toàn | `ToanTuan7` | Xóa tệp s.txt |
