# HiveFive: câu hỏi nghiên cứu và phương pháp đánh giá

## Mục tiêu và giả thuyết

Xây dựng trợ lý diễn tập dựa trên sự kiện, truy vết bằng chứng về con người,
phần mềm và thiết bị. Câu hỏi RQ1: hệ thống phân biệt phát hiện theo quy tắc,
thiếu bằng chứng và hồ sơ đầy đủ đúng trên các ca tổng hợp đến đâu?
RQ2: bộ điều phối LLM có chọn công cụ hợp lệ, đi kiểm tra sâu đúng điều kiện
và hoàn tất vòng xử lý trên cùng snapshot không? RQ3: người xem có giải thích
được sự việc và cách khắc phục khi dùng cảnh 3D gắn bằng chứng không?

RQ1/RQ2 có thực nghiệm kỹ thuật ban đầu. RQ3 cần khảo sát người dùng; chưa có
số liệu và không được tự kết luận giao diện làm tăng hiệu quả học tập.

## Phân định đóng góp

- Luật xác định trạng thái từ bằng chứng. Bất kỳ model nào cũng không được đổi
  kết luận bằng một đoạn văn. Null có nghĩa chưa biết, không phải false hoặc true.
- Workflow cố định cũng thu thập dữ liệu, rẽ nhánh theo điều kiện và quản lý công
  việc được. Tự động chạy không phải bằng chứng riêng cho năng lực LLM.
- LLM chọn thứ tự trong các công cụ được phép và nêu mục đích dựa trên quan sát.
  Nhật ký lưu các lựa chọn khả dụng, lựa chọn được thực thi và kết quả công cụ.
  Đây là agent chuyên biệt bị giới hạn, không tự thiết kế kiểm soát mới hoặc
  tự truy cập hệ thống doanh nghiệp thật. Khi chỉ có một công cụ khả dụng,
  quyết định đó không chứng minh năng lực lập kế hoạch.
- `inspect_evidence` truy vết trường thiếu, mã bằng chứng và bộ phận cần cung
  cấp. Không tự điền dữ liệu để hoàn thành mục tiêu. Trạng thái công việc chỉ
  hết phát hiện khi evaluator kiểm tra snapshot mới; AI không sửa snapshot.

## Căn cứ quy tắc và phạm vi

ISO/IEC 27001:2022 là yêu cầu về ISMS; Annex A có 93 kiểm soát tham chiếu.
ISO/IEC 27002:2022 cung cấp hướng dẫn kiểm soát. Đồ án không thay thế đánh giá
rủi ro, Statement of Applicability (SoA), xem xét ngoại lệ hay đánh giá viên.
Tên/ID A.6.1–A.6.8 là ánh xạ chủ đề; điều kiện boolean là chính sách mô phỏng
do dự án lựa chọn, không phải toàn văn hoặc ngưỡng chứng nhận của ISO.

| Chủ đề kiểm soát | Nguồn bằng chứng mô phỏng | Chính sách dự án / giới hạn |
|---|---|---|
| A.6.1 Thẩm tra | `screened` trong HR | Có hồ sơ thẩm tra; chưa xem tính hợp pháp, mức độ theo vai trò |
| A.6.2 Điều khoản lao động | `terms_signed` | Có cam kết; chưa kiểm chứng hiệu lực hoặc nội dung văn bản |
| A.6.3 Nhận thức, đào tạo | Kết quả HR/LMS, ngày hết hạn | Phân biệt hết hạn, chưa biết, hai nguồn mâu thuẫn; chưa đo thay đổi hành vi lâu dài |
| A.6.4 Quy trình kỷ luật | Chính sách, `disciplinary_informed` | Có quy trình và bằng chứng phổ biến; chưa kiểm tra công bằng/thực thi |
| A.6.5 Trách nhiệm sau thay đổi việc | HR, tài khoản, laptop, rà soát vai trò, ngoại lệ | Quyền chưa rà soát bị phát hiện; ngoại lệ phải đúng tài khoản, được duyệt, có lý do và còn hạn; chỉ là chính sách mô phỏng |
| A.6.6 Thỏa thuận bảo mật | `nda_signed` | Có cam kết NDA; chưa kiểm tra phạm vi/rà soát định kỳ |
| A.6.7 Làm từ xa | HR, laptop, VPN | Chính sách được phổ biến cho mọi hồ sơ; người đang làm từ xa có mã hóa/MFA; người nghỉ việc không bị báo thiếu VPN vì đã đóng |
| A.6.8 Báo cáo sự kiện | Kênh báo cáo, đào tạo, sự kiện giả lập | Đã hướng dẫn và ghi nhận báo cáo; chưa đo thời hạn hoặc tích hợp SIEM |

Không có bản tiêu chuẩn cấp phép đi kèm để thẩm định toàn văn. Cần chuyên gia
đối chiếu chính sách với bản tiêu chuẩn hợp pháp và SoA trước khi áp dụng thật.
48 A.7/A.8 chỉ có danh mục, chưa đánh giá; 56 là phạm vi catalog của đồ án.

## Thiết kế thực nghiệm có thể tái lập

`agent_core/research_benchmark.py` định nghĩa 37 ca với nhãn riêng, không dùng
`apply_scenario` hoặc nhãn benchmark cũ. Có 24 ca đúng/sai/unknown trên tám
kiểm soát, 4 ca tài sản/kết hợp và 9 ca thời hạn, mâu thuẫn nguồn, vai trò,
ngoại lệ được duyệt/chưa duyệt/hết hạn. Dữ liệu nền vẫn chung
schema với sản phẩm; vì vậy không gọi đây là tập kiểm định bên ngoài hay
holdout mù. Việc đo giúp xác minh đặc tả và chống hồi quy, chưa chứng minh
khả năng khái quát. Nhãn kỳ vọng không xuất hiện trong mục tiêu/quan sát LLM.

Ba điều kiện là rules (evaluator), workflow (thứ tự cố định, rẽ nhánh theo
điều kiện), ai (Ollama qwen2.5:7b chọn công cụ). Nghiên cứu mới chọn cùng 8 ca
đại diện cho cả ba, mỗi ca lặp 3 lần: tổng 72 lượt (24 lượt/chế độ).
Ca gồm nghỉ việc còn tài sản, đào tạo thiếu bằng chứng/hết hạn/mâu thuẫn,
vai trò chưa/đã rà soát và ngoại lệ còn/hết hạn. Mỗi lượt dùng SQLite tạm riêng,
cùng snapshot hash giữa chế độ/lần lặp, không làm thay đổi nguồn sống.
Thứ tự chế độ xoay vòng giữa lần lặp để giảm thiên lệch thứ tự cố định;
chưa random hóa hoàn toàn hoặc kiểm soát nhiệt độ/cache/phần cứng.

Lệnh: `py -3.11 -m agent_core.research_benchmark --paired --repeats 3`.
Bản đo cũ 28 ca và 3 ca AI lưu riêng `research-baseline-results.json`.
`paired_analysis` kiểm tra số lượt cân bằng và snapshot trùng, kèm thống kê
riêng từng ca. Độ lệch chuẩn trong summary là giữa toàn bộ lượt (gồm ca khác
nhau); dùng thống kê theo ca khi xem biến thiên do lặp.

Đơn vị nhãn là (control_id, person_id, finding/missing). Exact-match đòi toàn
bộ nhãn khớp, kể cả không có cảnh báo ngoài dự kiến. Precision=TP/(TP+FP),
recall=TP/(TP+FN) cho lần hoàn tất; mẫu số rỗng trả null. Lỗi tính thất bại
trong tỷ lệ exact-match và được báo riêng. Thời gian là thời gian xử lý toàn
lần, không phải độ trễ từ lúc phát sinh sự kiện hay SLA. So thời gian giữa
các chế độ phải lọc cùng case_id; không so trung bình hai tập khác nhau.

Kết quả thực chạy nằm ở `research-results.json`:

| Chế độ | Hoàn tất/khớp toàn bộ nhãn | TB ms | Median ms | Độ lệch chuẩn ms | Gọi model |
|---|---|---|---|---|---|
| Luật | 24/24 | 3.25 | 2.99 | 0.83 | 0 |
| Workflow | 24/24 | 29.40 | 28.23 | 3.76 | 0 |
| AI | 24/24 | 8764.67 | 8474.80 | 785.20 | 177 |

Workflow và AI đều chọn công cụ hợp lệ/đủ các bước yêu cầu 24/24 lượt, mỗi
chế độ 177 lần gọi công cụ. Chỉ số đủ bước là kiểm tra thực thi theo yêu cầu
case và phụ thuộc được engine cưỡng chế, không phải chuyên gia chấm chất
lượng lập luận hay minh chứng năng lực suy luận tự do. Những ca không có
required_tools riêng vẫn chịu kiểm tra phụ thuộc công cụ của agent.

Vì cùng evaluator và tập thử nhỏ, chưa chứng minh LLM tốt hơn luật/workflow.
Kết quả hiện tại cho thấy workflow hoàn thành các mục tiêu với thời gian thấp
hơn. Giá trị riêng của LLM cần thêm ca thực tế, đánh giá kế hoạch bởi chuyên
gia và đo token/chi phí; không biến kết quả này thành tuyên bố AI vượt trội.

## Kịch bản trình diễn và nghiên cứu tiếp

Chọn HF-042, ghi nhận chưa xác minh kết quả đào tạo. Quan sát thẻ trên cảnh
3D, hai trường từ true sang null, A.6.3 thiếu bằng chứng. Mở nhật ký để xem
`inspect_evidence` chỉ ra trường thiếu. Ghi nhận khắc phục trong hồ sơ, chờ
worker tự tái kiểm tra snapshot mới và xuất JSON. So revision báo cáo với
revision dữ liệu; báo cáo cũ không được diễn giải là xác minh dữ liệu mới.

Cần chuyên gia gán nhãn độc lập và tập kiểm định ẩn, random hóa thứ tự; đo
tỷ lệ kế hoạch hữu ích, token/chi phí,
độ trễ từ sự kiện, tải hệ thống, rồi khảo sát người dùng về mức hiểu mô phỏng.
Chưa có các số liệu đó; không tự điền vào luận văn.

SoA mô phỏng ở `SOA-MO-PHONG.md`; kịch bản bảo vệ, quy trình gán nhãn chuyên
gia và khảo sát crossover ở `BAO-VE-VA-KHAO-SAT.md`. Đây là quy trình chuẩn
bị, chưa phải kết quả thu thập từ người thật.
