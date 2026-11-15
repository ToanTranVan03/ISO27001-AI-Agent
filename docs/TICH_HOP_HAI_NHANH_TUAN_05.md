# Tích hợp hai nhánh tuần 5 vào main local — 15/11/2026

Tích hợp chọn lọc vào main, không merge nguyên lịch sử nhánh; đồng bộ cùng bản cập nhật ngày 15/11/2026. Nguồn: `Tu/Tuan5` tại `7ee5918`, `Tuan5` tại `538a5ba`. Không chạy script của nhánh để tạo tài khoản/nhãn hoặc sửa database thật.

| Phần mới | Cách tích hợp |
|---|---|
| CLI chấm qua tài khoản assessor | Lấy bản tương tác của `Tu/Tuan5`: người chấm tự nhập kết luận, căn cứ, hỗ trợ/tiếp xúc và xác nhận NOP; có tiếp tục nhãn còn thiếu |
| Chuẩn bị tài khoản | Lấy bản bảo toàn tài khoản/mật khẩu của Tú; không reset password, xóa session hay login attempts. Thống nhất tên Tú với máy này: `ledoanvantu` |
| UTF-8 Windows và test CLI | Giữ sửa lỗi xuất tiếng Việt và test mock; test không tạo kết quả người chấm thật |
| Pipeline bảng từng control, SoA và gợi ý xử lý | Viết lại từ ý tưởng `Tuan5`, dùng báo cáo đã lưu và cơ chế chấm hiện hành; xuất JSON/CSV/Markdown vào thư mục mới, không ghi đè kết quả cũ |
| Nhãn người đánh giá | Chỉ nhận nhãn đã nộp có danh tính, thời điểm, case ID, report/evidence hash; không tạo nhãn từ designer key hoặc tự gán Khoa/Tú |
| Bảng độ đúng | Tách theo từng report/engine/nguồn/rubric và từng người chấm; không có nhãn thì không có accuracy. Live không dùng đáp án replay |
| SoA và kế hoạch | Luôn dự thảo, tính áp dụng chờ quyết định; gợi ý kỹ thuật không phải yêu cầu nguyên văn ISO hoặc việc đã hoàn thành |

Không nhập các tệp `human_assessor_labels.json` và báo cáo “đã duyệt/đánh giá độc lập” do pipeline tự sinh ở nhánh `Tuan5`. Không mang `--auto`/`review-all`, mật khẩu mặc định hoặc chức năng reset tài khoản vào main. Những tệp đó vẫn ở nhánh nguồn để giữ lịch sử; chưa sửa/xóa nhánh của thành viên.

## Cách sử dụng

Khi ứng dụng đang chạy, người chấm dùng CLI theo [hướng dẫn chấm tương tác](HUONG_DAN_CHAM_THAT_A8.md). Chỉ gọi seed khi thực sự cần tài khoản; lần tích hợp này không chạy seed.

Xuất báo cáo đã lưu, không tạo nhãn hay chạy LLM lại:

```powershell
.\.venv\Scripts\python.exe scripts/run_a8_teacher_pipeline.py --reports docs/a8-results/raw-v2-combined.json --output-dir work/bao-cao-tich-hop-moi
```

Muốn đối chiếu người thật, thêm `--labels <tep-danh-sach-nhan-da-nop.json>`. Tệp phải chứa nhãn xuất từ lượt chấm thật, không dùng đáp án thiết kế đổi tên. Nhãn phải khớp report/hash nguồn; nhãn có hỗ trợ được giữ riêng trong phân tích, không tính là bộ tự khai độc lập. Tính độc lập/chuyên môn vẫn cần xác nhận thực tế.

Thư mục xuất phải chưa tồn tại. Nguồn đầu vào là báo cáo lịch sử, được kiểm tra hash và chống đưa trùng report. Các bảng tự động không thể tự chứng minh nguồn hoặc người chấm là độc lập.

## Kiểm chứng tích hợp

- 238 test Python đạt, 3 cảnh báo deprecation thư viện.
- Chạy thử raw v2: đọc đủ 12 report đã lưu, xuất `evaluation.json`, `per-control.csv`, `REPORT.md` tại `work/integrated-branches-export-20261115`.
- Không có nhãn người thật được thêm vào trong lần xuất thử. Không dùng tỷ lệ khớp designer để báo accuracy chuyên gia; SoA luôn dự thảo.
- Chưa khởi động lại bài, chưa thực hiện chấm thật hoặc phê duyệt. Không sửa dữ liệu nghiên cứu/database hoặc kết quả cũ.
