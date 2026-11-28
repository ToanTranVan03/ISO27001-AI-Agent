# Nghiệm thu bàn giao laptop khi nghỉ việc · A.6.5

Ca mô phỏng EMP-001, laptop DEVICE-001 tại Kho CNTT. Rubric của đồ án dùng tiêu chí “Có checklist thu hồi tài sản”. Lượt thử để tiêu chí cắt quyền ở trạng thái chưa rõ, nên kết luận toàn control là Chưa đủ bằng chứng.

| Bước | Kết quả và đường chạy |
|---|---|
| Ghi hiện trạng | API thật tạo doanh nghiệp, đợt, người, laptop, quan hệ giao thiết bị và nguồn trước; phát hiện giữ ID nguồn và baseline. |
| Giao việc, nhân viên xác nhận | Giao đúng người và hạn bằng API; trên React nhân viên mở đầu việc, sang danh sách bàn giao lọc theo nhân viên/A.6.5 và gửi phản hồi. Sau phản hồi kho vẫn chưa đánh dấu trả và chưa có thẩm định control. |
| Mã sai và nộp lại | Nộp tệp qua API. Trên React người tiếp nhận nhập DEVICE-999 và bị API chặn 409. Tệp đúng R-001/DEVICE-001 được chọn và ghi nhận trên React. Nhân viên tải bản gốc được viện dẫn từ yêu cầu. |
| Trả bổ sung, thẩm định và xác minh | API thật ghi yêu cầu bổ sung cho nguồn sai; tài khoản tư vấn khác người tiếp nhận và nhân viên rà nguồn đúng, thẩm định tiêu chí và đóng hành động. Lưu cả lần trả và lần đạt cùng baseline. |
| Báo cáo | Tải PDF/Excel từ React. Mở bằng pypdf/openpyxl để rà tiếng Việt, mã thiết bị, người xác minh, nguồn và lịch sử. Chưa rà bố cục desktop. |

MFA trước đó đã đạt lượt tập trung, bao gồm phản hồi bổ sung, xác minh theo tiêu chí, xuất PDF/Excel, chặn truy cập ngoài quyền và lưu sau restart. [Biên nhận MFA](../work/mfa-scoped-final.json). Các bước chưa bấm UI được ghi riêng trong [hồ sơ MFA](NGHIEM_THU_KHAC_PHUC_MFA.md). Lượt bàn giao chỉ dùng dữ liệu mô phỏng. Hai tệp báo cáo trước–sau lưu bản chụp cuối của lượt thử.

## Chạy lại

```powershell
npm --prefix frontend-react run build
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --governance --clients --employee-workflows --handover-only --output work/handover-new.json
```

Cần Edge và PostgreSQL. Runner tạo database dùng một lần và sinh mật khẩu thử. Tệp xuất và log nằm dưới thư mục tên database trong work. Các bước setup, giao việc, tải tệp lên và xác minh chuyên môn chưa được kiểm thử xuyên suốt bằng UI. Không dùng mock.

## Demo 5 phút

1. Phút 0–1. Dùng tài khoản tư vấn của đợt thử. Mở Tổng quan 56 control → Tư vấn & khắc phục. Chỉ laptop DEVICE-001, nhân viên EMP-001, nguồn kiểm kê ban đầu và tiêu chí checklist thu hồi.
2. Phút 1–2. Mở đầu việc đã giao hoặc duyệt/giao cho nhân viên thử. Dùng tài khoản nhân viên ở cửa sổ riêng, mở đầu việc rồi bấm **Mở yêu cầu bàn giao của người thực hiện**. Mở nhóm yêu cầu nhân viên và nộp phản hồi.
3. Phút 2–3. Đăng nhập người tiếp nhận. Mở yêu cầu tài sản, chọn nguồn và nhập mã trên biên nhận. Thử DEVICE-999, sau đó dùng biên nhận R-001 ghi DEVICE-001. Chuẩn bị sẵn nguồn để vừa thời lượng.
4. Phút 3–4. Người xác minh khác người tiếp nhận mở hồ sơ, đọc đúng nguồn từ liên kết biên nhận, thẩm định checklist. Chỉ ra lịch sử trả bổ sung và kết luận toàn control còn thiếu nguồn cắt quyền.
5. Phút 4–5. Tải PDF/Excel và đối chiếu tài sản, ID nguồn, người xác minh và lịch sử.

Tài khoản trong ca tự động gồm release_admin, employee_participant và employee_source_owner. Với demo trực tiếp, dùng tài khoản riêng đã cấp quyền trong đợt demo còn chạy, vì runner dọn database khi xong.

## File và giới hạn

- App.jsx, Scope56.jsx, CompanyInventory.jsx, RemediationWorkspace.jsx xử lý chuyển ngữ cảnh theo đợt, control và danh tính đã gán. Nếu nhân viên có nhiều yêu cầu A.6.5, phải chọn yêu cầu đúng theo mã tài sản.
- EmployeeWorkflows.jsx chuyển mã thực đọc từ biên nhận để kiểm tra đích và cho tải nguồn gốc theo chính sách quyền hiện hành. Người tiếp nhận vẫn cần đọc bản gốc. Mã nhập khớp không chứng minh nội dung tệp.
- frontend-react/tests/live-zzz-employee-workflows.spec.js và run_isolated_acceptance.py kiểm tra luồng ghi thật. Không cần migration. Tiêu chí và quyết định cấp control vẫn do người được phân quyền thẩm định.

[Biên nhận chạy đạt](../work/handover-verified.json) · [PDF](../work/handover-delivery/handover-before-after.pdf) · [Excel](../work/handover-delivery/handover-before-after.xlsx) · [Log Edge](../work/handover-delivery/browser.log). Hai lượt đầu qua kiểm tra trình duyệt nhưng runner hậu kiểm dùng tài khoản của ca khách hàng không được chạy ở chế độ tập trung. Đã dùng đúng tài khoản nhân viên của ca bàn giao và chạy lại đạt sau restart. Số dòng các bảng chính được theo dõi giữ nguyên, database thử đã dọn.
