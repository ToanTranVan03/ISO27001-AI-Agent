# Đối chiếu với đề cương và góp ý

Ngày 2026-11-26. Nguồn đối chiếu: `Ke_Hoach_De_Tai_AI_Agent_ISO27001_2022.docx` và nội dung người dùng dán trong cuộc trò chuyện. Giữ kiến trúc và lộ trình 10 tuần; tài liệu này bổ sung tiêu chí nghiệm thu cho mã nguồn trong dự án. Không coi điểm nhận xét về đề cương là số liệu thực nghiệm.

## Các bổ sung đã thực hiện

| Nội dung góp ý | Phần bổ sung | Giới hạn |
| --- | --- | --- |
| Bài 1 — Ma trận nghiệp vụ | [26 hàng tiêu chí](CONTROL_TRACEABILITY.md), công cụ, bằng chứng, điều kiện đạt, hành động, rủi ro, xác minh, ánh xạ 20 họ kịch bản. | Rubric nghiên cứu; chưa được chuyên gia và nguồn ISO có quyền sử dụng xác nhận. Danh mục đủ không đồng nghĩa mọi tool đều đã tích hợp nguồn thật. |
| Điểm tuân thủ | Công thức, trọng số 60/20/20, coverage, thiếu bằng chứng, không áp dụng và cận điểm; code tính điểm đã có kiểm thử. | Trọng số nghiên cứu, không phải điểm chứng nhận. |
| Tách báo cáo/trạng thái | SoA, Gap và Remediation có mục đích riêng; pending không làm tăng điểm tuân thủ. | Bản trích SoA cần chủ sở hữu ISMS rà soát phạm vi, rủi ro và lý do áp dụng. |
| Câu hỏi nghiên cứu | [RQ1–RQ5](EXPERIMENT.md), chỉ số, đối chứng, hiện trạng bằng chứng và phần cần thu. | Chưa có đủ thực nghiệm để trả lời mọi RQ. |
| Đối chứng và người tự nguyện | Yêu cầu cùng snapshot/policy, baseline đủ mạnh, M2 action N/A, thiết kế 10–20 người nếu có điều kiện. | Chưa triển khai bốn nhánh agent đầy đủ hoặc tuyển người. |
| Phân cấp và phục hồi | Low/medium/high, snapshot bản vá/cấu hình, endpoint rollback và nút trên dashboard. | Đã kiểm thử trên PostgreSQL mô phỏng, không phải khôi phục OS thật. |
| AI và điều phối | Graph people/hardware/software/report; tùy chọn chấm câu trả lời bằng Ollama, kiểm tra trích dẫn và lỗi. | Luồng graph xác định; chấm ngữ nghĩa còn bỏ sót ý, cần nhãn chuyên gia. |

## Phần còn thiếu theo lộ trình

| Giai đoạn đề cương | Hiện trạng và việc cần hoàn tất | Điều kiện nghiệm thu tiếp theo |
| --- | --- | --- |
| 1 · Tuần 1–2 · Tiêu chí và kịch bản | Đã có ma trận, 26 mã, 20 họ và nhãn mô phỏng. Cần rà soát nguồn, lý do ánh xạ và rubric với chuyên gia. | Có tài liệu được phép sử dụng cùng bảng xác nhận/điều chỉnh của người thẩm định. |
| 2 · Tuần 2–4 · Đa tenant và generator | Có PostgreSQL/RLS, ABC 50 người, sinh 25 doanh nghiệp và ground truth riêng. Cần mở rộng giữ lại theo thời gian, độ trễ và nhãn độc lập. | Manifest tái lập; test set khóa; kiểm tra phân tầng và nhãn không rò sang agent. |
| 3 · Tuần 3–5 · Tools, API, lab nền | NV015, training/retest, NDA, yêu cầu MFA, bản vá SIM-001 và khóa màn hình chạy trong mô phỏng. Còn email/VPN/kế toán tách hệ thống, USB, mã hóa, whitelist và baseline nhiều trường. Lab mới có khung. | Đóng từng luồng với bằng chứng trước/sau, lỗi, quyền, hết hạn, chống lặp. Lab cần inventory, snapshot và tài khoản thử được cho phép. |
| 4 · Tuần 5–7 · RAG và AI Agent | Có nhập/truy vấn vector lọc tenant, graph ba trụ cột và phỏng vấn. Báo cáo tra được đoạn trích theo tenant và hash. Đã có checkpoint yêu cầu và chạy nền qua API. Còn supervisor chọn tool, checkpoint giữa node và giám sát tiếp diễn. | Kiểm thử nguồn hợp lệ, nguồn thiếu/mâu thuẫn, nội dung chèn chỉ thị, khôi phục phiên và chu trình Inspect–Act–Verify có giới hạn. |
| 5 · Tuần 6–8 · Lab thật và dashboard | API/UI cục bộ chạy; có báo cáo và phê duyệt. Chưa thực thi/xác minh một thay đổi VM; đã kiểm thử toàn luồng Streamlit qua API thật và có trang xem tóm tắt benchmark. | Một hành động thật trên VM cho phép, đối chiếu mới và phục hồi có bằng chứng; demo giao diện trọn luồng. |
| 6 · Tuần 8–10 · Thực nghiệm và bảo vệ | Có kết quả phát hiện mock/Ollama riêng. Chưa có đối chứng hành động M1–M4 đầy đủ, chất lượng trích dẫn, đồng thuận chuyên gia, tổng hợp hiệu năng và báo cáo bảo vệ hoàn chỉnh. | Bộ số liệu thật theo RQ1–RQ5, giới hạn công bố rõ; đủ hai demo bắt buộc trong đề cương. |

## Hai minh chứng bắt buộc

1. Luồng con người: phỏng vấn → giao bài → nhân viên hoàn thành → kiểm tra lại → đọc bằng chứng mới. Đã có kiểm thử tích hợp mô phỏng; chưa chứng minh cải thiện nhận thức của người thật.
2. Một thay đổi cấu hình/tài khoản thật trên VM và đọc lại xác minh. **Chưa có**: cần VM cô lập, snapshot, định danh mục tiêu và quyền thao tác được cung cấp. Không dùng thay đổi JSON trong simulator để thay thế minh chứng này.

Nguồn ISO được phép dùng và VM là điều kiện bên ngoài còn thiếu. Các phần supervisor, nghiệp vụ, dashboard, benchmark và kiểm thử còn lại là công việc mã nguồn chưa hoàn tất; không gộp chúng thành trở ngại do thiếu VM. Kết quả thực tế của từng mục được ghi riêng để theo dõi nghiệm thu. Xem [trạng thái phase](IMPLEMENTATION_STATUS.md) và [AC01–AC15](ACCEPTANCE.md).
