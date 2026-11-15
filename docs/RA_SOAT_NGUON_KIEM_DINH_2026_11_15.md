# Rà soát tìm nguồn kiểm định trong project — 15/11/2026

Phạm vi: thư mục `D:\AI_Agent_ISO27001`, gồm dữ liệu/work bị Git bỏ qua và metadata bằng chứng PostgreSQL, SQLite cũ. Không tìm trong thư mục cá nhân ngoài project. Không thay đổi/xóa bằng chứng, nhãn hoặc database.

## Kết quả tìm kiếm

| Vị trí | Tìm thấy | Có dùng làm bộ kiểm định mới được xác nhận không? |
|---|---|---|
| `lab_a8/raw` | 6 profile × 18 control = 108 ca đã dùng phát triển/hồi quy | Không; bộ đã biết |
| `data/a8-study` | Các lượt đã lưu, capture live và nhãn cũ; không có gói external candidate | Không tự coi lịch sử đã xem là tập chưa dùng phát triển |
| `docs/a8-results` | Báo cáo, pilot, regression và gói sealed live v5 | Là kết quả/lịch sử, không phải nguồn kiểm định mới |
| `work` | Log chạy, export tích hợp, sealed live plan, QA connector | Không; dữ liệu kỹ thuật hoặc test, không phải bộ độc lập |
| `data/evidence-packages/<assessment>` | 56 thư mục control; tất cả manifest trống, chỉ có `_REQUIRED.md` và `manifest.json` | Mẫu yêu cầu chưa phải bằng chứng |
| `lab_company/inventory_seed.json` | Dữ liệu doanh nghiệp seed đã dùng trong hệ thống | Không tự tạo bằng chứng cho 56 control hoặc tính độc lập |
| `data/live/agent_runs.sqlite3` | 2 runs, 3 tasks, 1 live_state, 2 live_events của luồng cũ | Không có bộ nguồn raw mới đủ 18 control |
| PostgreSQL, đợt hiện tại | 67 bản ghi preset tổng hợp, 18 capture live đã dùng và 1 bản nộp ngoài preset | Không có external candidate; không tính số bản ghi thành ca kiểm định độc lập |

Ở thời điểm quét có 791 tệp ứng viên trong project sau khi loại mã phụ thuộc, cache, `.git` và bản build frontend. Không thấy thư mục nguồn raw ngoài 6 profile đã biết, tệp nén/tài liệu mới tạo thành bộ 18 control hoặc sealed plan được gắn nguồn external candidate.

## Hồ sơ nộp cần kiểm tra lại

Nguồn A.6.2 mang tên `bc.docx` chỉ có **1 ký tự nội dung trích xuất** trong PostgreSQL. Không kết luận tài liệu gốc không tồn tại hoặc bị hỏng, nhưng nội dung hệ thống đang có chưa đủ chứng minh tiêu chí hợp đồng/trách nhiệm bảo mật. Cần kiểm tra lại tệp gốc, khả năng trích xuất và nộp nguồn có nội dung phù hợp.

Màn hình đếm 19 control có nguồn ngoài preset vì đang đếm sự hiện diện nguồn, gồm 18 capture và A.6.2. Không được báo 19 control đã có nguồn đầy đủ. Có 37 control chưa có nguồn ngoài preset; A.6.2 là một control bổ sung cần rà chất lượng, không gộp việc đó thành “đã đủ”.

## Kết luận và cách tiếp tục

**Chưa tìm thấy bộ kiểm định mới đủ điều kiện trong phạm vi project đã kiểm tra.** Điều này không chứng minh nguồn không tồn tại ở máy/thư mục khác. Không đổi tên fixture, bản QA, output benchmark hoặc bản chấm giả lập để gọi là bộ kiểm định mới.

- Có thể dùng các nguồn hiện tại để demo, hồi quy và đối chiếu có hỗ trợ với tên gọi trung thực.
- Muốn công bố đối chiếu tự chấm/kiểm định mới: chủ nguồn/người phụ trách cần cung cấp cấu hình/log hoặc hồ sơ mới và xác nhận lịch sử tiếp xúc trước khi chạy/chấm.
- Luồng nhập và chấm gói ứng viên đã có tại [bàn giao nghiệm thu bổ sung](HOAN_THIEN_NGHIEM_THU_2026_11_15.md); nhập được không tự xác nhận độc lập.
- Mục cung cấp tập kiểm định, chấm độc lập, nguồn còn thiếu và duyệt SoA vẫn chưa được tích hoàn thành.
