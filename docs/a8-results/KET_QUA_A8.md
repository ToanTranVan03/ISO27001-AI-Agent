# Kết quả kiểm chứng ban đầu A.8 — 10/11/2026

## Thiết kế và giới hạn

18 control × 4 hồ sơ = 72 ca; hai thuộc tính Boolean/null mỗi control, chuẩn hóa sẵn trong export lab. Một lần lặp. Đáp án do nhóm thiết kế, không phải nhãn chuyên gia độc lập. Tên profile, đường dẫn profile và nhãn đáp án không gửi vào LLM. Các tiêu chí là rubric dự án, chưa bao phủ toàn bộ nội dung control ISO.

## Kết quả

| Engine | Khớp đáp án nhóm | Lỗi gọi/schema/viện dẫn | Trung bình/ca | Đối chiếu người đánh giá |
|---|---|---|---|---|
| Luật baseline | 72/72 (100%) | 0 | Xem JSON baseline | Chưa đo |
| Ollama Qwen2.5:7b | 70/72 (97,22%) | 0 | 5.458,66 ms | Chưa đo |

Không có fallback ngầm. Tỷ lệ 97,22% chỉ trên bộ ca đơn giản tự xây dựng, không phải độ chính xác ISO tổng quát hoặc độ đúng so với con người. Baseline và nhãn dùng cùng rubric nên việc đạt 100% không chứng minh tổng quát hóa.

## Bảng theo từng control

| Control | Đúng / số ca — LLM | Accuracy | Luật | Nhãn người đánh giá |
|---|---|---|---|---|
| A.8.1 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.2 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.3 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.5 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.7 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.8 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.9 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.10 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.12 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.13 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.15 | 3/4 | 75% | 4/4 | Chưa có |
| A.8.16 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.17 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.19 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.20 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.22 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.24 | 4/4 | 100% | 4/4 | Chưa có |
| A.8.32 | 3/4 | 75% | 4/4 | Chưa có |

## Hai trường hợp chưa khớp

- A.8.15-incomplete: một thuộc tính chưa có bằng chứng, Agent trả Partially Compliant; đáp án rubric là Insufficient Evidence.
- A.8.32-incomplete: cùng loại lỗi, Agent trả Partially Compliant thay vì Insufficient Evidence.

Giữ nguyên kết quả, không sửa theo đáp án. Cần bổ sung ca null/mâu thuẫn/hết hạn, phân tích lý do và đo lại trên tập kiểm định tách biệt nếu điều chỉnh prompt.

## Artifact

- [Kết quả LLM và từng ca](ollama-judgments.json)
- [Bảng LLM theo control CSV](ollama-judgments.csv)
- [Baseline luật](baseline-rules.json)
- [Dự thảo SoA đọc được](SOA_DU_THAO.md)
- [SoA JSON](ollama-judgments-soa.json)

Kiểm chứng phần mềm: 227 test Python và build frontend đạt. Chưa kiểm thử bấm toàn bộ UI có đăng nhập; kiểm thử review dùng dữ liệu thử, không tính là người đánh giá thực sự.
