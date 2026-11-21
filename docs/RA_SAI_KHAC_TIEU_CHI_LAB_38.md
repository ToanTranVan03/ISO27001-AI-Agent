# Rà sai khác theo tiêu chí — lab hồ sơ 38 control

Ngày 21/11/2026. Đây là phân tích kỹ thuật của trợ lý so với khóa thiết kế do trợ lý soạn; không phải nhãn người chấm độc lập, kết luận chuyên môn hoặc biên bản đã ký.

Lượt: `044f6f1b-7406-4204-8edd-b2ef01d1af1e`.
Hash báo cáo: `06361122ee78c7154d2c8756be5e47ae5af52bbcc1f906780d44cdabbce70777`.
Hash bộ nguồn: `9a4277bc02ab2df4552f871ec8c621445126f69dc820c9575456c865fed8d588`.

## Phát hiện

- 38 control được kiểm tra, không có bản ghi bị loại do phản hồi/viện dẫn không hợp lệ.
- 15 control lệch kết luận tổng, nhưng 18 control lệch ít nhất một tiêu chí: tổng 19 tiêu chí khác khóa thiết kế.
- Các control cùng kết luận tổng nhưng còn lệch tiêu chí: A.6.3, A.6.5, A.7.11. Chỉ xem tỷ lệ theo kết luận tổng sẽ bỏ sót các điểm này.
- 5 tiêu chí khóa ghi chưa rõ nhưng model ghi không đạt; 6 tiêu chí khóa ghi đạt nhưng model yêu cầu thêm nguồn; 1 tiêu chí khóa không đạt nhưng model ghi đạt; 7 sai khác còn lại. Đây là phân nhóm tương đối với khóa, chưa chứng minh bên nào đúng.
- Lượt cũ chưa lưu khóa tiêu chí chốt trước dự đoán: `LEGACY_CURRENT_KEY_NOT_FROZEN`. Giữ cảnh báo, không bổ sung hồi tố thành đã chốt. Lượt mới lưu snapshot và hash khóa trước khi gọi model; khóa không đi vào prompt.

## Danh sách cần rà

| Control / tiêu chí | Yêu cầu | Khóa thiết kế | Model | Lý do model |
|---|---|---|---|---|
| A.6.3 / 1 | Tỷ lệ nhân sự hoàn thành khóa học đạt 100% | Không đạt | Đạt | All employees have completed the course as the number of completed employees (48) equals the required number (50) minus the pending employees (2). |
| A.6.3 / 2 | Có bài kiểm tra đánh giá nhận thức | Đạt | Không đạt | There is no evidence of a test being conducted as the records do not include any information about a test or assessment results. |
| A.6.4 / 2 | Được truyền đạt đến toàn bộ nhân viên | Đạt | Chưa rõ | While the policy document has been published, there is no explicit record of it being distributed to all employees. |
| A.6.5 / 1 | Có checklist thu hồi tài sản | Đạt | Không đạt | The 'access_revocation_export' is not_collected due to IAM audit export not being supplied. |
| A.6.6 / 2 | Văn bản NDA còn hiệu lực | Không đạt | Chưa rõ | The records do not provide information on the current validity of the NDAs beyond their expiration dates. There is no explicit mention of whether the NDAs are still effective after their expiration dates. |
| A.6.8 / 2 | Nhật ký ghi nhận sự kiện ATTT | Đạt | Chưa rõ | While the artifact includes an event register, there is no explicit mention of an ATT&CK (Advanced Threat Detection and Knowledge) log, only a generic event register. |
| A.7.3 / 2 | Quy định khóa cửa ngoài giờ làm việc | Đạt | Chưa rõ | The artifact does not provide information on the key custodian's actions after 18:00 to confirm if the doors were locked as per the policy. |
| A.7.4 / 2 | Thời gian lưu trữ video đáp ứng quy định | Không đạt | Chưa rõ | The artifact does not provide information on the actual time period the video recordings are stored, only the policy and retention period. |
| A.7.5 / 1 | Biên bản nghiệm thu/bảo trì PCCC | Chưa rõ | Không đạt | The 'Biên bản nghiệm thu/bảo trì PCCC' is not collected according to the records. |
| A.7.6 / 2 | Quy định cấm quay phim/chụp ảnh | Đạt | Không đạt | The records do not contain any explicit prohibition against photography or any other form of media capture in secure areas. |
| A.7.9 / 2 | Thiết bị được mã hóa ổ cứng | Chưa rõ | Không đạt | The disk encryption status is not collected. |
| A.7.11 / 1 | Nhật ký bảo trì UPS, máy phát điện | Chưa rõ | Không đạt | The criterion requires 'Nhật ký bảo trì UPS, máy phát điện', but the artifact records show 'availability': 'not_collected' for 'ups_generator_records'. |
| A.7.12 / 2 | Biên bản kiểm tra hạ tầng vật lý | Đạt | Chưa rõ | The artifact does not contain a physical inspection report, only a synthetic inspection record. |
| A.7.13 / 2 | Biên bản bảo trì thiết bị lưu hệ thống | Đạt | Chưa rõ | The artifact does not contain any explicit 'Biên bản bảo trì thiết bị lưu hệ thống' (maintenance log) entries, only a register of completed and scheduled maintenance. |
| A.8.4 / 2 | Phân quyền read/write kho mã nguồn rõ ràng | Đạt | Không đạt | The roles are not clearly defined as read/write. LAB-AUDIT is listed as read, but there is no explicit write role defined for any member. |
| A.8.14 / 2 | Tài liệu kiến trúc hệ thống dự phòng | Chưa rõ | Không đạt | The 'architecture_document' and 'failover_test' records indicate that availability information is not collected, which is required by the criterion. |
| A.8.18 / 2 | Danh sách công cụ quản trị được cấp quyền hợp lý | Không đạt | Chưa rõ | The scenario does not provide a list of authorized utility programs or any review tickets related to the authorization process. |
| A.8.21 / 1 | Tài liệu yêu cầu SLA bảo mật với nhà cung cấp mạng | Chưa rõ | Không đạt | The criterion states that there should be a security SLA with the network service provider, but the artifact does not provide this information. |
| A.8.30 / 2 | Biên bản rà soát mã nguồn do bên gia công bàn giao | Đạt | Chưa rõ | There is no explicit mention of a source code review log or record in the provided artifact. |

## Việc tiếp theo

1. Người phụ trách đọc tiêu chí và artifact của từng dòng, xác định tiêu chí đang hỏi sự tồn tại của hồ sơ hay hiệu quả thực thi; không mặc định biên bản có điểm lỗi là không có biên bản.
2. Với nguồn không thu được, rà xem kết luận đúng phải là chưa rõ hay đã quan sát thất bại. Không có chữ ký khác với không thu được trang chữ ký.
3. Nếu sửa rubric/khóa, lưu phiên bản mới và lý do; báo cáo cũ giữ nguyên. Không sửa đáp án để hợp thức hóa kết quả Agent.
4. Nguồn thay đổi hoặc hash không khớp thì API từ chối phân tích với khóa hiện tại. Đây không thay việc xác nhận chất lượng/tính độc lập của bộ kiểm định.

Trên UI: **Doanh nghiệp → Lab hồ sơ bổ sung → Rà sai khác theo từng tiêu chí lab**. Chọn lượt cũ/mới, lọc ca lệch, bấm control để đọc nguồn và xuất JSON có hash báo cáo.

[JSON chi tiết](a8-results/document-lab-criterion-audit-2026-11-21.json). Không sửa nhãn khóa, dữ liệu đầu vào hoặc phê duyệt SoA khi xuất phân tích.
