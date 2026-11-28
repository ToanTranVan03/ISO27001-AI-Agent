# Đối chiếu và tích hợp KhoaTuan7

Nguồn `origin/KhoaTuan7` tại `9c192f7` bổ sung đồ thị People-Centric 8 bước, phỏng vấn theo phòng ban, bộ điều phối công cụ theo rủi ro, bộ sinh doanh nghiệp, adapter mô phỏng/lab, API /api/pc, Streamlit và benchmark M1–M4.

Tích hợp ý tưởng tình huống theo vai trò vào yêu cầu đào tạo A.6.3 hiện có, với ba mẫu Kế toán, Kỹ thuật và Văn phòng. Chuyên viên chọn mẫu để điền bản nháp, rà nội dung và giao bằng luồng đã phân quyền. Mẫu tập trung vào nhận diện dấu hiệu lừa đảo, thao tác cần tránh và kênh báo cáo để khớp rubric hiện tại. Phản hồi vẫn cần thẩm định, giữ phiên bản và lịch sử. Code tại frontend-react/src/EmployeeWorkflows.jsx.

Giữ React, hồ sơ 56 control, bảng bằng chứng, SoA và công cụ lab đã nghiệm thu của ToanTuan7. API /api/pc và kho riêng chưa tích hợp vì cần đối chiếu quyền từng doanh nghiệp và hợp đồng dữ liệu. Adapter ghi hệ thống và benchmark của nhánh Khoa chưa được chạy trong lượt này. Các kết quả benchmark mô phỏng không sử dụng làm độ đúng độc lập. Khi mở rộng nên ưu tiên ghép dữ liệu và kiểm quyền theo đợt trước.

Kiểm tra: lint/build đạt. Edge kết nối backend cục bộ kiểm ba mẫu điền đúng phiên bản và nội dung, xác nhận thao tác chọn mẫu không gửi yêu cầu ghi.

## Tích hợp tiếp vào khắc phục

Áp dụng ý tưởng danh mục thao tác có đích cố định vào hai công cụ đã có của ToanTuan7. Backend khai báo thao tác, đích, tiêu chí phù hợp và cách kiểm tra lại. Màn hình đầu việc hiện người/công cụ thực hiện, trạng thái và nguồn kiểm chứng. Hai tool chỉ chạy trên lab tổng hợp sau phê duyệt, vẫn kiểm đợt, vai trò, phiên bản, rubric và chống chạy lại. Công việc do người thực hiện giữ luồng giao và xác minh hiện có.

Không nhập cơ chế thực thi ngoài lab, backend /api/pc hay Streamlit. Các kết quả thực nghiệm mới cần cam kết phương pháp, phạm vi và tập kiểm định trước khi báo cáo. [Biên nhận kiểm thử](../work/khoa-playbook-2026-11-28.json).
