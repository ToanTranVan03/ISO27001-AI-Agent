# Kết quả raw v2 — 10/11/2026

## Bộ ca và nguồn

18 control × 6 nhóm = 108 ca duy nhất. Mỗi ca chạy 2 lần, tổng 216 lượt/engine. Nguồn là raw cấu hình/log trong container cô lập; phép thử tài khoản/quyền/tệp/backup chạy trong container, các dịch vụ khác vẫn là cấu hình và log fixture. Tiêu chí là hai kiểm tra đại diện/control, không phải đánh giá đầy đủ ISO.

## Kết quả đối chiếu đáp án nhóm

| Engine | Số lượt | Khớp đáp án | Lỗi engine (đã tính là sai) | Tỷ lệ khớp |
|---|---|---|---|---|
| Baseline luật | 216 | 216 | 0 | 100% |
| Ollama Qwen2.5:7b | 216 | 206 | 4 | 95,37% |

**Chưa có kết quả người đánh giá thực sự.** Nhãn designer được giữ riêng và không đưa vào context Agent. Nhãn trong test phần mềm không được tính là con người chấm. Hai lần lặp không phải 216 ca độc lập, chỉ có 108 ca duy nhất.

## Theo từng control

| Control | Khớp / lượt | Accuracy | Lỗi engine | Human |
|---|---|---|---|---|
| A.8.1 | 10/12 | 83.33% | 2 | Chưa đo |
| A.8.2 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.3 | 10/12 | 83.33% | 2 | Chưa đo |
| A.8.5 | 10/12 | 83.33% | 0 | Chưa đo |
| A.8.7 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.8 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.9 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.10 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.12 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.13 | 10/12 | 83.33% | 0 | Chưa đo |
| A.8.15 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.16 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.17 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.19 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.20 | 10/12 | 83.33% | 0 | Chưa đo |
| A.8.22 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.24 | 12/12 | 100.00% | 0 | Chưa đo |
| A.8.32 | 12/12 | 100.00% | 0 | Chưa đo |

## Phân tích sai khác

- A.8.1-mixed và A.8.3-mixed có ValueError ở mỗi lần lặp: tổng 4 lỗi engine, giữ trong mẫu số. Artifact cũ chỉ ghi loại lỗi, chưa lưu đầy đủ raw response bị từ chối; không suy thêm nguyên nhân vượt dữ kiện đã lưu.
- A.8.5-incomplete, A.8.13-incomplete và A.8.20-incomplete bị kết luận Partially Compliant thay vì Insufficient Evidence ở cả hai lần: 6 lượt sai phân loại.
- Nhóm stale/conflicting: 72/72 lượt khớp nhãn thiếu bằng chứng. Đây là lỗi hết hạn/digest độc lập không khớp trong bộ ca lab, không chứng minh xử lý được mọi mâu thuẫn ngữ nghĩa ngoài thực tế.

## Thời gian và giới hạn đo

- Pipeline LLM trung bình ghi nhận: 7823.31 ms/lượt control; baseline: 392.82 ms.
- Hai tiến trình đo LLM có thời gian chồng lấn trên cùng Ollama/GPU. Thời gian gồm collector và chờ hàng đợi, không phải benchmark tốc độ đơn luồng cô lập; không dùng để kết luận hiệu năng sản phẩm.
- Cùng rubric và bộ ca có chủ đích; không suy rộng tỷ lệ khớp thành độ chính xác ISO thực tế. Cần người chấm mù, tập kiểm định mới, và không tối ưu prompt theo chính tập báo cáo này rồi công bố như tập kiểm định độc lập.

## Artifact

- [Kết quả đầy đủ, precision/recall/F1 và confusion matrix](raw-v2-combined.json)
- [Bảng theo control CSV](raw-v2-combined.csv)
- [Baseline raw v2](raw-v2-rules.json)
- [SoA đọc được](SOA_RAW_V2.md), [SoA JSON](raw-v2-soa.json)
- [Quy trình chấm mù và phê duyệt](../QUY_TRINH_NGHIEM_THU_A8.md)

Kiểm chứng phần mềm: **235 test Python đạt**, build thành công. API thật đã chạy đủ 18 control từ Docker, chưa có nhãn human, SoA đúng trạng thái chưa duyệt. Công cụ điều khiển Windows báo native pipe unavailable nên chưa xác nhận bấm toàn bộ UI.
