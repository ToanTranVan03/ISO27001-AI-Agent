# Kiểm chứng đánh giá tuân thủ ngày 06/11/2026

## Thiết kế

8 ca tổng hợp tự xây dựng: thiếu bằng chứng đào tạo, nghỉ việc còn tài sản, đào tạo hết hạn, nguồn mâu thuẫn, rà soát quyền khi chuyển vai trò, ngoại lệ giữ tài khoản được duyệt/hết hạn. Nhãn expected không đưa vào ngữ cảnh model. Ba chế độ dùng cùng snapshot, mỗi ca một lần lặp. Đây chưa phải tập kiểm định ẩn hoặc nhãn chuyên gia.

| Chế độ | Hoàn tất | Khớp nhãn | Trung bình (ms) | Gọi model |
|---|---:|---:|---:|---:|
| rules | 8/8 | 8/8 | 4.69 | 0 |
| workflow | 8/8 | 8/8 | 24.07 | 0 |
| ai | 8/8 | 8/8 | 9361.26 | 59 |

LLM sử dụng Ollama thật, không tự chuyển workflow trong các lượt AI này. Cùng evaluator nên kết quả bằng nhau không chứng minh LLM phân loại tốt hơn luật. LLM chậm hơn; đóng góp hiện tại là chọn công cụ và diễn giải mục tiêu trong phạm vi giới hạn.

## Phục hồi khi model lỗi — báo cáo riêng

8 ca cố ý chặn transport model, giữ nguyên lỗi AI, sau đó benchmark harness chủ động chạy workflow. Cả 8 phục hồi hoàn tất và khớp nhãn. Đây là fault injection, không phải tỷ lệ fallback quan sát trong vận hành; không phải tính năng fallback ngầm được thêm vào Agent. Fallback SOC thực tế vẫn được ghi nguồn riêng trong hồ sơ sự cố.

## Tái lập

```powershell
.venv\Scripts\python.exe -m agent_core.research_benchmark --paired --repeats 1 --output docs/benchmark-2026-11-06.json
.venv\Scripts\python.exe -m agent_core.benchmark_provenance docs/benchmark-2026-11-06.json docs/benchmark-provenance-2026-11-06.json
```

File JSON lưu từng ca, nhãn, snapshot hash, trace công cụ, thời gian, lỗi và nguồn thực thi. Chưa đo chi phí/token, chưa lặp đủ để kết luận thống kê, chưa benchmark mọi luồng SOC hay dữ liệu doanh nghiệp thật. Benchmark tuần 3 cũ có lỗi thời gian không bị xóa hoặc thay số liệu bằng báo cáo này: đây là tập ca và engine khác.

## Hồ sơ trên giao diện

Đăng nhập → Hồ sơ ISO → chọn kiểm soát → xem tiêu chí lab, bằng chứng, kết luận và lịch sử → chạy/tái đánh giá → xem audit trail → xuất JSON. Nút từ Agent Workspace mở hồ sơ; Dashboard giữ luồng bổ sung bằng chứng và duyệt theo quyền hiện có.

Chưa đánh giá không được hiển thị đáp ứng dù preset healthy. Metadata bằng chứng bao gồm nguồn lab và tải lên/nhập của đúng đợt. Bằng chứng mới hơn lần đánh giá được cảnh báo cần tái đánh giá; thời điểm mới không tự chứng minh nội dung đúng. COMPLETED là trạng thái quy trình hiện có, không tự gán nghĩa người đã phê duyệt.

## Kiểm chứng kỹ thuật

176 test Python và 18 test JavaScript đạt, build frontend đạt; lint còn cảnh báo cũ, build cảnh báo kích thước chunk 3D. API hồ sơ thật trả 56 kiểm soát và 27 metadata bằng chứng tại thời điểm kiểm tra; không đăng nhập trả 401, test thành viên sai đợt trả 403 trước khi đọc dữ liệu.

Tái đánh giá A.6.1 qua API hoàn tất SUCCEEDED, lưu Partially Compliant cùng lịch sử và bằng chứng. Hai lỗi cũ được sửa: print tiếng Việt gây UnicodeEncodeError trên Windows CP1252; SDK ollama==0.4.0 không nhận schema dict ở format. Chuyển JSON mode, đưa schema vào prompt và giữ Pydantic validation; timeout model 45 giây. Chưa kiểm thử đầy đủ thao tác bấm trên UI có đăng nhập.
