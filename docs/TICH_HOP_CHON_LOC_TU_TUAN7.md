# Đối chiếu và tích hợp chọn lọc Tu/Tuan7 — 27/11/2026

Nguồn đã đọc: `origin/Tu/Tuan7`, commit `720943e` (lưu yêu cầu đánh giá và hoàn thiện báo cáo); README, AGENTS, CODEX_BUILD_SPEC, implementation status và mã interview/nda/asset_return/workflow/assessments. Nhánh này có kiến trúc `compliance_ai`/Streamlit/PostgreSQL riêng; main dùng React/FastAPI và phạm vi 56 control. Không ghép hai database hoặc thay main bằng nhánh khác.

| Phần mới trong nhánh Tú | Đối chiếu main | Quyết định tích hợp |
|---|---|---|
| Lưu yêu cầu đánh giá trước thực thi | Main có đợt/control/batch, chưa có phiếu mục đích và phạm vi riêng | Đã chuyển ý tưởng sang API/React hiện có, giữ baseline và lịch sử; không sao chép schema `app_data` |
| Hạn bàn giao theo ngày làm việc | Main đang giao hạn cụ thể theo từng hành động | Đã chuyển thuật toán `asset_return.return_due_date` thành preview lịch; chuyên viên áp dụng vào nháp nếu phù hợp |
| Phỏng vấn thích ứng, đào tạo và retest | Main chưa liên kết tài khoản người chấm với danh tính nhân viên thực hiện | Chưa nhập; cần ánh xạ danh tính, đồng thuận và nguồn kết quả riêng; không cho AI tự hoàn thành đào tạo |
| NDA theo phiên bản/hash và xác nhận nhân viên | Main có nguồn và review, chưa có luồng nhân viên xác nhận pháp lý | Chưa nhập; không coi một nút xác nhận mô phỏng là chữ ký thật hoặc bằng chứng hợp đồng |
| MFA enrollment/enforcement và quan sát nguồn riêng | Main có probe A.8 và review | Giữ luồng main; chưa nhập sự kiện mô phỏng làm bằng chứng IAM thật |
| Phiếu trả tài sản, biên nhận, đối chiếu người/thiết bị | Main có inventory và nguồn sau khắc phục | Tiếp nhận cách phân biệt yêu cầu/chờ/biên nhận/xác minh; chưa nhập adapter bàn giao của nhánh khác |
| Phê duyệt hai vai, dry-run, gate, rollback | Main đã có phiên bản, phân vai, nguồn trước/sau và chặn tự xác minh | Không ghép engine thao tác máy/rollback khác schema; chưa cho phép tác động host hoặc tài khoản thật |
| RAG, catalog 26, benchmark M1–M4 | Main dùng catalog/rubric 56 và benchmark riêng | Giữ phạm vi 56. Không thay bằng 26 hoặc dùng trọng số 60/20/20 như ngưỡng ISO |
| Gap/SoA/Remediation reports | Main đã có JSON/CSV/HTML/PDF/XLSX và SoA gate | Giữ engine xuất hiện hành; không nhập số liệu benchmark nhánh khác vào kết quả main |

## Đã bổ sung vào main

### Yêu cầu đánh giá

Mở **Tổng quan 56 control → Yêu cầu đánh giá · lưu mục đích và phạm vi**. Tư vấn/quản trị doanh nghiệp nhập tên, mục tiêu, control và căn cứ. API kiểm tenant, vai trò, ID duy nhất trong phạm vi 56; lưu rubric hash và baseline token/kết luận từng control. Hồ sơ lưu không tự chạy model hoặc tự xác nhận đạt.

Từ yêu cầu bấm control để mở nguồn hiện hành và dùng quy trình đánh giá/thẩm định đã có. Hủy yêu cầu giữ nguyên baseline/history; kiểm version 409 và quyền người lập/tư vấn. Trạng thái phiếu REQUESTED/CANCELLED là trạng thái tiếp nhận, **không phải tiến độ thực thi Agent**; xem batch/kết quả ở luồng hiện có.

Migration cộng thêm `enterprise_assessment_requests` (UUID, assessment FK, người tạo FK, version, JSONB, created_at) trong init_teamwork. API dưới `/api/assessments/{id}/enterprise/assessment-requests`: GET, POST, POST `/{request_id}/cancel`. Không có endpoint xóa lịch sử.

### Gợi ý hạn

Trong hành động chờ duyệt: **Gợi ý hạn theo ngày làm việc**. Nhập mốc có thời gian/múi giờ, số ngày và tham chiếu chính sách. Server chuẩn hóa UTC+7, tính thứ Hai–thứ Sáu (ngày 0 giữ ngày mốc; ngày 1 là ngày làm việc tiếp theo). Chưa loại lịch nghỉ lễ. Chỉ tư vấn được gọi `/remediation/deadline-preview`; kết quả `saved=false`.

Nút áp dụng chỉ điền hạn và căn cứ vào kế hoạch nháp; vẫn cần thao tác duyệt/giao cũ. Chính sách là người dùng khai, không phải quy định ISO mặc định. Không tự chọn mốc nghỉ việc, tự xác nhận trả tài sản, tự sửa máy hoặc tự giao hạn thay người phụ trách.

File chuyển thuật toán: `backend/business_deadline.py`; UI `BusinessDeadline.jsx`, nối vào RemediationWorkspace. Nguồn thuật toán ghi trong docstring và tài liệu này.

## Kiểm chứng

- [476 Python](a8-results/tu-tuan7-selective-python-final-2026-11-27.xml): các file test được Git theo dõi trên main + test mới. File test còn lưu từ nhánh Tú không được coi là test của main; không xóa chúng để làm xanh kết quả.
- Lint/build đạt. [Ba UI](a8-results/tu-tuan7-selective-ui-final-2026-11-27.json): tạo/hủy yêu cầu bằng API mock, client và khắc phục. [UI gợi ý hạn](a8-results/tu-tuan7-deadline-ui-2026-11-27.json): nhận hạn server mock và điền đúng form, chưa tự duyệt.
- [Ghi thật cô lập](a8-results/tu-tuan7-selective-isolated-final-2026-11-27.json): PostgreSQL/API/Qwen thật, tạo/hủy yêu cầu, stale version, cross-tenant, hạn gợi ý, quyền vai trò và yêu cầu tồn tại sau restart. Fixture synthetic không phải chấm/thẩm định thật.
- [UI lần đầu](a8-results/tu-tuan7-selective-ui-2026-11-27.json) lỗi locator label chứa option text; đã dùng accessible listbox role và chạy lại. Không bỏ test hoặc đổi đáp án.

Các luồng interview/NDA/MFA/biên nhận/rollback chưa được nhập và không đánh dấu hoàn thành. Đây là lựa chọn tích hợp phù hợp dữ liệu hiện hành, không tuyên bố đã gộp mọi tính năng của nhánh Tú. Dữ liệu/chấm/phê duyệt thật vẫn cần đúng người thực hiện.

Cập nhật tiếp 27/11: bốn luồng nhân viên đã được triển khai riêng trên main; xem [hướng dẫn và giới hạn](TICH_HOP_LUONG_NHAN_VIEN_TU_TUAN7.md). Phần chưa tích hợp nêu trên là trạng thái của lần tích hợp đầu.
