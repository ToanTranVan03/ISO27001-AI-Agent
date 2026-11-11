> **Phạm vi đồ án là 56 control.** Tài liệu này chỉ mô tả nhóm 18 A.8 ưu tiên thực nghiệm, không thay thế phần con người/phần cứng/phần mềm còn lại. SoA 18 A.8 là báo cáo con; màn hình Phạm vi 56 xuất SoA tổng thể. Xem [ma trận 56 control](MA_TRAN_56_CONTROL.md).

# Quy trình thực hiện và nghiệm thu A.8 — phiên bản raw v2

> **Runtime live mới:** [Live A.8 v2](LIVE_A8_V2.md) có 18 probe đại diện, dùng image Python/OpenSSL và schema riêng. Phần Ubuntu/raw bên dưới mô tả bộ replay lịch sử, không phải runtime live mới. Không gộp nhãn/kết quả qua các phiên bản rubric.

> Cập nhật v5: lượt mới chốt snapshot trước suy luận, yêu cầu model sửa tối đa một lần với lỗi đầu được giữ. Báo cáo tách lần đầu/sau sửa và từng người chấm; không tự ghép nhãn hoặc tạo đồng thuận. CLI hỗ trợ bộ nguồn tách riêng, nhưng chưa có tập kiểm định/nhãn người thật được xác nhận. Xem [bàn giao tuần 5](NGHIEM_THU_TUAN_05.md). Các mô tả raw v2 dưới đây là quy trình và kết quả lịch sử của nguồn replay.

## 1. Phạm vi, rubric và phê duyệt

Có 18 control trong `lab_a8/catalog.json`. Mỗi tiêu chí có nguồn cấu hình/log, điều kiện pass, fail, thiếu bằng chứng, loại kiểm chứng và người phụ trách. Ngưỡng là chính sách lab (ví dụ retention 30 ngày, key/access review 90 ngày, clock offset 0,1 giây), không phải yêu cầu bắt buộc được trích từ ISO.

Mở Đánh giá A.8 → Phạm vi/rubric. Người phụ trách đọc và ghi nhận phê duyệt bằng tài khoản admin. API lưu người duyệt, thời điểm, ghi chú và hash catalog. Chưa có thao tác này thì vẫn là PENDING_HUMAN_APPROVAL. Phê duyệt cũ không tự áp dụng khi catalog đổi.

Phạm vi là hai kiểm tra đại diện/control; không chứng nhận toàn nội dung control hoặc ISMS. Các nguồn chính sách/biên bản cần người xác nhận được ghi rõ; Agent không tự tạo chữ ký hoặc sự phê duyệt thật.

## 2. Dựng lab và lỗi chủ đích

```powershell
.venv\Scripts\python.exe lab_a8/build_raw_lab.py
docker compose -f docker-compose.a8.yml up -d
```

Container `iso-a8-lab` dùng Ubuntu 22.04, không có mạng và không mở cổng. Chỉ mount read-only raw fixtures/script, không mount Docker socket hoặc thư mục host nhạy cảm. Script chỉ thay đổi tài khoản và tệp trong container.

- Tạo tài khoản `labworker` thực trong container.
- Kiểm tra quyền ghi thư mục cài đặt bằng chính user đó.
- Tạo/xóa tệp hết hạn, ghi log kiểm chứng sự tồn tại.
- Đối chiếu backup/restore bằng dữ liệu và SHA-256; tạo sai lệch có chủ đích.
- Các nguồn SSH/sudoers/ACL, EDR/malware status, vulnerability, firewall, TLS, DLP, monitoring, review/change là cấu hình/log lab có chủ đích. Không phải kết nối IAM/EDR thật; log trạng thái của dịch vụ chưa được triển khai không được xem là attestation vận hành thật.

Sáu nhóm × 18 = **108 ca duy nhất**: conforming, mixed, nonconforming, incomplete, stale, conflicting. Nhóm incomplete thiếu file, stale quá hạn capture, conflicting có digest bản thu độc lập không khớp. Đáp án thiết kế ở `lab_a8/reference/designer_labels.json`, không được Agent/collector đọc.

Lab replay có `observed_at` và `assessment_as_of` cố định để tái lập; không lấy một bản thu lịch sử làm khẳng định trạng thái hiện tại. Khi chuyển sang nguồn vận hành thật phải dùng thời điểm đánh giá hiện tại và chính sách freshness được người phụ trách duyệt.

Muốn reset lab thì restart container để chạy lại script. Trong lúc đo không reset hoặc chỉnh nguồn; nếu thay đổi, tạo lượt mới và giữ hash mới.

## 3. Thu và đánh giá bằng chứng gốc

Chọn nguồn **Container iso-a8-lab** trong UI. Collector dùng các lệnh Docker cố định để đọc tệp đã allowlist; không nhận shell/đường dẫn tùy ý. Nguồn **Replay raw** đọc cùng định dạng từ repository để test offline.

Collector parse text/JSON/CSV/TSV, tính checksum và quan hệ CIDR, kiểm tra ngày/offset/quyền/trạng thái. Mỗi artifact có nội dung gốc, SHA-256; gói có thời điểm thu, thời điểm quan sát, nguồn và lỗi. Cache mỗi tệp trong một lượt thu control để facts khớp đúng nội dung đã lưu. Thiếu/sai định dạng/hết hạn/mâu thuẫn → unknown; không tự coi là đạt. Docker chưa chạy thì API từ chối khởi tạo thay vì báo thành công.

LLM nhận rubric, facts dẫn xuất và artifacts gốc, không nhận đường dẫn chứa profile hoặc đáp án. Đầu ra bắt buộc schema và ID bằng chứng hợp lệ. Timeout/JSON sai/viện dẫn giả là lỗi engine riêng, không fallback ngầm sang luật.

## 4. Người đánh giá chấm mù

1. Người A tạo lượt đánh giá.
2. Người B là tài khoản khác, thuộc cùng đợt, chọn lượt đó.
3. Trước khi B nộp đủ 18 control, API chỉ trả gói cấu hình/log và rubric; ẩn profile, dự đoán Agent, đáp án nhóm, facts dẫn xuất và SoA.
4. B ghi kết luận/lý do từng control. Nhãn gắn user_id, thời điểm, report hash và evidence hash; nhãn đã nộp bị khóa.
5. Sau khi B nộp đủ 18, mở kết quả đối chiếu. Kênh danh sách, chi tiết và tổng hợp đều không được lộ dự đoán trước đó.

Đây là giao thức làm mù trên API/UI, không ngăn người có quyền đọc repository hoặc quản trị máy mở đáp án ngoài hệ thống. Cần phân công người chấm không xem bộ đáp án nguồn và ghi cam kết/quy trình độc lập. Tài khoản khác không tự chứng minh người đó là chuyên gia. Chưa có người thực sự chấm thì kết quả human vẫn **Chưa đo**. Test tự động nhập nhãn chỉ kiểm tra phần mềm, không tính là đánh giá con người.

Rubric và gói source được giữ trong từng báo cáo; không dùng nhãn một lượt để chấm các lượt có hash bằng chứng khác. Khi nhiều người chấm, báo cáo tách từng người/từng lượt; chưa tự suy ra nhãn đồng thuận.

## 5. Đo, báo cáo và SoA

```powershell
.venv\Scripts\python.exe -m agent_core.a8_benchmark --mode rules --transport docker --repeats 2 --output work/a8-rules-new.json
.venv\Scripts\python.exe -m agent_core.a8_benchmark --mode llm --transport docker --repeats 2 --output work/a8-llm-new.json
```

CLI hỗ trợ `--profiles` để đo riêng nhóm; lưu số lần lặp, nguồn và engine. Hai lần chạy cùng ca không phải hai ca độc lập: báo cáo số ca duy nhất và số lượt riêng. Kết quả v1 giữ nguyên, không thay bằng v2 hoặc so sánh như cùng điều kiện.

Bảng theo control có accuracy, số ca có nhãn, số lỗi, confusion matrix, precision/recall/F1 từng lớp và thời gian trung bình. Engine lỗi tính là sai trên mẫu có nhãn. Mẫu chưa có nhãn human không được tính là đúng. UI Tổng hợp nhiều lượt tách engine, transport, hash catalog và phiên bản rubric. Nhãn human được ghép đúng report hash, không tái sử dụng nhãn qua lượt khác.

SoA tự sinh có control, lý do áp dụng, trạng thái lab, người phụ trách, bằng chứng/hash và hành động. Mặc định DRAFT_NOT_APPROVED. Người phụ trách chỉ phê duyệt sau khi rubric cùng hash được duyệt và một người chấm hoàn tất 18 control; phải nhập tính áp dụng, căn cứ và kế hoạch xử lý/duy trì cho từng control. Lưu lịch sử quyết định, không đổi kết luận Agent theo quyết định người duyệt.

Phê duyệt là **HUMAN_APPROVED_LIMITED_SCOPE**, không phải SoA đầy đủ ISMS. Các control ngoài phạm vi chưa được đánh giá tính áp dụng; muốn nộp SoA hoàn chỉnh cần xác định bối cảnh/rủi ro và rà toàn bộ phạm vi với người phụ trách.

## Checklist bàn giao thực tế

- [ ] Người phụ trách duyệt rubric 18 control và phạm vi nguồn mô phỏng.
- [ ] Người đánh giá độc lập chấm đủ gói bằng chứng, không xem đáp án/Agent trước.
- [ ] Phân tích bất đồng, lưu quyết định nếu điều chỉnh rubric; đo lại trên tập tách biệt.
- [ ] Người phụ trách quyết định tính áp dụng và phê duyệt SoA trong phạm vi.

Các mục trên là thao tác con người cần thực hiện; không tự đánh dấu hoàn thành bằng test phần mềm. Không ghi công việc này vào nhật ký tuần theo yêu cầu người dùng.
