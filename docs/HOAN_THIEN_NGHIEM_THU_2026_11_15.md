# Hoàn thiện kỹ thuật và bàn giao nghiệm thu — 15/11/2026

Phạm vi 56 control (8 A.6, 14 A.7, 34 A.8), thực nghiệm sâu 18 A.8. Tài liệu này phân biệt chức năng đã kiểm chứng với quyết định cần người thật xác nhận; không phải biên bản nghiệm thu đã ký.

## Phần đã thực hiện

1. **Kiểm tra căn cứ trước khi nộp.** Trên phiếu chấm có nút kiểm tra. Ký tự lặp/nội dung thử bị chặn; căn cứ trùng control khác hoặc nhắc nguồn của control khác được cảnh báo. Người chấm cần sửa hoặc đọc lại và xác nhận cảnh báo có chủ đích. Sửa nội dung sẽ bỏ xác nhận cũ. Đây là heuristic, không xác minh đầy đủ tính đúng, tác giả hay chuyên môn.
2. **Rà lịch sử không sửa nhãn.** Admin/người đã được mở kết quả xem danh sách nghi vấn. Lượt `0b7dc9e9` có 17 căn cứ bị khoanh tự động, gồm cả bản gốc bị trùng. Trợ lý đã đối chiếu 9 lỗi nội dung cụ thể: Tú A.8.2/.5/.15/.17; Khoa A.8.2/.10/.17/.22/.32. [Bản audit có report/hash căn cứ](a8-results/review-quality-audit-2026-11-15.json) được lưu riêng; không đổi 36 nhãn khóa thành nhãn đúng/độc lập.
3. **Không dùng căn cứ lỗi để mở duyệt.** Lượt có căn cứ hình thức bị chặn hoặc cảnh báo chưa xác nhận không tự trở thành nguồn đối chiếu chính hay SoA được duyệt chỉ bằng cờ “tự chấm”. So sánh tất cả nhãn vẫn lưu riêng để minh bạch.
4. **Nhập gói nguồn ngoài đã chốt.** Admin tải JSON chuẩn bị từ nguồn ngoài; server kiểm tra protocol/hash, model/recipe, rubric, đủ 18 control, artifact và tính lại facts từ bytes bằng collector tin cậy. Chặn facts giả, file phụ không thuộc capture, nguồn trùng fixture đã biết và claim độc lập tự gán. Worker chạy trên snapshot, không thu lại nguồn.
5. **Chấm mù nguồn mới.** Lượt ứng viên giữ giao thức khóa nhãn, không kế thừa đáp án designer; được đánh dấu `PENDING_HUMAN_VERIFICATION`, `independent_validation=false`. Không trùng hash không chứng minh độc lập. Khi mở gói chấm mù, bảng đáp án luyện tập được tạm ẩn.

## Chuẩn bị bộ kiểm định thực tế

Chủ nguồn cung cấp thư mục riêng theo định dạng `<root>/<profile>/A.8.x/<artifact>` trong [ma trận nguồn raw](MA_TRAN_A8.md), không sao chép/đổi tên fixture đã dùng phát triển. Xác nhận nguồn có nội dung, tình huống đa dạng và người nào đã tiếp xúc. Không dùng bài test sửa whitespace hoặc dữ liệu sinh bởi trợ lý để tuyên bố kiểm định độc lập.

```powershell
.\.venv\Scripts\python.exe -m agent_core.a8_protocol prepare --profile mixed --transport files --raw-root data/a8-validation/nguon-moi --coordinator "Tran Van Toan" --objective "External candidate awaiting supervisor verification" --output work/plan-kiem-dinh-moi.json
```

Thay `mixed` bằng profile tương ứng với cấu trúc bộ nguồn. Tên profile không tự tạo đáp án. Cần nhiều tình huống với đủ mức đạt/một phần/không đạt/thiếu nguồn; một lượt mixed toàn một phần không đủ chứng minh chất lượng phân loại đa lớp.

Trong **Thực nghiệm 18 A.8 → Nhập gói nguồn ứng viên đã chốt**, admin chọn file JSON và engine. Khoa/Tú dùng cùng run ID do admin cung cấp, đọc nguồn và tự nộp. Không đưa bảng đáp án hoặc kết luận của AI cho người chấm nếu định dùng làm đối chiếu tự chấm. Khai đúng hỗ trợ/tiếp xúc và lưu lịch sử.

**Chưa có bộ nguồn ngoài được nhóm xác nhận trong lần triển khai này.** Công cụ nhập đã hoàn thiện và được test bằng dữ liệu test tạm cô lập; không tạo hoặc đưa bộ test đó vào nghiên cứu thật.

## Phiếu cần người phụ trách/thầy xác nhận

| Nội dung cần chốt | Trạng thái |
|---|---|
| Bối cảnh, tài sản, kỳ đánh giá và 56 control áp dụng/loại trừ | Chờ người phụ trách ghi căn cứ |
| Rubric toàn phạm vi và 18 tiêu chí đại diện: ngưỡng lab, nguồn, giới hạn | Chờ xác nhận đúng phiên bản/hash |
| Người chấm và năng lực phù hợp; có chấp nhận thành viên phát triển hay cần người ngoài | Chờ thống nhất với giảng viên |
| Nguồn kiểm định mới, lịch sử tiếp xúc và thời điểm chốt trước dự đoán | Chờ người cung cấp/người phụ trách xác nhận |
| Cách báo cáo lỗi, bất đồng, số ca duy nhất và lần lặp | Công cụ có; cần rà phương pháp thực nghiệm |
| Kế hoạch xử lý, người nhận, hạn và cách kiểm tra lại | Công cụ có; chưa ghi quyết định thực tế |
| Người có trách nhiệm duyệt SoA và phạm vi phê duyệt | Chờ người thật thực hiện |

Người rà: ______; vai trò: ______; thời điểm: ______; phiên bản/hash đã rà: ______; căn cứ/ngoại lệ: ______. Phiếu trống không phải bằng chứng phê duyệt và không được nạp như nguồn tuân thủ.

## Checklist UI còn phải thao tác

Các dòng dưới đây chưa được tích bằng test API. Computer Use/native pipe và browser host không kết nối trong phiên kiểm tra, nên chưa xác nhận thao tác toàn giao diện.

| Thao tác trên UI | Kỳ vọng | Kết quả UI |
|---|---|---|
| Đăng nhập admin, Khoa, Tú; đăng xuất | Đúng danh tính/quyền, không dùng nhầm phiên | Chờ ghi người thực hiện |
| Chọn lượt cũ | Chỉ đọc, không hiện form nộp không hợp lệ | Chờ kiểm tra lại |
| Chọn cùng lượt hợp lệ ở hai người chấm | Cùng snapshot, không hiện dự đoán trước đủ nhãn | Chờ kiểm tra |
| Đọc artifact và chọn kết luận tiếng Việt | Giữ mã API đúng, cảnh báo thực tế tách khỏi hướng dẫn | Chờ kiểm tra |
| Kiểm tra căn cứ có ký tự thử/dán nhầm | Chặn nội dung thử, cảnh báo trước nộp; thay nội dung bỏ xác nhận | Chờ kiểm tra |
| Nộp nhãn, tải lại, admin xem tiến độ | Không mất/nhân đôi nhãn; đúng run ID; khóa nhãn đã nộp | Đã có thao tác người dùng một phần, chưa xác nhận toàn checklist |
| Mở gói chấm mù | Không hiện bảng đáp án luyện tập ngay cạnh phiếu | Chờ kiểm tra bản mới |
| Nhập gói ứng viên sai hash/trùng fixture | Thông báo lỗi, không tạo lượt nghiên cứu | Chờ kiểm tra UI; API đã kiểm chứng |
| Nhập gói nguồn ngoài phù hợp | Tạo lượt chờ xác minh, không tự gán độc lập/đáp án | Chờ nguồn thật và kiểm tra UI |
| Xuất JSON/CSV/Markdown | Đúng lượt, người chấm, nguồn, số mẫu; không ghi giả accuracy | Chờ mở tệp kiểm tra trên UI |
| Duyệt khi thiếu điều kiện/không đủ quyền | Bị chặn, không thay đổi phê duyệt | Chờ kiểm tra UI; API có hồi quy |
| Thu nguồn mới/chạy lại/thay quyết định | Hiển thị phiên bản mới và thẩm định/phê duyệt cũ không còn hiện hành | Chờ kiểm tra |

## Kết quả và giới hạn

- 246 test Python, 5 test JavaScript, lint/build đạt; 3 cảnh báo deprecation thư viện.
- Test kiểm tra quyền, chấm mù, khóa nhãn, cảnh báo/chặn căn cứ, giữ nguồn chốt, chặn trùng/hash/facts giả, không dùng designer cho ứng viên và không duyệt khi thiếu điều kiện. Những nhãn trong test chỉ tồn tại trong thư mục test tạm.
- Kiểm tra API thật: có audit 17 nghi vấn; preview nhận diện nội dung thử; từ chối nhập fixture cũ làm gói ứng viên. Tệp nghiên cứu trước/sau giữ nguyên hash.
- SoA vẫn dự thảo; 37 control còn thiếu nguồn ngoài preset. Chấm có AI hỗ trợ, bản audit của trợ lý và số test không thay nhãn độc lập hoặc thẩm quyền phê duyệt. Không đóng sáu mục nghiệm thu còn mở bằng kết quả kỹ thuật này.
