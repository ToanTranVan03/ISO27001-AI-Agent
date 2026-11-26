# Kiến trúc

FastAPI cung cấp giao diện HTTP tiếng Việt và OpenAPI. Cấu hình lấy từ môi trường hoặc tệp `.env` cục bộ. Kiểm tra `/health` xác nhận API phục vụ yêu cầu. Trạng thái sẵn sàng của kho dữ liệu được kiểm tra riêng.

PostgreSQL 16 cùng pgvector chạy trên địa chỉ loopback qua Docker Compose. API chạy độc lập bằng Uvicorn để tiện phát triển trên Windows. Tắt LAB và dùng SIMULATION cho các chức năng nghiệp vụ khi chúng được triển khai.

Tham khảo [pgvector](https://github.com/pgvector/pgvector) và [Alembic](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

## Luồng hiện có

Đánh giá dùng LangGraph với bước thu quan sát, ba node people/hardware/software rồi tính điểm và lưu báo cáo. Kết quả có workflow_steps để truy lại đường xử lý. Đây là điều phối theo luồng xác định; chưa phải supervisor LLM tự chọn công cụ. API lập kế hoạch, Policy Gate, phê duyệt, thực thi và xác minh làm việc qua sổ hành động PostgreSQL tách khỏi kết luận tuân thủ.

Phỏng vấn có một lượt hỏi bổ sung. Mặc định chấm theo cụm từ; người thử nghiệm có thể chọn Ollama khi backend được cấu hình. Provider chỉ kết nối máy cục bộ, không theo redirect hoặc proxy; đầu ra theo schema và trích dẫn phải nằm trong câu trả lời. Model lỗi hoặc yêu cầu thẩm định không được suy ra đạt. Trích dẫn khớp văn bản chưa bảo đảm model diễn giải đúng, nên cần đánh giá chuyên gia.

Medium endpoint actions lưu snapshot và cần phê duyệt độc lập. Rollback do người duyệt yêu cầu, chỉ khôi phục khi revision, postcondition và policy vẫn khớp; đọc lại và ghi bằng chứng trước khi trả ROLLED_BACK. Luồng hiện chỉ thay đổi dữ liệu mô phỏng. Checkpoint worker, giám sát liên tục và adapter VM đầy đủ còn thiếu.
