# Bàn giao nghiệm thu khắc phục Linux và hồ sơ 56 control

| Góp ý | Kết quả |
|---|---|
| Cùng đối tượng trước và sau | Nguồn đầu được thu theo môi trường đã chọn. Phát hiện lưu mã đợt, môi trường, ứng dụng, phiên bản và mã nguồn đầu. Đầu việc lấy đích từ phát hiện. Backend chặn yêu cầu khác đích, rồi kiểm lại ngay trong công cụ trước khi đổi gói. |
| Đúng bằng chứng và quyền | Chỉ nhận nguồn lab do server tạo cho bước ràng buộc. Nguồn sau gắn với đúng đầu việc và đích. Dùng quyền và khóa phiên bản hiện có. Hồ sơ cũ vẫn đọc được. Muốn chạy lại ca cũ thiếu định danh phải thu nguồn đầu và tạo phát hiện mới. |
| Việc nhân viên và chuyên viên | Nhân viên thao tác trên thẻ đầu việc, gắn nguồn đúng đích và gửi. Chuyên viên xác minh riêng. Ca A.8.8 ghi cải thiện một phần vì biên nhận ứng dụng mẫu chưa chứng minh tiêu chí bản vá hệ điều hành. |
| Báo cáo và hồ sơ phạm vi | PDF/Excel giữ biên nhận trước–sau và lịch sử. Đã xuất ma trận 56 control, SoA dự thảo và báo cáo đối chiếu theo đợt. |
| Chấm độc lập và phê duyệt | Báo cáo có 17 lượt thử được lưu. Chưa có người chấm đủ điều kiện đối chiếu độc lập trong báo cáo đã xuất. SoA còn chờ rubric, quyết định áp dụng và thẩm định của người phụ trách. |
| Nhiều thiết bị và hệ điều hành | Đã kiểm Windows tại backend và Debian 12 trong container cô lập. Container là đích thử ứng dụng tổng hợp. Tên thiết bị ở khoảng 08:43–09:35 của bản ghi chưa đủ rõ để chọn lab khác. |

## Kịch bản trình bày 7–10 phút

1. **Doanh nghiệp** (`#view=company`): chọn đợt demo riêng và giải thích đối tượng thử. Tài khoản tư vấn quản lý phạm vi. Ca tự động dùng cấu hình tổng hợp, không dùng danh mục doanh nghiệp thật.
2. **Tổng quan 56 control** (`#view=scope56&control=A.8.8`): trong Tư vấn & khắc phục chọn Linux Debian ở phần thu nguồn, thu phiên bản 1.0.0, tạo phát hiện A.8.8 chọn nguồn đầu đó. Lập kế hoạch, duyệt và giao cho nhân viên. Kiểm mã nguồn và đích đã khóa trên thẻ. Tư vấn chạy công cụ và lưu nguồn sau. Phiên bản quan sát 1.1.0, hash khớp.
3. **Hồ sơ ISO** (`#view=dossier&control=A.8.8`): xem nguồn trong đúng đợt và control. Nhân viên quay lại đầu việc, hoàn thành các bước, gắn biên nhận sau và gửi xác minh. Tư vấn đọc nguồn và kết luận mức cải thiện của đầu việc, giữ phần OS chưa có nguồn.
4. **Thực nghiệm A.8** (`#view=a8&control=A.8.8`): minh họa khác biệt giữa một lượt probe kỹ thuật và hồ sơ khắc phục. Chỉ mở lượt A.8 đã lưu khi có liên kết nguồn phù hợp. Ca cập nhật ứng dụng không tự tạo lượt thử A.8 và hiện chưa có mã finding dùng chung ở cả bốn màn hình.
5. Quay về **Tư vấn & khắc phục**, tải PDF/Excel, chỉ mã phát hiện, mã môi trường, nguồn đầu, phiên bản trước/sau, người duyệt/chạy/xác minh và kết quả còn thiếu.

Lượt hồi quy dùng tài khoản thử do runner tạo. Tạo phát hiện A.8.8, duyệt giao và thử quyền qua API trong bộ tự động. Thu nguồn, điền mẫu, chạy công cụ, lưu nguồn, cập nhật việc phía nhân viên, xác minh một phần và xuất báo cáo qua Edge. Không coi kịch bản bốn màn hình bên trên đã được chạy liền mạch bằng một mã phát hiện.

## Chạy lại và tệp liên quan

```powershell
npm --prefix frontend-react run build
$env:ISO_TEST_LINUX_LAB='1'
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --remediation-only --output work/linux-nghiem-thu-moi.json
```

Linux cần Docker và image cục bộ iso-a8-live-lab:v2. Dùng giá trị 0 cho biến kiểm thử Linux để chọn backend Windows. Biên nhận dùng dữ liệu thử, runner giữ kết quả và dọn database riêng.

Thay đổi ở backend/remediation_api.py, backend/compliance_report.py và evidence_collectors/control_packages.py để ràng buộc, lưu và đọc định danh nguồn lab. lab_a8/software_update_demo.py kiểm đích trong ca chạy. frontend-react/src/RemediationWorkspace.jsx chọn môi trường khi thu nguồn và giữ đích đã chọn ở phát hiện. frontend-react/tests/live-remediation-mfa.spec.js kiểm hồi quy. Dùng cột xuất xứ nguồn và JSONB sẵn có nên không cần migration mới.

Mốc đợt chính đã xuất: 19/56 có nguồn ngoài preset, 18 có nội dung dùng được, 0 quyết định áp dụng và 0 thẩm định hiện hành. Cần nguồn cho 37 control thiếu, chỉnh nguồn không dùng được, xác nhận rubric, tập kiểm định và người chấm độc lập. SoA đang ở dạng dự thảo. Phê duyệt cần người có thẩm quyền.


## Minh chứng đã kiểm

- [Linux qua Edge](../work/linux-nghiem-thu-2026-11-28.json), [Windows hồi quy](../work/windows-bound-2026-11-28.json), [bàn giao laptop](../work/ban-giao-hoi-quy-2026-11-28.json). MFA cũng chạy trong bộ Linux và Windows. Linux và bàn giao có kiểm sau restart. Database thử đã dọn.
- Phát hiện Linux `77c63f0d-8cd8-4bf7-8506-346484795a89` truy vết trong biên nhận và Excel sau khi database thử được dọn. [Mã phát hiện](../work/ban-giao-nghiem-thu-2026-11-28/ma-phat-hien-linux.json). PDF đã đối chiếu môi trường, ứng dụng, phiên bản và kết quả một phần. Dùng Excel hoặc JSON để tra UUID phát hiện.
- [PDF trước–sau](../work/ban-giao-nghiem-thu-2026-11-28/khoi-phuc-linux.pdf), [Excel trước–sau](../work/ban-giao-nghiem-thu-2026-11-28/khoi-phuc-linux.xlsx).
- [Ma trận nguồn 56](../work/ban-giao-nghiem-thu-2026-11-28/ma-tran-nguon-56.xlsx), [SoA dự thảo](../work/ban-giao-nghiem-thu-2026-11-28/soa-du-thao.json), [Đối chiếu người đánh giá theo từng lượt](../work/ban-giao-nghiem-thu-2026-11-28/doi-chieu-giang-vien.json).
- 38 test Python liên quan đạt, frontend lint/build đạt. Hai lần kiểm thử Edge ban đầu vấp vì phép kiểm checkbox chưa chờ API và phép đợi phản hồi bắt nhầm yêu cầu gắn nguồn. Đã chỉnh phép kiểm, chạy lại đạt. Windows chạy ca ràng buộc nguồn và công cụ trước khi bổ sung kiểm thao tác nhân viên ở bản Linux cuối.
