# Tuần 6 — Hoàn thiện bằng chứng, kiểm định và hồ sơ đánh giá tuân thủ

- Thời gian: **16/11/2026–22/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Đang thực hiện.**
- Lập kế hoạch: **15/11/2026**.
- Cập nhật: **21/11/2026**.

## Mục tiêu và kế hoạch

Giữ phạm vi 56 control (8 A.6, 14 A.7, 34 A.8), ưu tiên kiểm định sâu 18 A.8 theo góp ý giảng viên. Tuần 6 tập trung bổ sung nguồn, nâng chất lượng kết luận và hoàn thiện hồ sơ nghiệm thu; không mở rộng văn phòng 3D.

- [ ] Thống nhất với giảng viên/người phụ trách rubric, phạm vi nguồn và người đánh giá được chấp nhận; ghi nhận phiên bản và căn cứ xác nhận.
- [ ] Thu nguồn có nội dung cho 37 control còn thiếu; rà mức bao phủ của 19 control đã có nguồn, đặc biệt kiểm tra lại A.6.2 chỉ trích xuất được 1 ký tự.
- [ ] Chuẩn bị bộ nguồn kiểm định mới, xác nhận lịch sử tiếp xúc và chốt snapshot trước khi chạy/chấm; không dùng lại fixture đã biết rồi gọi là tập độc lập.
- [ ] Tổ chức người đánh giá đọc và chấm trên cùng mã lượt/bằng chứng; khai đúng mức hỗ trợ, giữ riêng kết quả có AI hỗ trợ và nhãn luyện tập.
- [x] Hoàn thiện phân tích kỹ thuật bất đồng/căn cứ và sai khác từng tiêu chí lab; lưu báo cáo riêng, giữ nhãn khóa và kết quả cũ.
- [ ] Người đánh giá rà và xác nhận xử lý các bất đồng thực tế; chưa thay bằng kết quả phân tích của trợ lý.
- [x] Chạy Agent trên 18 nguồn A.8 lab hiện hành, xuất kết quả từng control và giữ riêng các lần lỗi/kiểm tra lại.
- [x] Mở rộng thực nghiệm phát triển bằng 38 hồ sơ mô phỏng ngoài nhóm 18 A.8; chạy Agent, giữ lỗi/thử lại và xuất kết quả từng control.
- [ ] Đánh giá trên nguồn được chấp nhận trong phạm vi 56; đo độ đúng bằng bộ kiểm định và nhãn người đánh giá đủ điều kiện. Bộ phát triển 38 hồ sơ chưa hoàn tất mục này.
- [ ] Kiểm thử đầy đủ giao diện bằng các tài khoản: đọc/thu nguồn, chấm, khóa nhãn, cập nhật tiến độ, xuất báo cáo và các trường hợp bị chặn.
- [ ] Người phụ trách ghi 56 quyết định tính áp dụng, lý do và kế hoạch xử lý/duy trì; bổ sung người nhận, hạn và cách kiểm tra lại.
- [ ] Thẩm định từng tiêu chí trên nguồn hiện hành, hoàn thiện và trình người có trách nhiệm phê duyệt SoA khi đủ điều kiện.

Phần triển khai kỹ thuật đã hoàn thành trong tuần:

- [x] Kiểm tra nội dung nguồn trước suy luận, giữ dữ liệu cũ và yêu cầu nộp lại nguồn không dùng được.
- [x] Trực quan hóa và thống nhất bốn màn hình; phân biệt kết quả, tiến độ, bằng chứng và thẩm định.
- [x] Nối ngữ cảnh đợt/control/nhân viên/lượt nguồn giữa bốn màn hình; giữ mục đang xem khi tải lại hoặc Back/Forward, nhập nguồn A.8 dẫn về đúng hồ sơ và lọc nhân viên theo viện dẫn bằng chứng.
- [x] Bổ sung xem trước thay đổi doanh nghiệp, kiểm tra snapshot và lịch sử người cập nhật/giá trị trước–sau.
- [x] Nộp nguồn gốc trên web cho 56 control, lưu/tải bản gốc có hash và nối nguồn với hàng đợi đánh giá.
- [x] Kiểm tra lặp API bằng ba tài khoản và lưu báo cáo 39 bước ngày 20/11; chưa thay kiểm thử toàn UI.
- [x] Kiểm chứng mã/API và giao dịch PostgreSQL rollback; chưa thay cho kiểm thử đầy đủ UI hoặc nghiệm thu chuyên môn.
- [x] Bổ sung bảng điều kiện trình duyệt SoA theo từng control, cảnh báo hạn và chặn thiếu thông tin kế hoạch/nguồn thẩm định không dùng được.
- [x] Chuyển chạy lô nguồn sang server, lưu tiến độ PostgreSQL, chặn lô trùng, dừng có kiểm soát và ghi gián đoạn khi API khởi động lại.
- [x] Kiểm soát kích thước đầu vào/context model, giữ nguồn không cắt âm thầm; không hiển thị kết luận cũ như hiện hành khi job mới lỗi.
- [x] Đồng nhất bộ lọc chất lượng căn cứ của báo cáo CLI/web; hiển thị lỗi API có cấu trúc và phân biệt kế hoạch nháp với điều kiện trình duyệt.
- [x] Tách phiếu nguồn thiếu/không dùng được với rà mức bao phủ; kiểm thử Edge ba tài khoản cho điều hướng, xuất SoA và từ chối tệp lỗi. Chưa thay kiểm thử toàn bộ thao tác nộp/chấm/duyệt.
- [x] Bổ sung sổ xử lý bất đồng theo lượt/control/hash, lưu người ghi và thời điểm; xuất riêng và cùng báo cáo điều phối, không sửa nhãn khóa hoặc số liệu đối chiếu.
- [x] Bổ sung bảng hướng dẫn hoàn tất theo hồ sơ hiện hành: vai trò, bước làm, điều kiện kiểm tra, mở đúng control và xuất checklist. Chuẩn bị hướng dẫn cụ thể cho nhóm về nguồn, bộ kiểm định, chấm, thẩm định và SoA.
- [x] Mở rộng kiểm thử Edge cho nộp nguồn hợp lệ/tải bản gốc, chặn token thẩm định cũ, thẩm định tiêu chí/lưu kế hoạch nháp và nộp/khóa nhãn mù sau tải lại bằng phản hồi API mô phỏng; tách kết quả mô phỏng khỏi kiểm thử ghi thật và nghiệm thu chuyên môn.
- [x] Bổ sung kiểm thử tích hợp ghi thật trên PostgreSQL/backend/Edge cô lập: nguồn, thẩm định, kế hoạch, chu kỳ duyệt/hết hiệu lực SoA và hai tài khoản thử chấm 36 nhãn có hỗ trợ. Dữ liệu tổng hợp, không nhập vào đợt chính; giữ lần lỗi và dọn database thử.
- [x] Tích hợp khu lab hồ sơ riêng trong Doanh nghiệp, lịch sử chọn lượt, đọc/xuất nguồn và phiếu rà tiêu chí; kiểm tra phản hồi gốc/viện dẫn/hash. Lượt mới chốt snapshot/hash khóa trước suy luận, lượt cũ giữ cảnh báo chưa chốt; không cộng dữ liệu này vào nghiệm thu đợt chính.
- [x] Siết kiểm tra gói ứng viên: dò bản sao chỉ đổi định dạng JSON/xuống dòng cấu hình, kiểm tra kiểu snapshot/facts/artifact và trả 422 thay lỗi server. Giữ byte/hash gốc; không coi dò trùng là xác minh độc lập.
- [x] Bổ sung phiếu kiểm tra gói có hash/số artifact/tiêu chí chưa rõ và xuất JSON; yêu cầu kiểm tra lại khi đổi engine. Kiểm thử Edge chạy/dừng lô, giữ tiến độ sau tải lại, xuất lượt và chặn gói lỗi/lượt trùng bằng API mô phỏng.
- [x] Xuất lại snapshot bàn giao, 38 yêu cầu cung cấp/thay nguồn và 18 yêu cầu rà mức bao phủ theo API ngày 21/11; tách ba nhóm nguồn và hướng dẫn thao tác cho các việc cần nhóm xác nhận.
- [x] Kiểm thử ghi thật luồng lô/dừng/chạy tiếp bằng Ollama trên database riêng; nhập gói ứng viên qua worker luật, hai tài khoản thử đọc cùng gói mù. Sửa lưu JSON nguyên tử khi Windows tạm giữ tệp; giữ báo cáo lỗi và bản ghi cũ khi hết lượt thử.
- [x] Chạy đủ gói ứng viên kỹ thuật 18 control bằng Qwen thật, giữ snapshot/đường nguồn và số lần gọi; kiểm tra ngắt backend thử giữa lúc worker chạy, phục hồi trạng thái gián đoạn, mở khóa và giữ kết quả cũ. Không gọi gói hồi quy này là bộ kiểm định độc lập.
- [x] Nhập quyết định/kế hoạch theo lô có mẫu 56 dòng, xem trước thay đổi, kiểm tra quyền/đợt/fingerprint và lưu nguyên tử với danh tính/mã lô; không tự chọn tính áp dụng hoặc phê duyệt. Kiểm thử 55 quyết định tổng hợp trên database riêng và API xem trước không ghi vào đợt chính.

Chỉ đánh dấu hoàn thành khi có kết quả và minh chứng. Hoàn thành phần mềm, có nguồn hoặc chạy xong không đồng nghĩa control tuân thủ hay đã nghiệm thu chuyên môn.

## Công việc chuyển tiếp từ tuần 5

- Phần mềm đã có luồng đánh giá 56 control, probe đại diện 18 A.8, chấm mù, báo cáo, SoA dự thảo và công cụ nhập gói nguồn ngoài đã chốt.
- Còn 37 control thiếu nguồn ngoài preset; nguồn A.6.2 cần kiểm tra nội dung. Chưa có bộ kiểm định mới được xác nhận trong project.
- Hai tài khoản đã nộp đủ trên cùng lượt nhưng có AI hỗ trợ/chưa khai đủ; phát hiện 9 căn cứ cần rà. Giữ kết quả này làm lịch sử đối chiếu có hỗ trợ, không coi là bộ nhãn độc lập.
- Rubric, quyết định áp dụng, thẩm định hiện hành, kiểm thử toàn UI và phê duyệt SoA chưa hoàn tất.

Các thông tin trên là **trạng thái bàn giao từ tuần 5**, không phải kết quả thực hiện tuần 6.

## Nhật ký công việc chính

| Ngày | Công việc | Kết quả / minh chứng |
|---|---|---|
| 18/11/2026 | Củng cố kiểm tra nội dung nguồn và đầu vào Agent | Chặn tài liệu quá ít/ký tự lặp khi nạp mới, lọc nguồn cũ trước suy luận, giữ lịch sử; thêm cảnh báo và việc yêu cầu nộp lại trên Phạm vi 56 |
| 18/11/2026 | Kiểm chứng và rà nguồn A.6.2 | Nguồn 1 ký tự không đưa vào model; Mốc đầu: 253 test Python, 5 test JavaScript, lint/build đạt. Không coi ngưỡng văn bản là đủ bằng chứng tuân thủ |
| 18/11/2026 | Thống nhất giao diện hệ thống đánh giá | Bản đồ 56 control, tiến độ/Agent đang chạy, tìm kiếm và lọc; sắp xếp bốn màn hình, thu gọn quản trị/JSON, tách luyện tập khỏi chấm thật; giữ tên ISO 27001 và mô tả luôn hiện, điều hướng xuống hàng khi cửa sổ hẹp |
| 18/11/2026 | Hoàn thiện quản lý thay đổi doanh nghiệp | Xem trước và xác nhận trước khi lưu; chặn snapshot cũ; tra lịch sử theo nhân viên, người cập nhật và giá trị trước–sau |
| 18/11/2026 | Bổ sung tiếp nhận nguồn và bản gốc trên web | Hỗ trợ tài liệu/log/cấu hình/JSON/CSV cho 56 control; khai xuất xứ, thời điểm và giới hạn mẫu; kiểm tra đầu vào, chống nạp lại cùng nguồn, lưu/tải bản gốc theo quyền và SHA256 |
| 18/11/2026 | Nối hồ sơ đã nộp với công việc chung | Control chưa có collector riêng được đánh giá từ nguồn đã thu; nguồn không dùng được không thay bằng preset; bổ sung cảnh báo chất lượng nguồn trong hồ sơ bàn giao |
| 18/11/2026 | Kiểm chứng tổng hợp sau triển khai | 282 test Python, 7 test JavaScript, lint/build và render đạt; PostgreSQL thật kiểm tra lưu/nạp lại/tải bản gốc/đầu vào Agent bằng giao dịch rollback, không để lại dữ liệu thử; API đang chạy kiểm tra từ chối nguồn lỗi và giữ hồ sơ nguyên trạng |
| 18/11/2026 | Bổ sung hồ sơ tài khoản và vai trò người dùng | Hiển thị quản trị viên/người đánh giá, phân biệt tài khoản hệ thống với nhân viên giả lập; sửa họ tên, email, đơn vị và chức danh của chính mình; không cho tự đổi tên đăng nhập/quyền |
| 18/11/2026 | Kiểm chứng chức năng tài khoản | Mốc mới: 289 test Python, lint/build đạt; API hồ sơ hoạt động, từ chối tự đổi quyền và kiểm tra đúng tài khoản đăng nhập; chưa thay kiểm thử toàn bộ trình duyệt |
| 18/11/2026 | Hoàn thiện kiểm tra hồ sơ trước trình duyệt SoA | Control áp dụng cần thẩm định hiện hành, kế hoạch, người nhận, hạn/kỳ rà và cách kiểm tra lại; bổ sung giao thức/fingerprint mới, giữ lịch sử duyệt cũ |
| 18/11/2026 | Theo dõi việc cần bổ sung và hạn kế hoạch | Bảng 56 control có lý do bị chặn, lọc/tìm, mở đúng hồ sơ và xuất JSON/Markdown; nhắc rà hạn đã qua nhưng không tự gia hạn hoặc kết luận công việc đã/chưa hoàn tất |
| 18/11/2026 | Củng cố thẩm định và kiểm chứng SoA | Chặn kết luận đạt/không đạt từ nguồn không dùng được; 295 test Python, 7 test JavaScript, lint/build/render đạt; API thật chặn duyệt thiếu điều kiện và thẩm định nguồn lỗi, không lưu dữ liệu thử; kiểm thử toàn UI vẫn còn chờ |
| 18/11/2026 | Tự động hóa lượt đánh giá nguồn trên server | Không phụ thuộc giữ trang mở; lô hữu hạn, mỗi control tối đa một lần; giữ tiến độ/lỗi/bỏ qua, kiểm tra token nguồn/rubric và khóa job; kiểm chứng PostgreSQL bằng rollback |
| 18/11/2026 | Chạy thực tế và xử lý lỗi Agent | Lô 18 control đầu có 16 job lưu kết quả, 2 lỗi; tăng giới hạn phản hồi chưa đủ, sau sửa đóng gói/context hai lượt kiểm tra lại lưu được kết quả. Giữ mọi job cũ, không sửa thành thành công |
| 18/11/2026 | Xuất kết quả và kiểm chứng sau sửa | Kết quả máy mới nhất của 18 control: 3 không tuân thủ, 6 một phần, 9 thiếu bằng chứng; không phải độ đúng so với người chấm. 308 test Python, 7 test JavaScript, lint/build/render đạt; nguồn/rubric giữa các lần kiểm tra lại không đổi |
| 18/11/2026 | Tách yêu cầu bổ sung nguồn theo nhóm phụ trách | Xuất 38 phiếu: Nhân sự 8, Hành chính/vật lý 14, IT/ATTT 16; có tiêu chí, loại nguồn, checklist và chỗ ghi người nhận/hạn; phân biệt thiếu nguồn với nguồn lỗi. 310 test Python, lint/build đạt; không tự tạo bằng chứng hoặc xác nhận giao việc |
| 20/11/2026 | Tách kiểm tra gói kiểm định trước khi chạy | Admin kiểm tra nguồn/hash/rubric/facts và phần chưa rõ trước khi xác nhận chạy; preflight không gọi model, không tạo lượt hoặc lưu nhãn. 310 test hồi quy trước bổ sung và test mới về phân quyền/không tạo tác dụng phụ đạt; lint/build đạt. Chưa có bộ kiểm định mới được xác nhận |
| 20/11/2026 | Tự động kiểm tra nghiệm thu API ba tài khoản | CLI chạy lặp; 39/39 bước API thật bằng admin/Khoa/Tú đạt, gồm đọc bốn khu vực và chặn quyền sai/khác đợt. Không ghi mật khẩu/token, tạo lượt model, nhãn hoặc phê duyệt; mốc 314 test Python trước khi bổ sung kiểm thử Edge |
| 20/11/2026 | Đồng nhất báo cáo và điều kiện trình duyệt | Báo cáo CLI/web lọc căn cứ chưa đủ điều kiện; giao diện hiện lý do lỗi 409/422, tài liệu và form phân biệt lưu kế hoạch nháp với đủ điều kiện duyệt SoA |
| 20/11/2026 | Cập nhật yêu cầu nguồn và mức bao phủ | 38 yêu cầu cung cấp/thay nguồn (37 thiếu, A.6.2 cần thay), tách 18 yêu cầu rà mức bao phủ; xuất theo nhóm, cập nhật danh sách công việc từ API; không tự gán người/hạn |
| 20/11/2026 | Kiểm thử giao diện bằng Edge | Ba kịch bản admin/Khoa/Tú đạt: đăng nhập/đăng xuất, bốn màn hình, xuất SoA 56 dòng, chặn duyệt thiếu điều kiện, ẩn nút chạy lô với người chấm; admin nộp tệp một ký tự bị từ chối 422, form nhắc kế hoạch thiếu |
| 20/11/2026 | Bổ sung sổ xử lý bất đồng và căn cứ cần rà | Biên bản riêng gắn control/hash nguồn, người ghi/thời điểm; lịch sử chỉ bổ sung, xuất JSON/Markdown cùng báo cáo; kiểm tra quyền, hash, schema và không lộ sổ trong gói mù; không sửa nhãn, độ đúng hoặc phê duyệt |
| 20/11/2026 | Kiểm chứng cuối ngày 20/11 | 319 test Python, 9 test JavaScript, lint/build và 3 kịch bản Edge đạt. API lưu sổ kiểm tra bằng dữ liệu test tạm; form lưu dùng POST giả lập trên Edge, không ghi biên bản thử vào lượt thật |
| 21/11/2026 | Hướng dẫn hoàn tất và mở rộng kiểm thử UI | Checklist bảy bước theo dữ liệu hiện hành, mở đúng control và xuất hướng dẫn; 11 test JavaScript và 5 kịch bản Edge đạt, gồm thao tác ghi bằng API mô phỏng; không nộp nhãn/quyết định thật |
| 21/11/2026 | Kiểm thử tích hợp ghi thật trên môi trường riêng | PostgreSQL/backend/Edge thật, kho tệp và tài khoản thử tổng hợp; kiểm tra nguồn/thẩm định/kế hoạch, duyệt SoA thử rồi hết hiệu lực khi nguồn đổi; hai tài khoản nộp 36 nhãn có hỗ trợ. Lần 3 đạt, giữ hai lần lỗi và dọn database thử; số dòng ba bảng chính trước/sau không đổi |
| 21/11/2026 | Bổ sung 38 hồ sơ doanh nghiệp mô phỏng | 8 A.6, 14 A.7 và 16 A.8 ngoài nhóm 18; tình huống đúng/sai/thiếu có nội dung, nguồn do trợ lý tạo và khóa thiết kế tách khỏi đầu vào model; khu lab riêng không cộng vào hồ sơ nghiệm thu |
| 21/11/2026 | Chạy Agent và giữ lỗi/ca lệch | Qwen2.5:7b chạy 38/38 ca; 3 lỗi cấu trúc đầu, thử lại một lần bằng JSON Schema còn 0 lỗi cấu trúc. Khớp khóa thiết kế 22/38 lần đầu, 23/38 sau thử lại (60,53%); 15 ca lệch giữ nguyên, chưa phải accuracy so với con người |
| 21/11/2026 | Rà sai khác từng tiêu chí và chốt khóa cho lượt mới | 18 control lệch ít nhất một tiêu chí, tổng 19 tiêu chí khác khóa; A.6.3/A.6.5/A.7.11 trùng kết luận tổng nhưng tiêu chí vẫn lệch. UI có lý do, nguồn/hash, chọn lượt và xuất phiếu rà; khóa/hash được lưu trước lượt mới, không gán hồi tố cho lượt cũ |
| 21/11/2026 | Kiểm chứng cuối đợt cập nhật | 337 test Python, 11 test JavaScript, 5 kịch bản Edge và lint/build đạt; có thêm một kịch bản tích hợp ghi thật cô lập. Không sửa nhãn, xác nhận chuyên môn hoặc duyệt SoA đợt chính |
| 21/11/2026 | Hoàn thiện liên kết và khôi phục mục đang xem | Nhân viên → hồ sơ → control → lượt A.8; tải lại/Back giữ ngữ cảnh. Khởi tạo lựa chọn control từ đường dẫn ngay khi tải; giữ kiểm tra quyền và chấm mù |
| 21/11/2026 | Siết gói kiểm định và mở rộng kiểm thử tuần 6 | Dò bản sao chỉ đổi định dạng, chặn snapshot/facts/artifact sai kiểu; phiếu kiểm tra và xuất JSON; kiểm thử UI lô/dừng/gói bằng phản hồi mô phỏng. 339 test Python, 14 test JavaScript, 8 kịch bản Edge và lint/build đạt; API thật từ chối gói sao chép và snapshot lỗi bằng 422, không tạo lượt hoặc đổi fingerprint SoA |
| 21/11/2026 | Rà tồn đọng và chuẩn bị bàn giao nguồn | API xác nhận 37 control thiếu nguồn, A.6.2 cần thay; xuất lại 38 phiếu theo ba nhóm và 18 phiếu rà mức bao phủ. 56 quyết định áp dụng, thẩm định hiện hành, rubric và SoA vẫn chờ người phụ trách; không ghi nhận đã thực hiện thay nhóm |
| 21/11/2026 | Kiểm thử điều phối ghi thật và sửa lỗi lưu Windows | Lô hai control dùng Ollama thật: dừng sau A.6.1, lượt mới chỉ chạy A.6.2; cả hai job thành công. Gói ứng viên luật đủ 18 bản ghi, hai tài khoản thử cùng hash/gói mù. Lần đầu lỗi thay tệp quyết định được giữ; sửa tệp tạm riêng và thử lại có giới hạn, lần sau hai kịch bản ghi thật đạt. 345 test Python, 14 test JavaScript và lint/build đạt; database thử đã dọn, fingerprint/trạng thái nghiệm thu chính không đổi |
| 21/11/2026 | Kiểm chứng gói LLM và phục hồi sau ngắt API | Qwen2.5:7b trả đủ 18 bản ghi hợp lệ lần đầu trên gói hồi quy kỹ thuật; không fallback luật. Ngắt backend thử: job/lô gián đoạn, control được mở khóa, giữ kết quả cũ và snapshot; hai tài khoản thử cùng gói mù. Giữ lần lỗi bộ kiểm tra đọc nhầm endpoint và báo cáo chạy lại đạt; không phải đo độ đúng với người chấm |
| 21/11/2026 | Bổ sung nhập tính áp dụng và kế hoạch theo lô | Xuất mẫu 56 dòng không tự điền; xem trước, chặn sai đợt/fingerprint/dòng trùng/ngày sai và không có quyền, lưu một lô có lịch sử. Ghi thử 55 quyết định trên database riêng; API chính chỉ xem trước và giữ 0 quyết định. 355 test Python, 14 test JavaScript, 8 kịch bản Edge thường, hai kịch bản ghi thật và phép thử khởi động lại đạt; lint/build đạt |

## Kết quả và minh chứng

Cập nhật sửa lỗi F5: đã tách khôi phục ngữ cảnh khỏi cuộn tới chi tiết. Tải lại giữ control/nhân viên đang chọn nhưng mở đầu trang; chỉ cuộn khi chủ động mở hồ sơ. Kiểm tra cả Tổng quan, Hồ sơ ISO và Doanh nghiệp, không gửi POST chạy Agent khi F5. **355 test Python, 14 test JavaScript, 9 kịch bản Edge và lint/build đạt**; [báo cáo UI](../docs/a8-results/f5-scroll-ui-2026-11-21.json). Đã build và xác nhận cổng 8000 phục vụ đúng bản sửa; các mốc 8 kịch bản dưới đây là lịch sử trước sửa lỗi này.

### Trạng thái chốt ngày 21/11

- **Liên kết giao diện bổ sung:** đã kiểm chứng điều hướng nhân viên → hồ sơ → control → lượt A.8 và quay lại; 14 test JavaScript, 6 kịch bản Edge và lint/build đạt. POST nhập nguồn trong kịch bản điều hướng được mô phỏng; fingerprint SoA và trạng thái nghiệm thu đợt chính không đổi. Không tự chạy Agent hoặc duyệt khi chuyển màn hình.
- **Kiểm tra ghi sau nối điều hướng:** một kịch bản PostgreSQL/backend/Edge cô lập đạt, gồm nguồn/thẩm định/kế hoạch/SoA và hai tài khoản thử. Hai lần lỗi thư mục kết quả được giữ lại; đã tách thư mục Playwright từng lượt và 5 test bảo vệ database đạt. Database thử được dọn, ba bảng chính không đổi; không tạo phê duyệt hay nhãn người thật.

- **Kiểm chứng phần mềm mới nhất:** 355 test Python, 14 test JavaScript, 8 kịch bản Edge thường và lint/build đạt. Bộ tích hợp mở rộng có hai kịch bản ghi thật, gói 18 control dùng Qwen2.5:7b và phép thử khởi động lại backend riêng đạt; giữ riêng lỗi bộ kiểm tra ở lượt trước. Nguồn ứng viên trong phép thử là fixture đã sửa, không phải kiểm định độc lập. Database thử đã dọn; API chính chỉ xem trước gói quyết định, giữ 0 quyết định và fingerprint/trạng thái nghiệm thu không đổi. Các mốc trong bảng là lịch sử, không cộng dồn số test.
- **18 nguồn A.8 hiện hành:** đã lưu kết quả thực thi; kết luận máy mới nhất gồm 3 không tuân thủ, 6 một phần, 9 thiếu bằng chứng. Không phải độ đúng so với người chấm.
- **38 hồ sơ phát triển:** chạy đủ, giữ phản hồi gốc và 3 lần thử lại lỗi; khớp khóa thiết kế 23/38 sau thử lại. Có 15 control lệch kết luận tổng, 18 control lệch tiêu chí và tổng 19 tiêu chí khác khóa. Đây là bộ do trợ lý tạo, chưa được xác nhận chuyên môn hoặc tính độc lập.
- **Đợt đánh giá chính:** 19/56 control có nguồn ngoài preset, 18 qua ngưỡng nội dung; 37 còn thiếu nguồn được chấp nhận và A.6.2 cần thay nguồn. Chưa có quyết định áp dụng/thẩm định hiện hành; rubric và SoA chưa được phê duyệt. Hồ sơ mô phỏng mới không tự thay đổi trạng thái này.
- **Khóa thiết kế:** lượt lab mới lưu snapshot/hash trước suy luận; lượt cũ ghi `LEGACY_CURRENT_KEY_NOT_FROZEN`. Không xác nhận hồi tố hoặc sửa đáp án/nhãn để tăng điểm.

### Tài liệu đối chiếu

- [Nhập quyết định và kế hoạch theo lô](../docs/NHAP_QUYET_DINH_KE_HOACH_THEO_LO.md): mẫu, trường dữ liệu, xem trước và lịch sử; [gói LLM/phục hồi đạt](../docs/a8-results/isolated-llm-restart-2026-11-21-retry.json), [API xem trước không ghi](../docs/a8-results/decision-batch-preview-2026-11-21.json).
- [Kiểm thử điều phối ghi thật](../docs/KIEM_THU_DIEU_PHOI_GHI_THAT.md): lô/dừng/chạy tiếp, gói ứng viên, hai tài khoản thử và sửa lỗi lưu JSON Windows; [báo cáo đạt](../docs/a8-results/isolated-orchestration-2026-11-21-retry.json) giữ riêng với [lần đầu lỗi](../docs/a8-results/isolated-orchestration-2026-11-21.json).
- [Chốt việc theo snapshot 21/11](../docs/CHOT_VIEC_TUAN_06_2026_11_21.md): trạng thái API, ba nhóm phiếu nguồn, các bước và đầu vào nhóm cần thực hiện; [8 kịch bản Edge](../docs/a8-results/week6-ui-2026-11-21.json), [kiểm tra API gói lỗi](../docs/a8-results/week6-preflight-api-2026-11-21.json).
- [Liên kết bốn màn hình](../docs/LIEN_KET_DIEU_HUONG_HE_THONG.md): cách đi theo control/nhân viên/lượt nguồn, khôi phục đường dẫn và giới hạn kiểm chứng.
- [Kết quả 18 nguồn A.8](../docs/KET_QUA_DANH_GIA_NGUON_18_2026_11_18.md): job, lỗi và kết quả từng control.
- [Kết quả 38 hồ sơ mô phỏng](../docs/KET_QUA_LAB_HO_SO_38_2026_11_21.md): snapshot nguồn, phản hồi đầu/thử lại và khóa thiết kế.
- [Rà sai khác tiêu chí lab 38](../docs/RA_SAI_KHAC_TIEU_CHI_LAB_38.md): 19 tiêu chí cần rà, lý do model và viện dẫn/hash; chưa kết luận bên nào đúng.
- [Kiểm thử ghi thật cô lập](../docs/KIEM_THU_GHI_THAT_CO_LAP.md): môi trường riêng, báo cáo ba lần chạy và giới hạn; không tạo chấm/phê duyệt thật cho nhóm.
- [Kiểm thử Edge và cách chạy lại](../docs/KIEM_THU_RELEASE_2026_11_20.md), [39 bước API ba tài khoản](../docs/a8-results/api-acceptance-2026-11-20.json): minh chứng từng mốc, không coi là bao phủ toàn bộ UI.
- [Sổ xử lý bất đồng A.8](../docs/SO_XU_LY_BAT_DONG_A8.md): ghi biên bản riêng, giữ nhãn khóa.
- [Hướng dẫn nhóm chốt việc tuần 6](../docs/HUONG_DAN_CHOT_VIEC_TUAN_06.md): bước làm, hồ sơ cần Toàn/Khoa/Tú cung cấp; phân công là đề xuất, chưa xác nhận đã thực hiện.
- [Phiếu nguồn hiện hành](../docs/YEU_CAU_NGUON_56_HIEN_HANH.md), [việc cần hoàn thiện](../docs/VIEC_CAN_HOAN_THIEN_56.md): snapshot API ngày 20/11, cần xuất lại khi dữ liệu đổi.
- [Kiểm tra nội dung nguồn](../docs/KIEM_TRA_NOI_DUNG_NGUON.md), [thu nguồn gốc trên web](../docs/THU_NGUON_WEB_56.md), [lịch sử doanh nghiệp](../docs/LICH_SU_DOANH_NGHIEP.md): tiếp nhận, bản gốc, snapshot và phần chưa xác minh.
- [Điều kiện duyệt SoA](../docs/DIEU_KIEN_DUYET_SOA_56.md), [đánh giá theo lô](../docs/DANH_GIA_THEO_LO_TREN_SERVER.md): gate hồ sơ, kế hoạch, khóa/dừng và giới hạn tự động hóa.

Tài liệu bàn giao tuần trước: [Nhật ký tuần 5](TUAN_05.md), [phiếu xác nhận và checklist UI](../docs/HOAN_THIEN_NGHIEM_THU_2026_11_15.md), [rà nguồn kiểm định](../docs/RA_SOAT_NGUON_KIEM_DINH_2026_11_15.md), [hướng dẫn chấm](../docs/HUONG_DAN_CHAM_THAT_A8.md).

## Vướng mắc và giới hạn

- Thiếu nguồn và xác nhận chuyên môn thực tế; công cụ không thể tự tạo phê duyệt hoặc nhãn độc lập thay con người.
- Probe lab chỉ kiểm tra tiêu chí đại diện, chưa chứng minh đầy đủ nội dung từng control hoặc toàn bộ ISMS.
- Sổ xử lý đã có công cụ nhưng chưa có biên bản đối soát chuyên môn thật; ghi chú không tự giải quyết căn cứ sai hoặc biến nhãn có hỗ trợ thành độc lập.
- Bộ 38 hồ sơ do trợ lý tạo là dữ liệu phát triển, chưa có người xác nhận phạm vi/chất lượng khóa thiết kế; 15 ca Agent lệch khóa vẫn cần rà cả tiêu chí, dữ liệu và kết luận. Không dùng bộ này để tuyên bố kiểm định độc lập hoặc tự đóng 37 control thiếu nguồn chính thức.
- Đã kiểm thử ghi thật trên đợt riêng cho nguồn/thẩm định/SoA, nhập quyết định theo lô, lô/dừng/chạy tiếp với Ollama và gói 18 control bằng LLM; đã ngắt/khởi động lại backend thử để xác nhận giữ kết quả/snapshot và mở khóa. Chưa bao phủ mọi lỗi đồng thời, mất mạng, mọi thời điểm ngắt hoặc mọi loại gói; chưa tích hoàn tất kiểm thử toàn UI. Tập thử vẫn là fixture đã sửa, không phải bộ kiểm định mới độc lập. Chấm thật, xác nhận rubric, quyết định thật và duyệt doanh nghiệp vẫn cần đúng người thực hiện.
- Quét trùng mới nhận biết thêm bản sao chỉ thay định dạng, không chứng minh nguồn mới độc lập. Gói ứng viên chuẩn bị theo cơ chế cũ cần đóng gói lại với `cosmetic-text-v2`; lịch sử đã lưu không sửa. Bộ kiểm định mới và lịch sử sử dụng vẫn cần nhóm cung cấp/xác nhận.

## Việc chuyển tiếp sang tuần 7

Chưa xác định. Rà kết quả cuối tuần 6 rồi chốt; chưa tạo file tuần 7–10.

## Đồng bộ GitHub

Ghi gọn theo ngày/nhánh; ghi người đồng bộ theo từng lần thực hiện. Không ghi thao tác chạy/dừng hoặc chuyển nhánh. Tên trong nhật ký là thông tin nhóm ghi nhận, không thay danh tính tài khoản GitHub xác thực thao tác push.

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 18/11/2026 | 10:32, 12:18, 12:44, 20:03 | Trần Văn Toàn | `Tuan6` | Kiểm tra chất lượng nguồn; thống nhất giao diện; xem trước/lịch sử doanh nghiệp; nộp, tải bản gốc và nối nguồn với hàng đợi đánh giá 56 control; hồ sơ tài khoản/vai trò; điều kiện duyệt SoA; lô server và báo cáo 18 control; sửa đầu vào model; 38 phiếu yêu cầu nguồn theo nhóm |
| 20/11/2026 | 12:29 (`main`), 12:36 (cả hai nhánh) | Trần Văn Toàn | `main`, `Tuan6` | Đồng bộ tiến độ tuần 6: kiểm tra gói nguồn, nghiệm thu API/Edge ba tài khoản, đồng nhất báo cáo và điều kiện SoA, phiếu nguồn/mức bao phủ, sổ xử lý bất đồng và nhật ký |
| 21/11/2026 | 11:16 | Lê Đoàn Văn Tú, Trần Văn Toàn | `main`, `Tuan6` | Hướng dẫn chốt việc; kiểm thử ghi thật cô lập; 38 hồ sơ lab và kết quả LLM; rà 19 tiêu chí lệch, chốt khóa thiết kế cho lượt mới; cập nhật nhật ký và mốc 337 test Python |
