# Tuần 5 — Phạm vi 56 control, ưu tiên đánh giá sâu A.8

- Thời gian: **09/11/2026–15/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Đang thực hiện.**
- Cập nhật: **10/11/2026**.

## Mục tiêu và kế hoạch

Điều chỉnh theo góp ý của giảng viên: dừng phát triển văn phòng 3D và điều khiển nhân viên bằng bình luận; giữ phạm vi 56 control con người/phần cứng/phần mềm; ưu tiên Agent đánh giá sâu 18 control A.8 từ bằng chứng, đối chiếu người đánh giá và sinh SoA. Góp ý này không phải thu hẹp đề tài xuống 18 control.

- [x] Xây dựng phạm vi và rubric thử nghiệm cho 18 control A.8; nêu nguồn, điều kiện đạt/sai/thiếu bằng chứng.
- [x] Bổ sung doanh nghiệp lab có cấu hình/log đúng, sai, thiếu, hết hạn và mâu thuẫn có chủ đích.
- [x] Phát triển collector đọc bằng chứng gốc, lưu nội dung, hash, thời điểm và lỗi thu thập.
- [x] Xây dựng luồng người đánh giá chấm mù, khóa nhãn và đối chiếu đúng lượt/bằng chứng.
- [x] Bổ sung báo cáo từng control và SoA tự sinh, có điều kiện phê duyệt của người phụ trách.
- [ ] Người phụ trách rà soát/phê duyệt rubric và phạm vi thực tế.
- [ ] Người đánh giá thực sự chấm độc lập; phân tích bất đồng và đo độ đúng so với con người.
- [ ] Kiểm thử đầy đủ thao tác UI và hoàn thiện hồ sơ nghiệm thu/SoA được người phụ trách phê duyệt.

Các dấu hoàn thành trên chỉ xác nhận phần triển khai kỹ thuật, không thay thế việc con người thẩm định/phê duyệt.

## Nhật ký công việc chính

| Ngày | Công việc | Kết quả chính |
|---|---|---|
| 09/11/2026 | Viết lại README theo tên đề tài và cấu trúc hệ thống | Làm rõ mục tiêu, chức năng, kiến trúc, cài đặt, cấu trúc thư mục và giới hạn; loại các tuyên bố chưa có bằng chứng |
| 10/11/2026 | Điều chỉnh trọng tâm theo góp ý giảng viên | Chuyển giao diện chính sang đánh giá A.8; giữ mã 3D/bình luận làm lịch sử, dừng phát triển phần này |
| 10/11/2026 | Xây phạm vi và rubric 18 control kỹ thuật | Tiêu chí đại diện, nguồn bằng chứng, điều kiện pass/fail/unknown và bước người phụ trách duyệt rubric theo hash |
| 10/11/2026 | Tạo bộ hồ sơ và lab Docker cô lập | 108 ca duy nhất thuộc 6 nhóm: đạt, một phần, không đạt, thiếu, hết hạn, mâu thuẫn; có phép thử tài khoản, quyền tệp, xóa tệp và backup/restore trong container |
| 10/11/2026 | Phát triển collector và Agent đánh giá bằng chứng | Đọc cấu hình/log gốc, parse text/JSON/CSV/TSV, tính checksum, kiểm tra quyền/CIDR/thời gian; lưu nguồn/hash; tách LLM và baseline luật, không fallback ngầm |
| 10/11/2026 | Bổ sung đánh giá mù và quản lý nhãn | Người khác tài khoản chấm cùng bằng chứng; API ẩn kết quả/đáp án/profile trước khi nộp đủ 18 control; khóa nhãn đã nộp và gắn đúng report/evidence hash |
| 10/11/2026 | Đo và xuất báo cáo đánh giá | Raw v2 chạy 2 lần trên 108 ca: LLM khớp đáp án nhóm 206/216 (95,37%), baseline 216/216; giữ 4 lỗi engine và 6 lượt sai phân loại; có bảng từng control, precision/recall/F1 và confusion matrix |
| 10/11/2026 | Hoàn thiện SoA và quy trình nghiệm thu | Xuất JSON/Markdown; tách tính áp dụng khỏi kết luận kiểm tra; phê duyệt cần rubric được duyệt, người chấm đủ 18 control và quyết định/kế hoạch xử lý từng control |
| 10/11/2026 | Kiểm chứng kỹ thuật và soạn hướng dẫn test | 235 test Python đạt, build thành công; API thật thu đủ 18 control từ Docker; có hướng dẫn chạy baseline, LLM, chấm mù và kiểm tra điều kiện duyệt SoA |

## Bổ sung thống nhất phạm vi ngày 10/11/2026

- Giữ đủ 56 control trong giao diện và ma trận tiến độ; đặt 18 A.8 là nhóm ưu tiên thực nghiệm sâu.
- Bổ sung màn hình tổng thể theo ba nhóm, nộp bằng chứng, theo dõi đánh giá và SoA đủ 56 dòng; tách kết quả ca thử khỏi kết luận của đợt.
- Ghi rõ 27 control có kiểm tra lab đại diện, 29 có luồng tài liệu nhưng chưa có collector riêng; không ghi là đã hoàn thành tự động hóa đủ 56.
- 240 test Python và build đạt; vẫn cần người thật rà tiêu chí, đánh giá bằng chứng và phê duyệt phạm vi/SoA.
- Minh chứng: [Ma trận 56 control](../docs/MA_TRAN_56_CONTROL.md).

## Kết quả và minh chứng

- [Ma trận 18 control và tiêu chí raw v2](../docs/MA_TRAN_A8.md).
- [Quy trình nghiệm thu 5 bước](../docs/QUY_TRINH_NGHIEM_THU_A8.md).
- [Kết quả raw v2 và phân tích sai khác](../docs/a8-results/KET_QUA_RAW_V2.md), [bảng từng control CSV](../docs/a8-results/raw-v2-combined.csv).
- [SoA dự thảo](../docs/a8-results/SOA_RAW_V2.md).
- [Collector cấu hình/log gốc](../evidence_collectors/a8_raw.py), [Agent đánh giá](../agent_core/a8_assessment.py), [API chấm mù và phê duyệt](../backend/a8_api.py).

**Phân biệt các mốc:** bản v1 dùng 72 hồ sơ chuẩn hóa, LLM khớp 70/72 (97,22%). Bản raw v2 dùng 108 ca duy nhất, 2 lần lặp thành 216 lượt, khớp 206/216 (95,37%). Đây là hai điều kiện đo khác nhau, không lấy tỷ lệ v1 thay kết quả v2 hoặc kết luận chất lượng tăng/giảm trực tiếp.

Các tỷ lệ trên đối chiếu **đáp án do nhóm thiết kế**, chưa phải độ đúng so với người đánh giá thực sự. 216 lượt không phải 216 ca độc lập. Lỗi engine đã tính là sai trong mẫu số; thời gian LLM có chờ hàng đợi do hai tiến trình đo chồng lấn, chưa phải đo tốc độ đơn luồng cô lập.

## Vướng mắc và giới hạn

- Chưa có người thật xác nhận rubric, chấm độc lập và quyết định tính áp dụng/phê duyệt SoA. Test phần mềm nhập nhãn không được tính là khảo sát hoặc đánh giá chuyên gia.
- Một số phép thử chạy thực trong container; các dịch vụ còn lại là cấu hình/log mô phỏng, chưa phải tích hợp IAM/EDR hoặc chứng cứ vận hành production. Hai kiểm tra đại diện/control chưa bao phủ toàn bộ nội dung ISO.
- Còn 4 lỗi engine ở A.8.1/A.8.3 và 6 lượt nhầm thiếu bằng chứng ở A.8.5/A.8.13/A.8.20; giữ nguyên để phân tích, chưa được coi là đã khắc phục.
- Công cụ điều khiển Windows chưa kết nối native pipe; chưa xác nhận thao tác bấm toàn bộ UI có đăng nhập. Cần kiểm tra thủ công theo checklist hoặc khôi phục công cụ.
- SoA A.8 là báo cáo con; đã có SoA tổng thể đủ 56 control nhưng vẫn là dự thảo, chưa phải SoA đầy đủ ISMS; cần bối cảnh/rủi ro và phê duyệt người có thẩm quyền.

## Việc tiếp tục trong tuần 5

- [ ] Người phụ trách rà rubric và xác nhận nguồn bằng chứng được chấp nhận cho từng control.
- [ ] Phân công người đánh giá chấm mù, không xem đáp án nhóm ngoài hệ thống; thu kết luận và căn cứ thật.
- [ ] Phân tích lỗi engine và các ca thiếu bằng chứng, bổ sung tập kiểm định tách biệt nếu chỉnh prompt/rubric.
- [ ] Kiểm tra thủ công các luồng UI, xuất báo cáo và các trường hợp bị chặn duyệt.
- [ ] Hoàn thiện kế hoạch xử lý, quyết định áp dụng và SoA trong phạm vi sau khi đủ điều kiện.

## Việc dự kiến chuyển sang tuần 6

Chưa chốt. Tổng kết cuối tuần 5 rồi xác định công việc chuyển tiếp; chưa tạo file tuần 6–10.

## Bổ sung quy trình hồ sơ và SoA toàn phạm vi — 10/11/2026

- Bổ sung connector thư mục hồ sơ cho đủ 56 control, mẫu yêu cầu và manifest nguồn; đọc tài liệu/cấu hình/log, kiểm tra hash/phiên bản và chống nhập trùng. Đây là connector hồ sơ chung, không phải 56 probe kỹ thuật chuyên biệt.
- Thêm chế độ Agent chỉ đánh giá hồ sơ đã thu, không để preset nhân sự/lab thay kết luận; thiếu nguồn thì trả thiếu bằng chứng và không gọi model.
- Thêm xác nhận rubric toàn phạm vi, thẩm định từng control có danh tính/căn cứ/viện dẫn và phê duyệt SoA 56 với kiểm tra điều kiện. Nguồn, kết quả hoặc tiêu chí đổi làm thẩm định/phê duyệt cũ không còn hiện hành.
- 250 test Python và build đạt; kiểm tra PostgreSQL nhập một lần/dùng lại khi thu trùng bằng giao dịch QA rollback, không giữ bằng chứng giả. SoA thực tế vẫn chờ người thật rà tiêu chí, cung cấp nguồn, thẩm định và phê duyệt.
- Giữ nguyên kết quả thực nghiệm A.8 95,37%; chưa có kết quả người đánh giá thật và chưa tuyên bố đã khắc phục hết ca sai.
- Hướng dẫn: [Thu hồ sơ và thẩm định 56](../docs/THU_HO_SO_VA_THAM_DINH_56.md), [checklist hồ sơ từng control](../docs/CHECKLIST_HO_SO_56.md).
