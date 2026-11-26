# Rubric Phase 02

Danh mục dùng cú pháp JSON tương thích YAML. Từ thư mục dự án, chạy `python -m compliance_ai.cli validate-catalog`. Ba chính sách mẫu ABC, small và regulated có ngưỡng do đề tài chọn. Kiểm tra ngưỡng dùng giá trị tại phiên bản chính sách đang đánh giá.

Bộ quy tắc dùng quan sát đã xác minh từ nguồn nghiệp vụ. Trường nhị phân biểu diễn kết quả đối chiếu do nguồn được ủy quyền cung cấp. Trường thời gian hoàn thành, điểm đào tạo và thời gian khóa màn hình được kiểm tra theo ngưỡng. Bằng chứng thiếu, hết hạn, chưa xác minh, sai kiểu hoặc mâu thuẫn cho trạng thái thiếu bằng chứng. Ngoại lệ phạm vi được đưa vào chính sách có lý do. H04 và D06 cần thẩm định thủ công. Rubric phỏng vấn tiếng Việt có tình huống kiểm tra lại riêng.

Mỗi cặp tiêu chí và đối tượng chỉ tính một lần. Sau khi loại trừ các trường hợp có lý do, các đối tượng trong cùng tiêu chí chia đều trọng số của tiêu chí. Điểm trụ cột sử dụng trọng số tiêu chí, còn điểm tổng hợp dùng 60/20/20. Khi trụ cột thiếu dữ liệu cần thiết, chỉ số tổng hợp phụ thuộc vào trụ cột đó hiển thị N/A. Điểm đối chứng cho mỗi tiêu chí trọng số bằng nhau. Điểm trên phần đã biết, độ bao phủ và cận dưới/cận trên dùng mẫu số tương ứng. Hồ sơ hành động đang chờ không được đưa vào như bằng chứng hoàn thành.

Xem [ma trận truy vết](CONTROL_TRACEABILITY.md) để đối chiếu mã và nhóm tình huống. Các nguồn nghiệp vụ, triển khai công cụ, bộ sinh kịch bản và luồng phỏng vấn được kiểm thử ở các phase tiếp theo.
