# Liên kết bốn màn hình đánh giá

Ngày kiểm tra: 21/11/2026.

## Cách sử dụng

1. Trong **Doanh nghiệp**, chọn nhân viên rồi bấm **Xem hồ sơ liên quan**. Hồ sơ lọc theo mã nhân viên được ghi rõ trong bằng chứng; không suy ra kết luận cá nhân từ kết luận control.
2. Trong **Hồ sơ ISO**, mở một control rồi bấm **Tổng quan** để xem đúng control đó. Có thể quay về đúng nhân viên bằng nút liên kết doanh nghiệp.
3. Trong **Tổng quan 56 control**, mục liên kết hồ sơ mở cùng control ở Hồ sơ ISO hoặc mở đúng lượt A.8 đã tạo ra nguồn. Chọn control khác sẽ bỏ mã lượt không liên quan.
4. Trong **Thực nghiệm A.8**, chọn lượt/control rồi mở hồ sơ tương ứng. Sau khi nhập nguồn vào hồ sơ 56, ứng dụng tự mở control liên quan; phiếu tiếp nhận vẫn được tải về.
5. Tải lại trang hoặc dùng Back/Forward để trở lại màn hình và mục đang xem. Nếu control không có trong lượt A.8 đang chọn, giao diện báo rõ để tránh đọc nhầm nguồn.

Cập nhật lỗi cuộn trang: F5 vẫn giữ mã control/nhân viên/lượt trong đường dẫn nhưng mở ở đầu trang, không tự kéo xuống hồ sơ. Chỉ khi chủ động bấm mở control, nhân viên hoặc liên kết hồ sơ tương ứng, ứng dụng mới cuộn tới chi tiết. Tải lại không gửi lệnh chạy Agent hoặc lưu dữ liệu.

## Ngữ cảnh và giới hạn

- Đường dẫn dùng các trường hash `view`, `assessment`, `control`, `employee`, `run`. Không đưa mật khẩu, token, nội dung hồ sơ hoặc kết luận vào URL.
- Liên kết chỉ có tác dụng trong đợt mà tài khoản có quyền truy cập. Đăng xuất xóa ngữ cảnh đang mở. Quyền API và quy trình chấm mù vẫn được giữ nguyên.
- Chuyển màn hình không tự chạy Agent, ghi nhãn hay phê duyệt SoA. Các biểu mẫu chưa lưu không được bảo đảm giữ lại sau khi rời màn hình.
- Hồ sơ nhân viên chỉ lọc theo `entity_refs.employees` trong bằng chứng. Kết luận vẫn thuộc control của đợt đánh giá, không phải chứng nhận nhân viên tuân thủ.
- Lượt A.8, hồ sơ 56 và dữ liệu lab phát triển vẫn giữ phạm vi riêng; liên kết giao diện không biến dữ liệu thử thành bằng chứng nghiệm thu.

## Kiểm chứng

- `node --test tests/navigation.test.mjs tests/api_request.test.mjs tests/completion_guide.test.mjs`: 14 test đạt.
- `npm run lint` và `npm run build` trong `frontend-react`: đạt.
- `npm run test:ui`: 6 kịch bản Edge đạt. Kịch bản điều hướng đọc dữ liệu thật, kiểm tra nhân viên → hồ sơ → control → lượt nguồn, tải lại/Back và đăng xuất. Riêng POST nhập nguồn được chặn bằng phản hồi mô phỏng, không nhập hồ sơ thử vào đợt chính; fingerprint SoA và trạng thái nghiệm thu trước/sau không đổi.

- Kiểm thử ghi thật trên PostgreSQL/backend/Edge riêng: [lượt cuối đạt](a8-results/isolated-navigation-2026-11-21-final.json), database thử đã dọn, số dòng ba bảng chính không đổi. Nguồn, thẩm định, kế hoạch, vòng đời SoA và 36 nhãn thử của hai tài khoản đều là dữ liệu tổng hợp. Hai lần trước bị lỗi thư mục kết quả Playwright, được giữ ở [lần đầu](a8-results/isolated-navigation-2026-11-21.json) và [lần hai](a8-results/isolated-navigation-2026-11-21-retry.json); đã tách thư mục kết quả cho từng lượt để tránh tranh chấp/quyền ghi. Năm test bảo vệ database tạm đạt.

Đây là kiểm chứng phần mềm, không thay thế thẩm định rubric, nguồn bằng chứng hoặc phê duyệt của người phụ trách.
