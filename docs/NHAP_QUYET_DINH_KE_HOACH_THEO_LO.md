# Nhập tính áp dụng và kế hoạch xử lý theo lô

Chức năng cho người phụ trách quản lý phạm vi 56 control; không tự đưa ra quyết định, tạo thẩm định hoặc duyệt SoA.

## Cách sử dụng

1. Đăng nhập admin, mở **Tổng quan 56 → Quản lý nguồn, tiêu chí và hồ sơ bàn giao → Nhập tính áp dụng & kế hoạch theo lô**.
2. Bấm **Xuất mẫu quyết định 56 control**. Mẫu giữ quyết định đã ghi; các giá trị chưa có để trống/null. Không tự gán toàn bộ control là áp dụng hoặc loại trừ.
3. Điền quyết định thực tế trong JSON. Có thể giữ từ 1 đến 56 dòng; xóa các dòng chưa quyết định. Giữ nguyên `assessment_id` và `expected_fingerprint` từ mẫu.
4. Chọn tệp và ghi **Căn cứ nhập gói / xuất xứ quyết định**: hồ sơ/trao đổi nào đã dùng, phạm vi đã rà. Bấm **Xem trước**, đọc từng thay đổi và điều kiện còn thiếu. Xem trước không lưu.
5. Chỉ bấm **Lưu N quyết định/kế hoạch đã xem trước** sau khi người phụ trách đã rà nội dung. Gói được kiểm tra lại trên server; nếu hồ sơ đã đổi, phải xuất/đối chiếu mẫu mới. Thay đổi chưa được lưu một phần khi gói có dòng trùng, sai phạm vi hoặc sai định dạng.

## Các trường trong mỗi dòng

| Trường JSON | Ý nghĩa |
|---|---|
| `control_id` | Mã thuộc phạm vi A.6.1–A.6.8, A.7.1–A.7.14, A.8.1–A.8.34 |
| `applicable` | `true` = áp dụng, `false` = đề xuất loại trừ có căn cứ; phải do người phụ trách quyết định |
| `reason` | Căn cứ áp dụng/loại trừ, ít nhất 10 ký tự |
| `treatment` | Kế hoạch xử lý/duy trì hoặc nội dung cần rà đối với loại trừ, ít nhất 10 ký tự |
| `treatment_owner` | Người nhận thực tế; được để `null` khi chưa thống nhất và đang lưu nháp |
| `treatment_due` | Ngày lịch `YYYY-MM-DD`, hoặc `null` khi chưa xác định |
| `verification_plan` | Nguồn/cách kiểm tra lại, ít nhất 10 ký tự nếu điền; được để `null` khi lưu nháp |

Tệp tối đa 1 MB trên giao diện. API kiểm tra schema, ngày lịch, quyền admin, mã đợt, fingerprint và control trùng/ngoài phạm vi. Không tự sửa hoặc bỏ qua dòng sai để lưu phần còn lại.

## Lịch sử và điều kiện duyệt

- Mỗi dòng thay đổi có người lưu, thời điểm, mã lô, căn cứ nhập và fingerprint đã dựa vào. Lịch sử cũ được giữ; dòng không đổi không tạo lịch sử trùng.
- Gói được lưu một lần bằng cơ chế thay tệp JSON nguyên tử hiện có. Lỗi lưu không được báo thành công.
- Có thể lưu kế hoạch nháp thiếu người nhận/hạn/cách kiểm tra lại. Control áp dụng vẫn bị chặn trình duyệt nếu còn thiếu các trường này hoặc chưa thẩm định hiện hành.
- Số hồ sơ dự kiến đủ điều kiện trong phần xem trước không phải số control tuân thủ. Phê duyệt SoA vẫn là thao tác riêng và chịu các gate hiện hành.
- Nhãn mù, bằng chứng, kết quả Agent và xác nhận rubric không được tạo/thay đổi bởi chức năng nhập quyết định.

Không loại trừ một control chỉ vì chưa thu được hồ sơ. Không dùng dữ liệu kiểm thử tổng hợp làm quyết định thật của nhóm.
