# Thực nghiệm mô phỏng

## Chạy lại

```powershell
python -m compliance_ai.cli generate --companies 25 --seed 2026 --split test
python -m compliance_ai.cli benchmark --mode mock --limit 25
python -m compliance_ai.cli benchmark --mode llm --model qwen2.5:1.5b --limit 25 --max-cases 8
```

Chế độ LLM gửi bằng chứng có cấu trúc của các ca tổng hợp đến Ollama tại loopback. Dữ liệu của mỗi phương pháp đến từ cùng snapshot và chính sách. Nhãn được đọc qua tài khoản evaluator tách riêng sau khi đã tính dự đoán. Mô hình chỉ trả trạng thái có kiểu. Thiếu hoặc sai kết quả được ghi trong `failures.jsonl` và tính là thiếu bằng chứng. Tệp manifest ghi model, số ca, lỗi, phiên bản prompt và thời gian chạy.

M1 dùng bộ quy tắc có cấu trúc. M2 và M3 dùng cùng dự đoán phát hiện của provider trong phép đo này. M4 báo thiếu bằng chứng khi quy tắc và provider mâu thuẫn. Chưa đo hành động theo phương pháp, chi phí, chất lượng trích dẫn, đánh giá hành vi con người hoặc hiệu quả trên hạ tầng thật. Các lượt `MOCK_TEST_ONLY` kiểm tra công cụ chạy, xuất và tính chỉ số. Kết quả LLM giả lập không đại diện cho dữ liệu doanh nghiệp thật.

Báo cáo giữ ma trận nhiều trạng thái và ca có lỗi. Ca ngoài phạm vi và nhãn thiếu bằng chứng được loại khỏi ma trận nhị phân. Phát hiện vi phạm bị bỏ phiếu vì thiếu bằng chứng vẫn là âm tính giả trong phép đo nhị phân. Mẫu số bằng 0 cho giá trị trống. Tỷ lệ bao phủ tính trên ca áp dụng.

## Câu hỏi nghiên cứu và bằng chứng cần thu

Đối chiếu với mục 6 của đề cương và phần góp ý người dùng cung cấp. Bảng sau là thiết kế thực nghiệm; không phải kết luận rằng hệ thống đã trả lời được mọi câu hỏi.

| Mã | Câu hỏi | Phép đo và đối chứng | Bằng chứng hiện có / còn thiếu |
| --- | --- | --- | --- |
| RQ1 | Agent phát hiện điểm chưa tuân thủ chính xác hơn phương pháp truyền thống không? | Precision, Recall, F1, FPR, ma trận trạng thái và coverage; cùng snapshot, policy, split, bộ ca và giới hạn tài nguyên cho M1–M4. Báo lỗi và khoảng tin cậy theo doanh nghiệp. | Có benchmark phát hiện trên 25 doanh nghiệp tổng hợp. Chưa có đủ bốn phương pháp như thiết kế; chưa kết luận vượt trội. |
| RQ2 | Phỏng vấn thích ứng đánh giá nhận thức và cách ứng xử ATTT đến mức nào? | Bộ câu trả lời chưa dùng để chỉnh prompt, rubric ba tiêu chí và nhãn chuyên gia độc lập; so sánh chấm theo cụm từ và LLM. Đo đồng thuận từng tiêu chí, đúng/sai, tỷ lệ chuyển người thẩm định và số câu hỏi bổ sung. | Có luồng hỏi–hỏi bổ sung–giao học–kiểm tra lại; có bộ chấm Ollama tùy chọn. Chưa có bộ nhãn chuyên gia hoặc dữ liệu người tự nguyện. Câu trả lời tình huống chưa chứng minh hành vi thực tế. |
| RQ3 | Hành động có an toàn và xác minh được kết quả không? | Đo chọn đúng công cụ/đích, tỷ lệ thành công, tỷ lệ xác minh bằng bằng chứng mới, chặn hành động không hợp lệ, pending, thất bại, thời gian và khôi phục. Mẫu số phải ghi rõ từng trạng thái. | Có kiểm thử PostgreSQL cho NV015, đào tạo, bản vá, cấu hình, khôi phục và chặn revision cũ. Chưa có batch hành động theo từng phương pháp hoặc bằng chứng máy ảo thật. |
| RQ4 | Hệ thống thích ứng với quy mô và chính sách khác nhau không? | Phân tầng theo quy mô, chính sách, tỷ lệ dữ liệu thiếu/lỗi; giữ seed và nhãn; báo coverage, chất lượng, độ trễ p50/p95 và lỗi mỗi tầng. Kiểm tra cách ly tenant riêng. | Có generator 25 doanh nghiệp, ba chính sách mẫu và kiểm thử cách ly. Chưa có tổng hợp hiệu quả/thời gian theo từng tầng quy mô và chính sách. |
| RQ5 | RAG, Rules và Verification đóng góp gì vào giảm kết luận/hành động sai? | Ablation từng thành phần trên cùng dữ liệu; đo kết luận sai, trích dẫn có nguồn/đúng nội dung, hành động sai, xác minh độc lập và abstention. Giữ Policy Gate trong mọi biến thể. | Chưa có ablation đầy đủ. M2/M3 đang dùng chung dự đoán phát hiện; phép giao giữa rules và model của M4 chưa chứng minh đóng góp RAG/Verification. |

## Thiết kế đối chứng công bằng

| Phương pháp theo đề cương | Năng lực cần triển khai trong phép so sánh đầy đủ | Phạm vi hiện đo |
| --- | --- | --- |
| M1 — Rule-based | Bộ quy tắc đủ mạnh, cùng dữ liệu có cấu trúc; chấm tự do bằng rubric xác định; công cụ cố định và đọc lại kết quả khi phù hợp. | Phát hiện trên bằng chứng có cấu trúc. |
| M2 — LLM + RAG | Đánh giá tĩnh với tài liệu được phép dùng, trích dẫn kiểm tra được, không thực thi. | Dự đoán trạng thái từ provider; chưa đánh giá RAG và trích dẫn đầu cuối. Hành động, rollback và tỷ lệ xác minh: **N/A**, không tính là thất bại. |
| M3 — Agent + RAG + Tools | Lựa chọn công cụ có kiểu, không dùng bộ Rules kết luận hoặc Verification của M4; vẫn giữ kiểm soát quyền và Policy Gate. | Dùng chung dự đoán provider với M2; chưa là đối chứng agent độc lập. |
| M4 — Hệ thống đề xuất | RAG + Rules + Tools + Verification, phỏng vấn và bằng chứng mới sau hành động. | Đối chiếu rules với provider trong benchmark; luồng hành động riêng có kiểm thử tích hợp, chưa đo theo batch. |

Trước mỗi phép đo hành động, khôi phục cùng trạng thái mô phỏng ban đầu cho từng phương pháp. Không để M4 đọc nhãn chuẩn, lịch sử kết quả của phương pháp khác hoặc dữ liệu test để chọn prompt. Mỗi hành động phải lưu đề xuất, quyết định của gate, lý do chặn, đối tượng, thời gian, bằng chứng trước/sau và trạng thái cuối. Thành công công cụ, xác minh đạt và đang chờ là ba đại lượng riêng.

Lưu manifest gồm commit hoặc hash mã nguồn khi chưa commit, phiên bản dependency, seed, split, hash dataset/policy/rubric/prompt, model và phiên bản/digest, cấu hình lấy mẫu, giới hạn thời gian, lỗi, token và chi phí thực đo. Thiếu số liệu dùng N/A, không tự điền 0. Các kết quả lịch sử chưa ghi đủ manifest phải nêu rõ thiếu trường nào. Khóa cấu hình trước khi chạy test; chọn prompt trên tập phát triển riêng. Báo chênh lệch từng cặp trên cùng doanh nghiệp và khoảng tin cậy; không coi các ca cùng doanh nghiệp là mẫu độc lập hoàn toàn.

## Nhóm người tự nguyện — tùy điều kiện

Có thể bổ sung 10–20 người đồng ý tham gia, dùng mã ẩn danh, tình huống giả lập không có liên kết thật và quyền rút lui. Chốt trước mục đích, nội dung thu thập, thời gian lưu/xóa và yêu cầu của cơ sở đào tạo; không thu mật khẩu hoặc hồ sơ nhân sự. Tối thiểu hai người chấm độc lập, không thấy kết quả model, sau đó thống nhất bất đồng theo rubric. Tách bộ câu hỏi trước/sau có độ khó tương đương và giữ phần chưa dùng để chỉnh prompt.

Thu kết quả câu hỏi, số lượt hỏi bổ sung, thời gian, điểm theo người chấm và phản hồi sử dụng. Đo thay đổi điểm tình huống trước/sau chỉ là kết quả thăm dò trên mẫu nhỏ, chưa chứng minh thay đổi hành vi hoặc tác động nhân quả. Chưa tuyển người, chưa thu dữ liệu và chưa có kết quả nhóm này. Không cần nhóm này để kiểm thử kỹ thuật với nhân viên giả lập.

## Phân biệt kết quả và minh họa

Điểm 9,1/10 trong phần góp ý là nhận xét về kế hoạch. Ví dụ 72/100 từ 65/80/85 với trọng số 60/20/20 là minh họa công thức. Cả hai không phải số liệu đánh giá hệ thống. Điểm sản phẩm phải truy được về lần chạy, bằng chứng, phạm vi áp dụng và phiên bản chính sách; xem [ma trận tiêu chí](CONTROL_TRACEABILITY.md) và [rubric](RUBRIC.md).
