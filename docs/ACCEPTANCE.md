# Nghiệm thu bản mô phỏng

Ngày kiểm tra 2026-11-26. Mã nguồn nằm trong cây làm việc của dự án. Chưa tạo commit mới trong đợt triển khai này. FAIL trong bảng nghĩa là tiêu chí nghiệm thu còn thiếu hạng mục.

| ID | Trạng thái | Bằng chứng và phạm vi |
| --- | --- | --- |
| AC01 | PASS | PostgreSQL, migration, Compose, HTTP /ready và Streamlit health. |
| AC02 | PASS | ABC 50 nhân viên. Hai lượt sinh 25 doanh nghiệp cho cùng manifest và 1.650 ca. |
| AC03 | BLOCKED | 26 mã và 20 họ kịch bản đã qua xác thực. Còn đối chiếu nguồn ISO được cấp phép và chuyên gia. |
| AC04 | PASS | Kiểm thử âm tính cho API, hành động, vector, kho nhãn và quyền nhân viên trong phạm vi API hiện có. |
| AC05 | PASS | Bằng chứng, phiên bản chính sách và trạng thái thiếu dữ liệu trong bài kiểm thử rubric và đánh giá. |
| AC06 | FAIL | Luồng phỏng vấn, hỏi bổ sung, giao bài và retest có kiểm thử. Đã thêm Ollama ngữ nghĩa và chạy hai câu tổng hợp; model còn bỏ sót ý. Cần bộ nhãn chuyên gia để nghiệm thu chất lượng. Nhóm người tự nguyện chưa thực hiện. |
| AC07 | PASS | H09/M01 đã xác minh sau thu hồi. D02 chờ đến khi kho mô phỏng ghi biên nhận của đúng thiết bị, nhân viên và phiếu. Kiểm thử đối chiếu cùng mã biên nhận ở hành động và kết quả đánh giá mới. |
| AC08 | PASS | Endpoint mô phỏng có sai lệch bản vá và khóa màn hình. Đã chạy phê duyệt, cập nhật và xác minh cả hai trên PostgreSQL test. |
| AC09 | PASS (mô phỏng) | Chạy thử, duyệt và thực thi dùng chung điều kiện về đích, chính sách và thời hạn. Đã kiểm thử hết hạn trước/sau khi duyệt, chặn tự duyệt, tài khoản bảo vệ, revision cũ, gửi lặp và khôi phục endpoint bằng snapshot. Phần VM thuộc AC11. |
| AC10 | PASS | Giao dịch xác minh độc lập đọc lại revision. Bài đào tạo và trả tài sản vẫn chờ nếu chưa có chứng cứ. |
| AC11 | BLOCKED | Có script đọc và đổi timeout cho đúng người dùng thử nghiệm. Đã kiểm tra cú pháp. Cần VM Windows cô lập, snapshot, danh sách cho phép và phê duyệt để thu bằng chứng đổi và phục hồi thật. |
| AC12 | FAIL | API chạy trên Compose, dashboard tải được. AppTest đăng nhập qua Uvicorn thật và kiểm tra danh sách tenant của auditor. Luồng phía máy chủ có kiểm thử đầu cuối. Chưa có kiểm thử trình duyệt suốt toàn bộ luồng. |
| AC13 | FAIL | M1–M4 có kết quả phát hiện trên 25 doanh nghiệp, chế độ mock và Ollama riêng. M2/M3 dùng chung dự đoán phát hiện trong phép đo này. Còn so sánh tool use, hành động, tỷ lệ xác minh và chất lượng trích dẫn theo từng phương pháp. |
| AC14 | PASS | Điểm, độ bao phủ, khoảng từ cận dưới đến cận trên và trạng thái hành động lưu riêng. Kiểm thử đối chiếu trước/sau cùng phạm vi và phiên bản. |
| AC15 | FAIL | Có lockfile, Compose, README, hướng dẫn và kết quả có thể tái chạy. Nghiệm thu toàn đặc tả còn các mục ở trên. |

Lệnh kiểm thử PostgreSQL trên Windows là `& .\scripts\test-postgres.ps1`. Xem [trạng thái chi tiết](IMPLEMENTATION_STATUS.md), [hướng dẫn trình diễn](USER_GUIDE.md) và [thực nghiệm](EXPERIMENT.md).

Đợt bổ sung ngày 2026-11-26: 30 bài kiểm thử đạt, không skip; Ruff, mypy (38 tệp), pip check và xác thực danh mục đều đạt. Số lượng test không thay thế các tiêu chí còn FAIL/BLOCKED.
