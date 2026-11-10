# Thu hồ sơ và thẩm định toàn bộ 56 control

## Phần đã bổ sung

- Connector thư mục bằng chứng dùng cho đủ 56 control, ngoài các probe raw/lab hiện có.
- Mỗi control có manifest nguồn và mẫu yêu cầu từ tiêu chí hiện hành. Mẫu không phải bằng chứng, không tạo kết luận đạt.
- Thu PDF/DOCX, text/Markdown, JSON, CSV/TSV, cấu hình và log; kiểm tra loại bằng chứng theo control, giới hạn kích thước, đường dẫn/symlink, thời điểm quan sát.
- Lưu hash tệp gốc, bản trích xuất, thông tin nguồn và người thực hiện. Cùng nguồn/nội dung/metadata được dùng lại; thay đổi tạo phiên bản bằng chứng mới, không xóa bản cũ.
- Chế độ đánh giá hồ sơ `evidence_only=true` chỉ dùng nguồn người phụ trách nộp/thu vào đợt, không sinh hoặc dùng preset nhân sự/lab để thay kết luận hồ sơ. Không có hồ sơ thì trả Insufficient Evidence và không gọi model.
- Người đánh giá đọc nguồn, ghi kết luận/căn cứ và viện dẫn có kiểm tra; thẩm định gắn phiên bản dữ liệu. Thay đổi bằng chứng/đánh giá/snapshot làm thẩm định cũ không còn hiện hành.
- SoA đủ 56: cần người phụ trách xác nhận phiên bản tiêu chí/rubric toàn phạm vi trước, rồi quyết định tính áp dụng cho mọi control, thẩm định hiện hành cho control áp dụng, không có job đang chạy, rồi admin ghi phê duyệt có căn cứ. Loại trừ phải do người phụ trách quyết định có lý do; không tự loại trừ control thiếu dữ liệu.

Đây là tự động hóa thu nhận và quản lý hồ sơ, **không đồng nghĩa 56 probe kỹ thuật hoặc tự động xác minh hoàn toàn mọi tiêu chí ISO**. Nguồn văn bản/tệp không tự được coi xác thực chỉ vì parse/hash thành công.

## Cách sử dụng

1. Mở **Phạm vi 56 control**, rà tiêu chí và ghi xác nhận toàn phạm vi bằng tài khoản người phụ trách. Việc xác nhận lưu hash danh mục và rubric, không chỉ nhóm 18 A.8. Sau đó chọn **Chuẩn bị thư mục hồ sơ đủ 56**.
2. Giao diện trả các thư mục `data/evidence-packages/{assessment_id}/{control_id}`. Xem `_REQUIRED.md` của từng control để chuẩn bị đúng hồ sơ.
3. Đặt bản gốc cùng thư mục, khai báo trong `manifest.json`. Không khai báo file mẫu hoặc chính manifest làm bằng chứng.

Ví dụ cấu trúc manifest cho A.6.1 (chỉ là ví dụ, không phải hồ sơ đã tồn tại):

```json
{
  "control_id": "A.6.1",
  "sources": [
    {
      "file": "screening-register.csv",
      "evidence_type": "EVID_PPL_HR_RECORD",
      "observed_at": "2026-11-10T08:00:00+07:00",
      "origin": "HR export supplied by responsible officer",
      "note": "Nguồn cần người phụ trách xác nhận, không tự suy từ tên file."
    }
  ]
}
```

4. Bấm **Thu nhận gói hồ sơ đủ 56** hoặc chọn một control → **Thu hồ sơ control này**. Tệp sai/thiếu hiện trong issues; chỉ nguồn đọc hợp lệ mới được nhập.
5. Bấm **Đọc nội dung bằng chứng**; đối chiếu tài liệu gốc và nguồn xác nhận.
6. Chạy **Agent đánh giá hồ sơ đã thu (không dùng preset)**. Nguồn tổng hợp phải được đọc trong phạm vi context model; tài liệu dài/phức tạp cần chia hồ sơ và kiểm tra thủ công, không coi model đã hiểu toàn bộ mọi trang chỉ vì trích xuất thành công.
7. Người đánh giá chọn kết luận, ghi căn cứ và xác nhận. Kết luận đạt/một phần bắt buộc có ID bằng chứng thuộc đúng đợt/control. UI hiện viện dẫn tập bằng chứng của control, người chấm cần đọc kỹ và nêu căn cứ cụ thể trong lý do.
8. Người phụ trách ghi tính áp dụng và kế hoạch xử lý/duy trì. Làm lần lượt đủ 56 control.
9. SoA hiển thị danh sách phần còn thiếu. Khi đủ điều kiện, admin phê duyệt; xuất JSON/Markdown. Phê duyệt có danh tính/thời điểm/hash trạng thái và tự không còn hiệu lực khi nguồn hoặc quyết định đổi.

## Phân biệt hai quy trình con người

- **Thẩm định hồ sơ 56 control:** người đánh giá có thể xem kết quả Agent, phục vụ quản trị/SoA; không phải đánh giá mù hoặc số liệu chuyên gia độc lập.
- **Thực nghiệm 18 A.8:** giữ giao thức chấm mù đã có, ẩn đáp án và kết quả đến khi nộp đủ 18. Số liệu nghiên cứu chỉ dùng kết luận thật theo quy trình này; không lấy thẩm định hồ sơ hoặc test phần mềm thay cho nhãn nghiên cứu.

Không ai được hệ thống tự gán là chuyên gia. Vẫn cần người thật cung cấp hồ sơ, xác nhận tiêu chí, chấm và phê duyệt. Hệ thống không tạo thay chữ ký hoặc thực hiện xác nhận giả.

## Phê duyệt SoA có nghĩa gì?

`HUMAN_APPROVED_PROJECT_SCOPE` là người phụ trách chấp thuận bản SoA trong phạm vi 56 control của đồ án. Có thể vẫn còn kết luận không đạt/thiếu bằng chứng với kế hoạch xử lý ghi rõ. Đây không phải chứng nhận ISO hoặc xác nhận doanh nghiệp đã đáp ứng tất cả control.

## Kiểm chứng

- Test đường dẫn, file mẫu/gói rỗng, dữ liệu thay đổi, không gọi model khi không có nguồn, chặn viện dẫn giả và chặn phê duyệt khi chưa đủ điều kiện.
- Kiểm tra API thật tạo 56 bộ mẫu trống, quét 56, nhập 0 bằng chứng khi chưa cung cấp nguồn; không ghi nhãn hoặc phê duyệt con người giả.
- Kết quả A.8 95,37% trước đó giữ nguyên, không tự thay bằng số liệu mới. Có thêm diagnostic loại lỗi/ID viện dẫn/hash phản hồi cho lượt lỗi tương lai; chưa tuyên bố đã sửa hết các ca sai hoặc tăng accuracy.

## Kết quả kiểm chứng bản bổ sung

250 test Python đạt; build thành công; lint còn cảnh báo cũ, không có lỗi chặn. Đã kiểm tra PostgreSQL thật: lần thu đầu nhập 1 nguồn, thu lại dùng lại 1 nguồn; giao dịch QA rollback nên không giữ bằng chứng giả trong đợt. API tạo/quét đủ 56 bộ mẫu trống, không tự tạo bằng chứng hay phê duyệt. Kiểm thử UI bấm toàn bộ vẫn chưa được xác nhận do kết nối điều khiển Windows trước đó không hoạt động.
