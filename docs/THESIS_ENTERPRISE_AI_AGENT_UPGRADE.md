# Nâng cấp AI Agent đánh giá tổng thể nhiều doanh nghiệp

Cập nhật 26/11/2026. Tài liệu phân biệt chức năng đã chạy, kết quả phát triển và phần còn cần dữ liệu/nghiệm thu chuyên môn. Không coi toàn bộ prompt đã hoàn thành chỉ vì có code.

## 1. Mục tiêu đề tài

Xây dựng hệ thống AI Agent đánh giá tuân thủ an toàn thông tin theo ISO/IEC 27001:2022 từ bằng chứng, quản lý phát hiện–khắc phục–xác minh và lịch sử nhiều kỳ. Phạm vi đồ án giữ **56 control: 8 A.6, 14 A.7, 34 A.8**; 18 A.8 là nhóm thực nghiệm sâu, không phải toàn bộ ISMS/Annex A hay dịch vụ chứng nhận.

## 2. Đối chiếu yêu cầu

| Yêu cầu | Đã có trước | Mức đáp ứng / nâng cấp ngày 26/11 | Phần chưa hoàn tất |
|---|---|---|---|
| Nhiều doanh nghiệp | Khách hàng/đợt/membership, CRUD danh mục | Giữ API hiện hành; kiểm tenant cho tìm kiếm/timeline/snapshot; dữ liệu mô phỏng có classification riêng | Chưa vận hành trên khách hàng thật hoặc kiểm định multi-tenant bên ngoài |
| Nhân sự/phòng ban/tài khoản/tài sản/phần mềm | Danh mục liên kết theo assessment | Generator 30/100/500 người, nhiều phòng ban; importer nạp người/tài khoản/tài sản qua API vào **khách hàng mới** | Không tự suy hợp đồng, MFA, mã hóa hoặc kết luận từ khai báo danh mục |
| Nguồn tiêu chuẩn | Catalog/rubric 56 + sổ yêu cầu có nguồn/phiên bản/quyền sử dụng | Tái sử dụng, không nhập chuẩn có bản quyền | Toàn văn/luật/chuẩn được cấp phép và xác nhận chuyên môn do nhóm cung cấp |
| Nhiều file | Một file hoặc connector thư mục | UI tối đa 100 file/lần, tuần tự, ghi từng kết quả, tiếp tục khi file lỗi, kiểm trùng nội dung trong lô và server | Lô upload không chạy nền khi đóng trang; không có hàng đợi upload phân tán |
| Định dạng | PDF/DOCX/TXT/CSV/JSON/log… | Thêm XLSX read-only; không thực thi công thức; chặn giải nén/nội dung quá lớn | Ảnh/PDF scan cần OCR ngoài; chưa triển khai OCR và không giả vờ đã đọc ảnh |
| Tìm nhiều nguồn | Thu và gắn nguồn theo control | PostgreSQL full-text `simple`, bắt buộc tenant và tùy chọn control, ID/hash/trích đoạn/giới hạn kết quả | Không phải embedding/vector search hoặc truy xuất ngữ nghĩa đã benchmark |
| Agent tổng thể | Graph đánh giá từng control + batch server tối đa 56 + dossier/SoA | Tái dùng để điều phối nhiều control, nhiều nguồn đúng đợt; timeline tổng hợp từ kết quả lưu | Chưa chứng minh LLM đọc/tổng hợp toàn bộ 1.000 file; giữ input budget, không cắt ngầm |
| Dữ liệu theo thời gian | Nhiều đợt và lịch sử từng control | Ngày bắt đầu/kết thúc + loại kỳ, so sánh trạng thái, công thức tỷ lệ, bản lưu kỳ bất biến/idempotent | So sánh trạng thái không tự chứng minh cải thiện nhân quả hoặc rubric/phạm vi tương đương |
| Dữ liệu mô phỏng | Lab và bộ phát triển cũ | Generator deterministic nhiều kỳ + hash manifest; ZIP web; importer/preflight/receipt; dọn thư mục sinh có guard | Bộ sinh không phải dữ liệu người thật hay bộ kiểm định độc lập |
| Phát hiện/khắc phục | Baseline, Qwen nháp, giao việc/phối hợp, nguồn sau, thẩm định/xác minh | Giữ và hồi quy xuyên suốt trên DB riêng | Chưa thay được chuyên viên xác nhận nguyên nhân/rủi ro/phê duyệt |
| Độ đúng AI | Chấm mù, phân loại hỗ trợ, đối chiếu từng người | Giữ khóa nguồn/report/hash và nhãn cũ | Không công bố accuracy/F1 độc lập mới khi chưa có chuyên gia và bộ held-out hợp lệ |
| Hiệu năng | Input budget + batch durable | Đã đo intake 10/100/500/1.000 file, duplicate/error và lexical index | Chưa đo tải nhiều người dùng, PostgreSQL 1.000 file, OCR, GPU hoặc LLM end-to-end trên bộ lớn |

## 3. Kiến trúc hiện tại

React/Vite → API FastAPI → PostgreSQL và kho bản gốc theo assessment → collector/quality → LangGraph/Qwen → kết quả/history → dossier/SoA → remediation. Tài khoản phải có membership đúng đợt trước khi đọc/tải nguồn hoặc xem kết quả. Có phân vai consultant/verifier/business_admin/operator và kiểm quyền backend.

## 4. Kiến trúc nâng cấp

Mở rộng các module sẵn có; không tạo hệ đánh giá song song:

- `team_api.py`, `teamwork.py`: timeline, loại/ngày kỳ, snapshot append-only, tải gói mô phỏng.
- `enterprise_comparison.py`: công thức và so sánh trên dữ liệu được phép xem, fingerprint bỏ trường sinh báo cáo nhưng giữ nguồn/kết luận/thẩm định.
- `source_search.py`: lexical retrieval theo tenant/control, trích đoạn chỉ hỗ trợ tìm nguồn.
- `document_parser.py`, `control_packages.py`, `source_intake.py`: XLSX đi cùng luồng kiểm chất lượng và giữ bản gốc hiện có.
- `generate_enterprise_dataset.py`, `import_enterprise_dataset.py`, `benchmark_enterprise_intake.py`: nguồn phát triển có nguồn gốc, nạp qua API, phép đo riêng.
- UI: `EnterpriseTimeline`, `EnterpriseDatasetTools`, `EnterpriseSourceSearch`, `MultiSourceIntake`, nối các màn hình hiện có.

Migration cộng thêm: `assessment_campaigns.period_metadata`, bảng `enterprise_period_snapshots` (ID, assessment, người tạo, fingerprint nguồn, JSONB, thời điểm, unique assessment/fingerprint), index `(assessment_id,control_id)` trên evidence. Không DROP, không đổi nhãn hoặc xóa lịch sử cũ. [Kiểm migration và API local](a8-results/enterprise-main-migration-2026-11-26.json): số dòng bảng chính theo dõi giữ nguyên, không thêm client/snapshot mô phỏng vào DB chính.

## 5. Nguồn dữ liệu

Ba lớp tách biệt: **rubric/knowledge dự án**, **nguồn doanh nghiệp nộp**, **fixture mô phỏng**. Tài liệu chính sách không tự chứng minh triển khai. Hash xác nhận bản lưu khớp, không xác nhận tính thật. Không có nguồn không tự suy thành vi phạm. Nguồn có thời điểm không đồng nghĩa còn hiệu lực; thời hạn phải theo tiêu chí/nguồn đã được chấp nhận, không áp một tuổi nguồn chung cho mọi control.

## 6. Cơ chế mô phỏng

Generator tạo số doanh nghiệp/quy mô/tháng/seed tùy chọn, manifest hash, profile, nhân sự–tài khoản–thiết bị, hồ sơ screening, backup và quan sát mâu thuẫn. Các kỳ đầu/giữa/sau có khác biệt; một số người nghỉ việc đã thu hồi tài khoản, một số chưa; sau tháng thứ sáu có tình huống phục hồi. Có đủ các scenario compliant/noncompliant/partial/missing/stale/conflict **ở cấp thiết kế tình huống**, không tự gán nhãn đạt toàn bộ control.

Đã sinh và kiểm hash **507 file, 3 doanh nghiệp 30/100/500 người, 24 tháng**, tương đương 72 kỳ và 15.120 dòng người–kỳ. [Biên nhận](a8-results/enterprise-generated-24months-2026-11-26.json). Bộ lớn được lưu dưới `work/enterprise-demo-v2-2026-11-26`, không đưa hàng trăm fixture vào Git hoặc nạp vào hồ sơ chính.

## 7. Doanh nghiệp cung cấp dữ liệu

Trong hồ sơ control, chọn loại bằng chứng và nguồn gốc; nộp một hoặc nhiều file. UI nhiều file: tối đa 100 file/lần, 100MB tổng, 15MB/file. Có trạng thái riêng từng file, dừng sau file hiện tại, không bỏ cả lô chỉ vì một file lỗi. Dùng lại API upload có xác thực/hash/bản gốc/chống trùng. Không tự phân loại control từ tên file; người dùng chọn phạm vi đúng trước khi nộp. Hỗ trợ CSV cho dữ liệu cấu trúc; XLSX không thực thi macro/công thức.

## 8. AI dùng dữ liệu như thế nào

Agent nhận assessment/control, đọc nguồn đúng đợt và rubric, kiểm chất lượng, suy luận có schema/guard, lưu ID/hash/lý do/lỗi. Batch điều phối nhiều control, không gộp mất nguồn gốc. Tìm kiếm mới chỉ hỗ trợ người dùng định vị bằng chứng; **chưa tự thay collector bằng top-k rồi tuyên bố model đã đọc tất cả nguồn**. Input vượt budget vẫn trả lỗi cần chia phạm vi; đây là giới hạn được giữ để tránh cắt ngầm.

## 9. Train model hay RAG

Không cần train lại Qwen khi thêm doanh nghiệp. Dữ liệu doanh nghiệp là input truy xuất, không tự đưa vào huấn luyện. Knowledge base là catalog/rubric/sổ yêu cầu; metadata là tenant/control/kỳ/hash/xuất xứ. Embedding chuyển đoạn văn thành vector; vector search tìm gần nghĩa; bản mới dùng lexical full-text, chưa cài embedding/vector DB. RAG là truy xuất nguồn liên quan rồi cung cấp cho model; không đồng nghĩa fine-tuning. Fine-tuning chỉ nên cân nhắc sau khi có bộ nhãn hợp lệ, quyền dùng dữ liệu và bằng chứng rằng prompt/truy xuất chưa đủ; hiện chưa có lý do triển khai.

## 10. Multi-enterprise và bảo mật

API timeline/search kiểm membership ngay tại backend. Mọi truy vấn tìm nguồn có assessment filter. Snapshot chỉ thuộc doanh nghiệp/đợt được phép xem; biết ID doanh nghiệp khác vẫn 403. Importer chỉ tạo khách hàng **mới**, đánh dấu `synthetic_development`, không nhận ID đợt có sẵn để ghi đè. Không đổi classification từ mô phỏng thành dữ liệu thật bằng API sửa profile. Design-key không được upload hoặc dùng làm nhãn con người.

## 11. Dữ liệu nhiều kỳ

Đợt có ngày bắt đầu/kết thúc hợp lệ và loại initial/monthly/quarterly/annual/ad_hoc/reassessment. Timeline sắp theo ngày kỳ (fallback ngày tạo cho đợt cũ). Kết quả hiện hành được tính từ dữ liệu lưu; **Chốt bản lưu kỳ** giữ bản scope/summary/fingerprint riêng, không ghi đè. Lặp chốt cùng fingerprint trả cùng ID. Khi nguồn/thẩm định/kết luận đổi, phải tải lại; hash cũ bị chặn. Chốt kỳ không khóa source, không duyệt SoA, không thay chứng nhận.

## 12. Workflow Agent

Chọn doanh nghiệp/kỳ → cung cấp nguồn → kiểm chất lượng → chạy lô trên nguồn hiện hành → từng control nhận kết luận/ID/hash → tổng hợp độ phủ → tư vấn rà phát hiện → AI nháp phương án → người duyệt giao việc → thực hiện/nguồn mới → đánh giá lại → người khác thẩm định/xác minh → so sánh/chốt bản lưu → báo cáo. Kết quả trước, lỗi ban đầu và các nhãn khóa không sửa để tăng điểm.

## 13. Tổng hợp và công thức

Gọi N là số control trong phạm vi, X là số có quyết định loại trừ được ghi, C là số máy kết luận tuân thủ hiện hành; A là số đã đánh giá với trạng thái compliant/partial/noncompliant/insufficient. Tỷ lệ C/(N−X)×100; độ phủ A/(N−X)×100. Mẫu số 0 trả null; control chưa chạy và kết quả cũ/lỗi được tách riêng. Loại trừ là **quyết định đã ghi**, không tự khẳng định đã được duyệt SoA.

Không cộng confidence vào tỷ lệ này. Không coi tỷ lệ máy là accuracy, tỷ lệ đầy đủ ISMS hoặc tỷ lệ chứng nhận. Human-review-current đếm riêng; chưa có chuyên gia thì không tự tạo precision/recall/F1. Thay đổi trạng thái giữa kỳ luôn kèm lưu ý đối chiếu rubric/phạm vi/nguồn trước khi nói cải thiện.

## 14. Phát hiện và khắc phục

Dùng remediation hiện có: nhiều hành động mỗi phát hiện, task/người chính/phối hợp/hạn, baseline bất biến, nguồn sau, lịch sử xác minh. Người thực hiện không tự xác minh. Đạt phải có chính người xác minh thẩm định hiện hành viện dẫn nguồn sau. Theo dõi trạng thái chờ/làm lại/một phần/đạt; đóng việc không tự đổi control hoặc SoA.

## 15. Chức năng đã nâng cấp

- UI nguồn nhiều file + XLSX trong cả web intake và connector thư mục.
- Tìm nguồn lexical theo tenant/control với ID/hash/trích đoạn.
- Timeline nhiều kỳ + metadata ngày/loại kỳ + snapshot bất biến.
- Generator CLI/ZIP web, validator và dọn thư mục sinh có guard.
- Import qua API có preflight và receipt từng khách hàng/kỳ/file; nạp cả danh mục liên kết. Không nạp design keys, không gọi model hoặc tạo review/approval.
- Benchmark intake/search Python 10–1.000 file, ghi riêng duplicate/rejected; không lẫn với điểm AI.

## 16. Kiểm thử

- [Python release](a8-results/enterprise-upgrade-python-release-2026-11-26.xml): 464 đạt; 14 JavaScript, lint/build đạt. Test fingerprint, period dates, XLSX, tenant search, generator deterministic/liên kết/tamper/cleanup và import preflight.
- [Ghi thật](a8-results/enterprise-upgrade-isolated-release-2026-11-26.json): HTTP/PostgreSQL/Qwen/UI trên database tạm, nhập bộ 6 người × 2 tháng, nộp nhiều file có trùng/lỗi, tìm đúng tenant, timeline, snapshot stale/idempotent, nguyên luồng khắc phục và restart. Database thử được dọn, bảng chính theo dõi không đổi.
- [Hồi quy UI](a8-results/enterprise-upgrade-ui-final-2026-11-26.json): 17 kịch bản; form/API mock được tách khỏi luồng ghi thật ở trên. [Lần UI trước](a8-results/enterprise-upgrade-ui-2026-11-26.json) có lỗi locator trùng nhãn “Cách kiểm tra lại” khi doanh nghiệp chính có nhiều kế hoạch. Đã làm rõ nhãn tư vấn, giữ nhãn quyết định hiện có và chạy lại, không xóa test.
- [Lần ghi thật đầu](a8-results/enterprise-upgrade-isolated-first-2026-11-26.json), [lần bổ sung](a8-results/enterprise-upgrade-isolated-final-2026-11-26.json) giữ lịch sử riêng. Lúc đầu dịch vụ PostgreSQL/Ollama đang tắt; đã bật container/volume hiện có, không tạo database chính mới hoặc xóa volume.

## 17. Kết quả hiệu năng

[Báo cáo benchmark](a8-results/enterprise-intake-benchmark-2026-11-26.json):

| File | Trích xuất | Trùng | Bị từ chối | Thời gian giây | Peak Python allocation |
|---|---:|---:|---:|---:|---:|
| 10 | 9 | 0 | 1 | 0,050 | 84.463 B |
| 100 | 84 | 11 | 5 | 0,308 | 412.678 B |
| 500 | 420 | 62 | 18 | 1,553 | 1.680.091 B |
| 1.000 | 844 | 122 | 34 | 2,299 | 2.459.900 B |

Đây là TXT tổng hợp được tạo để đo extraction/dedupe/index lexical trong Python. CPU seconds có trong JSON; memory là `tracemalloc`, **không phải RSS tổng của tiến trình**. Model calls = 0. Không suy từ bảng này rằng LLM hoặc PostgreSQL đã đánh giá 1.000 file, cũng không suy throughput production.

## 18. Giới hạn còn lại

Chưa có: OCR ảnh/scan; vector/semantic retrieval tích hợp; map-reduce LLM bảo toàn đầy đủ 1.000 nguồn; benchmark model trên toàn bộ bộ 507 file; vận hành nhiều người dùng/HA; bộ kiểm định chuyên gia mới. Toàn văn chuẩn/pháp lý và nguồn cho 37 control còn thiếu vẫn cần nhóm cung cấp. Các mẫu mô phỏng là dữ liệu phát triển đã biết, không phải held-out độc lập. Không tự tạo approval hoặc đo accuracy con người từ design key.

Dọn dữ liệu hiện hỗ trợ thư mục generated dưới work với manifest/hash và không có file lạ/link. Chưa cung cấp xóa cascade khách hàng/kỳ đã có audit qua UI; giữ dữ liệu theo nguyên tắc không mất lịch sử. Nếu muốn dọn demo trong DB, dùng môi trường cô lập đã tạo/dọn bằng runner, không xóa nhầm doanh nghiệp thật.

## 19. Hướng sử dụng và phát triển

Xem [hướng dẫn dữ liệu mô phỏng](SYNTHETIC_DATA_GUIDE.md) và [pipeline](AI_AGENT_DATA_PIPELINE.md). Mở Doanh nghiệp → Khách hàng → sinh ZIP hoặc so sánh kỳ; Tổng quan56 → tìm bằng chứng; hồ sơ control → nộp nhiều file. Sau khi nhập, chạy batch hiện có tối đa 56 control có nguồn; không tự chạy khi chỉ tải ZIP hoặc import danh mục.

Ưu tiên tiếp theo cần nguồn thực tế: rubric/phạm vi được xác nhận, nguồn còn thiếu, bộ held-out có lịch sử tiếp xúc và nhãn chuyên gia; sau đó mới đo AI và cân nhắc semantic retrieval/map-reduce theo số liệu. Không thay giới hạn input bằng cắt nguồn âm thầm.

## 20. Kết luận

Đã triển khai và kiểm chứng thêm nền tảng nhiều nguồn/nhiều kỳ/dữ liệu mô phỏng và so sánh có nguồn gốc, tiếp tục dùng Agent và vòng đời khắc phục hiện có. Chưa tuyên bố đáp ứng trọn mọi mục của prompt hoặc sử dụng production/chứng nhận ISO. Các giới hạn ở mục 18 là việc còn mở, không được đánh dấu hoàn thành bằng dữ liệu tạo sẵn.
