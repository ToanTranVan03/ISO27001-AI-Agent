# Tuần 7 — Kiểm tra liên kết, nghiệm thu theo đề tài và chuẩn bị bảo vệ

- Thời gian: **23/11/2026–29/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Đang thực hiện — đã kiểm tra liên kết, nghiệm thu theo đề tài và chuẩn bị hồ sơ bảo vệ (25/11).**
- Lập kế hoạch và cập nhật: **22/11/2026** (Chủ nhật cuối tuần 6).

## Mục tiêu và kế hoạch

Giữ phạm vi 56 control Annex A (8 A.6, 14 A.7, 34 A.8). Tuần 7 **không xây thêm chức năng mới** (chỉ sửa lỗi thật). Trọng tâm: kiểm tra liên kết toàn hệ thống, nghiệm thu theo mục tiêu đề tài và chuẩn bị hồ sơ bảo vệ đồ án.

**Việc đã làm (có minh chứng, xem nhật ký bên dưới):**

- [x] Kiểm tra liên kết và đồng bộ toàn hệ thống; sửa lỗi phát hiện và bổ sung test hồi quy.
- [x] Nghiệm thu theo mục tiêu đề tài: ma trận 56 control, đánh giá năng lực AI Agent, 10 tình huống độc lập (kiểm thử kỹ thuật).
- [x] Soạn hồ sơ bảo vệ: kiến trúc, test case nghiệm thu, kịch bản demo 15 phút + dữ liệu demo, đề cương báo cáo, slide, câu hỏi phản biện.

**Việc còn lại trong tuần:**

- [ ] Chạy thử kịch bản demo 15 phút trên giao diện, điền cột "Kết quả thực tế / Pass-Fail / Minh chứng" trong bộ test case nghiệm thu (chỉ điền khi đã chạy thật).
- [ ] Chụp ảnh màn hình cho slide và báo cáo; dựng slide từ đề cương.
- [ ] Viết nội dung báo cáo đồ án theo đề cương 6 chương.
- [ ] Gửi giảng viên xem hồ sơ; ghi nhận góp ý, người/ngày xác nhận.

**Phụ thuộc người thật — không tự hoàn thành thay** (chuyển tiếp từ tuần 6, vẫn mở): bổ sung nguồn cho 37 control thiếu và thay nguồn A.6.2; bộ kiểm định và người chấm độc lập; 56 quyết định tính áp dụng; thẩm định và phê duyệt SoA.

Chỉ tích hoàn thành khi có kết quả thực tế; chạy Agent xong không đồng nghĩa control tuân thủ.

## Nền tảng bàn giao từ tuần 6

Đây là trạng thái tại mốc bàn giao **21–22/11**, không phải thành tích thực hiện tuần 7:

- Đã hoàn thiện [vòng đời tư vấn/khắc phục](../docs/TU_VAN_VA_KHAC_PHUC_ISO.md), [nâng cấp theo s.txt](../docs/HOAN_THIEN_THEO_S_TXT_2026_11_22.md) và [nghiệm thu toàn diện](../docs/FINAL_ACCEPTANCE_2026.md): quản lý nhiều khách hàng/đợt riêng (`inventory_mode = 'client'`, bắt đầu rỗng), khai báo danh mục doanh nghiệp có snapshot, profile ISMS, baseline phát hiện, AI tư vấn có cấu trúc chi tiết + câu hỏi làm rõ, giao việc người chính/phối hợp/bước con, nguồn sau, xác minh độc lập, sổ rủi ro 5×5 & sổ yêu cầu có nguồn, dashboard 3 góc nhìn, thông báo hộp thư + tùy chọn SMTP an toàn, báo cáo trước–sau PDF/XLSX/CSV/HTML/JSON và `/api/health`, PostgreSQL lưu qua restart. Đợt chính giữ nguyên không chèn hồ sơ giả; các giới hạn ngoài phạm vi đồ án (toàn văn tiêu chuẩn bản quyền, điều khoản ISMS 4–10/A.5, hình ảnh/OCR, hàng đợi phân tán HA) được ghi rõ trong tài liệu nghiệm thu.
- Bổ sung gate SoA chặn quyết định thiếu/sai kiểu tính áp dụng; đã kiểm Edge cho lý do khóa nút thiếu nguồn và điều hướng mở hồ sơ; giữ nguyên các mục chờ nguồn/quyết định thật.
- **Hành động khắc phục (hoàn thành 22/11, commit lúc 18:18–21:12):** từ phát hiện (control, khoảng cách, địa điểm/tài sản, giả thuyết nguyên nhân, ưu tiên rủi ro → lưu phát hiện và baseline), bấm "AI đề xuất có cấu trúc — chờ từ chối/duyệt" để sinh thẻ **Hành động khắc phục**. Mở "Phân tích tư vấn / thông tin cần xác minh" sẽ thấy: sai gì, thiếu gì, checklist việc phải làm, bằng chứng cần nộp thêm và điều kiện nghiệm thu để đạt chuẩn; kèm câu hỏi làm rõ. Người duyệt chấp nhận/từ chối, giao người chính/phối hợp/bước con, có hạn và thông báo; người thực hiện nộp nguồn sau, người khác xác minh độc lập rồi mới đánh giá lại. Đã thêm hướng dẫn mở khóa phát hiện và mở sẵn khung phân tích trên giao diện.
- Đã có CLI và web kiểm tra trước tệp nguồn ngày 22/11, không nhập database và không gọi Agent. Dùng khi nhóm cung cấp nguồn mới theo [hướng dẫn](../docs/KIEM_TRA_NGUON_TRUOC_KHI_NOP.md); các mục chờ nguồn/xác nhận vẫn mở.
- Đã có luồng quản lý 56 control, thu/kiểm toàn vẹn nguồn, Agent chạy lô, chấm mù, thẩm định, báo cáo và SoA dự thảo; có nhập quyết định/kế hoạch theo lô và điều hướng bốn màn hình.
- Kiểm chứng mới nhất cuối ngày 22/11: **442 test Python, 14 JavaScript, 17 kịch bản giao diện Edge**, lint/build đạt; API 39 kiểm tra ba tài khoản và kiểm thử xuyên suốt ghi thật PostgreSQL + Qwen2.5:7b + UI qua khởi động lại trên database riêng đạt. Xem [báo cáo nghiệm thu cuối cùng](../docs/FINAL_ACCEPTANCE_2026.md), [hoàn thiện theo s.txt](../docs/HOAN_THIEN_THEO_S_TXT_2026_11_22.md) và [báo cáo khóa sổ 22/11](../docs/HOAN_THIEN_TUAN_06_2026_11_22.md); không chuyển công việc này thành thành tích tuần 7.
- Đã chạy lại 18 A.8 lab và 38 hồ sơ mô phỏng ngày 22/11, không lỗi kỹ thuật cuối; bộ 38 khớp khóa phát triển 23/38, còn 15 lệch tổng và 19 lệch tiêu chí. Có công cụ so sánh hai lượt và xuất hiện trạng nguồn 56; đây vẫn là thực nghiệm phát triển, chưa phải độ đúng độc lập.
- Bổ sung ngày 22/11: thống nhất kiểm tra nội dung ở connector thư mục/web, 385 test Python đạt; quét 56 thư mục chưa có nguồn mới hợp lệ. Không chuyển phần đã làm này thành nhiệm vụ tuần 7 hoặc coi các nguồn thiếu đã được bổ sung.
- Đợt chính: 19 control có nguồn ngoài preset, 18 qua ngưỡng nội dung; 37 thiếu nguồn và A.6.2 cần thay. Có 0 quyết định áp dụng, 0 thẩm định hiện hành; rubric/SoA chưa được phê duyệt ở mốc bàn giao.
- 38 hồ sơ do trợ lý tạo và gói ứng viên kỹ thuật là dữ liệu phát triển/hồi quy; không thay bộ kiểm định độc lập hoặc nguồn được người phụ trách chấp nhận.

## Nhật ký công việc chính

| Ngày | Ý chính | Kết quả / minh chứng |
|---|---|---|
| 25/11/2026 (sáng) | Kiểm tra toàn diện tính liên kết và đồng bộ hệ thống (khách hàng–đợt–control–bằng chứng–finding–khắc phục–xác minh–dashboard–báo cáo). | [INTEGRATION_AUDIT_2026.md](../docs/INTEGRATION_AUDIT_2026.md), `tests/test_integration_audit_2026.py` |
| 25/11/2026 | Sửa lỗi phát hiện khi audit: `record_id` của `context` và đồng bộ tên doanh nghiệp (`backend/team_api.py`); đồng bộ `human_review_current` lên kết luận dashboard (`backend/remediation.py`); làm mới UI theo revision ở `RemediationWorkspace.jsx`, `RemediationNotifications.jsx`. | Test hồi quy đạt |
| 25/11/2026 | Kiểm tra lại luồng hành động khắc phục từ đầu đến cuối: phát hiện → AI đề xuất → duyệt → giao việc → nộp nguồn sau → xác minh độc lập → đánh giá lại → dashboard/báo cáo. Sửa để kết luận sau thẩm định (`human_review_current`) hiện đúng trên dashboard, thẻ hành động và thông báo tự làm mới khi có revision mới. | `backend/remediation.py`, `RemediationWorkspace.jsx`, `RemediationNotifications.jsx`; [INTEGRATION_AUDIT_2026.md](../docs/INTEGRATION_AUDIT_2026.md) |
| 25/11/2026 | Chuẩn bị hồ sơ bảo vệ: báo cáo kiến trúc + sơ đồ Mermaid, bộ test case nghiệm thu (không tự điền Pass), kịch bản demo 15 phút + dữ liệu demo tách khỏi đợt chính, đề cương báo cáo 6 chương, 18 slide, 28 câu hỏi phản biện. | [docs/defense/](../docs/defense/) |
| 25/11/2026 | Nghiệm thu theo mục tiêu đề tài: xác minh 56 control/rubric khớp 1–1; chạy 10 tình huống AI độc lập (IND-01…IND-10B) với `qwen2.5:7b`, guardrail và schema đạt; lập checklist trước buổi bảo vệ. | [THESIS_FINAL_VALIDATION.md](../docs/THESIS_FINAL_VALIDATION.md), [AI_EVALUATION.md](../docs/thesis-validation/AI_EVALUATION.md), [TEST_CASES.md](../docs/thesis-validation/TEST_CASES.md), [DEMO_CHECKLIST.md](../docs/thesis-validation/DEMO_CHECKLIST.md) |
| 25/11/2026 | Bổ sung `tests/test_thesis_final_validation.py`, `tests/test_final_acceptance_2026.py`; cập nhật README liên kết các tài liệu mới. | **449 test Python**, 14 test JavaScript đạt; oxlint 0 lỗi; build production đạt |

## Kết quả và minh chứng

- Hệ thống liên kết xuyên suốt sau khi sửa 3 nhóm lỗi đồng bộ; bộ hồ sơ bảo vệ và báo cáo nghiệm thu theo đề tài đã sẵn sàng.
- 10 tình huống độc lập là kiểm thử kỹ thuật (guardrail/schema), **chưa** thay nhãn của người đánh giá đủ điều kiện; các mục checklist phía trên vẫn chờ nguồn và xác nhận chuyên môn thật.

Tài liệu để tiếp tục:

- [Nhật ký tuần 6](TUAN_06.md): công việc và minh chứng đã có.
- [Hồ sơ bảo vệ](../docs/defense/), [nghiệm thu theo đề tài](../docs/THESIS_FINAL_VALIDATION.md), [kiểm tra liên kết](../docs/INTEGRATION_AUDIT_2026.md): tài liệu chính của tuần 7.
- [Hướng dẫn nhóm chốt việc](../docs/HUONG_DAN_CHOT_VIEC_TUAN_06.md), [phiếu nguồn theo nhóm](../docs/CHOT_VIEC_TUAN_06_2026_11_21.md): hồ sơ và xác nhận cần cung cấp; cập nhật lại khi nguồn thay đổi.
- [Nhập quyết định/kế hoạch theo lô](../docs/NHAP_QUYET_DINH_KE_HOACH_THEO_LO.md), [điều kiện duyệt SoA](../docs/DIEU_KIEN_DUYET_SOA_56.md): thao tác và điều kiện hoàn tất.
- [Toàn vẹn nguồn](../docs/KIEM_TRA_TOAN_VEN_NGUON.md), [ma trận UI](../docs/MA_TRAN_NGHIEM_THU_UI_TUAN_06.md): phạm vi kiểm tra và giới hạn kỹ thuật.

## Vướng mắc và giới hạn

- Đến 25/11 nhóm vẫn chưa cung cấp nguồn mới, bộ kiểm định hoặc xác nhận chuyên môn; không tự tạo phê duyệt hay nhãn độc lập thay người thật.
- Dữ liệu demo bảo vệ là doanh nghiệp giả lập, tách khỏi đợt đánh giá chính; không dùng làm kết quả đánh giá thực tế.
- Probe lab chỉ kiểm tra tiêu chí đại diện; hash khớp không chứng minh nguồn thật hoặc đủ nội dung control.
- Chốt kiểm thử các luồng UI chính không đồng nghĩa bao phủ mọi ngoại lệ hoặc nghiệm thu chuyên môn. Giữ lịch sử lỗi, nhãn khóa và tách dữ liệu thử khỏi đợt chính.

## Việc chuyển tiếp sang tuần 8

Chưa chốt. Rà kết quả cuối tuần 7 rồi xác định; chưa tạo trước nhật ký tuần 8–10.

## Đồng bộ GitHub

Ghi gọn theo ngày/nhánh; ghi người đồng bộ theo từng lần thực hiện. Không ghi thao tác chạy/dừng hoặc chuyển nhánh. Tên trong nhật ký là thông tin nhóm ghi nhận, không thay danh tính tài khoản GitHub xác thực thao tác push.

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 25/11/2026 | 12:03 | Trần Văn Toàn | `main` | Kiểm tra liên kết toàn hệ thống và sửa lỗi đồng bộ (`context`, `human_review_current`, làm mới UI khắc phục); nghiệm thu theo mục tiêu đề tài + 10 tình huống AI độc lập; hồ sơ bảo vệ (`docs/defense/`); test mới nâng lên 449 test Python; cập nhật README và nhật ký tuần 7 |
