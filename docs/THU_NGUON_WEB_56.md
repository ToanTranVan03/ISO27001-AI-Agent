# Thu nguồn gốc và tiếp tục đánh giá 56 control

## Luồng sử dụng

1. Mở **Tổng quan 56 control**, chọn control và mở hồ sơ/thẩm định.
2. Trong **01 · Đọc tiêu chí & bổ sung bằng chứng**, đọc yêu cầu; chọn loại nguồn phù hợp.
3. Chọn bản gốc PDF/DOCX/TXT/MD/JSON/CSV/TSV/CONF/LOG, ghi xuất xứ, thời điểm quan sát nếu biết và giới hạn mẫu. Thời điểm trên form dùng múi giờ máy, gửi UTC tới API. Không biết thì để trống, không đoán ngày.
4. **Lưu nguồn và bản gốc**. Hệ thống kiểm tra đầu vào, lưu hash SHA256 và bản gốc; yêu cầu lặp cùng nội dung/metadata không nạp trùng.
5. Tải lại **Bản gốc** để đối chiếu. Chỉ tài khoản thuộc đúng đợt được tải; API kiểm tra hash trước khi phục vụ tệp.
6. Chạy **Agent đánh giá hồ sơ đã thu**. Nguồn mới làm kết quả cũ cần được rà/tái đánh giá; không dùng kết quả ca thử A.8 thay cho kết luận chính thức.
7. Người đánh giá thẩm định từng tiêu chí trên nguồn hiện hành. Người phụ trách ghi tính áp dụng, lý do, kế hoạch, người nhận, hạn và cách kiểm tra lại; chỉ duyệt SoA khi đủ điều kiện.

Trang **Hồ sơ ISO** cũng có thể tiếp tục control tài liệu chưa có collector riêng khi đã có nguồn dùng được. Nếu có nguồn ngoài preset, hàng đợi chỉ đánh giá nguồn đó. Nếu toàn bộ nguồn ngoài preset không dùng được, không thay bằng preset lab. Control chưa có nguồn/collector không tự suy ra kết luận.

## Kiểm tra và giới hạn

- Tối đa 15MB/tệp, 100000 ký tự trích xuất; JSON kiểm tra cú pháp, văn bản UTF-8, không nhận tệp thực thi hoặc đường dẫn lồng/vượt thư mục.
- Xuất xứ là **khai báo người cung cấp**, chưa phải xác thực độc lập. Hash chứng minh sự nhất quán nội dung, không chứng minh nguồn thật, nội dung đủ control hoặc tuân thủ ISO.
- PDF/DOCX ảnh không trích xuất đủ văn bản cần OCR trước khi nộp; chưa có OCR tự động trong luồng này.
- Bản gốc lưu tại `data/evidence-originals/<assessment-id>/<sha256>.bin`, tách từng đợt và không đưa vào Git. Cần sao lưu cả PostgreSQL và thư mục này khi bàn giao.
- Các nguồn tải qua màn hình PDF/DOCX cũ hoặc nhập gói trước đây không tự có bản gốc hồi tố. Giữ lịch sử; nộp lại từ tệp thực nếu cần lưu bản gốc.
- Nội dung nguồn trong metadata wrapper được kiểm tra riêng; metadata dài không che được nguồn trống/1 ký tự. Dữ liệu cũ vẫn giữ nguyên nhưng nguồn không dùng được bị loại trước suy luận.
- Tiêu chí và hồ sơ vẫn cần người phụ trách xác nhận; không tạo 37 hồ sơ còn thiếu, nhãn người thật hoặc phê duyệt bằng dữ liệu giả lập để đánh dấu hoàn thành.

## Kiểm chứng phần mềm

- 282 test Python, 7 test JavaScript; lint/build frontend đạt.
- Đã kiểm tra trên PostgreSQL thật: lưu nguồn, nạp lại không trùng, đọc bản gốc, kiểm tra hash và đưa vào đầu vào Agent. Toàn bộ dữ liệu thử nằm trong giao dịch rollback; đã xác nhận không còn bằng chứng thử trong đợt thật.
- Chưa kiểm chứng toàn bộ thao tác trình duyệt; kiểm thử mã/API không thay cho kiểm thử UI và thẩm định chuyên môn.

Các việc còn để nghiệm thu chuyên môn: bổ sung nguồn thực cho control còn thiếu và A.6.2; xác nhận rubric/mức bao phủ; bộ kiểm định mới; nhãn đủ điều kiện từ người đánh giá và phân tích bất đồng; quyết định áp dụng/thẩm định/phê duyệt SoA. Công cụ sẵn có không đồng nghĩa dữ liệu này đã được cung cấp.
