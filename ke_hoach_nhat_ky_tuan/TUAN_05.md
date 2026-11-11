# Tuần 5 — Phạm vi 56 control, ưu tiên đánh giá sâu A.8

- Thời gian: **09/11/2026–15/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Đang thực hiện.**
- Cập nhật: **11/11/2026**.

## Mục tiêu và kế hoạch

Điều chỉnh theo góp ý của giảng viên: dừng phát triển văn phòng 3D và điều khiển nhân viên bằng bình luận; giữ phạm vi 56 control con người/phần cứng/phần mềm; ưu tiên Agent đánh giá sâu 18 control A.8 từ bằng chứng, đối chiếu người đánh giá và sinh SoA. Góp ý này không phải thu hẹp đề tài xuống 18 control.

- [x] Xây dựng phạm vi và rubric thử nghiệm cho 18 control A.8; nêu nguồn, điều kiện đạt/sai/thiếu bằng chứng.
- [x] Bổ sung doanh nghiệp lab có cấu hình/log đúng, sai, thiếu, hết hạn và mâu thuẫn có chủ đích.
- [x] Phát triển collector đọc bằng chứng gốc, lưu nội dung, hash, thời điểm và lỗi thu thập.
- [x] Xây dựng luồng người đánh giá chấm mù, khóa nhãn và đối chiếu đúng lượt/bằng chứng.
- [x] Bổ sung báo cáo từng control và SoA tự sinh, có điều kiện phê duyệt của người phụ trách.
- [x] Thống nhất quản lý đủ 56 control, connector hồ sơ, thẩm định và SoA tổng thể; không trộn kết quả ca thử vào kết luận chính thức của đợt.
- [x] Bổ sung 5 probe live đại diện, rà soát lỗi nguồn/viện dẫn/kết luận và sửa quyền chấm mù.
- [x] Gỡ mã và tài liệu demo không còn phù hợp; tách nghiệp vụ doanh nghiệp dùng chung, cập nhật hướng dẫn và kiểm tra sau dọn.
- [ ] Người phụ trách rà soát/phê duyệt rubric và phạm vi thực tế.
- [ ] Người đánh giá thực sự chấm độc lập; phân tích bất đồng và đo độ đúng so với con người.
- [ ] Kiểm thử đầy đủ thao tác UI và hoàn thiện hồ sơ nghiệm thu/SoA được người phụ trách phê duyệt.

Các dấu hoàn thành trên chỉ xác nhận phần triển khai kỹ thuật, không thay thế việc con người thẩm định/phê duyệt.

## Hiện trạng đến ngày 11/11/2026

- Đã có luồng quản lý, hồ sơ và SoA cho đủ 56 control; 18 A.8 là nhóm thực nghiệm sâu. Nguồn live mới có 5 probe đại diện, 13 control còn lại trong nhóm 18 chưa có probe live.
- Sau đợt dọn mã mới nhất: 140 test Python, 5 test JavaScript và build đạt; lint không còn cảnh báo. Các số test/cảnh báo ở những mục trước là mốc kiểm chứng từng phiên bản, không phải các kết quả hiện hành mâu thuẫn nhau.
- Kho doanh nghiệp được giữ nguyên: 50 nhân viên, 202 tài khoản, 70 thiết bị; hash snapshot trước/sau dọn không đổi.
- Chưa có hồ sơ đầy đủ cho toàn phạm vi, người đánh giá thật hoàn tất chấm độc lập hoặc phê duyệt chuyên môn. Tuần 5 vẫn đang thực hiện, chưa tổng kết cả tuần.

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
- Bộ raw v2 lưu 4 lỗi engine ở A.8.1/A.8.3 và 6 lượt nhầm thiếu bằng chứng ở A.8.5/A.8.13/A.8.20. Lượt hồi quy sau sửa khớp 36/36 ca đã biết; không thay thế kết quả v2 hoặc kiểm định độc lập. Lỗi suy luận live A.8.3 vẫn tồn tại và được guard chặn, chưa coi model đã suy luận đúng.
- Chưa xác nhận đầy đủ thao tác bấm UI có đăng nhập; cần kiểm tra thủ công các luồng và trường hợp bị chặn theo checklist.
- SoA A.8 là báo cáo con; đã có SoA tổng thể đủ 56 control nhưng vẫn là dự thảo, chưa phải SoA đầy đủ ISMS; cần bối cảnh/rủi ro và phê duyệt người có thẩm quyền.

## Việc tiếp tục trong tuần 5

- [ ] Người phụ trách rà rubric và xác nhận nguồn bằng chứng được chấp nhận cho từng control.
- [ ] Phân công người đánh giá chấm mù, không xem đáp án nhóm ngoài hệ thống; thu kết luận và căn cứ thật.
- [x] Phân tích bước đầu lỗi engine/thiếu bằng chứng, bổ sung guard và chạy hồi quy trên ca đã biết; giữ nguyên báo cáo lỗi cũ.
- [ ] Chốt tập kiểm định tách biệt và đo lại sau thay đổi, tiếp tục xử lý lỗi suy luận live A.8.3.
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

## Củng cố bằng chứng và nghiệm thu — 11/11/2026

- Bổ sung nguồn live cho 5 control A.8.3/.10/.13/.15/.19: thu quyền/tồn tại tệp, backup/restore, log ứng dụng và inventory gói tại thời điểm kiểm tra trong container cô lập. 13 control khác chưa có probe live trả thiếu bằng chứng; không dùng bộ replay thay trạng thái live.
- Tách rubric/version live khỏi raw v2, không lấy đáp án replay chấm kết quả live. Luồng chấm mù và phê duyệt theo hash tiếp tục áp dụng; chưa có nhãn người đánh giá thật hoặc phê duyệt thật.
- Kiểm chứng 20 tình huống live và thử thay đổi tệp restore: collector phát hiện không khớp/hash đổi, sau đó khôi phục tài nguyên lab. Đây là kiểm thử kỹ thuật, không phải độ đúng AI hay thẩm định chuyên gia.
- Bổ sung chặn kết luận không đủ căn cứ, ghi diagnostic và bỏ gọi model khi không có nguồn; giữ rõ nguồn kết luận, không fallback ngầm. Sửa tương thích JSON mode SDK Ollama sau lượt thử bị ValidationError, giữ log lỗi riêng.
- Kiểm tra hồi quy Ollama trên 36 ca mixed/incomplete: 36/36 khớp đáp án nhóm, không lỗi engine. Ca đã biết dùng sửa hệ thống, chưa là kiểm định độc lập; giữ nguyên kết quả raw v2 95,37%.
- Màn hình 56 control nêu việc cần làm tiếp, loại nguồn cần rà và số thẩm định hiện hành; màn hình A.8 hiển thị coverage, thiếu nguồn và lỗi. Không coi có hồ sơ hoặc chạy xong là đáp ứng kiểm soát.
- Hướng dẫn và giới hạn: [Đối chiếu góp ý và nghiệm thu](../docs/HOAN_THIEN_THEO_GOP_Y_GIANG_VIEN.md).
- Lượt live phát hiện A.8.3 kết luận mâu thuẫn rubric; giữ nguyên báo cáo gốc. Bản guard v4 chặn thành lỗi có chẩn đoán, không sửa thành đáp án luật. Kiểm tra lại live mixed: 4 phản hồi hợp lệ, 1 lỗi A.8.3 bị chặn, 13 control chưa có probe trả thiếu bằng chứng; chưa có accuracy live độc lập.
- Kiểm chứng cuối: 262 test Python, 15 test JavaScript và build đạt; chưa thay thế đánh giá chuyên gia hoặc kiểm thử bấm toàn bộ UI.

## Rà soát và sửa lỗi mã nguồn — 11/11/2026

- Sửa quyền tạo lượt A.8 và không xuất answer key đầy đủ; dùng giao thức chấm mù mới cho lượt tạo mới, giữ lịch sử cũ và tách cohort theo giao thức.
- Thống nhất rubric runtime với nguồn được xác nhận; chặn viện dẫn lẫn ID bịa và confidence thiếu/sai thay vì tự gán 85%.
- Sửa định danh bằng chứng theo bytes gốc, ràng buộc đường dẫn đúng đợt/control và sửa cảnh báo độ mới sai ở đánh giá tài liệu.
- Nối API đồng bộ cũ vào cùng khóa công việc và bảo vệ upload khi Agent đang chạy; sửa dependency polling Hồ sơ ISO.
- 278 test Python, 15 test JavaScript và build đạt; kiểm tra cú pháp, dependency và truy vấn PostgreSQL thật. Còn 5 cảnh báo lint ở component cũ; chưa coi đã kiểm thử toàn bộ UI hoặc hoàn tất nghiệm thu chuyên môn.
- Báo cáo: [Rà soát mã nguồn](../docs/RA_SOAT_CODE_2026_11_11.md).

## Dọn project theo phạm vi hiện hành — 11/11/2026

- Gỡ 111 tệp văn phòng/bình luận/mission/SOC demo, giao diện HTML cũ, benchmark/khảo sát/ảnh và hướng dẫn không còn phù hợp; giữ bằng chứng nghiên cứu A.8 và dữ liệu doanh nghiệp.
- Tách kho danh bạ/tài sản và kiểm tra A.6 khỏi mã demo; giữ liên kết EMP, tài khoản, thiết bị và lịch sử database. Kiểm tra snapshot trước/sau không đổi: 50 nhân viên, 202 tài khoản, 70 thiết bị.
- Cập nhật README/hướng dẫn/CLI về đánh giá 56 control và thực nghiệm A.8; bỏ dependency chỉ dùng bởi mã đã gỡ.
- Sau dọn: 140 test Python, 5 test JavaScript hiện hành và build đạt; lint không còn cảnh báo. Số test thay đổi do loại các test của chức năng đã xóa, không phải bỏ qua lỗi.
- Danh sách và minh chứng: [Dọn project](../docs/DON_GON_PROJECT.md).

## Đồng bộ GitHub

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 11/11/2026 | 13:37 | Trần Văn Toàn | `main` | Hoàn thiện đánh giá tuân thủ, bổ sung bằng chứng live và dọn mã demo cũ. |
