# HiveFive — kế hoạch triển khai

Đặc tả `docs/SPEC-people-simulation.md` được người dùng duyệt ngày 2026-10-30.

1. Tạo fixture 50 nhân sự, tài khoản và laptop; kiểm thử các tình huống và
   đánh giá A.6.1–A.6.8 dựa trên bằng chứng, không dùng đáp án benchmark.
2. Thêm API mô phỏng, giải thích qua Ollama có timeout và lỗi rõ ràng;
   giữ API cũ và cho phép chế độ quy tắc khởi động độc lập với model.
3. Tạo giao diện local tiếng Việt, xem hồ sơ, chọn tình huống, xem kết quả
   và bằng chứng; kiểm thử API và trình duyệt.
4. Theo yêu cầu bổ sung: mô hình 3D một tòa nhà ba tầng trên Trái Đất, lấy
   góc nhìn và phong cách nhân vật từ video tham khảo. Hiển thị 50 nhân vật,
   chọn nhân sự, xem nội thất, chuyển phòng ban và đồng bộ phát hiện.

Thiết kế: bảng điều khiển nền sáng, màu xanh đậm và vàng mật ong, nội dung
ưu tiên tình huống và phát hiện. Không dùng tài nguyên bên ngoài. Một cột
trên màn hình nhỏ, bảng có vùng cuộn riêng, trạng thái tải/lỗi có văn bản.

Kiểm tra: `py -3.11 -m unittest discover -s tests -v`, kiểm tra trình duyệt
local và gọi model Ollama thực tế nếu khả dụng.

Hoàn tất: kiểm thử logic/API, kiểm thử WebGL qua Edge, lọc nhân sự, chọn nhân
vật, chuyển tầng và nội/ngoại thất, bốn kích thước màn hình và lỗi Ollama.

Theo phản hồi giao diện rối: hoàn tất chế độ một phòng, di chuyển nhân vật
bằng click/WASD/nút điều khiển với tránh bàn và biên phòng, luồng ba bước,
kết quả liên quan mở trước và chi tiết thu gọn. 3 test tìm đường và kiểm thử
trình duyệt cho di chuyển đã đạt; 16 test Python vẫn đạt.

Theo phản hồi chưa giống Agent: thêm vòng lặp LLM chọn công cụ có điều kiện,
nguồn doanh nghiệp hỗn hợp độc lập tình huống, công việc SQLite chống trùng,
tái kiểm tra snapshot mới, API stream và giao diện giao mục tiêu. Đã kiểm tra
model Ollama thật hoàn tất vòng lặp; 25 kiểm thử Python đạt.

Theo yêu cầu thao tác xong Agent tự phát hiện: đã chuyển màn hình chính sang
nguồn sống theo sự kiện, lưu dữ liệu trước/sau và revision, worker máy chủ tự
kiểm tra và tái kiểm tra khi người dùng khắc phục. Không cần nút chạy Agent.
Đã kiểm thử qua UI/Ollama thật với nghỉ việc và đào tạo. 33 test Python đạt.
Đã làm lại nội thất/vật liệu/ánh sáng/nhân vật, đưa mô hình lên đầu và bảng
nghiệp vụ cạnh cảnh 3D. Tài liệu thiết kế đồ án ở `docs/THIET-KE-DO-AN.md`.

## Nâng cấp theo đánh giá học thuật (2026-10-30)

Người dùng yêu cầu thực hiện các cải tiến đã đề xuất. Giữ dữ liệu sống hiện có.
1. Hồ sơ sự việc theo nhân sự: hiển thị thay đổi trước/sau, bằng chứng,
   phân biệt vi phạm và thiếu dữ liệu, đề xuất khắc phục rồi tự tái kiểm tra.
   Đạt khi chọn nhân vật thấy bằng chứng tương ứng và khắc phục qua API hiện có.
2. Agent kiểm tra sâu cả bằng chứng thiếu; ghi thời gian, lựa chọn công cụ và
   kết quả thực tế. Đạt khi kiểm thử thiếu dữ liệu và giới hạn công cụ đều qua.
3. Bộ thực nghiệm độc lập với các kịch bản UI, nhãn kỳ vọng viết riêng; so sánh
   luật, workflow và Ollama trên cùng snapshot. Đạt khi xuất JSON có kết quả
   từng ca, thời gian, độ chính xác và lỗi; không tuyên bố AI tốt hơn khi chưa có số liệu.
4. Giao diện đặt hồ sơ sự việc cạnh mô hình, luồng xử lý rõ ràng, xuất bằng chứng;
   kiểm tra trình duyệt, màn hình nhỏ và cập nhật tài liệu phương pháp/giới hạn.

Thiết kế giữ màu sage/oak hiện có; giảm hero, ưu tiên một nhân sự/một hồ sơ.
Rủi ro: bộ dữ liệu tổng hợp nhỏ không đại diện doanh nghiệp thật; cùng evaluator
ở ba chế độ nên không dùng accuracy để chứng minh đóng góp riêng của LLM.

## Đào sâu ngữ cảnh và đánh giá ghép cặp

Đã triển khai thời hạn đào tạo, mâu thuẫn HR/LMS, rà soát khi đổi vai trò,
ngoại lệ giữ tài khoản HR với phê duyệt mô phỏng và hạn dùng. Đồng hồ mô phỏng
có ngày cố định, có thao tác tăng ngày và tái đánh giá tự động. Agent dùng
inspect_context để thu thập căn cứ; không tự cấp phê duyệt hoặc chọn nguồn đúng.
Nghiên cứu cùng 8 ca × 3 lần lặp × 3 chế độ, có hash nguồn và snapshot, đã chạy.
SoA, quy trình chuyên gia gán nhãn và mẫu khảo sát đã chuẩn bị; chưa có người
tham gia thật. Giới hạn runtime cuối đợt được ghi trong docs/VALIDATION.md.
