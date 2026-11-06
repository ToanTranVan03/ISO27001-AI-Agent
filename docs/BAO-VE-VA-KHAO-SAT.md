# Bảo vệ kết quả và đánh giá người dùng

## Luận điểm bảo vệ

HiveFive kết hợp evaluator minh bạch với bộ điều phối công cụ LLM, nguồn
bằng chứng phiên bản hóa và mô hình doanh nghiệp tương tác. Tự động hóa
sự kiện, rẽ nhánh và quản lý công việc cũng thực hiện được bằng workflow;
không nhận các khả năng đó là đóng góp riêng của LLM. Thực nghiệm cần trả
lời liệu LLM có chọn đủ bước, kết thúc hợp lệ và chi phí thời gian ra sao.
Nếu workflow làm cùng việc nhanh hơn, phải báo cáo điều đó, không sửa mục
tiêu hay số liệu để buộc AI thắng. Chưa chứng minh khả năng thích nghi ngoài
bộ công cụ được định nghĩa sẵn hoặc lợi ích trên nghiệp vụ chưa biết trước.

## Trình diễn 7 phút

1. Giới thiệu phạm vi A.6, dữ liệu giả lập và phân định luật/LLM.
2. Chọn HF-042: ghi nhận HR/LMS mâu thuẫn. Hai nguồn được giữ nguyên;
   kết luận là thiếu bằng chứng, không tự gán nhãn người vi phạm.
3. Mở công cụ inspect_evidence và inspect_context để thấy căn cứ và yêu
   cầu đối soát. Sau khi người vận hành ghi nhận hoàn tất đào tạo, Agent
   tự tái kiểm tra; đối chiếu revision/hash và công việc hết phát hiện.
4. Chuyển vai trò, nhìn phát hiện A.6.5 và ghi nhận rà soát quyền mới.
5. Với HF-025 đã nghỉ việc: đề nghị giữ HR, ghi nhận người quản lý phê duyệt.
   Quan sát còn một tài khoản giữ có điều kiện; chuyển ngày mô phỏng hai
   lần để hết hạn và tự phát hiện lại. Thu hồi để đóng vòng xử lý.
6. Xuất JSON bằng chứng và xem bảng nghiên cứu ghép cặp. Nêu rõ việc còn
   thiếu: dữ liệu thật, đánh giá độc lập, khảo sát người dùng.

## Khảo sát để trả lời RQ3 (chưa thực hiện với người tham gia)

Thiết kế crossover: mỗi người làm nhiệm vụ ở hai điều kiện: bảng bằng chứng
và bảng kèm 3D. Giữ cùng dữ liệu/kịch bản, đổi thứ tự AB/BA giữa người tham
gia; dùng hai ca tương đương để hạn chế học thuộc. Cỡ mẫu dự kiến 12–20
người chỉ là kế hoạch pilot, chưa được tính power hoặc xác nhận đủ thống kê.

Nhiệm vụ: tìm người có vấn đề; xác định mã kiểm soát và bằng chứng; phân
biệt vi phạm với mâu thuẫn nguồn; chọn cách xử lý; xác định khắc phục đã
được xác minh ở revision nào. Ghi thời gian hoàn thành, số lỗi và câu trả
lời đúng theo đáp án do chuyên gia duyệt trước. Không lấy cảm giác đẹp làm
thước đo duy nhất. Báo cáo chênh lệch theo từng người, median, khoảng phân
tán; không suy luận quan hệ nhân quả từ mẫu nhỏ hoặc thứ tự không cân bằng.

Câu hỏi sau mỗi điều kiện (thang 1–5): dễ tìm người liên quan; hiểu căn cứ
cảnh báo; hiểu bước xử lý tiếp theo; phân biệt trạng thái dữ liệu và AI;
mức độ rối của giao diện. Thêm câu mở: chi tiết nào giúp/cản trở hiểu sự việc?

## Gán nhãn chuyên gia (chưa thực hiện)

Giao snapshot không chứa expected labels hoặc đáp án model cho hai người
có chuyên môn. Mỗi người độc lập ghi: kiểm soát, person_id, finding/missing/
không phát hiện, bằng chứng, lý do và yêu cầu bước kiểm tra. Lưu nhãn ban đầu,
đo tỷ lệ thống nhất/Cohen's kappa khi phù hợp, rồi phân xử bất đồng. Tách tập
phát triển và tập kiểm định ẩn trước khi điều chỉnh luật. Hiện tập ca được
dự án tự xây dựng, chưa được gọi là nhãn chuyên gia hay đánh giá mù.

Mẫu thu thập ở `MAU-KHAO-SAT.tsv`; để trống, không coi là kết quả thực nghiệm.
