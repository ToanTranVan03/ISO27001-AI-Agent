# Hướng dẫn chạy nhanh — People-Centric ISO/IEC 27001:2022 Agent

Hệ thống đánh giá tuân thủ lấy **con người làm trung tâm**, liên kết chéo phần cứng và phần mềm, theo chu trình khép kín 8 bước
`Observe → Assess → Detect → Plan → Act → Verify → Report → Monitor` và 6 trạng thái
`Compliant · Non-compliant · Partial · Insufficient Evidence · Not Applicable · Pending Remediation`.

## 1. Cài đặt

```powershell
python -m pip install -r requirements.txt
```

> **Lưu ý phiên bản:** `fastapi==0.115.0` cần `starlette<0.39`, trong khi `streamlit` mới có thể kéo `starlette` cao hơn.
> Nếu `pip` báo xung đột, chạy dashboard và API trong **hai môi trường ảo riêng**, hoặc kiểm tra bằng
> `streamlit run dashboard_streamlit/app.py` sau khi cài. Bộ test (`AppTest`) không khởi động server nên không bị ảnh hưởng.

## 2. Dashboard Streamlit (chạy độc lập, không cần PostgreSQL)

```powershell
streamlit run dashboard_streamlit/app.py
```

Dashboard dùng kho dữ liệu in-memory, tự sinh 25 doanh nghiệp (kèm hồ sơ chuẩn `COMP-CANONICAL-01` chứa 4 kịch bản).

| Tab | Việc làm được |
| :--- | :--- |
| Tổng quan 3 Trụ cột | Quét toàn diện, xem 6 trạng thái, vết 8 bước từng control |
| Phê duyệt hành động (HITL) | Duyệt / từ chối lệnh `HIGH`/`MEDIUM` (ví dụ khóa AD `NV015`), xem `snapshot_before` |
| Phỏng vấn thích ứng | Nhân viên trả lời tình huống mở `A.6.8`; kiểm toán viên xác minh |
| Benchmark đối chứng | Chạy / xem bảng và biểu đồ M1–M4 |

Sidebar: chọn `company_id`, chế độ `simulation` / `hybrid_lab`, dry-run, bật SLM `qwen2.5:7b`.

## 3. FastAPI

```powershell
python -m uvicorn backend.main:app --reload
```

Mọi endpoint yêu cầu `Authorization: Bearer <token>` (đăng nhập qua `POST /api/auth/login`). Thao tác ghi quan trọng
(sinh dữ liệu, quyết định hành động, xác minh phỏng vấn, chạy benchmark) chỉ dành cho vai trò `admin`.

| Method & đường dẫn | Mô tả |
| :--- | :--- |
| `GET /api/pc/companies` | Danh sách doanh nghiệp |
| `POST /api/pc/companies/generate` | Sinh `count` doanh nghiệp (mặc định 25) kèm 4 kịch bản chuẩn |
| `POST /api/pc/companies/{id}/assess` | Chạy đồ thị 8 bước; trả `assessment_run_id` và trạng thái từng control |
| `GET /api/pc/companies/{id}/assessments` | Kết quả mới nhất từng control |
| `GET /api/pc/companies/{id}/actions?status=PENDING_APPROVAL` | Lệnh chờ duyệt |
| `POST /api/pc/actions/{action_id}/decision` | `APPROVE` / `REJECT`, tùy chọn kèm `assessment_run_id` để chặn kết quả cũ |
| `POST /api/pc/interviews/start` · `POST /api/pc/interviews/{session_id}/submit` · `POST .../verify` | Phỏng vấn thích ứng |
| `POST /api/pc/benchmark/run` · `GET /api/pc/benchmark/latest` | Ablation Benchmark 4 mô hình |

Ví dụ:

```powershell
$h = @{ Authorization = "Bearer $token" }
Invoke-RestMethod -Method Post -Headers $h -ContentType 'application/json' -Uri http://127.0.0.1:8000/api/pc/companies/generate -Body '{"count":25}'
Invoke-RestMethod -Method Post -Headers $h -ContentType 'application/json' -Uri http://127.0.0.1:8000/api/pc/companies/COMP-CANONICAL-01/assess -Body '{"controls":["A.8.8","A.6.5"]}'
```

Kho dữ liệu mặc định là **in-memory** (mất khi khởi động lại). Đặt `PC_STORAGE=postgres` để dùng các bảng `pc_*` trong PostgreSQL.

## 4. Quy tắc an toàn đã được kiểm thử

- Lệnh `HIGH` **không bao giờ** tự chạy: dừng ở `PENDING_APPROVAL` → control ở `Pending Remediation` cho đến khi admin duyệt.
- Sau khi duyệt, Verification Agent **thu thập lại bằng chứng mới**; không đủ bằng chứng thì không lên `Compliant`
  (ví dụ `NV015` bị khóa tài khoản nhưng laptop `LT-NV015` chưa trả → vẫn chưa đạt).
- Từ chối một lệnh sẽ đánh giá lại control đúng thực trạng (`Non-compliant`), không để trạng thái chờ duyệt cũ.
- `assessment_run_id` không khớp → `409`, tránh duyệt nhầm theo kết quả đã lỗi thời.
- Phỏng vấn: `disciplinary_blocked` luôn `True`; chỉ con người xác minh mới cập nhật hồ sơ nhân sự.
- `hybrid_lab` **không** chạy WinRM/SSH thật nếu chưa đặt `ISO_LAB_ENABLE_REAL=1` (kèm `ISO_LAB_AD_PASSWORD`,
  `ISO_LAB_AD_USERNAME`, và `lab_config` của doanh nghiệp); mặc định tự lùi về `simulation`.
- Không có tool nào nhận chuỗi lệnh thô; mọi tham số đi qua schema Pydantic `extra='forbid'` và có audit log `SHA-256`.

## 5. Benchmark (M1 – M4)

```powershell
python -c "from benchmark.ablation_runner import run_ablation_benchmark, export_benchmark_results; print(export_benchmark_results(run_ablation_benchmark(enterprise_count=25), 'data/pc-benchmark'))"
```

Xuất `ablation_benchmark_summary.csv` và `ablation_benchmark_report.json`. Ground Truth chỉ được đọc sau khi cả 4 mô hình chạy xong.
Các mô hình `M2`/`M3` mô phỏng hành vi SLM không có guardrail (xác định, tái lập được) khi không bật `use_live_ollama`,
vì vậy số liệu phản ánh thiết kế thí nghiệm chứ không phải độ chính xác của một mô hình ngôn ngữ cụ thể.

## 6. Kiểm thử

```powershell
python -m pytest tests -q -rs
```
