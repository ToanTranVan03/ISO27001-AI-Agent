# Nghiệm thu truy vết bản thu A.8 và phát hiện

Ngày 28/11/2026, Edge chạy qua FastAPI và PostgreSQL trên database kiểm thử riêng. Lượt A.8 live dùng engine luật trong container lab. Từ A.8.8 đã mở đúng phát hiện, quay lại đúng lượt và đọc được liên kết sau khi khởi động lại API. Runner đã dọn database thử.

| Bản ghi | Định danh |
| --- | --- |
| Lượt Thực nghiệm A.8 | `4414d015-09ca-4024-93c7-eb407143525a` |
| Phát hiện A.8.8 từ bản thu inventory | `01b1d356-2b24-4bb3-8789-0757984e2906` |
| Đối tượng bản thu | `08b11382ce92` |
| Nguồn đã nhập | `A8CAP-1d7d32f5ee8c6cc55a65448b131ee15a36ad3b75` |

Thao tác trên dữ liệu mới gồm chạy live, nhập nguồn, tạo phát hiện trong Tổng quan 56 control và chọn **Bản thu Thực nghiệm A.8 làm căn cứ**. Trong lượt nghiệm thu tự động, bước chạy, nhập và tạo dùng API. Bước từ lượt đến phát hiện và quay lại lượt đi qua Edge. Lượt đang xem chỉ hiện các phát hiện có cùng mã lượt, control và hash báo cáo. Bản thu phải có định danh đối tượng, đúng đợt và hash. JSON, PDF và Excel giữ mã lượt cùng nguồn. Hai định danh trong bảng thuộc database thử đã dọn. [Biên nhận kiểm thử](../work/a8-lien-ket-phat-hien-2026-11-28.json).

Đây là phát hiện cho bản thu inventory. Phát hiện cập nhật ứng dụng mẫu A.8.8 đã kiểm chứng ở lượt trước có chuỗi nguồn trước–sau riêng. Muốn nối chính ca ứng dụng vào một lượt nghiên cứu, lượt đó phải thu được cùng đối tượng, ứng dụng và phép đo, rồi chốt bộ nguồn theo rubric của lượt. API chặn ghép nguồn inventory với nguồn đầu của ca cập nhật mẫu.

## Xem phép đo của chính ca cập nhật ứng dụng

Trong Tổng quan 56 control, chọn **Theo dõi phát hiện này**, rồi mở **Thực nghiệm A.8 · phát hiện**. Mục **Phép đo trước–sau ứng dụng mẫu A.8.8** đọc biên nhận đã lưu của đúng đầu việc. Mục này hiển thị mã phép đo, phiên bản, thời điểm quan sát, SHA-256 trước–sau và kết quả xác minh hồ sơ. Biên nhận thuộc ca ứng dụng; lượt nghiên cứu 18 control có bộ nguồn và rubric riêng.

Gói ứng dụng thử được đóng gói xác định để lần đọc mới có thể so SHA-256 với nguồn đã chốt. Với nguồn đầu mới, công cụ chỉ chạy khi khớp nền tảng, ứng dụng, phiên bản và hash. Ca thử tạo thư mục tạm, đọc lại ứng dụng trên đúng đích lab sau thao tác và ghi biên nhận; trạng thái ứng dụng của ca thử kết thúc cùng môi trường tạm.

Edge đã kiểm mở phép đo `c45b562650c1c0aa` từ phát hiện `015c3700-2971-463a-9bea-5dd08d018257`, xem hash và kết luận cải thiện một phần, tải lại trang rồi quay về hồ sơ. Đã đọc lại các báo cáo xuất từ ca thử. [Biên nhận Edge](../work/a8-phep-do-ung-dung-2026-11-28.json), [PDF](../work/ban-giao-nghiem-thu-2026-11-28/a8-phep-do-ung-dung.pdf), [Excel](../work/ban-giao-nghiem-thu-2026-11-28/a8-phep-do-ung-dung.xlsx), [JSON](../work/ban-giao-nghiem-thu-2026-11-28/a8-phep-do-ung-dung.json).

## Phần còn chờ

- Xác nhận tên/model và hệ điều hành ở đoạn 08:43–09:35. Ca vá hệ điều hành cần máy thử cô lập có quyền thao tác, bản vá xác định trước và phương án phục hồi.
- Bổ sung nguồn ngoài preset cho 37 control và thay tệp A.6.2 chỉ trích xuất một ký tự. Danh sách yêu cầu và bộ phận phụ trách nằm trong [hồ sơ bàn giao 56 control](BAN_GIAO_NGHIEM_THU_LINUX.md).
- Thu nhãn chấm độc lập trên bộ nguồn đã chốt, ghi quyết định áp dụng và thẩm định trước khi trình SoA.

## Chạy lại

```powershell
npm --prefix frontend-react run build
$env:ISO_TEST_LINUX_LAB='1'
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --remediation-only --output work/a8-lien-ket-phat-hien-moi.json
```

491 test Python thuộc nhánh và 16 test JavaScript đạt. Lint và build đạt. Kiểm thử báo cáo xác nhận đủ các trường truy vết trong PDF và Excel. Không cần migration.
