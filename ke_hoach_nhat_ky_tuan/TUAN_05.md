# Tuần 5 — Phạm vi 56 control, ưu tiên đánh giá sâu A.8

- Thời gian: **09/11/2026–15/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Đang thực hiện.**
- Cập nhật: **12/11/2026**.

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
- [x] Bổ sung thẩm định từng tiêu chí cho 56 control; chốt nguồn trước suy luận, sửa phản hồi có giới hạn và báo cáo bất đồng từng người chấm.
- [x] Chuẩn bị CLI nhận bộ nguồn tách riêng và dò trùng ca đã biết; không tự nhận bộ ứng viên là kiểm định độc lập.
- [x] Mở rộng runtime live từ 5 lên 18 probe đại diện, tách rubric v2; kiểm chứng 72 tình huống và 5 phép đổi/khôi phục nguồn thực.
- [x] Nối nguồn live với hồ sơ 56, chống nhập trùng; chạy đánh giá riêng, xuất SoA 56 hiện tại và danh sách việc thiếu.
- [x] Làm rõ tiến độ từng người chấm và khai báo mức hỗ trợ; tách nhãn có AI hỗ trợ/chưa khai báo khỏi đối chiếu độc lập.
- [x] Bổ sung gói bàn giao 56 control / 113 tiêu chí, yêu cầu nguồn và dự thảo việc xử lý; xuất JSON/Markdown.
- [x] Bổ sung chấm giả định và lưu riêng theo tài khoản; admin theo dõi tổng hợp, không tính vào chấm thật hoặc điều kiện duyệt SoA.
- [x] Bổ sung người phụ trách, hạn xử lý và cách kiểm tra lại vào hồ sơ/SoA; nhắc kế hoạch còn thiếu thông tin.
- [x] Bổ sung báo cáo điều phối theo yêu cầu giảng viên, tách kết quả từng lượt/nguồn/rubric/engine và metadata lịch sử chưa đầy đủ.
- [ ] Người phụ trách rà soát/phê duyệt rubric và phạm vi thực tế.
- [ ] Người đánh giá thực sự chấm độc lập; phân tích bất đồng và đo độ đúng so với con người.
- [ ] Kiểm thử đầy đủ thao tác UI và hoàn thiện hồ sơ nghiệm thu/SoA được người phụ trách phê duyệt.

Các dấu hoàn thành trên chỉ xác nhận phần triển khai kỹ thuật, không thay thế việc con người thẩm định/phê duyệt.

## Hiện trạng đến ngày 12/11/2026

- Đã có luồng quản lý, hồ sơ và SoA cho đủ 56 control; 18 A.8 là nhóm thực nghiệm sâu. Runtime live v2 có 18 probe đại diện (5 quan sát tài nguyên, 13 phép thử chủ động ứng dụng lab). Các phép thử chưa bao phủ toàn bộ nội dung ISO; lượt live v1 và nhãn cũ được giữ riêng.
- Kiểm chứng mới nhất: **220 test Python, 5 test JavaScript, lint/build đạt**; còn 3 cảnh báo deprecation thư viện. Các số test ở mục lịch sử là mốc từng phiên bản, không phải kết quả hiện hành.
- Kho doanh nghiệp được giữ nguyên: 50 nhân viên, 202 tài khoản, 70 thiết bị; hash snapshot trước/sau dọn không đổi.
- Chưa có hồ sơ đầy đủ cho toàn phạm vi, người đánh giá thật hoàn tất chấm độc lập hoặc phê duyệt chuyên môn. Tuần 5 vẫn đang thực hiện, chưa tổng kết cả tuần.
- API thực tế hiện có 29/56 control có bằng chứng; 19 có nguồn dùng trong chế độ không lấy preset (18 capture live lab, 1 có hồ sơ nộp). Chưa có quyết định áp dụng/rubric được duyệt/thẩm định hiện hành. Không coi số lượng này là số control đạt.
- Còn 37 control cần nguồn tương ứng. Đánh giá 18 nguồn nhập theo rubric toàn phạm vi cho kết quả 9 thiếu bằng chứng, 8 một phần, 1 không đạt; khác kết quả ca thử đại diện do phạm vi tiêu chí khác nhau.
- Khoa đã nộp 2/18 nhãn ở lượt cũ; nhãn giữ nguyên, chưa khai báo mức hỗ trợ và chưa tính là đánh giá độc lập. Chưa có bộ nhãn người đánh giá hoàn tất để công bố accuracy với con người.
- Đã lưu 18 kết quả giả lập cho mỗi tài khoản admin/Khoa/Tú (54 nhãn luyện tập), tách khỏi nhãn nghiên cứu và phê duyệt; số này không phải 54 ca kiểm định.
- Báo cáo điều phối tổng hợp 56 control và 17 lượt thực nghiệm có report hợp lệ; 3 lượt lịch sử thiếu metadata được đánh dấu riêng. Đã có gói bàn giao 113 tiêu chí và theo dõi kế hoạch xử lý; các phần triển khai này chưa thay thế thẩm định/nghiệm thu thật.

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
| 11/11/2026 | Rà mã, dọn demo và củng cố đánh giá | Gỡ mã không còn phù hợp, giữ dữ liệu doanh nghiệp; sửa kiểm tra nguồn/viện dẫn/kiểu dữ liệu, tiến độ người chấm và mức hỗ trợ |
| 11/11/2026 | Mở rộng live A.8 lên 18 probe đại diện | 72/72 tình huống kỹ thuật; 5 phép đổi/khôi phục nguồn; pilot LLM giữ lỗi lần đầu và lần sửa, không nhận là accuracy chuyên gia |
| 11/11/2026 | Nối nguồn với hồ sơ toàn phạm vi và xuất bàn giao | Nhập 18 capture, đánh giá lại theo rubric 56; xuất SoA 56 dự thảo và danh sách thiếu; 202 test Python, 5 test JavaScript, lint/build đạt |
| 12/11/2026 | Hoàn thiện gói bàn giao và yêu cầu hồ sơ | Đủ 56 control / 113 tiêu chí; chỉ ra nguồn, vai trò và vướng mắc; xuất JSON/Markdown, sửa chỉ dẫn khi control chỉ có preset |
| 12/11/2026 | Bổ sung chấm giả định và tổng hợp admin | Lưu riêng 18 kết quả mẫu/tài khoản, admin thấy 54 nhãn luyện tập; không sửa nhãn thật hoặc dùng giả lập làm accuracy độc lập |
| 12/11/2026 | Hoàn thiện theo dõi xử lý và báo cáo điều phối | Nối người phụ trách/hạn/cách kiểm tra lại vào SoA; báo cáo 56 control và A.8 từng lượt, đánh dấu lịch sử thiếu metadata; 220 test Python, 5 test JavaScript, lint/build đạt |

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
- [Live v2: phạm vi, tiêu chí và giới hạn](../docs/LIVE_A8_V2.md), [pilot LLM từng control](../docs/a8-results/live-v2-ollama-pilot.csv).
- [Đánh giá nguồn nhập theo rubric toàn phạm vi](../docs/a8-results/dossier-capture-evaluations.json), [SoA 56 hiện tại](../docs/a8-results/SOA_56_HIEN_TAI.md), [SoA 56 JSON](../docs/a8-results/soa56-current-draft.json).
- [Danh sách việc/hồ sơ còn thiếu](../docs/VIEC_CAN_HOAN_THIEN_56.md), [hướng dẫn nối nguồn và phân loại nhãn](../docs/HOAN_THIEN_HO_SO_56.md).
- [Collector cấu hình/log gốc](../evidence_collectors/a8_raw.py), [Agent đánh giá](../agent_core/a8_assessment.py), [API chấm mù và phê duyệt](../backend/a8_api.py).
- [Gói bàn giao 113 tiêu chí](../docs/BAN_GIAO_TUAN_05_2026_11_12.md), [chấm giả lập tách riêng](../docs/CHAM_GIA_LAP_2026_11_12.md).
- [Theo dõi kế hoạch xử lý](../docs/KE_HOACH_XU_LY_VA_KIEM_TRA_LAI.md), [báo cáo điều phối và snapshot](../docs/BAO_CAO_DIEU_PHOI_GIANG_VIEN.md).

**Phân biệt các mốc:** bản v1 dùng 72 hồ sơ chuẩn hóa, LLM khớp 70/72 (97,22%). Bản raw v2 dùng 108 ca duy nhất, 2 lần lặp thành 216 lượt, khớp 206/216 (95,37%). Đây là hai điều kiện đo khác nhau, không lấy tỷ lệ v1 thay kết quả v2 hoặc kết luận chất lượng tăng/giảm trực tiếp.

Các tỷ lệ trên đối chiếu **đáp án do nhóm thiết kế**, chưa phải độ đúng so với người đánh giá thực sự. 216 lượt không phải 216 ca độc lập. Lỗi engine đã tính là sai trong mẫu số; thời gian LLM có chờ hàng đợi do hai tiến trình đo chồng lấn, chưa phải đo tốc độ đơn luồng cô lập.

## Vướng mắc và giới hạn

- Chưa có người thật xác nhận rubric, chấm độc lập và quyết định tính áp dụng/phê duyệt SoA. Test phần mềm nhập nhãn không được tính là khảo sát hoặc đánh giá chuyên gia.
- Cần xác nhận với giảng viên người đánh giá được chấp nhận: góp ý yêu cầu đối chiếu với người đánh giá, chưa quy định bắt buộc Khoa/Tú hoặc chuyên gia ngoài nhóm. Phân công nội bộ là bước chuẩn bị; khác tài khoản hoặc tự khai báo chưa chứng minh độc lập/chuyên môn.
- Thiếu nguồn phù hợp ở 37 control trong chế độ không lấy preset; 19 control có nguồn cũng chưa đồng nghĩa đủ chất lượng hoặc đủ nội dung control. Chưa hoàn tất 56 quyết định áp dụng và 56 thẩm định hiện hành.
- Runtime live v2 thực hiện phép thử trong container, nhưng scanner, xác thực, monitoring, time reference, DLP và zone gate là thành phần lab. Chưa phải tích hợp IAM/EDR/SIEM, đồng bộ NTP hay VLAN thực; tiêu chí đại diện chưa bao phủ toàn bộ nội dung ISO.
- Bộ raw v2 lưu 4 lỗi engine ở A.8.1/A.8.3 và 6 lượt nhầm thiếu bằng chứng ở A.8.5/A.8.13/A.8.20. Lượt hồi quy sau sửa khớp 36/36 ca đã biết; không thay thế kết quả v2 hoặc kiểm định độc lập. Pilot live v5 sửa hợp lệ A.8.3 ở lần hai nhưng giữ lỗi lần đầu; chưa coi model hết lỗi hoặc đã có accuracy với người thật.
- Chưa xác nhận đầy đủ thao tác bấm UI có đăng nhập. Trong phiên kiểm tra, công cụ browser/native không kết nối được; API, build và test đạt không thay thế checklist bấm UI.
- SoA A.8 là báo cáo con; đã có SoA tổng thể đủ 56 control nhưng vẫn là dự thảo, chưa phải SoA đầy đủ ISMS; cần bối cảnh/rủi ro và phê duyệt người có thẩm quyền.

## Việc tiếp tục trong tuần 5

- [ ] Người phụ trách rà rubric và xác nhận nguồn bằng chứng được chấp nhận cho từng control.
- [x] Chuẩn bị tài khoản riêng và phân công nội bộ dự kiến cho người chấm; đã có tiến độ và phân loại nguồn hỗ trợ.
- [ ] Xác nhận người đánh giá/phương pháp với giảng viên; thu kết luận và căn cứ thật, ghi đúng mức hỗ trợ/tiếp xúc đáp án.
- [ ] Bổ sung nguồn cho 37 control còn thiếu; rà chất lượng/phạm vi nguồn của 19 control đã có, không tạo hồ sơ trống hoặc preset thay bằng chứng.
- [x] Phân tích bước đầu lỗi engine/thiếu bằng chứng, bổ sung guard và chạy hồi quy trên ca đã biết; giữ nguyên báo cáo lỗi cũ.
- [x] Bổ sung sửa phản hồi có giới hạn, giữ lỗi đầu và kiểm tra lại live A.8.3 trên cùng nguồn đã chốt.
- [x] Chuẩn bị luồng nhận nguồn kiểm định tách riêng, dò trùng nội dung và khóa recipe/snapshot trước chạy.
- [x] Chuẩn bị gói bàn giao, khu chấm giả định và báo cáo admin; giữ tách biệt với kết quả nghiên cứu và phê duyệt thật.
- [x] Hoàn thiện công cụ ghi người phụ trách/hạn/cách kiểm tra lại và xuất cùng SoA; chưa tự điền các quyết định thực tế.
- [ ] Nhóm cung cấp và xác nhận tập kiểm định chưa dùng phát triển; thu nhãn thật và đo trên tập đó. Công cụ đã có không đồng nghĩa dữ liệu này đã tồn tại.
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

## Củng cố bằng chứng và nghiệm thu — 11/11/2026 (mốc live v1)

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

## Hoàn thiện luồng đánh giá và chuẩn bị chấm — 11/11/2026

- Thẩm định 56 control theo từng tiêu chí/căn cứ/viện dẫn; chặn bỏ sót hoặc kết luận mâu thuẫn. Giữ thẩm định cũ trong lịch sử, yêu cầu rà lại theo giao thức mới; form không tự dùng token nguồn mới khi người chấm đang đọc nguồn cũ.
- Chốt snapshot và recipe trước suy luận A.8; tối đa một lần yêu cầu model sửa phản hồi không hợp lệ, không thay bằng luật. Báo cáo tách kết quả lần đầu/sau sửa, số lượt/ca và các lỗi.
- Phân tích từng người chấm, agreement/kappa và bảng bất đồng gắn đúng hash. Không ghép nhãn nhiều người thành một đáp án hoặc tự tạo đồng thuận.
- Pilot mixed live: 5 probe có nguồn, 13 chưa hỗ trợ giữ thiếu bằng chứng; A.8.3 sai lần đầu và sửa hợp lệ lần hai, 4 probe khác hợp lệ ngay. Lượt này không có lỗi cuối; chưa có nhãn người thật nên không công bố accuracy live. Giữ nguyên số đo lịch sử.
- Chuẩn bị CLI nhận bộ nguồn mới tách riêng, kiểm tra trùng nội dung với ca đã biết; bộ ứng viên vẫn chờ người xác nhận độc lập. Không tạo bộ held-out giả từ các ca cũ.
- Theo danh sách thành viên được cung cấp, chuẩn bị phân công: Trần Văn Toàn điều phối/rà rubric; Lê Đăng Khoa và Lê Đoàn Văn Tú chấm riêng. Chưa ghi nhận ai đã thực sự chấm/duyệt; thành viên nhóm không tự được coi là chuyên gia độc lập bên ngoài.
- Sau bước chuẩn bị đã tạo hai tài khoản assessor riêng, kiểm tra truy cập đúng gói và sửa hiển thị tiến độ đang chấm/chấm đủ. Đây là triển khai luồng cộng tác, không xác nhận hoàn tất đối chiếu người thật.
- Rà thêm lỗi facts rỗng/sai kiểu có thể bị hiểu là đạt và nhãn thiếu reviewer ID; đã sửa, kiểm tra 157 test ở mốc đó. Bản chấm đối chiếu của trợ lý được lưu riêng, không nộp dưới tên thành viên và không dùng làm nhãn độc lập: [bản chấm AI](../docs/CHAM_DOI_CHIEU_TRO_LY.md).
- 152 test Python, 5 test JavaScript, lint và build đạt. API thật xác nhận phạm vi/SoA/tiêu chí 56; UI tương tác chưa xác nhận do công cụ trình duyệt không khả dụng. Hồ sơ, chấm và phê duyệt thật còn chờ, không đóng tuần 5 thay người phụ trách.
- Hướng dẫn và minh chứng: [Bàn giao tuần 5](../docs/NGHIEM_THU_TUAN_05.md), [pilot v5](../docs/a8-results/live-v5-pilot.json), [nguồn đã chốt](../docs/a8-results/live-v5-sealed-plan.json).

## Mở rộng bằng chứng live 18 A.8 — 11/11/2026

- Bổ sung 13 phép thử chủ động cho xác thực, mã hóa tệp, scanner mẫu, inventory/advisory lab, baseline, DLP, monitoring, nguồn thời gian ký, TCP ACL/zone gate, TLS và rollback; giữ 5 probe quan sát hiện có.
- Dùng image Python/OpenSSL trong container không có mạng ngoài; collector đọc kết quả thao tác và nội dung nguồn, kiểm tra schema/danh tính/thời gian/hash. Thiếu nguồn hoặc công cụ lỗi giữ unknown, không suy đoán đạt.
- Tách rubric `a8-live-v2-active`, đặt tên tiêu chí theo đúng phép thử; không biến mã hóa tệp thành mã hóa ổ đĩa, loopback gate thành VLAN hoặc nguồn thời gian cùng container thành NTP độc lập.
- Kiểm chứng 72/72 tình huống lab; 5 phép đổi nguồn thực đều được phát hiện và khôi phục. Đây là kiểm chứng kỹ thuật theo thiết kế nhóm, không phải accuracy chuyên gia.
- Giao diện hiển thị năng lực probe/rubric hiện tại, danh sách lượt mới nhất trước và mã lượt; lượt Khoa đang chấm giữ snapshot/nhãn cũ. Chưa có phê duyệt hoặc nhãn người thật mới do trợ lý tạo.
- Agent đã chạy qua API thật trên cả 18 probe mixed: 17 phản hồi hợp lệ lần đầu, A.8.3 sửa hợp lệ lần hai, không lỗi cuối. Lượt pilot không có nhãn người thật nên chưa có accuracy độc lập; đã xuất JSON/CSV và SoA dự thảo. Kiểm tra sau triển khai giữ nguyên report và 2 nhãn của lượt cũ.
- 190 test Python, 5 test JavaScript, lint và build đạt; chưa thay thế việc kiểm thử toàn bộ UI hoặc thẩm định chuyên môn.
- Ma trận và giới hạn: [Live A.8 v2](../docs/LIVE_A8_V2.md); minh chứng: [72 tình huống](../docs/a8-results/live-v2-engineering.json), [đổi nguồn và khôi phục](../docs/a8-results/live-v2-mutations.json).

## Nối nguồn với hồ sơ và phân loại nhãn — 11/11/2026

- Thêm nhập nguồn live vào hồ sơ 56: kiểm tra hash, khóa khi Agent chạy, nhập lặp không trùng; chỉ chuyển artifacts/metadata, giữ nhãn lab và không chép kết luận/đáp án.
- Đã nhập 18 bản thu: số control có bằng chứng tăng 15 → 29; nguồn dùng được trong chế độ không lấy preset là 19, còn 37 cần hồ sơ tương ứng. Danh sách việc thiếu theo vai trò xuất được JSON/Markdown và mở trực tiếp từng control.
- Chạy đánh giá riêng 18 control trên nguồn đã nhập: 9 thiếu bằng chứng, 8 một phần, 1 không đạt; không có kết luận đạt toàn control. Giữ 18 job lỗi SQL của lần tích hợp đầu, sửa bộ lọc và thêm hồi quy; lượt chạy lại đều thành công, không nhận lỗi SQL là lỗi suy luận LLM.
- Đã xuất SoA tổng thể hiện tại đủ 56 dòng ở Markdown/JSON; giữ `DRAFT_NOT_APPROVED`, tính áp dụng chưa xác định và các thiếu sót chưa được người phụ trách xác nhận.
- Thêm khai báo tự chấm/AI hỗ trợ/đã xem đáp án; nhãn hỗ trợ hoặc chưa khai báo được tách khỏi đối chiếu độc lập. Hai nhãn cũ của Khoa giữ nguyên, chưa tự gán là độc lập.
- Màn hình chấm hiển thị điều kiện và từng artifact, không mặc định chọn đạt. 202 test Python, 5 test JavaScript, lint/build đạt; kiểm thử bấm toàn UI vẫn chưa xác nhận vì công cụ không kết nối.
- Hướng dẫn: [Hoàn thiện hồ sơ 56](../docs/HOAN_THIEN_HO_SO_56.md), [việc cần làm](../docs/VIEC_CAN_HOAN_THIEN_56.md), [kết quả đánh giá nguồn nhập](../docs/a8-results/dossier-capture-evaluations.json). Không tự hoàn tất nhãn/phê duyệt hoặc tạo hồ sơ thay người phụ trách.

## Hoàn thiện bàn giao theo tiêu chí — 12/11/2026

- Bổ sung gói bàn giao động đủ 56 control / 113 tiêu chí: yêu cầu nguồn, vai trò đề nghị, ID/hash bằng chứng, vướng mắc và dự thảo xử lý; xuất JSON/Markdown ngay trên giao diện.
- Chỉ lấy thẩm định hiện hành làm kết quả tiêu chí; không tự gán người nhận, hạn xử lý, nhãn hoặc phê duyệt. Sửa chỉ dẫn thu nguồn khi control chỉ có preset.
- Kiểm tra API thật giữ nguyên trạng thái: 19 control có nguồn ngoài preset, 37 thiếu nguồn; chưa có quyết định áp dụng/rubric/thẩm định/SoA được duyệt. Không đóng các mục cần người thật hoặc nguồn mới.
- 207 test Python, 5 test JavaScript, lint/build đạt. Computer Use vẫn lỗi kết nối native pipe; kiểm thử bấm toàn UI chưa hoàn tất.
- Minh chứng và thao tác tiếp: [Bàn giao 12/11](../docs/BAN_GIAO_TUAN_05_2026_11_12.md).

## Chấm giả lập tách riêng — 12/11/2026

- Theo yêu cầu đẩy tiến độ kỹ thuật, bổ sung chấm giả lập theo facts/rubric lab trên cùng snapshot; admin xem bảng và xuất JSON riêng. Không tạo nhãn dưới tài khoản thành viên hoặc mở đáp án cho người chấm mù.
- Đã chạy 18 control của lượt live v2: 18 kết luận một phần, khớp kết luận cuối Agent 18/18. Đây là đối chiếu cùng rubric/guard, không phải accuracy người thật; giữ lỗi lần đầu A.8.3 và trạng thái thiếu nguồn toàn phạm vi.
- Chặn nhãn có dấu giả lập khỏi phân tích người chấm ngay cả khi khai sai mức hỗ trợ. Nhãn thật, SoA và các phê duyệt giữ nguyên; chấm thật thực hiện sau.
- 211 test Python, 5 test JavaScript, lint/build đạt. [Bảng chấm giả lập](../docs/CHAM_GIA_LAP_2026_11_12.md).

- Bổ sung ngày 12/11: tài khoản người chấm có nút chấm nhanh 18 control mẫu trong khu luyện tập riêng; không mở lượt chấm mù, không nộp nhãn thật. Ví dụ dùng bộ phát triển raw mixed, yêu cầu khai đúng mức tiếp xúc khi chấm thật. 212 test Python, lint/build đạt.
- Đã lưu gói giả lập riêng 18/18 cho từng tài khoản admin/Khoa/Tú; ghi người thực hiện là bộ máy giả lập, không phải chủ tài khoản. Kiểm tra hash xác nhận nhãn thật/quyết định/phê duyệt không đổi; 6 test mô phỏng đạt, lint/build đạt. Gói nằm ngoài kho nhãn nghiên cứu và tự hiện lại ở khu luyện tập khi đăng nhập đúng tài khoản.
- Bổ sung bảng admin tổng hợp chấm giả định các tài khoản, tự cập nhật 4 giây; hiển thị rõ 54 nhãn giả lập của 3 tài khoản, tách khỏi tiến độ chấm thật theo lượt. Sửa tiêu đề/thông báo để tránh nhầm giả định đã lưu với nhãn thật chưa nộp; API và 6 test mô phỏng, lint/build đạt.

## Theo dõi kế hoạch xử lý và kiểm tra lại — 12/11/2026

- Bổ sung người chịu trách nhiệm, hạn xử lý và cách kiểm tra lại cho quyết định từng control; API kiểm tra đầu vào, giữ lịch sử, đổi kế hoạch làm fingerprint/phê duyệt SoA cũ không còn hiện hành.
- Nối các thông tin vào SoA và gói bàn giao; danh sách việc nhắc kế hoạch áp dụng còn thiếu chi tiết. Không tự phân công, đặt hạn hay ghi công việc đã xong.
- 215 test Python, 5 test JavaScript, lint/build đạt; API thật xác nhận đủ 56 dòng và không sửa nhãn/quyết định/phê duyệt. Các mục cần nguồn, người thật, tập kiểm định và kiểm thử UI vẫn mở.
- Hướng dẫn: [Kế hoạch xử lý và kiểm tra lại](../docs/KE_HOACH_XU_LY_VA_KIEM_TRA_LAI.md).

## Báo cáo điều phối theo góp ý giảng viên — 12/11/2026

- Bổ sung báo cáo admin tổng hợp 56 control, kết quả A.8 theo từng lượt/nguồn/rubric/engine, lỗi đầu/cuối, đối chiếu từng người và việc còn thiếu; xuất JSON/Markdown.
- Tách 54 nhãn luyện tập khỏi chấm thật/mẫu kiểm định; không cộng kết quả khác điều kiện thành một accuracy. Nêu lượt bị loại do dữ liệu/hash và đánh dấu metadata lịch sử còn thiếu.
- API thật xác nhận 56 control, 17 lượt report hợp lệ, 3 lượt thiếu metadata; chưa có lượt hoàn tất nhãn khai báo độc lập. Tệp nhãn/quyết định/phê duyệt giữ nguyên.
- 220 test Python, 5 test JavaScript, lint/build đạt. [Hướng dẫn và snapshot báo cáo](../docs/BAO_CAO_DIEU_PHOI_GIANG_VIEN.md). Các mục cần nguồn, người thật và kiểm thử UI chưa đóng.

## Đồng bộ GitHub

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 11/11/2026 | 13:37, 22:27 | Trần Văn Toàn | `main` | Hoàn thiện đánh giá tuân thủ, bằng chứng live và dọn demo; mở rộng 18 probe A.8, nối nguồn với hồ sơ 56 và bổ sung báo cáo. |
| 12/11/2026 | 10:21 | Trần Văn Toàn | `main` | Bổ sung gói bàn giao 56 control, chấm giả định tách riêng, kế hoạch xử lý và báo cáo điều phối theo góp ý giảng viên. |
