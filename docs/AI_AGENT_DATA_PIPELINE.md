# Pipeline dữ liệu và AI Agent

## Dữ liệu và nguồn kiến thức

- Catalog/rubric 56 và sổ yêu cầu lưu tiêu chí dự án, nguồn tham chiếu, phiên bản, quyền sử dụng; không phải bản toàn văn tiêu chuẩn được tự sao chép.
- Company/client, assessment và membership phân tách tenant. Nhân viên/tài khoản/tài sản là bối cảnh; chúng không tự trở thành bằng chứng đạt.
- File nộp → parser → kiểm chất lượng → giữ raw/hash → evidence theo assessment/control/type. Trường quan sát/xuất xứ là khai báo chưa xác thực.
- XLSX mở read-only, không thực thi công thức, không lấy external links; chặn archive giải nén trên 40MB, trên 200.000 ô hoặc hơn 100.000 ký tự. PDF scan/ảnh không có OCR không được báo đã trích xuất thành công.

## Truy xuất và suy luận

`GET /api/assessments/{id}/sources/search?q=...&control_id=...&limit=10` dùng PostgreSQL full-text `simple`. Membership được kiểm trước truy vấn; filter assessment luôn bắt buộc. Trả trích đoạn, ID, hash, lexical rank và has_more. Rank là thứ tự từ khóa, không phải confidence. React hiển thị text, không render HTML từ nguồn.

Agent hiện dùng collector và gói nguồn đã kiểm chất lượng theo control, không tự lấy một số search hit rồi tuyên bố đã đọc hết corpus. Graph plan/collect/evaluate/validate và batch giữ kết quả/lỗi từng control. Input model có ngân sách; vượt thì lỗi rõ thay vì cắt nguồn âm thầm. Model không được quyền phê duyệt, cấp chứng nhận hoặc biến missing thành noncompliant chỉ từ thiếu tài liệu.

Đây là kiến trúc truy xuất dữ liệu + workflow có kiểm soát; chưa triển khai embedding/vector index hoặc map-reduce LLM lớn. Thêm doanh nghiệp không cần train lại; không gửi dữ liệu doanh nghiệp để training. Fine-tuning chưa cần khi còn thiếu nhãn hợp lệ và phép đo held-out.

## Kỳ đánh giá và báo cáo

`period_metadata` trên assessment: ngày bắt đầu/kết thúc và loại kỳ. Timeline chỉ lấy các đợt của client mà tài khoản là thành viên. Mỗi control: chưa đánh giá / cần đánh giá lại / compliant / partial / noncompliant / insufficient / loại trừ đã ghi. Số thẩm định hiện hành tách riêng.

`POST /api/clients/{client}/periods/{assessment}/seal` nhận expected fingerprint; tư vấn hoặc quản trị doanh nghiệp chốt bản scope hiện có vào bảng snapshot append-only. Hash không khớp trả 409; chốt cùng bản trả cùng ID. Không xóa/đổi kết quả trước, không phê duyệt SoA. Timeline JSON có summary và sealed snapshots; JSON export giữ công thức và lưu ý.

Giá trị tỷ lệ được tính từ mẫu số công khai, không lấy confidence làm tuân thủ. Trạng thái tốt hơn giữa hai kỳ chưa chứng minh cùng phạm vi/rubric hoặc tác động khắc phục; phải đối chiếu nguồn/thẩm định trước.

## Kiểm thử và triển khai

Unit/mock UI, API/PostgreSQL thật, Qwen thật, synthetic data và chấm người thật phải báo riêng. Benchmark intake 1.000 file không phải benchmark LLM 1.000 file. Bản lưu/hash không chứng minh nguồn thật. Người đánh giá và người phụ trách phải tự xác nhận rubric, nhãn và SoA.

Xem [báo cáo nâng cấp](THESIS_ENTERPRISE_AI_AGENT_UPGRADE.md) và [hướng dẫn bộ mô phỏng](SYNTHETIC_DATA_GUIDE.md).
