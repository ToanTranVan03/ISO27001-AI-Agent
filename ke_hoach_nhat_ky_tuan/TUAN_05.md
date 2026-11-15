# Tuần 5 — Phạm vi 56 control, ưu tiên đánh giá sâu A.8

- Thời gian: **09/11/2026–15/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Đang thực hiện — còn việc nghiệm thu chuyển tiếp.**
- Cập nhật: **15/11/2026**.

## Mục tiêu và kế hoạch

Điều chỉnh theo góp ý giảng viên: dừng văn phòng 3D/điều khiển nhân viên bằng bình luận, tập trung Agent đánh giá tuân thủ từ bằng chứng, đối chiếu người đánh giá và sinh SoA. Giữ phạm vi **56 control: 8 A.6 con người, 14 A.7 vật lý, 34 A.8 công nghệ**; 18 A.8 là nhóm thực nghiệm sâu, không thay thế 38 control còn lại.

- [x] Xây rubric thử nghiệm 18 A.8, bộ raw đúng/sai/thiếu/quá hạn/mâu thuẫn và collector cấu hình/log gốc có hash, thời điểm, lỗi.
- [x] Mở rộng live lên 18 probe đại diện; chốt nguồn trước suy luận, sửa phản hồi có giới hạn và giữ lỗi lần đầu/sau sửa.
- [x] Triển khai hồ sơ, thẩm định từng tiêu chí và SoA dự thảo đủ 56 control; nhập nguồn live chống trùng, đánh giá không dùng preset.
- [x] Hoàn thiện chấm mù, khóa nhãn, khai báo hỗ trợ/tiếp xúc và phân tích bất đồng theo từng người, đúng report/hash.
- [x] Bổ sung gói bàn giao 113 tiêu chí, yêu cầu nguồn, kế hoạch xử lý và báo cáo điều phối JSON/CSV/Markdown.
- [x] Tách chấm giả định khỏi nhãn nghiên cứu; kiểm tra chất lượng căn cứ và lưu audit riêng, không sửa nhãn khóa.
- [x] Tích hợp chọn lọc công cụ hai nhánh, nhập gói nguồn ngoài đã chốt, kiểm tra lại facts từ artifact; không tự gán nhãn người thật hoặc độc lập.
- [x] Gỡ demo cũ, giữ dữ liệu doanh nghiệp; sửa điều hướng lượt chấm, cảnh báo gây nhầm và Việt hóa kết luận; kiểm chứng kỹ thuật.
- [ ] Người phụ trách rà soát/phê duyệt rubric và phạm vi thực tế.
- [ ] Người đánh giá thực sự chấm độc lập; phân tích bất đồng và đo độ đúng so với con người.
- [ ] Kiểm thử đầy đủ thao tác UI và hoàn thiện hồ sơ nghiệm thu/SoA được người phụ trách phê duyệt.

Dấu hoàn thành xác nhận phần triển khai có minh chứng, không thay thế xác nhận chuyên môn hoặc chứng nhận ISO.

## Nhật ký công việc chính của nhóm

Nội dung main là công việc Trần Văn Toàn điều phối và triển khai với trợ lý trong phiên làm việc. Nội dung Khoa/Tú được tổng hợp theo commit trên hai nhánh và đã phân biệt với kết quả tích hợp local; thời gian commit không tự xác nhận ngày thực hiện toàn bộ công việc hoặc người đã thao tác chấm.

| Ngày / mốc ghi nhận | Thành viên / nguồn | Công việc và kết quả chính |
|---|---|---|
| 09/11/2026 | Trần Văn Toàn — main | Rà và viết lại README: Làm rõ tên đề tài, mục tiêu, kiến trúc, cấu trúc thư mục, hướng dẫn và giới hạn; bỏ tuyên bố chưa có bằng chứng |
| 10/11/2026 | Trần Văn Toàn — main | Điều chỉnh theo góp ý giảng viên: Chuyển giao diện chính sang đánh giá tuân thủ, dừng hướng 3D/bình luận; giữ phạm vi 56 control, ưu tiên 18 A.8 |
| 10/11/2026 | Trần Văn Toàn — main | Xây rubric, raw lab và collector A.8: 108 ca thuộc 6 profile; đọc cấu hình/log gốc, lưu nguồn/hash và lỗi; tách LLM với baseline luật, không fallback ngầm |
| 10/11/2026 | Trần Văn Toàn — main | Bổ sung chấm mù, báo cáo và SoA: Khóa nhãn theo report/bằng chứng; có bảng từng control và báo cáo tự sinh. Raw v2 LLM khớp đáp án nhóm 206/216, giữ lỗi và ca phân loại sai |
| 10/11/2026 | Trần Văn Toàn — main | Mở rộng hồ sơ toàn phạm vi: Danh mục 56 control, connector gói tài liệu, chế độ đánh giá không dùng preset, thẩm định và quyết định tính áp dụng/phê duyệt theo phiên bản |
| 11/11/2026 | Trần Văn Toàn — main | Rà mã và dọn demo cũ: Gỡ mã/tài liệu không phù hợp; giữ kho 50 nhân viên, 202 tài khoản, 70 thiết bị. Sửa quyền chấm, viện dẫn, confidence, kiểu dữ liệu và khóa công việc |
| 11/11/2026 | Trần Văn Toàn — main | Củng cố Agent và mở rộng live: Chốt snapshot/recipe, tối đa một lần sửa phản hồi, giữ lỗi đầu; live từ 5 lên 18 probe đại diện, kiểm chứng 72 tình huống và 5 phép đổi/khôi phục nguồn |
| 11/11/2026 | Trần Văn Toàn — main | Nối nguồn live với hồ sơ 56: Nhập 18 capture, chống trùng; đánh giá theo rubric toàn phạm vi, kết quả 9 thiếu bằng chứng, 8 một phần, 1 không đạt. Sửa lỗi SQL tích hợp, giữ lịch sử lỗi |
| 12/11/2026 | Trần Văn Toàn — main | Hoàn thiện bàn giao và báo cáo: Gói 56 control/113 tiêu chí, danh sách nguồn còn thiếu, người phụ trách/hạn/cách kiểm tra lại; xuất báo cáo điều phối và SoA dự thảo |
| 12/11/2026 | Trần Văn Toàn — main | Bổ sung chấm giả định: Gói luyện tập riêng 18 kết quả/tài khoản, admin tổng hợp 54 nhãn giả lập; không tính vào đối chiếu người thật hoặc duyệt SoA |
| 13/11/2026 | Công cụ chung hai nhánh — Git: Gera-YCYC | Bổ sung script chuẩn bị tài khoản, CLI chấm A.8 và hướng dẫn nghiệm thu (`c29d128`); là commit nền chung, không tính thành hai công việc độc lập. |
| 13/11/2026 | Lê Đoàn Văn Tú — Tu/Tuan5 | Sửa CLI sang chấm tương tác: người chấm tự nhập kết luận/căn cứ, khai hỗ trợ/tiếp xúc, xác nhận trước nộp; bảo toàn tài khoản hiện có, thêm test và sửa UTF-8 Windows (`39c4fae`, `7ee5918`). Có công cụ chấm, chưa chứng minh người thật đã tự chấm độc lập. |
| 14/11/2026 | Lê Đăng Khoa — Tuan5 (Git: Gera-YCYC) | Bổ sung công cụ hỗ trợ PostgreSQL/hiển thị tiến độ và pipeline tổng hợp 18 A.8, 108 ca đã có, bảng độ đúng, SoA JSON/CSV/Markdown và gợi ý xử lý (`8a297a4`, `538a5ba`). Phần tự sinh nhãn mang tên người thật/tự duyệt không được công nhận, đã sửa khi tích hợp. |
| 15/11/2026 | Trần Văn Toàn — main | Tích hợp hai nhánh thành viên: CLI chấm tương tác, chuẩn bị tài khoản bảo toàn mật khẩu và pipeline xuất báo cáo; sửa cơ chế tự sinh nhãn người thật/tự duyệt. Xuất thử 12 report lịch sử, không chạy LLM mới |
| 15/11/2026 | Trần Văn Toàn — main | Sửa giao diện và kiểm tra hai tài khoản: Phân biệt lượt cũ chỉ đọc/lượt có thể chấm, tách hướng dẫn unknown khỏi cảnh báo nguồn, Việt hóa kết luận; xác minh đăng nhập/API Khoa và Tú |
| 15/11/2026 | Trần Văn Toàn — main | Rà căn cứ và nhập nguồn ứng viên: Chặn nội dung thử, cảnh báo trùng/viện dẫn sai control; audit riêng 9 lỗi nội dung. Nối nhập gói ngoài đã chốt, kiểm tra hash/recipe/facts và trùng fixture; ẩn đáp án luyện tập khi chấm mù |
| 15/11/2026 | Trần Văn Toàn — main | Rà nguồn và chuẩn bị tuần 6: Kiểm tra project, thư mục bị Git bỏ qua và database; chưa thấy bộ kiểm định mới, phát hiện A.6.2 chỉ trích xuất 1 ký tự; lập kế hoạch chuyển tiếp tuần 6 |
| 15/11/2026 | Hai tài khoản Khoa/Tú — dữ liệu ứng dụng | Nộp đủ 18/18 mỗi tài khoản trên cùng lượt 0b7dc9e9; có AI hỗ trợ/chưa khai đủ, 9 căn cứ cần rà. Ghi nhận tiến độ nộp qua tài khoản, không suy ra hai thành viên tự chấm độc lập. |

## Bổ sung công việc từ thành viên

Các ý chính đã có bằng chứng ở hai nhánh được gộp vào bảng trên, không chỉ ghi ở mục GitHub. Công việc ngoài commit hoặc thông tin chi tiết thành viên chưa cung cấp được giữ chờ xác nhận, không tự suy ra đã hoàn thành.

Khi nhận thêm thông tin của Khoa/Tú: bổ sung vào đúng ngày ở bảng chung, ghi ngắn gọn việc làm, kết quả và tệp/commit minh chứng; gộp với dòng đã có nếu cùng công việc. Ngày 13–14/11 hiện là mốc commit, sẽ điều chỉnh ngày thực hiện nếu thành viên xác nhận khác. Kết quả tự sinh, có AI hỗ trợ và phê duyệt thật phải được phân biệt.

## Kết quả và minh chứng

- **Kiểm chứng kỹ thuật mới nhất:** 246 test Python, 5 test JavaScript, lint/build đạt; 3 cảnh báo deprecation thư viện. API thật đã kiểm tra; chưa xác nhận bấm toàn UI. Bỏ các số test trung gian khỏi nhật ký tóm tắt, giữ minh chứng từng phiên bản trong tài liệu riêng.
- **Thực nghiệm raw v2:** 108 ca duy nhất × 2 lần = 216 lượt; LLM khớp đáp án thiết kế **206/216 (95,37%)**, baseline luật **216/216**. Giữ 4 lỗi engine và 6 lượt sai phân loại; đây chưa phải accuracy với người đánh giá độc lập. Thời gian LLM có chờ hàng đợi, chưa dùng kết luận tốc độ đơn luồng.
- **Live v2:** 18 probe đại diện (5 quan sát tài nguyên, 13 phép thử chủ động); 72/72 tình huống kỹ thuật và 5 phép đổi/khôi phục nguồn. Pilot `67d38694`: 17 phản hồi hợp lệ lần đầu, A.8.3 sửa hợp lệ lần hai, không lỗi cuối. Không thay số liệu lịch sử bằng kết quả hồi quy/pilot.
- **Hồ sơ 56:** 29 control có bằng chứng, 19 có nguồn ngoài preset gồm 18 capture lab và A.6.2. Nguồn A.6.2 `bc.docx` chỉ trích xuất 1 ký tự, cần kiểm tra/nộp lại. Có nguồn không đồng nghĩa đủ nội dung; còn 37 control chưa có nguồn ngoài preset.
- **Đối chiếu có hỗ trợ:** Khoa/Tú cùng nộp đủ 18/18 ở lượt `0b7dc9e9`; khớp Agent lần lượt 18/18 và 17/18, đồng thuận 17/18 (94,44%). Nhãn có AI hỗ trợ/chưa khai đủ; phát hiện 9 căn cứ lỗi, tự động khoanh 17 nghi vấn gồm cả bản gốc bị trùng. Giữ nguyên nhãn, không công bố số khớp này là accuracy chuyên gia. Hai nhãn Khoa ở lượt cũ vẫn giữ lịch sử.
- **Nghiệm thu:** chưa có rubric được duyệt, 0/56 quyết định tính áp dụng, 0 thẩm định hiện hành; SoA vẫn dự thảo. Phạm vi 56 không phải toàn bộ Annex A/ISMS.

Tài liệu minh chứng chính:

- [Ma trận 56 control](../docs/MA_TRAN_56_CONTROL.md), [rubric/nguồn 18 A.8 raw](../docs/MA_TRAN_A8.md), [quy trình nghiệm thu](../docs/QUY_TRINH_NGHIEM_THU_A8.md).
- [Kết quả raw v2 và ca sai](../docs/a8-results/KET_QUA_RAW_V2.md), [CSV từng control](../docs/a8-results/raw-v2-combined.csv), [phạm vi và kiểm chứng live v2](../docs/LIVE_A8_V2.md).
- [Đánh giá nguồn nhập theo rubric 56](../docs/a8-results/dossier-capture-evaluations.json), [SoA 56 dự thảo](../docs/a8-results/SOA_56_HIEN_TAI.md), [thu hồ sơ và thẩm định](../docs/THU_HO_SO_VA_THAM_DINH_56.md).
- [Gói bàn giao 113 tiêu chí](../docs/BAN_GIAO_TUAN_05_2026_11_12.md), [theo dõi xử lý](../docs/KE_HOACH_XU_LY_VA_KIEM_TRA_LAI.md), [báo cáo điều phối](../docs/BAO_CAO_DIEU_PHOI_GIANG_VIEN.md).
- [Tích hợp hai nhánh](../docs/TICH_HOP_HAI_NHANH_TUAN_05.md), [hướng dẫn chấm tương tác](../docs/HUONG_DAN_CHAM_THAT_A8.md), [audit căn cứ lưu riêng](../docs/a8-results/review-quality-audit-2026-11-15.json).
- [Bàn giao nghiệm thu bổ sung và checklist UI](../docs/HOAN_THIEN_NGHIEM_THU_2026_11_15.md), [kết quả rà nguồn trong project](../docs/RA_SOAT_NGUON_KIEM_DINH_2026_11_15.md).

## Vướng mắc và giới hạn

- Thiếu nguồn cho 37 control và cần rà chất lượng nguồn đã có, đặc biệt A.6.2. 56 thư mục hồ sơ trên đĩa mới có mẫu/manifest trống; chưa tìm thấy bộ kiểm định mới được xác nhận trong project.
- Chưa thống nhất với giảng viên người đánh giá/phương pháp và chưa có bộ nhãn độc lập đủ điều kiện. Tài khoản riêng, nhãn tự khai hoặc chấm có AI hỗ trợ không tự chứng minh chuyên môn/độc lập.
- Probe và rubric lab chỉ đại diện một phần control; chưa phải tích hợp EDR/IAM/SIEM production, NTP hay VLAN thật. 27 control có kiểm tra lab đại diện; 29 có luồng hồ sơ nhưng chưa có collector chuyên biệt.
- Công cụ Computer Use/browser host chưa kết nối; test/API/build đạt không thay checklist thao tác UI có đăng nhập.
- Tính áp dụng, thẩm định và phê duyệt SoA cần người có trách nhiệm thực hiện. Công cụ nhập gói ứng viên và kiểm tra trùng không tự xác nhận nguồn kiểm định độc lập.

## Việc tiếp tục trong tuần 5

- [x] Chuẩn bị công cụ chấm, khai báo hỗ trợ, báo cáo từng người và kiểm tra căn cứ; giữ nhãn lịch sử, tách giả lập khỏi đối chiếu độc lập.
- [x] Chuẩn bị thu/nhập nguồn ngoài đã chốt, kiểm tra trùng/hash/facts và cơ chế tái đánh giá; chưa coi là đã có nguồn kiểm định mới.
- [x] Chuẩn bị bàn giao, kế hoạch xử lý và xuất báo cáo/SoA; kiểm tra đăng nhập/API cả Khoa/Tú, không tự điền quyết định thực tế.
- [ ] Người phụ trách rà rubric, nguồn chấp nhận và xác nhận phạm vi; thống nhất người đánh giá/phương pháp với giảng viên.
- [ ] Bổ sung nguồn cho 37 control còn thiếu và rà chất lượng/phạm vi 19 control đã có, đặc biệt kiểm tra lại A.6.2.
- [ ] Nhóm cung cấp và xác nhận tập kiểm định chưa dùng phát triển; thu nhãn thật và đo trên tập đó.
- [ ] Kiểm tra thủ công đầy đủ các luồng UI, xuất báo cáo và các trường hợp bị chặn duyệt.
- [ ] Hoàn thiện kế hoạch xử lý, quyết định áp dụng, thẩm định và phê duyệt SoA sau khi đủ điều kiện.

## Việc chuyển tiếp sang tuần 6

Đã lập [kế hoạch tuần 6 — 16/11–22/11/2026](TUAN_06.md), chưa ghi công việc tương lai là đã thực hiện:

- Thu nguồn còn thiếu và xử lý nguồn không đủ nội dung; rà/phê duyệt rubric, quyết định tính áp dụng.
- Có bộ kiểm định mới được xác nhận và người chấm phù hợp trên cùng snapshot; thu kết luận thật và phân tích bất đồng.
- Hoàn tất kiểm thử UI, thẩm định hiện hành, kế hoạch xử lý và trình duyệt SoA.

## Đồng bộ GitHub

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 11/11/2026 | 13:37, 22:27 | Trần Văn Toàn | `main` | Hoàn thiện đánh giá tuân thủ, bằng chứng live và dọn demo; mở rộng 18 probe A.8, nối nguồn với hồ sơ 56 và bổ sung báo cáo |
| 12/11/2026 | 10:22 | Trần Văn Toàn | `main` | Gói bàn giao 56 control, chấm giả định tách riêng, kế hoạch xử lý và báo cáo điều phối |
| 15/11/2026 | 11:37 | Trần Văn Toàn | `main` | Tích hợp hai nhánh, hoàn thiện chấm A.8, kiểm tra nguồn và cập nhật nhật ký tuần 5–6 |

### Hai nhánh thành viên đã có trên GitHub

Đối chiếu remote ngày 15/11. Thời gian dưới đây là **giờ commit (UTC+7), không phải giờ push**; Git không xác nhận người bấm push. Nhánh Tú/Khoa theo phân công người dùng, tác giả Git ghi nguyên.

| Ngày commit | Giờ (UTC+7) | Thành viên / tác giả Git | Nhánh | Commit và nội dung chính |
|---|---|---|---|---|
| 13/11/2026 | 17:59 | Nền chung — Git: `Gera-YCYC` | `Tu/Tuan5`, `Tuan5` | `c29d128`: công cụ tài khoản, CLI và hướng dẫn chấm A.8; một commit chung |
| 13/11/2026 | 18:58, 19:03 | Lê Đoàn Văn Tú — Git: `Lê Tú` | `Tu/Tuan5` | `39c4fae`, `7ee5918`: sửa CLI yêu cầu tự nhập kết luận và xuất UTF-8 |
| 14/11/2026 | 15:32, 15:44 | Nhánh Khoa — Git: `Gera-YCYC` | `Tuan5` | `8a297a4`, `538a5ba`: công cụ PostgreSQL/CLI, pipeline độ đúng và SoA; nhãn tự sinh chưa được công nhận là chấm thật |

Đã tích hợp chọn lọc về main local ngày 15/11; phần tích hợp/sửa bổ sung được đưa vào lần đồng bộ main ghi ở bảng trên. Không nhập các nhãn tự gán người thật hoặc trạng thái SoA tự duyệt từ nhánh nguồn. Không ghi thao tác chạy/dừng hệ thống hoặc chuyển nhánh vào nhật ký.
