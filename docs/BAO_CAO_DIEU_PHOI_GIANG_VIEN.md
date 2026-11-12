# Báo cáo điều phối đánh giá theo yêu cầu giảng viên

Cập nhật 12/11/2026. Vào **Phạm vi 56** bằng admin, mở phần **Báo cáo điều phối theo yêu cầu giảng viên** ở đầu trang. Có xuất JSON/Markdown và lấy snapshot mới.

## Nội dung báo cáo

- Danh mục 56 control, nguồn ngoài preset, kết luận máy, thẩm định hiện hành và bước tiếp theo.
- Kết quả từng control A.8 theo từng lượt: engine, nguồn, rubric/catalog hash, report hash, mức quan sát, lỗi đầu/cuối và số lần sửa hợp lệ.
- Bảng đối chiếu từng người chỉ khi đủ nhãn cùng report/hash và khai báo phù hợp; thiếu nhãn thì ghi chưa có kết quả, không điền 0% hay 100%.
- Tổng hợp luyện tập giả định riêng, không tính số tài khoản thành số ca kiểm định.
- Các lượt hash sai/rỗng/trùng control được nêu trong danh sách loại khỏi tổng hợp; không im lặng giảm mẫu số. Các lượt cũ thiếu metadata được đánh dấu, không tự gán nguồn/rubric mới.
- Tình trạng SoA và danh sách việc chưa hoàn tất; không đổi trạng thái nghiệm thu chuyên môn.

Endpoint chỉ admin có quyền: `GET /api/assessments/{assessment_id}/enterprise/scope56/teacher-report`. Người chấm không xem được kết quả/đáp án trước khi chấm qua báo cáo này. Endpoint chỉ đọc, không ghi nhãn/quyết định/phê duyệt.

## Snapshot kiểm tra

[JSON xuất từ API ngày 12/11](a8-results/teacher-progress-2026-11-12.json): 56 control, 17 lượt hoàn tất có report hợp lệ, 3 lượt cũ thiếu metadata. 54 nhãn luyện tập tách riêng; chưa có lượt đủ nhãn tự khai báo độc lập. Vẫn còn 37 control thiếu nguồn ngoài preset; 19 có nguồn không đồng nghĩa đủ mức bao phủ.

Đây là tổng hợp các lượt lịch sử có điều kiện khác nhau. Không cộng 17 lượt thành một phép đo duy nhất, không gọi các capture khác hash là mẫu độc lập và không suy ra accuracy chuyên gia từ số khớp rubric/guard. Bản snapshot cũ không tự cập nhật; xuất lại sau khi bổ sung hồ sơ hoặc nhãn.

## Kiểm chứng

220 test Python, 5 test JavaScript, lint/build đạt; 3 cảnh báo deprecation thư viện. API thật trả 200, đủ dữ liệu; hash toàn bộ tệp nghiên cứu trước/sau không thay đổi. Kiểm thử tương tác toàn UI vẫn chưa được xác nhận. Hồ sơ, người chấm thật, xác nhận tập kiểm định và phê duyệt vẫn là đầu vào thực tế chưa hoàn tất.
