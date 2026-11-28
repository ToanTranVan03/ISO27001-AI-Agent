# Tiếp nhận bằng chứng bản vá hệ điều hành A.8.8

Ca vá hệ điều hành đang chờ xác nhận tên thiết bị và hệ điều hành ở đoạn 08:43–09:35 của ghi âm, một máy thử cô lập có quyền thao tác, mã bản vá, phiếu phê duyệt và phương án phục hồi. Ca ứng dụng mẫu có hồ sơ riêng.

## Kiểm tra gói nhận từ người vận hành

Đặt tệp JSON và ba bản gốc trong cùng một thư mục. Người vận hành khai metadata dựa trên các bản gốc thực tế.

| Nhóm | Trường bắt buộc |
| --- | --- |
| Cả ba bản ghi `before`, `execution`, `after` | `asset_id`, `os_family`, `patch_id`, `artifact` gồm `file` là tên tệp và `sha256` |
| `before` | `observed_at` có múi giờ, `os_build`, `patch_present: false` |
| `execution` | `approved_at`, `executed_at` có múi giờ, `approval_reference`, `status: "succeeded"` nếu biên nhận ghi thành công |
| `after` | `observed_at` có múi giờ, `os_build`, `patch_present: true`, `health: "ok"` nếu đã kiểm; `reboot_state: "completed"` hoặc `"not_required"` kèm `reboot_reason` |

```powershell
.venv\Scripts\python.exe -m evidence_collectors.os_patch_preflight <duong-dan-manifest.json>
```

Lệnh kiểm tra định danh khớp nhau, thứ tự thời gian và hash từng tệp thật. Kết quả **Chờ chuyên viên đối chiếu nội dung gốc** xác nhận gói đã qua kiểm tra cấu trúc và tính toàn vẹn. Chuyên viên vẫn cần đọc nguồn, đối chiếu phê duyệt và căn cứ cho từng trường. Lệnh chỉ đọc tệp cục bộ.

Trong Tổng quan 56 control → A.8.8 → **Nộp hồ sơ, log hoặc cấu hình gốc**, nộp riêng nguồn đo trước, biên nhận và nguồn đo sau. Tạo phát hiện cho tiêu chí vá hệ điều hành từ nguồn trước. Khi người vận hành hoàn thành đầu việc, gắn phép đo sau và gửi cho chuyên viên xác minh. Chuyên viên ghi kết quả theo tiêu chí và xuất báo cáo trước–sau.

## Hồ sơ 56 control còn chờ

Rà lại thư mục gói của đợt chính ngày 28/11/2026 có 56 manifest trống và 0 tệp nguồn mới đi kèm. Hồ sơ hiện hành vẫn cần bổ sung nguồn ngoài preset cho 37 control. A.6.2 cần bản đọc được của điều khoản ATTT kèm phạm vi và ngày hiệu lực. Giao diện A.6.2 có hướng dẫn kiểm số ký tự trích xuất trước khi lưu. Nhãn chấm độc lập, quyết định áp dụng, thẩm định và phê duyệt SoA cần người phụ trách thực hiện trên nguồn đã chốt. [Quy trình thu và thẩm định](THU_HO_SO_VA_THAM_DINH_56.md).

Kiểm thử kỹ thuật đạt 25 bài, gồm kiểm gói hợp lệ, chặn đổi mã máy, sai thứ tự, sai hash, dùng lại biên nhận làm nguồn sau và đường dẫn ngoài gói. Lint và build frontend đạt. Ca vá trên máy thật vẫn chờ các đầu vào ở đầu tài liệu.
