# Kết quả 38 hồ sơ phát triển mô phỏng — 21/11/2026

Bộ dữ liệu do trợ lý tạo để phát triển hệ thống, bổ sung nhóm ngoài 18 A.8. Không phải tập kiểm định độc lập hoặc nhãn thật của Toàn/Khoa/Tú. Không nhập nguồn/quyết định/phê duyệt vào đợt chính.

Model: qwen2.5:7b. Run: `044f6f1b-7406-4204-8edd-b2ef01d1af1e`.
Hash bộ nguồn: `9a4277bc02ab2df4552f871ec8c621445126f69dc820c9575456c865fed8d588`.

## Kết quả thực thi

- 38 lần gọi đầu: 3 lỗi cấu trúc tiêu chí; giữ nguyên phản hồi trong `results`.
- Thử lại đúng 3 lỗi bằng JSON Schema, mỗi ca tối đa một lần: 0 lỗi cuối; giữ `repair_attempts` và `final_results` riêng.
- Khớp đáp án thiết kế: lần đầu 22/38; sau thử lại 23/38 (60,53%). Đây chỉ là khớp khóa thiết kế do trợ lý soạn, chưa có người thẩm định; không phải accuracy so với người đánh giá.
- Kết luận máy cuối: 5 tuân thủ theo tiêu chí lab, 18 một phần, 12 thiếu bằng chứng, 3 không tuân thủ. Không suy rộng ra cả control hoặc toàn doanh nghiệp.
- 15 control lệch khóa thiết kế được giữ nguyên. Cần rà cả cách hiểu tiêu chí, độ đầy đủ của tình huống và lý do model; không mặc định đáp án trợ lý là chân lý chuyên gia.

## Bảng từng control

| Control | Thiết kế của trợ lý | Agent sau thử lại | Khớp thiết kế |
|---|---|---|---|
| A.6.1 | Partially Compliant | Partially Compliant | Có |
| A.6.2 | Partially Compliant | Partially Compliant | Có |
| A.6.3 | Partially Compliant | Partially Compliant | Có |
| A.6.4 | Compliant | Insufficient Evidence | Không |
| A.6.5 | Insufficient Evidence | Insufficient Evidence | Có |
| A.6.6 | Partially Compliant | Insufficient Evidence | Không |
| A.6.7 | Non-Compliant | Non-Compliant | Có |
| A.6.8 | Compliant | Insufficient Evidence | Không |
| A.7.1 | Partially Compliant | Partially Compliant | Có |
| A.7.2 | Partially Compliant | Partially Compliant | Có |
| A.7.3 | Compliant | Insufficient Evidence | Không |
| A.7.4 | Partially Compliant | Insufficient Evidence | Không |
| A.7.5 | Insufficient Evidence | Partially Compliant | Không |
| A.7.6 | Compliant | Partially Compliant | Không |
| A.7.7 | Non-Compliant | Non-Compliant | Có |
| A.7.8 | Partially Compliant | Partially Compliant | Có |
| A.7.9 | Insufficient Evidence | Partially Compliant | Không |
| A.7.10 | Compliant | Compliant | Có |
| A.7.11 | Insufficient Evidence | Insufficient Evidence | Có |
| A.7.12 | Partially Compliant | Insufficient Evidence | Không |
| A.7.13 | Compliant | Insufficient Evidence | Không |
| A.7.14 | Partially Compliant | Partially Compliant | Có |
| A.8.4 | Partially Compliant | Non-Compliant | Không |
| A.8.6 | Partially Compliant | Partially Compliant | Có |
| A.8.11 | Compliant | Compliant | Có |
| A.8.14 | Insufficient Evidence | Partially Compliant | Không |
| A.8.18 | Non-Compliant | Insufficient Evidence | Không |
| A.8.21 | Insufficient Evidence | Partially Compliant | Không |
| A.8.23 | Compliant | Compliant | Có |
| A.8.25 | Partially Compliant | Partially Compliant | Có |
| A.8.26 | Compliant | Compliant | Có |
| A.8.27 | Insufficient Evidence | Insufficient Evidence | Có |
| A.8.28 | Partially Compliant | Partially Compliant | Có |
| A.8.29 | Partially Compliant | Partially Compliant | Có |
| A.8.30 | Compliant | Insufficient Evidence | Không |
| A.8.31 | Partially Compliant | Partially Compliant | Có |
| A.8.33 | Compliant | Compliant | Có |
| A.8.34 | Partially Compliant | Partially Compliant | Có |

## Gợi ý rà các ca lệch

Đối chiếu `checks` theo từng tiêu chí trong JSON với artifact gốc ở `bundle_snapshot`. Phân biệt không có bản ghi (unknown) với quan sát sai (not_met); phân biệt tồn tại biên bản với kết quả biên bản đạt. Không sửa nhãn người chấm hay đổi khóa thiết kế âm thầm để tăng điểm.

Dữ liệu chi tiết: [JSON đầy đủ](a8-results/document-lab-38-2026-11-21.json).

## Trên giao diện

Vào **Doanh nghiệp → Lab hồ sơ bổ sung · 38 control** để đọc nguồn, xuất gói không có đáp án và xem kết quả lab riêng. Admin có thể chạy lượt mới; không thay luồng chấm mù A.8 hay các điều kiện SoA 56.
