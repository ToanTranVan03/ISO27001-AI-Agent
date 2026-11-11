# Bàn giao tuần 5 — đánh giá theo bằng chứng

> Mốc hồ sơ mới: [Nhập nguồn live vào 56, phân loại hỗ trợ khi chấm và danh sách việc còn thiếu](HOAN_THIEN_HO_SO_56.md). Nhãn có AI hỗ trợ/chưa khai báo không được tự tính thành nhãn độc lập. Màn hình nguồn đã tách tiêu chí/artifact để đọc dễ hơn.

> **Mốc mới:** runtime đã có 18 probe đại diện với rubric `a8-live-v2-active`, kiểm chứng 72 tình huống và sửa/khôi phục 5 nguồn thực. Xem [phạm vi và giới hạn live v2](LIVE_A8_V2.md). Các đoạn mô tả 5 probe/pilot v5 bên dưới là mốc trước khi mở rộng; không sửa lại kết quả lịch sử thành 18 probe.

Cập nhật 11/11/2026. Phạm vi vẫn là 56 control A.6–A.8, ưu tiên thực nghiệm 18 A.8. Đây là kế hoạch nghiệm thu và kết quả kiểm chứng kỹ thuật, chưa phải biên bản chuyên gia phê duyệt.

## Phần kỹ thuật đã bổ sung

1. **Thẩm định theo từng tiêu chí cho cả 56 control.** Người chấm ghi đạt/không đạt/chưa rõ, căn cứ và ID bằng chứng cho từng tiêu chí. API chặn bỏ sót, trùng tiêu chí, viện dẫn sai và kết luận không khớp rubric dự án. Thẩm định tổng hợp cũ còn trong lịch sử nhưng không đủ điều kiện duyệt SoA theo giao thức mới `human-criteria-review-v2`.
2. **Chốt nguồn trước suy luận.** Lượt A.8 qua API lưu snapshot cấu hình/log, rubric, thời điểm và recipe trước khi gọi model. Hai engine có thể đánh giá cùng snapshot mà không thu lại nguồn khác. Hash phát hiện thay đổi, không tự chứng minh nguồn đúng hoặc độc lập.
3. **Sửa phản hồi có giới hạn.** Tối đa hai lần gọi model. Chỉ lỗi schema, viện dẫn hoặc mâu thuẫn rubric được yêu cầu sửa một lần; timeout/kết nối không lặp. Không đưa đáp án thiết kế hoặc đáp án luật vào phản hồi sửa. Lỗi lần đầu, proposed status và hash phản hồi vẫn được giữ; lỗi cuối không bị thay bằng kết luận baseline.
4. **Đo tách lần đầu và sau sửa.** Báo cáo có `first_pass_accuracy`, accuracy cuối, số ca sửa và số ca duy nhất/số lượt. Ca không có nhãn vẫn là chưa đo; không gộp 13 control chưa có probe thành độ đúng của 5 probe.
5. **Phân tích người chấm.** Nhãn phải khớp report/evidence hash; từng người có bảng riêng. Có bảng bất đồng Agent/người chấm và người/người, agreement và Cohen's kappa trên các cặp có nhãn. Không lấy đa số làm đáp án, không sửa nhãn mù gốc, không ghép các nhãn rời của nhiều người thành một đáp án tổng.
6. **Nhận bộ nguồn tách riêng.** CLI nhận thư mục raw khác bộ tích hợp, chốt snapshot và dò trùng nội dung với 108 ca đã biết, bỏ qua metadata capture khi dò trùng. Đổi tên asset hoặc ngày không biến ca cũ thành held-out. Kết quả luôn là ứng viên cần người xác nhận, không tự chứng nhận độc lập.

## Kết quả kiểm chứng mới

- [Lượt pilot live v5](a8-results/live-v5-pilot.json), [gói chốt trước chạy](a8-results/live-v5-sealed-plan.json), [đối chiếu cùng nguồn](a8-results/live-v5-paired-check.json).
- Nguồn mixed: 5 control có quan sát; 13 control không có probe trả thiếu bằng chứng, không gọi LLM.
- Trong 5 control có probe: A.8.3 lần đầu mâu thuẫn rubric, model sửa hợp lệ ở lần hai; 4 control còn lại hợp lệ lần đầu. Không còn lỗi cuối trong **một lượt pilot này**, không khẳng định model hết lỗi.
- Baseline chạy trên chính snapshot đó để kiểm tra quan hệ nguồn/kết quả. Chưa có nhãn con người nên **không công bố accuracy live**.
- Báo cáo raw v2 206/216 vẫn giữ nguyên; không dùng pilot mới thay số đo lịch sử.
- Kiểm tra API thật: danh mục/SoA 56 dòng, chi tiết tiêu chí đủ 56. Đợt hiện tại có 15 control có bằng chứng, 1 control có nguồn nộp ngoài preset, chưa có quyết định áp dụng/rubric được duyệt/thẩm định hiện hành. Đây là số lượng hồ sơ, không phải số control đạt.
- Công cụ browser/native không kết nối được trong phiên kiểm tra. Build/lint/API/test không thay việc kiểm tra bấm toàn bộ UI. Không đánh dấu mục UI hoàn tất.

## Phân công chuẩn bị cho ba thành viên

Theo danh sách người dùng cung cấp; phân công dưới đây phục vụ tổ chức chấm, chưa phải xác nhận những người này đã thực hiện.

| Người | Vai trò chuẩn bị | Sản phẩm cần chính người đó xác nhận |
|---|---|---|
| Trần Văn Toàn | Điều phối, rà rubric/phạm vi, chuẩn bị nguồn và trình duyệt | Căn cứ ngưỡng lab, tính áp dụng 56 control, kế hoạch xử lý và SoA |
| Lê Đăng Khoa | Người chấm B, tài khoản riêng | Chấm cùng nguồn trước khi xem Agent/đáp án, nêu căn cứ từng control |
| Lê Đoàn Văn Tú | Người chấm C, tài khoản riêng | Chấm riêng, chưa xem nhãn của Khoa; sau đó phân tích bất đồng |

Cả ba là thành viên nhóm phát triển. Hai người chấm khác tài khoản **không đồng nghĩa chuyên gia độc lập bên ngoài**. Ghi nhận mức đã tiếp xúc mã/đáp án; nếu đã thấy bộ replay thì chỉ dùng bộ đó cho hồi quy hoặc đối chiếu nội bộ. Nhờ giảng viên/người phù hợp rà rubric và tập kiểm định mới nếu cần kết luận chuyên môn độc lập. Không tạo tài khoản, chữ ký, nhãn hoặc phê duyệt thay thành viên.

## Thao tác để hoàn tất hồ sơ

1. Toàn cùng người phụ trách đọc [ma trận 56](MA_TRAN_56_CONTROL.md), rubric và checklist nguồn. Xác nhận ngưỡng là chính sách lab, không tự gán là yêu cầu nguyên văn ISO. Phê duyệt trong ứng dụng bằng danh tính thật.
2. Thu nguồn còn thiếu vào gói của từng control; ghi thời điểm, chủ sở hữu và phần chỉ mô phỏng. A.7 cần hồ sơ/quan sát vật lý phù hợp; không suy ra từ inventory thiết bị.
3. Trong **Phạm vi 56**, chạy Agent trên hồ sơ đã thu; người chấm điền từng tiêu chí, chọn đúng nguồn, rồi ghi kết luận tổng. Khi còn chưa rõ, giữ thiếu bằng chứng thay vì ép đạt.
4. Chạy A.8 bằng người điều phối; Khoa và Tú dùng tài khoản riêng, chấm mù đủ 18 trên cùng gói. Không tự tạo lượt để xem đáp án trước. Không dùng test tự động nhập nhãn làm kết quả người thật.
5. Xuất phân tích từng người và bảng bất đồng. Thảo luận căn cứ, giữ nhãn ban đầu; nếu đổi rubric thì lập phiên bản/tập đo mới, không sửa báo cáo cũ để tăng điểm.
6. Chốt tập kiểm định mới **trước** khi xem dự đoán; nguồn không dùng sửa prompt/guard. Tách tập phát triển và kiểm định bằng nội dung, không bằng tên profile. Đo mẫu đủ đa dạng và ghi số ca/lượt/phạm vi từng control.
7. Toàn ghi quyết định áp dụng, lý do loại trừ hợp lệ và kế hoạch khắc phục/duy trì; người có trách nhiệm duyệt SoA khi đủ điều kiện. Kết quả không đạt vẫn được đưa vào SoA với kế hoạch xử lý, không tự đổi thành đạt.

## Chốt nguồn trước đo bằng CLI

```powershell
.venv\Scripts\python.exe -m agent_core.a8_protocol prepare --profile mixed --transport live --coordinator "Tran Van Toan" --objective "Live pilot, not independent validation" --output work/plan-moi.json
.venv\Scripts\python.exe -m agent_core.a8_protocol execute --plan work/plan-moi.json --mode rules --output work/rules-cung-nguon.json
.venv\Scripts\python.exe -m agent_core.a8_protocol execute --plan work/plan-moi.json --mode llm --output work/llm-cung-nguon.json
```

Nhập nguồn mới theo định dạng raw hiện hành (`<root>/<profile>/A.8.x/<artifact>`), đủ 18 control:

```powershell
.venv\Scripts\python.exe -m agent_core.a8_protocol prepare --profile mixed --transport files --raw-root data/a8-validation/dot-moi --coordinator "Tran Van Toan" --objective "Candidate dataset awaiting independent review" --output work/ung-vien-kiem-dinh.json
```

Thư mục mẫu trống hoặc bản sao ca cũ không phải tập kiểm định hợp lệ. CLI không gắn nhãn thiết kế replay cho dữ liệu mới. Việc không trùng hash chưa chứng minh độc lập về nội dung; người phụ trách vẫn phải xác nhận nguồn, lịch sử tiếp xúc và nhãn trước khi công bố kết quả.

## Điều kiện còn chờ người thật

- [ ] Xác nhận rubric, phạm vi nguồn và mức độc lập của người chấm.
- [ ] Cung cấp nguồn có nội dung phù hợp cho các control còn thiếu.
- [ ] Khoa và Tú thực sự chấm, nêu căn cứ và phân tích bất đồng.
- [ ] Có bộ kiểm định chưa dùng phát triển, nhãn được chốt và kết quả đo trên bộ đó.
- [ ] Kiểm tra thao tác UI có đăng nhập và xuất báo cáo.
- [ ] Người có trách nhiệm duyệt tính áp dụng/kế hoạch/SoA.

Không đóng các mục này bằng dữ liệu giả hoặc thao tác của trợ lý thay người đánh giá. Hoàn thiện phần mềm và nghiệm thu chuyên môn là hai mốc khác nhau.
