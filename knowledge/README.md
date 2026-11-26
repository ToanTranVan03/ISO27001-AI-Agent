# Nguồn tham chiếu

Chế độ hiện tại là `research_rubric`. Danh mục chỉ lưu mã tham chiếu và mô tả do đề tài soạn. Đối chiếu tài liệu cần bản mà người vận hành có quyền nhập và sử dụng. Trước khi nhập, ghi nguồn, phiên bản, điều kiện sử dụng, phạm vi truy cập và người duyệt. Giữ tệp cấp phép ngoài Git. Phase 08 triển khai công cụ nhập, truy xuất và dẫn nguồn.

Lệnh nhập cục bộ:

```powershell
python -m compliance_ai.cli knowledge-ingest --tenant <uuid> --file <path.txt> --metadata <metadata.json> --confirm-rights
```

Metadata gồm `control_id`, `title`, `reference`, `edition`, `rights_reference` và `source_type`. Dùng `authorized_material` cho nguồn được cấp quyền và `research_rubric` cho nguồn đề tài tự soạn. Truy vấn qua `GET /api/v1/companies/{company_id}/knowledge/{control_id}?query=...`. Nội dung được trả dưới dạng dữ liệu tham chiếu. Quy tắc đánh giá hiện hành vẫn dựa vào rubric phiên bản của dự án.

Dashboard hiển thị các đoạn được chọn tại **Tài liệu tham chiếu theo tiêu chí**. Mỗi đánh giá mới lưu mã đoạn và hash nội dung vào báo cáo để kiểm tra lại. Quyền đọc và hash được kiểm tra khi mở đoạn đã dẫn.
