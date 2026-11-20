# Sổ xử lý bất đồng và căn cứ cần rà — A.8

Trong **Thực nghiệm A.8 → mở lượt đã hoàn tất → Sổ xử lý bất đồng & căn cứ cần rà**, admin chọn control, hướng xử lý và ghi căn cứ đối soát (30–3000 ký tự).

Ba hướng xử lý: cần bổ sung bằng chứng, cần lượt chấm mới, đã ghi nội dung thảo luận. Không có trạng thái tự xác nhận nhãn đúng, chuyên gia độc lập hoặc SoA đã duyệt.

Mỗi bản ghi lưu người ghi, thời điểm, ID riêng, hash báo cáo và hash nguồn của control. Lịch sử chỉ bổ sung, không ghi đè. Có thể ghi trên lượt cũ để lưu quá trình rà lịch sử nhưng không mở lại quyền nộp nhãn cũ. API yêu cầu admin thuộc đợt, lượt hoàn tất, hash báo cáo hợp lệ và control đúng phạm vi.

```text
POST /api/assessments/{assessment_id}/a8/runs/{run_id}/review-followups
{control_id, report_sha256, state, note}
```

`state`: `needs_evidence`, `needs_new_review`, `discussion_recorded`. Trường ngoài schema bị từ chối. Hash cũ/sai hoặc lượt chưa hoàn tất bị chặn 409, control ngoài lượt bị chặn 422, người chấm bị chặn 403.

Sổ riêng có nút xuất JSON. Báo cáo điều phối admin cũng xuất lịch sử trong JSON/Markdown. Gói chấm mù chưa hoàn thành không chứa các ghi chú này để tránh lộ thông tin thảo luận trước chấm.

**Không thay kết quả nghiên cứu:** bản ghi không sửa nhãn khóa, căn cứ, khai báo hỗ trợ, bảng độ đúng hoặc phê duyệt. Ghi “đã thảo luận” không xóa cảnh báo chất lượng và không làm người chấm trở thành độc lập. Nếu cần kết luận mới, tổ chức lượt chấm/nguồn mới theo giao thức phù hợp và giữ lịch sử cũ.

## Kiểm chứng 20/11/2026

- 319 test Python đạt, gồm kiểm tra append-only, giữ nhãn/báo cáo, ràng buộc nguồn, quyền, schema, hash và không lộ sổ vào gói mù.
- Lint/build đạt; ba kịch bản Edge admin/Khoa/Tú đạt. Form mới được kiểm tra trên Edge với request POST giả lập riêng; không ghi ghi chú thử vào lượt thật. API ghi/lưu được kiểm tra bằng TestClient và thư mục tạm, không phải bằng chứng chấm thật.
- Chưa có biên bản xử lý chuyên môn thực tế được tạo bởi trợ lý. Người phụ trách cần đọc các căn cứ, ghi kết quả thảo luận và việc tiếp theo bằng thông tin thật.
