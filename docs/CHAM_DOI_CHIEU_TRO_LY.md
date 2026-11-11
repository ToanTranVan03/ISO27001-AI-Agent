# Chấm đối chiếu tự động của trợ lý — 11/11/2026

Nguồn: lượt `2370c707-bbb6-4b6c-b2e0-b19ea1a869b7`, report SHA256 `292b66ad3e10b898436a78e312556fb4a586f55102a84e904ce4396e6462a2fc`.

**Đây là trợ lý AI đọc nguồn đã lưu và đối chiếu rubric lab; không phải nhãn người thật, không chấm mù và không dùng làm accuracy độc lập. Không nộp dưới tài khoản Toàn/Khoa/Tú, không phê duyệt rubric hoặc SoA.**

| Control | Trợ lý | Agent | Căn cứ |
|---|---|---|---|
| A.8.1 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.2 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.3 | Partially Compliant | Partially Compliant | Mã quyền ghi là 1; stat 644 root root. Theo phép thử lab, labworker không ghi được tệp.; Bản ghi labworker có decision=rejected, không thỏa điều kiện approved trong rubric. |
| A.8.5 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.7 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.8 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.9 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.10 | Partially Compliant | Partially Compliant | retention_days=30 nằm trong khoảng 1–30 ngày của lab.; Có biên nhận nhưng object_exists_rc=0: đối tượng vẫn tồn tại, chưa đạt phép kiểm xóa. |
| A.8.12 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.13 | Partially Compliant | Partially Compliant | SHA256 nội dung backup khớp seal đã lưu.; Nội dung restored.dat khác backup.dat: chưa phục hồi đúng dữ liệu. |
| A.8.15 | Partially Compliant | Partially Compliant | Log có sự kiện application_start do ứng dụng lab ghi.; Hash log hiện tại không khớp seal; quyền tệp 644 không khắc phục sai lệch toàn vẹn. |
| A.8.16 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.17 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.19 | Partially Compliant | Partially Compliant | Mã quyền ghi là 1 và thư mục 755 root root: labworker không có quyền ghi thư mục cài.; Danh mục dpkg thực thu khác danh mục phê duyệt lab; approved.tsv không chứa inventory tương ứng. |
| A.8.20 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.22 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.24 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |
| A.8.32 | Insufficient Evidence | Insufficient Evidence | Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này.; Chưa có probe live/nguồn quan sát cho tiêu chí trong lượt này. |

## Kết luận

- 5 control có quan sát: một phần theo hai tiêu chí đại diện; chưa kết luận đạt toàn control.
- 13 control chưa có probe: thiếu bằng chứng, không coi là không tuân thủ hoặc đạt.
- Khớp kết luận cuối của Agent 18/18 theo rubric lab, trong đó 13 là thiếu nguồn. Đây không phải 100% accuracy so với chuyên gia; guard của Agent cũng dựa trên rubric này.
- Bằng chứng/hash của gói đã được kiểm tra; hash không tự chứng minh nguồn là xác thực.
- Bản chấm chỉ nằm trong tệp riêng, không sửa nhãn/phê duyệt trong hệ thống.

## Rà mã liên quan

Kiểm chứng sau sửa: **157 test Python đạt**, còn 3 cảnh báo thư viện; `git diff --check` đạt. Đây là kiểm thử kỹ thuật, không phải số ca người đánh giá.

- Đã sửa luật không được coi facts rỗng, chuỗi hoặc số là các boolean hợp lệ; thiếu check bắt buộc bị chặn trước model.
- Đã sửa nhãn thiếu reviewer_id không được biến thành một người chấm mang tên chuỗi None.
- Luồng graph hiện là PLAN → COLLECT → EVALUATE → VERIFY → REPORT, điều phối sẵn; không phải Agent tự lập mọi kế hoạch kiểm toán.
- Nhánh A.6 dùng luật được ghi rõ nguồn; nguồn live 5 control không đồng nghĩa tự thu đủ 18 hoặc 56.
- Guard so với luật làm kết quả cuối phụ thuộc rubric: cần báo cáo lỗi đầu, lần sửa và tập kiểm định mới; không dùng tỷ lệ khớp luật để suy ra chất lượng độc lập.
- Đây là rà các đường đánh giá/chấm liên quan, không phải cam kết toàn project không còn lỗi.
