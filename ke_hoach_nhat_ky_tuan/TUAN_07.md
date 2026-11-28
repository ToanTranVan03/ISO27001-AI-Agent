# Tuần 7 — Từ đánh giá đến khắc phục và xác minh

- **Thời gian:** 23/11/2026–29/11/2026 (thứ Hai–Chủ nhật).
- **Trạng thái:** Đang thực hiện. Đã nghiệm thu các ca kỹ thuật chính trên môi trường thử.
- **Cập nhật:** 28/11/2026.

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
| 27/11 | Làm rõ mục đích của bốn màn hình. Khu Tư vấn & khắc phục trong Tổng quan 56 control hiển thị người duyệt, người thực hiện, đích và bằng chứng trước–sau. |
| 28/11 | Tích hợp chọn lọc từ `KhoaTuan7`: ba mẫu luyện tập theo vai trò và cách đăng ký công cụ đích cố định cho ca MFA, cập nhật ứng dụng. [Phạm vi tích hợp](../docs/TICH_HOP_KHOA_TUAN7.md) |
| 28/11 | **Nghiệm thu Linux và truy vết A.8.8:** tạo phát hiện, duyệt giao, chạy công cụ, gắn nguồn và xác minh qua Edge. Giữ cùng mã phát hiện qua bốn màn hình, tải lại và mở từ báo cáo. Lượt live A.8 thu thêm phiên bản và hash của ứng dụng mẫu; backend kiểm tra khớp đợt, cấu hình đích, ứng dụng, phiên bản và hash trước khi gắn lượt với phát hiện. Đối chiếu PDF, Excel và JSON. [Biên bản và báo cáo](../docs/NGHIEM_THU_LIEN_KET_BAN_THU_A8.md) |
| 28/11 | **Chuẩn bị ca vá hệ điều hành:** bổ sung kiểm gói nguồn đo trước, biên nhận và đo lại; tạo manifest nhập hồ sơ A.8.8 và kiểm lại SHA-256 khi nhập. Hướng dẫn nộp nguồn trên A.8.8 và kiểm nội dung trích xuất của bản thay thế A.6.2. [Hướng dẫn tiếp nhận](../docs/NOP_BANG_CHUNG_BAN_VA_A88.md) |

## Kết quả và minh chứng

**Mốc kiểm chứng ngày 28/11:** 496 test Python thuộc nhánh, 16 test JavaScript đạt. Lint và build đạt ở lượt kiểm giao diện gần nhất. Ca Edge sử dụng FastAPI và PostgreSQL thử riêng; hồi quy Linux, Windows, MFA và bàn giao laptop có biên nhận kiểm thử. Liên kết lượt A.8 với phát hiện vẫn đọc được sau khi khởi động lại API.

## Vướng mắc và giới hạn

- Trong ca nối A.8.8, bước khởi chạy lượt nghiên cứu và nhập bản thu được kiểm qua API. Các bước tạo phát hiện, duyệt giao, cập nhật và xác minh được kiểm qua Edge.
- Ca cập nhật ứng dụng mẫu ghi **cải thiện một phần**. Ca vá hệ điều hành chờ xác nhận thiết bị trong ghi âm, máy thử cô lập được cấp quyền, mã bản vá, phê duyệt và phương án phục hồi.
- Đợt chính còn 37 control thiếu nguồn ngoài preset và A.6.2 cần bản đọc được thay thế. Rà thư mục gói ngày 28/11 có 56 manifest trống và chưa có tệp nguồn mới. Độ đúng đối chiếu độc lập và phê duyệt SoA còn chờ.

## Việc chuyển tiếp sang tuần 8

- [ ] Chạy diễn tập bảo vệ bằng giao diện và bộ dữ liệu riêng; chốt minh chứng, ảnh giao diện, slide và báo cáo theo kịch bản đã cập nhật.
- [ ] Thu hồ sơ còn thiếu và rà lại mức bao phủ trên đợt chính.
- [ ] Xác nhận rubric, phạm vi và nguồn được chấp nhận; chốt tập kiểm định mới và thu nhãn của người đánh giá đủ điều kiện.
- [ ] Hoàn thiện quyết định áp dụng, thẩm định và trình người phụ trách duyệt SoA. [Điều kiện duyệt SoA](../docs/DIEU_KIEN_DUYET_SOA_56.md)
- [ ] Chốt thiết bị và quyền thử, thực hiện ca vá đã duyệt, nộp ba nguồn trước–thực thi–sau và thẩm định riêng tiêu chí vá hệ điều hành.

## Đồng bộ GitHub

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 25/11/2026 | 12:03 | Trần Văn Toàn | `main` | Sửa đồng bộ hồ sơ, kiểm thử với Qwen và bổ sung tài liệu bảo vệ. |
| 27/11/2026 | 07:20, 10:12, 10:21, 10:23 | Trần Văn Toàn | `ToanTuan7` | Tích hợp luồng nhân viên, nghiệm thu MFA và bàn giao, bổ sung ca cập nhật ứng dụng và báo cáo trước–sau; cập nhật nhật ký và dọn `s.txt`. |

### Nhánh thành viên được tích hợp chọn lọc

Mốc do GitHub ghi nhận, quy đổi sang UTC+7. Sự kiện tạo nhánh là lần nhánh xuất hiện trên GitHub.

| Ngày | Giờ (UTC+7) | Thành viên · tài khoản GitHub | Nhánh | Hoạt động |
|---|---|---|---|---|
| 26/11/2026 | 21:05:39, 21:20:51 | Lê Đoàn Văn Tú · `vantu1410` | `Tu/Tuan7` | Tạo nhánh tại `3dbcf10`; push `720943e` bổ sung yêu cầu đánh giá và báo cáo. |
| 28/11/2026 | 00:22:24 | Lê Đăng Khoa · `Gera-YCYC` | `KhoaTuan7` | Tạo nhánh tại `9c192f7`; nhóm tích hợp chọn lọc mẫu luyện tập và danh mục công cụ. |
