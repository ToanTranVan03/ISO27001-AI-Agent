# Theo dõi xử lý và kiểm tra lại — tuần 5

Cập nhật 12/11/2026. Đây là chức năng theo dõi hồ sơ; không tự tuyên bố hoàn tất đánh giá tuân thủ.

## Chức năng vừa hoàn thiện

Trong **Phạm vi 56 → chọn control → Tính áp dụng và kế hoạch xử lý**, người phụ trách có thể ghi:

- Kế hoạch xử lý/duy trì và căn cứ tính áp dụng.
- Người chịu trách nhiệm xử lý.
- Ngày đến hạn theo định dạng ngày lịch.
- Cách kiểm tra lại: nguồn nào phải thu lại, đối tượng nào cần kiểm tra và cách xác minh kết quả.

API kiểm tra định dạng ngày, độ dài thông tin và quyền admin trước khi ghi. Thông tin theo cùng lịch sử quyết định hiện có; thay đổi bất kỳ phần nào của quyết định làm fingerprint SoA thay đổi. Không tự gán thành viên, hạn hoặc đánh dấu công việc hoàn thành.

Kế hoạch đã ghi được đưa vào SoA JSON/Markdown và gói bàn giao. Kế hoạch cũ thiếu người nhận/hạn/cách kiểm tra lại được nhắc trong danh sách việc cần làm nếu control áp dụng. Đây là nhắc hoàn thiện kế hoạch; chưa đặt thêm điều kiện phê duyệt bắt buộc cho các trường tùy chọn này. Không tự suy ra người nhận đã đồng ý hoặc đã thực hiện.

## Cách dùng để đẩy tiến độ

1. Với nguồn còn thiếu: ghi người có hồ sơ, ngày cung cấp và tiêu chí cần chứng minh. Nộp nguồn thực sự có nội dung, không dùng mẫu trống để tăng số lượng.
2. Với điểm không đạt/một phần: ghi biện pháp cụ thể và cách kiểm tra lại. Ví dụ backup: sửa lịch/scope backup, chạy phục hồi và đối chiếu hash trên dữ liệu đại diện.
3. Sau xử lý: thu lại nguồn, chạy Agent và thẩm định snapshot mới. Kế hoạch đã ghi hoặc ngày đến hạn không tự biến kết luận thành đạt.
4. Với thiếu bằng chứng: giữ kết luận chưa đủ căn cứ. Chấm giả lập tiếp tục ở khu riêng; chưa thay nhãn người thật.
5. Xuất gói bàn giao và SoA mới sau mỗi lần rà. Bản xuất cũ là lịch sử, không tự cập nhật.

## Trạng thái chưa được đóng

37 control còn thiếu nguồn ngoài preset; 19 control đã có nguồn vẫn cần rà chất lượng và mức bao phủ. Rubric, 56 quyết định áp dụng, thẩm định hiện hành, nhãn độc lập và SoA chưa được người thật xác nhận. Tập kiểm định mới và kiểm tra thao tác toàn UI cũng chưa hoàn tất. Các mục này cần đầu vào hoặc thao tác thực tế; không thể đóng bằng test hay chấm giả lập.

Kiểm chứng: 215 test Python, 5 test JavaScript, lint/build đạt; API thật trả đủ 56 dòng SoA có trường theo dõi. Kiểm tra đọc API không thay đổi tệp nhãn/quyết định/phê duyệt. Có 3 cảnh báo deprecation thư viện; chưa xác nhận kiểm thử bấm toàn UI.
