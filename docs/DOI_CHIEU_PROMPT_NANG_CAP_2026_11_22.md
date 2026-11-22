# Đối chiếu prompt nâng cấp — 22/11/2026

Đối chiếu toàn bộ prompt đính kèm với code và kiểm thử thực tế. Bản đính kèm mới trùng nội dung bản yêu cầu trước. Phạm vi vẫn là 56 control (8 A.6, 14 A.7, 34 A.8), ưu tiên sâu 18 A.8; không tự mở rộng thành toàn bộ ISMS hoặc cấp chứng nhận ISO.

## Phần đã có và phần bổ sung

| Nhóm yêu cầu | Đã triển khai / minh chứng | Giới hạn còn lại |
|---|---|---|
| Tiếp nhận doanh nghiệp | Bối cảnh có tên/lĩnh vực/phạm vi/địa điểm/phòng ban/tài sản/nghĩa vụ/liên hệ; phiên bản, lịch sử, cùng assessment với inventory | Dữ liệu doanh nghiệp thật cần nhóm cung cấp; chưa có quản trị nhiều tổ chức đầy đủ |
| Yêu cầu và tiêu chuẩn | Catalog 56, rubric và SoA hiện có; thêm sổ yêu cầu có nguồn, phiên bản, quyền sử dụng, phạm vi, liên kết control; sửa có lịch sử và phải rà lại | Không tự sao chép toàn văn chuẩn, thêm luật hoặc giả mạo phê duyệt |
| Đánh giá hiện trạng | Agent đọc nguồn, kiểm chất lượng, kết luận từng control và giữ lịch sử; giữ nguyên 18 A.8 và luồng Scope56 | Probe đại diện chưa bao phủ toàn control; thiếu nguồn vẫn thiếu |
| Phát hiện / phân tích gap | Tạo thủ công hoặc ứng viên từ kết quả trên nguồn hiện hành; khóa baseline/tiêu chí/hash/bối cảnh, chống trùng | Nguyên nhân/mức rủi ro đề nghị cần người có trách nhiệm xác định |
| Rủi ro | **Mới:** sổ rủi ro có asset, kịch bản, likelihood/impact, điểm trước/còn lại, phương án, owner/hạn, liên kết control/phát hiện | Thang 5×5 là quy ước dự án. Rà sổ khác người sửa không tự trở thành chấp nhận rủi ro chuyên môn |
| Kế hoạch khắc phục | Nháp thủ công hoặc Qwen thật có cấu trúc, bước làm/nguồn lực/nghiệm thu/ưu tiên; tư vấn sửa rồi duyệt | AI không tự giao người/hạn, sửa máy doanh nghiệp hoặc phê duyệt |
| Giao việc / phối hợp | Nhiều hành động/task mỗi phát hiện; **mới:** một người chính và nhiều người phối hợp cùng đợt; chỉ người chính gửi xác minh | Phụ thuộc task tuần tự; chưa có DAG tùy ý |
| Theo dõi thực hiện | Trạng thái, task, note và lịch sử theo actor/thời gian; kiểm phiên bản chống ghi đè | Chưa có trò chuyện thời gian thực hoặc chữ ký điện tử |
| Bằng chứng thực hiện | Nộp bản gốc qua luồng hiện có, gắn nguồn mới sau baseline; kiểm control/hash/chất lượng | Chưa có ảnh/video/OCR mới; không tạo nguồn giả |
| Xác minh / đánh giá lại | Người thực hiện, kể cả người phối hợp, không tự xác minh; đạt cần chính người xác minh thẩm định hiện hành viện dẫn nguồn sau; trả bổ sung/làm lại/một phần | Người thật phải đọc và quyết định; hoàn thành task không tự đổi control thành tuân thủ |
| Trước–sau / audit | Giữ baseline bất biến, nguồn/hash, trạng thái, lịch sử task, xác minh và kết quả hiện hành; chặn snapshot/rubric/bối cảnh cũ | Không sửa nhãn khóa hoặc xóa lỗi cũ để tăng số liệu |
| Thông báo / hạn | **Mới:** inbox riêng, đánh dấu đã đọc, giao việc/gửi/xác minh; worker nhắc 3 ngày sắp đến hạn và quá hạn, chống trùng theo ngày | Chỉ trong ứng dụng; chưa cấu hình email/SMS ra ngoài |
| Báo cáo | JSON/CSV/HTML trước–sau; **mới:** XLSX 5 sheet và PDF Unicode trực tiếp theo quyền tài khoản | File chứa dữ liệu cần bảo quản theo quyền doanh nghiệp; không phải chứng chỉ ISO |
| Phân vai hai bên | consultant/verifier/business_admin/operator theo đợt; chặn tự xác minh, kiểm membership và phiên bản ở backend | Phân vai thực tế phải do quản trị có thẩm quyền thực hiện |
| Dữ liệu / triển khai | PostgreSQL thật; migration không xóa bảng cũ; context/finding/risk/requirement/inbox lưu server; kiểm restart trên DB thử | Chưa phải dịch vụ production với HA/DR, email và triển khai Internet đầy đủ |
| Giao diện | Module trực tiếp trong Tổng quan56 → Tư vấn & khắc phục; link control, sổ, task, inbox, báo cáo | Kiểm thử UI không thay đánh giá khả dụng với người dùng thật |
| SoA / chứng nhận | Giữ điều kiện SoA và quy trình quyết định/thẩm định/phê duyệt hiện có; module mới không tự bật gate | Cần nguồn, quyết định và phê duyệt thực tế; không tự tuyên bố đã chứng nhận |
| Độ đúng / nghiệm thu | Tách bài thử tích hợp và kết quả nghiệp vụ; biên nhận ghi rõ synthetic / không phải chấm thật | Chưa có bộ kiểm định và người đánh giá độc lập đủ điều kiện |

## Kiểm chứng

- [432 test Python](a8-results/upgrade-full-2026-11-22-python.xml): engine, API, nguồn, phân quyền, export, sổ và thông báo. 14 test JavaScript; lint/build đạt.
- [Luồng ghi thật cô lập](a8-results/upgrade-final-2026-11-22-isolated.json): PostgreSQL + HTTP thật + Qwen thật, giữ dữ liệu qua restart; DB thử đã dọn, các bảng chính được theo dõi giữ nguyên số dòng. Bao gồm sổ rủi ro/yêu cầu và thông báo riêng.
- [Hồi quy giao diện](a8-results/upgrade-final-ui-2026-11-22.json): kết quả chi tiết từng kịch bản; các form mới dùng API mô phỏng, ghi thật được kiểm riêng ở trên.
- [Ghi thật với người phối hợp](a8-results/upgrade-collaboration-2026-11-22-isolated.json): quyền xem/thực hiện và chặn gửi thay người chính; [migration local](a8-results/upgrade-main-migration-2026-11-22.json): API mới 200, không thêm hồ sơ giả, số dòng bảng chính theo dõi không đổi.
- Để chạy lại trên DB thử riêng: `.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --governance --output docs/a8-results/NEW-upgrade.json`.

Các test dùng hồ sơ tổng hợp riêng, không nộp nhãn hoặc tạo phê duyệt doanh nghiệp chính. Các mốc kiểm thử trước vẫn được giữ.

## Việc chưa thể tự hoàn tất

1. Nhóm cung cấp nguồn còn thiếu, thay A.6.2, xác nhận chất lượng và phạm vi nguồn.
2. Người phụ trách/giảng viên xác nhận rubric, phương pháp và người chấm; cung cấp nguồn tiêu chuẩn/pháp lý hợp pháp nếu muốn mở rộng.
3. Người chấm tự đọc cùng snapshot, khai đúng hỗ trợ và nộp kết luận; có tập kiểm định mới chưa dùng phát triển.
4. Người có thẩm quyền quyết định áp dụng, xử lý rủi ro, thẩm định và phê duyệt SoA.
5. Các chức năng chưa triển khai: quản trị đa tổ chức đầy đủ, toàn bộ điều khoản ISMS/A.5, OCR/video/chữ ký, email/SMS và DAG tùy ý. Không đánh dấu chúng đã hoàn thành.

Không dùng các sổ mới hoặc bài thử để tự đóng 37 control thiếu nguồn hay công bố accuracy với chuyên gia.
