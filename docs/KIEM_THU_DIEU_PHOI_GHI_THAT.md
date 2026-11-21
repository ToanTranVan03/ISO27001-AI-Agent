# Kiểm thử điều phối bằng API, worker và trình duyệt thật

Ngày 21/11/2026. [Báo cáo đạt](a8-results/isolated-orchestration-2026-11-21-retry.json); [lần đầu lỗi](a8-results/isolated-orchestration-2026-11-21.json) được giữ nguyên.

## Đã thực hiện

Hai kịch bản Edge chạy tuần tự trên PostgreSQL/backend/kho tệp riêng:

1. Nộp nguồn tổng hợp, tải bản gốc, thẩm định tiêu chí, lưu kế hoạch, duyệt SoA thử rồi làm hết hiệu lực khi nguồn thay đổi; hai tài khoản thử nộp 36 nhãn có hỗ trợ. Đây là kịch bản tích hợp đã có, chạy lại để kiểm tra hồi quy.
2. Khởi chạy lô hai control với **Ollama thật** và nguồn tổng hợp. Yêu cầu chạy trùng trả về cùng lô; dừng sau A.6.1, tải lại trang vẫn theo dõi được. Lượt mới chỉ chạy A.6.2 còn lại. Cả hai job lưu thành công; kiểm tra lịch sử có `MODEL_INPUT_BYTES` và `EVALUATE`, không thay model bằng stub.
3. Kiểm tra gói ứng viên trên giao diện không tạo lượt; sau đó nhập/chạy qua worker bằng **engine luật**, đủ 18 bản ghi và đúng hash snapshot. Tải lại giữ đúng lượt. Nguồn là fixture đã sửa nội dung riêng cho kiểm thử đường truyền, không phải bộ kiểm định mới độc lập.
4. Hai tài khoản `release_rater1`/`release_rater2` đọc cùng report hash và 18 nguồn trong gói mù; không thấy report/plan/facts, không có quyền tạo lô. Không nộp nhãn cho gói ứng viên mới.

Kết quả: cả hai bài Edge đạt; database thử đã dọn, số dòng `evidence`, `evaluations`, `team_users` của database chính không đổi. Kết quả này không đo độ đúng của Agent với con người và không xác nhận toàn bộ lỗi đồng thời/mất mạng/khởi động lại worker.

## Lỗi phát hiện và sửa

Lần đầu, Windows trả `PermissionError [WinError 5]` khi thay tệp JSON quyết định SoA; kịch bản điều phối mới vẫn đạt nhưng toàn bộ lượt được ghi **failed** vì kịch bản SoA lỗi.

Hàm lưu JSON dùng tệp tạm duy nhất trong cùng thư mục và vẫn thay thế nguyên tử. Khi Windows tạm giữ tệp mở, chỉ thử lại các mã lỗi 5/32/33, tối đa năm lần, tổng thời gian chờ 150 ms. Lỗi kéo dài vẫn được báo; bản cũ giữ nguyên, không ghi đè trực tiếp hoặc báo thành công giả. Tệp tạm được dọn khi có thể.

Sáu test hồi quy kiểm tra bản cũ còn đọc được khi bị giữ mở, lưu đúng UTF-8 sau thử lại và giữ nguyên bản cũ khi hết lượt thử/không có quyền. Tổng hồi quy: **345 test Python, 14 test JavaScript, lint/build đạt**. Tám kịch bản UI thường đã đạt ở đợt trước, không cộng thành kiểm thử đầy đủ toàn giao diện.

## Chạy lại

```powershell
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --extended --output docs/a8-results/isolated-orchestration-MOC_MOI.json
```

Yêu cầu PostgreSQL và Ollama local đang chạy, dependencies đã cài, giao diện đã build. Chọn tên báo cáo mới để giữ lịch sử. Runner tạo database có tên riêng, kho tệp và tài khoản thử riêng; sau kiểm thử dọn database. Kết quả trình duyệt từng lượt lưu dưới `work/iso_acceptance_.../browser-results`.

Không dùng các hồ sơ, quyết định, phê duyệt hoặc nhãn tổng hợp của kiểm thử làm bằng chứng nghiệm thu của nhóm. Rubric, nguồn được chấp nhận, chấm thật và SoA chính vẫn do đúng người thực hiện.
