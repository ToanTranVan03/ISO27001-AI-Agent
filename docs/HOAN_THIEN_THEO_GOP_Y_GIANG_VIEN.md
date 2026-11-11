> **Sau đợt dọn mã 11/11/2026:** các mô tả component demo/cảnh báo và số test trước đây là mốc lịch sử. Xem [cấu trúc và kiểm chứng sau dọn](DON_GON_PROJECT.md).

# Đối chiếu góp ý giảng viên và cách nghiệm thu

> **Cập nhật live v2 ngày 11/11/2026:** đã có 18 probe đại diện, gồm 13 phép thử chủ động mới; tiêu chí mới khác live v1 và chỉ bao phủ một phần control. Xem [ma trận live v2 và kiểm chứng](LIVE_A8_V2.md). Các số liệu/giới hạn 5 probe, 13 chưa hỗ trợ dưới đây mô tả các lượt live v1 đã lưu, không phải năng lực runtime mới.

Ngày cập nhật: 11/11/2026. Phạm vi đồ án vẫn là **56 control**; 18 A.8 là nhóm thực nghiệm sâu.

## Hiện trạng có thể chứng minh

| Hạng mục | Đã triển khai | Giới hạn phải giữ khi báo cáo |
|---|---|---|
| Phạm vi | Danh mục, tiêu chí, hồ sơ, thẩm định và SoA đủ 8 A.6 + 14 A.7 + 34 A.8 | Không phải toàn bộ Annex A/ISMS; không có nghĩa đủ bằng chứng cho 56 control |
| Bộ thử A.8 | 108 ca raw, 6 profile, 18 control, nguồn/hash và đáp án thiết kế tách khỏi Agent | Replay cấu hình/log của nhóm; hai tiêu chí đại diện/control |
| Nguồn live mới | Probe read-only trên tài nguyên container cho A.8.3, .10, .13, .15, .19; 4 profile cố ý | Chỉ 5 control có phép thử live. 13 control khác trả thiếu bằng chứng, không lấy fixture thay thế |
| Kết luận | JSON mode tương thích SDK hiện tại, kiểm tra schema, viện dẫn evidence, chặn kết luận xác định khi tiêu chí bắt buộc còn unknown | Chặn lỗi không có nghĩa đã nâng độ đúng; giữ lỗi engine và đo lại riêng |
| Người đánh giá | Người khác tài khoản chấm mù cùng gói bằng chứng, khóa nhãn, gắn report hash | Chưa có người thật hoàn tất; không dùng nhãn test làm kết quả chuyên gia |
| SoA | Dự thảo đủ 56; báo cáo con 18 A.8; có điều kiện xác nhận rubric, tính áp dụng, thẩm định và phê duyệt | Chưa có phê duyệt thật; trạng thái dự thảo được giữ |
| Theo dõi thiếu sót | Màn hình 56 nêu bước tiếp theo, loại nguồn cần rà và số thẩm định hiện hành; A.8 nêu coverage/lỗi/thiếu nguồn | Số có hồ sơ không phải số đạt; hồ sơ nộp không tự trở thành nguồn đã xác thực |

## Live khác replay như thế nào?

Trong **Thực nghiệm 18 A.8**, chọn nguồn:

- **Trạng thái live:** truy vấn ngay quyền tệp bằng tài khoản `labworker`, sự tồn tại của đối tượng, nội dung backup/restore, log ứng dụng và inventory `dpkg-query`. Nguồn thu có thời điểm hiện tại và hash. Không truy vấn máy thật bên ngoài lab.
- **Raw v2 trong container / Replay file:** đọc lại bộ ca đã chốt tại thời điểm capture. Phục vụ tái lập thực nghiệm cũ, không xác nhận hiện trạng hệ thống hôm nay.

Probe live và replay có rubric/hash/version riêng. Không lấy đáp án replay tính độ đúng live. Live hiện chưa có nhãn đánh giá độc lập hoặc bộ nhãn thiết kế được chốt riêng nên bảng tỷ lệ hiển thị **chưa đo**, không hiển thị 0% hoặc 100% thay thế.

| Live control | Thực sự quan sát | Phần chưa được khẳng định |
|---|---|---|
| A.8.3 | Quyền ghi tài nguyên nghiệp vụ bằng `labworker`, stat, hồ sơ review lab | Không bao phủ IAM doanh nghiệp; review do lab dựng, chưa là phê duyệt quản trị thật |
| A.8.10 | Retention cấu hình và kiểm tra đối tượng sau thao tác xóa | Không chứng minh secure erase, vòng đời mọi dữ liệu hay hệ thống retention tự vận hành |
| A.8.13 | Hash backup, đọc dữ liệu phục hồi và đối chiếu | Không chứng minh RPO/RTO, offsite, lịch backup dài hạn |
| A.8.15 | Sự kiện ứng dụng thực ghi, hash seal và quyền log | Không phải auditd/SIEM, log tập trung hoặc cơ chế chống quản trị viên sửa cả log và seal |
| A.8.19 | Quyền ghi thư mục cài và inventory gói hiện tại so với danh mục lab | Không chứng minh toàn bộ quy trình phê duyệt phần mềm; chưa chặn mọi cách cài trên OS |

Các phép thử là **đại diện cho một phần control**, không đổi định nghĩa ISO thành kiểm tra quyền tệp đơn lẻ. Rubric live chưa được người phụ trách duyệt thì phê duyệt replay không thay thế được.

Kiểm chứng kỹ thuật: [20 tình huống và thử sửa/khôi phục tệp](a8-results/live-v1-probe-verification.json). Phép thử đã đổi tệp restore trong container, thu lại được kết quả không khớp/hash đổi, sau đó khôi phục và kiểm tra lại thành công. Đây là kiểm chứng collector, **không phải accuracy của LLM hoặc đánh giá con người**.

## Kiểm tra hồi quy kết luận

Sau khi bổ sung kiểm tra viện dẫn/unknown, [lượt hồi quy v3](a8-results/raw-v3-regression.json) dùng Qwen2.5:7b trên 36 ca (18 mixed + 18 incomplete, một lần lặp): **36/36 khớp đáp án nhóm, không lỗi engine**. Không chạy đồng thời hai tiến trình benchmark LLM trong lượt này. Đây là bộ ca đã biết/dùng chỉnh hệ thống; chưa có tập kiểm định độc lập nên chưa kết luận chất lượng đã được xác nhận ngoài bộ ca này. Số đo raw v2 206/216 vẫn được giữ nguyên.

Một lần thử định dạng JSON schema trực tiếp trước đó bị SDK Ollama đang cài từ chối tại kiểm tra tham số, trước khi gọi model: [log 36 lỗi ValidationError](a8-results/raw-v3-sdk-validation-failure.json). Đã sửa để dùng JSON mode tương thích SDK và kiểm tra schema bằng Pydantic. Lượt lỗi kỹ thuật này giữ riêng, không gộp thành số đo suy luận của model.

Lượt [live qua API trước chặn đầy đủ](a8-results/live-v1-api-llm.json) cho thấy A.8.3 có facts `true/false` nhưng model trả `Non-Compliant`, mâu thuẫn rubric `Partially Compliant`. Không sửa báo cáo gốc. Bản `evidence-guard-v4` kiểm tra toàn bộ tính nhất quán của kết luận với rubric đại diện, ngoài viện dẫn và unknown; mâu thuẫn được ghi **lỗi**, giữ proposed status và hash phản hồi, không đổi ngầm sang đáp án luật.

Kiểm tra [live v4, profile mixed](a8-results/live-v4-ollama.json): 5 control có probe, 4 phản hồi LLM hợp lệ và 1 lỗi bị chặn ở A.8.3; 13 control chưa có probe trả thiếu bằng chứng qua kiểm tra nguồn, không gọi LLM. Không có nhãn live độc lập nên **không công bố accuracy live**. Đây là phát hiện lỗi còn tồn tại của model, không ghi rằng đã sửa được khả năng suy luận. Báo cáo mới lưu version, hash mã assessor/collector và phiên bản SDK; tổng hợp tách theo các phiên bản này.

Kiểm thử cuối: **262 test Python, 15 test JavaScript và build frontend đạt**. Lint còn 6 cảnh báo cũ ở các màn hình khác; chưa kiểm thử bấm toàn bộ UI có đăng nhập. Các kết quả này chứng minh hành vi phần mềm đã kiểm tra, không thay thế nghiệm thu chuyên môn.

## Cách nhóm hoàn thiện hồ sơ chính

1. Vào **Phạm vi 56 control**, người phụ trách rà tiêu chí và quyết định tính áp dụng từng control; ghi căn cứ loại trừ, không loại trừ vì chưa viết collector.
2. Dùng checklist nguồn của từng control để thu hồ sơ lab/doanh nghiệp. Kiểm tra nội dung, ngày, người sở hữu và provenance; không chỉ đếm số tệp. Danh sách loại nguồn chưa thấy là gợi ý rà, chưa là kết luận thiếu/đủ cuối cùng.
3. Chạy **Agent đánh giá hồ sơ đã thu**. Xem viện dẫn, thiếu sót và lịch sử. Dữ liệu preset không được thay nguồn nộp trong chế độ này.
4. Người đánh giá thẩm định kết luận thực tế và kế hoạch khắc phục. Hồ sơ hoặc tiêu chí đổi phải thẩm định lại; số liệu ca thử không tự ghi thành kết luận chính thức của đợt.
5. Với nghiên cứu 18 A.8, dùng tài khoản khác người khởi chạy để chấm mù, nộp căn cứ thật trước khi xem Agent/đáp án. Chốt tập đo, rubric và người đánh giá trước khi chạy; không dùng ca vừa sửa prompt làm tập kiểm định độc lập.
6. Xuất bảng từng control, giữ lỗi trong mẫu số có nhãn và tách nguồn nhãn. Với live, nêu rõ mẫu có probe và mẫu chưa có probe; không để 13 kết luận thiếu bằng chứng làm che khuất chất lượng của 5 probe đã triển khai.
7. Người phụ trách rà SoA, tính áp dụng và kế hoạch; duyệt khi đủ điều kiện. Kiểm tra lại SoA bị trả về dự thảo khi nguồn/kết luận/tiêu chí thay đổi.

## Những việc không thể thay bằng code hoặc dữ liệu giả

- Người phụ trách thực sự xác nhận rubric, phạm vi, nguồn bằng chứng và quyết định SoA.
- Nhóm cung cấp hồ sơ có nội dung thật cho phạm vi 56 hoặc ghi rõ control nào chưa đủ nguồn.
- Người đánh giá độc lập thực sự chấm; nếu có bất đồng cần ghi nhận, giải thích và xử lý theo quy trình đã chốt.
- Tập kiểm định tách khỏi ca dùng điều chỉnh hệ thống; mẫu đủ đa dạng trước khi suy rộng kết quả.

**Kết luận để báo cáo:** đã hoàn thiện thêm cơ chế thu trạng thái live và theo dõi khoảng thiếu; hệ thống đang ở mức thử nghiệm có kiểm chứng kỹ thuật. Chưa đủ căn cứ tuyên bố nghiệm thu toàn bộ 56 control, độ đúng với chuyên gia hoặc được chứng nhận ISO.
