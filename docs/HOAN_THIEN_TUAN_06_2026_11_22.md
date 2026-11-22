# Khóa sổ kỹ thuật tuần 6 — 22/11/2026

Báo cáo do trợ lý AI thực hiện trên máy dự án. Phạm vi giữ nguyên **56 control: 8 A.6, 14 A.7, 34 A.8**; thử sâu 18 A.8. Không tạo nguồn doanh nghiệp, nhãn người thật hoặc xác nhận giảng viên. Các lần chạy mới là thực nghiệm kỹ thuật, không được nhập thay nguồn của đợt chính.

## Kết quả thực hiện

| Yêu cầu | Trước đợt này | Đã kiểm chứng trong đợt này | Phần còn chờ |
|---|---|---|---|
| 1. Rubric/phạm vi | Đã có rubric, chưa duyệt | Rà 56 control/113 tiêu chí, 18 A.8/36 phép kiểm tra; lưu hash raw/live/scope và ma trận nguồn trong [phiếu rà rubric](RA_SOAT_RUBRIC_2026_11_22.md) | Giảng viên/người phụ trách xác nhận phiên bản, mức bao phủ và người chấm |
| 2. Nguồn | 19 control có nguồn, 37 thiếu; A.6.2 không dùng được | Đọc lại API thật và xuất gói 56 dòng, yêu cầu bổ sung/rà nguồn theo nhóm; giữ metadata/hash, không xuất nội dung riêng tư vào bảng tổng hợp | Cung cấp 37 nguồn còn thiếu và bản gốc thay A.6.2; thẩm định đủ nội dung |
| 3. Kiểm định/snapshot | Có chốt nguồn, thiếu bộ mới | Chốt snapshot 18 và nguồn/khóa 38 trước suy luận; thêm so sánh hai báo cáo có kiểm hash, tách thay nguồn/đổi recipe/lỗi; giữ lịch sử | Bộ chưa dùng phát triển và xác nhận lịch sử tiếp xúc thực tế |
| 4. Hồ sơ/xác minh | Có gói bàn giao và luồng chấm | Xuất lại packet/worklist/CSV; ghi rõ máy tạo, hỗ trợ AI, kết quả mô phỏng và phần chưa xác nhận | Người thật ghi kết luận và căn cứ đúng nguồn |
| 5. Kiểm thử | 367 test Python đã đạt | 380 Python, 14 JavaScript; API 39 kiểm tra ba tài khoản; database thử có thao tác nguồn/thẩm định/SoA và được dọn | Không suy từ test sang kết quả tuân thủ; ngoại lệ chưa phủ vẫn cần kiểm tra khi phát sinh |
| 6. Agent 18 A.8 | Có lượt cũ | Qwen2.5:7b chạy 18/18; không lỗi đầu/cuối, không thử lại; 18 kết luận một phần; có 18 file theo control | Người đánh giá kiểm tra lý do và mức bao phủ; không gọi là accuracy độc lập |
| 7. Bộ 38 | Có kết quả trước và bất đồng | Chạy mới đủ 38 ngoài nhóm 18; 0 lỗi đầu/cuối; 23/38 khớp khóa phát triển; giữ 15 lệch tổng và 19 lệch tiêu chí ở 18 control | Người thật rà kết luận/căn cứ và xác nhận khóa; không biến fixture thành hồ sơ thật |
| 8. Độ đúng 56 | Chưa có nhãn độc lập phù hợp | CSV đủ 56 ID không trùng giữa hai nhóm, tách loại dữ liệu và loại đối chiếu | Chưa có accuracy/precision/recall so với người đánh giá đủ điều kiện |
| 9. UI/quyền | 11 kịch bản cũ; danh sách nguồn mới chưa test trình duyệt | 11 luồng cũ đạt; ca nguồn mới đạt sau sửa thao tác test mở khối thu gọn; tổng 12 kịch bản được kiểm chứng qua hai lần chạy, không bỏ qua ca nào | Không phải 12 đạt trong một lần; kết quả UI không thay nghiệm thu chuyên môn |
| 10. SoA | Dự thảo | Xuất SoA A.8 dự thảo và packet 56; chặn thiếu quyết định/thẩm định vẫn giữ nguyên | 56 quyết định áp dụng/kế hoạch, thẩm định hiện hành và người có trách nhiệm duyệt |

## Nguồn và rubric thực tế

[Snapshot API](a8-results/release-2026-11-22-scope/snapshot.json): 29 control có bản ghi bằng chứng nói chung; **19** có nguồn ngoài preset (18 bản thu lab + A.6.2), **18** có nguồn qua ngưỡng nội dung, **37** thiếu nguồn ngoài preset. Không nhầm 29 bản ghi có cả preset với 29 nguồn được chấp nhận.

- Quyết định áp dụng: 0; thẩm định hiện hành: 0; rubric và SoA chưa duyệt.
- A.6.2 một ký tự là lỗi `too_little_extracted_text`, không phải ngưỡng được chấp nhận. Ngưỡng 20 ký tự chữ/số chỉ lọc nội dung kỹ thuật. Chưa có bản gốc để phân biệt tệp ít nội dung hay ảnh cần OCR.
- [CSV nguồn 56 control](a8-results/release-2026-11-22-scope/controls.csv) phân biệt có bản ghi, thiếu nguồn, nội dung không dùng được, lỗi toàn vẹn, chưa xác minh bản gốc và chưa xác nhận bao phủ. Nguồn qua ngưỡng không tự được coi phù hợp chuyên môn.
- [Phiếu yêu cầu nguồn](a8-results/release-2026-11-22-scope/source-requests.md), [packet](a8-results/release-2026-11-22-scope/handoff.json), [việc còn thiếu](a8-results/release-2026-11-22-scope/worklist.json).
- [Kiểm tra bảo toàn](a8-results/release-2026-11-22-preservation.json): hash packet/rubric và chỉ số nghiệm thu trước–sau không đổi. Không sửa nguồn/nhãn/quyết định chính.
- [Kiểm tra lại sau UI](a8-results/release-2026-11-22-after-ui-preservation.json): packet/chỉ số chính vẫn không đổi. [Manifest artifact](a8-results/release-2026-11-22-manifest.json) ghi hash và kích thước các file kết quả mới để truy vết.

## Kết quả Agent và giới hạn

### 18 A.8

ID: A.8.1, A.8.2, A.8.3, A.8.5, A.8.7, A.8.8, A.8.9, A.8.10, A.8.12, A.8.13, A.8.15, A.8.16, A.8.17, A.8.19, A.8.20, A.8.22, A.8.24, A.8.32.

[Plan trước suy luận](a8-results/release-2026-11-22-a8-plan.json), [kết quả LLM](a8-results/release-2026-11-22-a8-result.json), [file từng control](a8-results/release-2026-11-22-a8-controls), [SoA/bảng xuất](a8-results/release-2026-11-22-a8-export/REPORT.md).

- Nguồn là runtime container lab `mixed`, rubric `a8-live-v2-active`, không phải doanh nghiệp sản xuất.
- 18 kết luận một phần phù hợp các facts true/false của snapshot. [Luật cùng snapshot](a8-results/release-2026-11-22-a8-rules.json) chỉ là kiểm tra nhất quán kỹ thuật, không phải người đánh giá.
- [So sánh với lượt cũ](a8-results/release-2026-11-22-a8-comparison.json): cùng recipe, hash nguồn 18 control thay đổi, trạng thái 18 control không đổi. Hash capture có cả thời gian; không suy đây là remediation hoặc nguồn mới độc lập. Lượt cũ được chọn là báo cáo lab, không phải lô nguồn doanh nghiệp 18/11.
- Lý do LLM vẫn cần rà: ví dụ A.8.1 đề cập mã hóa ổ đĩa trong khi phép thử chỉ kiểm tệp mẫu; A.8.2 diễn giải cờ review như một hành động phê duyệt bị từ chối. Không dùng kết luận cấu trúc đúng để khẳng định mọi lời giải thích đều có căn cứ. Schema hiện không có confidence; không tự thêm số confidence.

### 38 hồ sơ ngoài nhóm 18

[Manifest trước chạy](a8-results/release-2026-11-22-development/manifest.json), [snapshot](a8-results/release-2026-11-22-development/source-snapshot.json), [báo cáo](a8-results/release-2026-11-22-development/report.json), [audit từng tiêu chí](a8-results/release-2026-11-22-development/criterion-audit.json).

- 5 tuân thủ, 18 một phần, 3 không tuân thủ, 12 thiếu bằng chứng **theo dữ liệu mô phỏng**.
- Khớp khóa phát triển 23/38 ở cả lần đầu và cuối; không thử lại khi chỉ khác đáp án. Không tính tỷ lệ này là accuracy độc lập.
- Một tiêu chí khóa không đạt/model đạt; sáu khóa đạt/model chưa rõ; năm khóa chưa rõ/model không đạt; bảy khác biệt khác. Chưa xác định khóa hay model đúng bằng xác nhận chuyên môn.
- Runner mới lưu UUID trước chạy, snapshot khóa và nguồn; báo cáo lần chạy thực tế trước khi bổ sung UUID giữ nguyên. File `audit-compatible-report.json` là adapter dẫn xuất sau chạy, ghi rõ nguồn/hash và ID dẫn xuất, không giả là đăng ký trước.

[CSV tổng hợp 56 kết quả thực nghiệm](a8-results/release-2026-11-22-all56.csv) và [tổng hợp kiểm tra hai tập không trùng](a8-results/release-2026-11-22-all56-summary.json). Không gộp hai loại đối chiếu thành một tỷ lệ chung hoặc ghi vào SoA chính.

## Kiểm thử và lỗi giữ lại

- [Python JUnit lần đầu](a8-results/release-2026-11-22-python.xml), [sau chốt tương thích runner/audit](a8-results/release-2026-11-22-python-final.xml): 380 đạt, có cảnh báo thư viện cũ; không xóa test.
- [JavaScript](a8-results/release-2026-11-22-javascript.log): 14 đạt; [lint cuối không cảnh báo](a8-results/release-2026-11-22-lint-final.log), [build cuối](a8-results/release-2026-11-22-build-final.log). Hai escape dư ở test CSV đã sửa, giữ log lint trước sửa.
- [UI lần đầy đủ](a8-results/release-2026-11-22-ui.json): 11 đạt, ca mới lỗi do test chưa mở hai khối `details` cha. Sửa đúng thao tác mở, [chạy lại ca nguồn đạt](a8-results/release-2026-11-22-ui-source-retry.json). [Tổng hợp UI](a8-results/release-2026-11-22-ui-summary.json): 12 kịch bản khác nhau được kiểm chứng, không skip; không tuyên bố tất cả đạt trong cùng một lần. Ba trạng thái nguồn dùng GET mô phỏng; test kiểm không phát sinh ghi nguồn, packet/SoA chính không đổi.
- [API lần đầu](a8-results/release-2026-11-22-api.json) chưa đủ do thiếu hai biến mật khẩu tài khoản chấm; giữ báo cáo này. Cấp thông tin có sẵn qua môi trường tiến trình, không đổi mật khẩu: [lần sau 39 kiểm tra đạt](a8-results/release-2026-11-22-api-retry.json).
- [Ghi thật trên database riêng](a8-results/release-2026-11-22-isolated.json): đạt, đã dọn database thử, số dòng các bảng chính được theo dõi không đổi. Nhãn/phê duyệt trong test là mô phỏng, không gắn tên thành viên hoặc cộng vào chấm thật.
- Docker ban đầu chưa chạy nên API khởi động lỗi kết nối PostgreSQL; đã khởi động Docker và chạy lại API thành công, giữ log trong `work/release-2026-11-22.stderr.log` và `work/release-retry-2026-11-22.stderr.log`. Không thay cấu hình dữ liệu để né lỗi.
- [Kiểm tra ứng dụng sau build](a8-results/release-2026-11-22-startup.json): giao diện 8000/5173 và OpenAPI trả HTTP 200.

## Công cụ mới và cách chạy lại

```powershell
.venv\Scripts\python.exe scripts/export_scope_readiness.py --assessment-id 7f7c009b-bdcd-5b33-934e-15251ad2c976 --output-dir work/NEW-scope-export
.venv\Scripts\python.exe scripts/run_development_regression.py --output-dir work/development-lab/NEW-run --model qwen2.5:7b
.venv\Scripts\python.exe -m agent_core.assessment_comparison --before OLD-report.json --after NEW-report.json --output work/NEW-comparison.json
```

Chọn tên mới; công cụ chặn ghi đè. Đổi nội dung nguồn/recipe thì chốt plan mới trước suy luận. Không sao chép fixture thành bộ kiểm định độc lập.

File mã/test mới: `agent_core/assessment_comparison.py`, `scripts/export_scope_readiness.py`, `scripts/run_development_regression.py`, `tests/test_assessment_comparison.py`, `tests/test_scope_readiness_export.py`, `tests/test_development_regression.py`. Sửa `frontend-react/tests/acceptance-closure.spec.js` để kiểm UI nguồn mới. Tài liệu mới: báo cáo này, phiếu rà rubric và các artifact dẫn ở trên; cập nhật nhật ký tuần 6/7 đúng mốc bàn giao.

## Checklist trước và sau

Tám nhóm mục cần nguồn/xác nhận bên ngoài của tuần 6 **vẫn để `[ ]`**: chưa đủ bằng chứng để hoàn thành. Đã bổ sung/tích riêng phần kỹ thuật có minh chứng: export hiện trạng 56, so sánh hai lần chạy, runner 38 có snapshot và hồi quy UI. Không chuyển thành tích ngày 22/11 sang công việc tuần 7.

Để đóng các mục còn mở, nhóm cần: (1) nội dung xác nhận rubric/phạm vi/người chấm; (2) nguồn thật phù hợp cho các control thiếu và bộ kiểm định tách khỏi phát triển; (3) người chấm tự nộp kết luận/căn cứ; (4) người có trách nhiệm quyết định áp dụng, thẩm định và duyệt SoA. Hệ thống đã có luồng tiếp nhận, chạy lại và xuất báo cáo; không thể thay những đầu vào/xác nhận này bằng test đạt.
