# Tuần 3 — Benchmark, ground truth và guardrail

- Thời gian: **26/10/2026–01/11/2026 (thứ Hai–Chủ nhật).**
- Nguồn ghi chép: Script benchmark và kết quả lịch sử trong `docs/week3`.

## Mục tiêu và kế hoạch

- [ ] Chạy bộ ground truth qua Agent để đánh giá kết quả theo từng ca.
- [ ] Kiểm tra guardrail đối với bằng chứng thiếu, sai hoặc chứa nội dung can thiệp.
- [ ] Ghi nhận độ chính xác, các ca không khớp và nguyên nhân.
- [ ] Đối chiếu cấu hình thời gian của dữ liệu và môi trường benchmark.

## Nhật ký

Lưu ý: file benchmark bên dưới mang tên tuần 3 nhưng có timestamp **18/10/2026**,
nằm trong tuần 1 theo lịch đồ án. Đây là tài liệu tham chiếu lịch sử, chưa xác nhận
là công việc thực hiện trong khoảng 26/10–01/11; cần đối chiếu nhật ký nhóm trước khi chốt.

| Ngày | Công việc | Kết quả / minh chứng | Ghi chú |
|---|---|---|---|
| 18/10/2026 theo timestamp trong file | Có kết quả benchmark lịch sử | [week3_benchmark_results.json](../docs/week3/week3_benchmark_results.json) | File ghi 15 ca, accuracy 33,33%; chưa chạy lại trong lần tạo nhật ký này |
| Chưa bổ sung | Có runner benchmark và xử lý guardrail | [week3_benchmark.py](../week3_benchmark.py) | Cần bổ sung lịch thực hiện và người phụ trách |

## Kết quả và minh chứng

- Bộ kết quả lịch sử ghi `total_testcases: 15`, `accuracy_percent: 33.33`.
- Có ca bị chặn do timestamp bằng chứng được nhận diện ở tương lai.
- Kết quả trên phản ánh lượt chạy được lưu trong file, không đại diện mặc định cho bản hiện tại.

## Vướng mắc và việc chuyển tiếp

- [ ] Phân tích các ca dự đoán không khớp ground truth.
- [ ] Kiểm tra lỗi dữ liệu ngày giờ trước khi quy nguyên nhân cho mô hình.
- [ ] Chạy lại benchmark khi cấu hình và dữ liệu đã được xác nhận; giữ bản kết quả cũ để so sánh.
- [ ] Không nhầm số lượng unit test đạt với độ chính xác benchmark.
