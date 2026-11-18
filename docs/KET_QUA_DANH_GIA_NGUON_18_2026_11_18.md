# Đánh giá lại 18 nguồn A.8 hiện có — 18/11/2026

Lô server: `37dd8327-e54f-44ee-b8dd-aa017f99b4f0`. Nguồn/rubric không đổi giữa các lần kiểm tra lại (token từng control được đối chiếu).

- Lần đầu: 18 mục được xử lý; 16 job lưu kết quả, 2 lỗi JSON/schema ở A.8.8 và A.8.19.
- Tăng riêng giới hạn phản hồi lên 512: hai job kiểm tra lại vẫn lỗi; giữ nguyên các job này.
- Sau đóng gói nguồn không mất dữ liệu, giới hạn đầu vào và context 16K: hai job kiểm tra lại lưu kết quả. Tổng hợp lần thực thi mới nhất: 18/18 job có kết quả đã lưu.
- Đây không phải 18/18 control tuân thủ, không phải 100% accuracy và không phải chấm độc lập. Không sửa nhãn người chấm, không phê duyệt SoA hoặc tạo nguồn mới.

| Control | Lần đầu | Sau sửa giới hạn phản hồi | Sau sửa đầu vào/context | Kết luận máy của lần thực thi mới nhất |
|---|---|---|---|---|
| A.8.2 | Đã lưu | Không chạy lại | Không chạy lại | Không tuân thủ |
| A.8.3 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |
| A.8.5 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |
| A.8.7 | Đã lưu | Không chạy lại | Không chạy lại | Tuân thủ một phần |
| A.8.8 | Lỗi | Lỗi | Đã lưu | Tuân thủ một phần |
| A.8.9 | Đã lưu | Không chạy lại | Không chạy lại | Tuân thủ một phần |
| A.8.10 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |
| A.8.12 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |
| A.8.13 | Đã lưu | Không chạy lại | Không chạy lại | Tuân thủ một phần |
| A.8.15 | Đã lưu | Không chạy lại | Không chạy lại | Tuân thủ một phần |
| A.8.16 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |
| A.8.17 | Đã lưu | Không chạy lại | Không chạy lại | Không tuân thủ |
| A.8.19 | Lỗi | Lỗi | Đã lưu | Không tuân thủ |
| A.8.20 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |
| A.8.22 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |
| A.8.24 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |
| A.8.32 | Đã lưu | Không chạy lại | Không chạy lại | Tuân thủ một phần |
| A.8.1 | Đã lưu | Không chạy lại | Không chạy lại | Chưa đủ bằng chứng |

[Dữ liệu chi tiết: job/evaluation ID, nguồn viện dẫn, source token và audit trail](a8-results/source-batch-2026-11-18.json).

Các nguồn này là bản thu lab đã có trong dự án, không chứng minh trạng thái production tại ngày đánh giá. Kết luận máy còn cần thẩm định từng tiêu chí; nguồn kiểm định mới và nhãn đủ điều kiện vẫn chưa được cung cấp.
