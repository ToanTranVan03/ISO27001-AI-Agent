# Tuần 6 — Hoàn thiện bằng chứng, kiểm định và hồ sơ đánh giá tuân thủ

- Thời gian: **16/11/2026–22/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Đang thực hiện.**
- Lập kế hoạch: **15/11/2026**.
- Cập nhật: **20/11/2026**.

## Mục tiêu và kế hoạch

Giữ phạm vi 56 control (8 A.6, 14 A.7, 34 A.8), ưu tiên kiểm định sâu 18 A.8 theo góp ý giảng viên. Tuần 6 tập trung bổ sung nguồn, nâng chất lượng kết luận và hoàn thiện hồ sơ nghiệm thu; không mở rộng văn phòng 3D.

- [ ] Thống nhất với giảng viên/người phụ trách rubric, phạm vi nguồn và người đánh giá được chấp nhận; ghi nhận phiên bản và căn cứ xác nhận.
- [ ] Thu nguồn có nội dung cho 37 control còn thiếu; rà mức bao phủ của 19 control đã có nguồn, đặc biệt kiểm tra lại A.6.2 chỉ trích xuất được 1 ký tự.
- [ ] Chuẩn bị bộ nguồn kiểm định mới, xác nhận lịch sử tiếp xúc và chốt snapshot trước khi chạy/chấm; không dùng lại fixture đã biết rồi gọi là tập độc lập.
- [ ] Tổ chức người đánh giá đọc và chấm trên cùng mã lượt/bằng chứng; khai đúng mức hỗ trợ, giữ riêng kết quả có AI hỗ trợ và nhãn luyện tập.
- [ ] Phân tích bất đồng và chất lượng căn cứ; lưu xử lý riêng, không sửa nhãn khóa hoặc thay đổi báo cáo cũ để tăng điểm.
- [x] Chạy Agent trên 18 nguồn A.8 lab hiện hành, xuất kết quả từng control và giữ riêng các lần lỗi/kiểm tra lại.
- [ ] Mở rộng đánh giá trên nguồn còn thiếu trong phạm vi 56; đo độ đúng bằng bộ kiểm định và nhãn người đánh giá đủ điều kiện.
- [ ] Kiểm thử đầy đủ giao diện bằng các tài khoản: đọc/thu nguồn, chấm, khóa nhãn, cập nhật tiến độ, xuất báo cáo và các trường hợp bị chặn.
- [ ] Người phụ trách ghi 56 quyết định tính áp dụng, lý do và kế hoạch xử lý/duy trì; bổ sung người nhận, hạn và cách kiểm tra lại.
- [ ] Thẩm định từng tiêu chí trên nguồn hiện hành, hoàn thiện và trình người có trách nhiệm phê duyệt SoA khi đủ điều kiện.

Phần triển khai kỹ thuật đã hoàn thành trong tuần:

- [x] Kiểm tra nội dung nguồn trước suy luận, giữ dữ liệu cũ và yêu cầu nộp lại nguồn không dùng được.
- [x] Trực quan hóa và thống nhất bốn màn hình; phân biệt kết quả, tiến độ, bằng chứng và thẩm định.
- [x] Bổ sung xem trước thay đổi doanh nghiệp, kiểm tra snapshot và lịch sử người cập nhật/giá trị trước–sau.
- [x] Nộp nguồn gốc trên web cho 56 control, lưu/tải bản gốc có hash và nối nguồn với hàng đợi đánh giá.
- [x] Kiểm tra lặp API bằng ba tài khoản và lưu báo cáo 39 bước ngày 20/11; chưa thay kiểm thử toàn UI.
- [x] Kiểm chứng mã/API và giao dịch PostgreSQL rollback; chưa thay cho kiểm thử đầy đủ UI hoặc nghiệm thu chuyên môn.
- [x] Bổ sung bảng điều kiện trình duyệt SoA theo từng control, cảnh báo hạn và chặn thiếu thông tin kế hoạch/nguồn thẩm định không dùng được.
- [x] Chuyển chạy lô nguồn sang server, lưu tiến độ PostgreSQL, chặn lô trùng, dừng có kiểm soát và ghi gián đoạn khi API khởi động lại.
- [x] Kiểm soát kích thước đầu vào/context model, giữ nguồn không cắt âm thầm; không hiển thị kết luận cũ như hiện hành khi job mới lỗi.
- [x] Đồng nhất bộ lọc chất lượng căn cứ của báo cáo CLI/web; hiển thị lỗi API có cấu trúc và phân biệt kế hoạch nháp với điều kiện trình duyệt.
- [x] Tách phiếu nguồn thiếu/không dùng được với rà mức bao phủ; kiểm thử Edge ba tài khoản cho điều hướng, xuất SoA và từ chối tệp lỗi. Chưa thay kiểm thử toàn bộ thao tác nộp/chấm/duyệt.

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
| 20/11/2026 | Tự động kiểm tra nghiệm thu API ba tài khoản | Bổ sung CLI chạy lặp, không ghi mật khẩu/token; 39/39 bước API thật bằng admin/Khoa/Tú đạt, gồm đọc bốn khu vực và chặn quyền sai/khác đợt. Không tạo model/nhãn/phê duyệt. 314 test Python đạt; kiểm thử toàn UI vẫn chờ kết nối trình duyệt |

## Kết quả và minh chứng

### Bổ sung ngày 20/11 — rà soát trước bàn giao

- Đồng nhất điều kiện đối chiếu người chấm giữa CLI và web; giữ nguyên nhãn khóa, tách người còn căn cứ lỗi/cảnh báo chưa xác nhận khỏi bảng đủ điều kiện.
- Hiển thị chi tiết lỗi 409/422; đồng bộ tài liệu và form kế hoạch với chính sách duyệt SoA hiện hành, không nhầm lưu nháp là phê duyệt.
- Cập nhật snapshot việc cần làm: 38 yêu cầu nguồn (37 thiếu, A.6.2 cần thay) và 18 yêu cầu rà mức bao phủ tách riêng; chưa tự giao người/hạn hoặc tạo hồ sơ.
- Kiểm chứng: **316 test Python, 9 test JavaScript, lint/build và 3 kịch bản Edge admin/Khoa/Tú đạt**. Đã kiểm tra đăng nhập/đăng xuất, bốn màn hình, xuất SoA 56 dòng, nút duyệt bị khóa, người chấm không có nút chạy lô; admin nộp tệp một ký tự bị từ chối 422 và form nhắc kế hoạch thiếu. Không nộp nhãn/quyết định/phê duyệt hoặc chạy model.
- [Biên bản và cách chạy lại](../docs/KIEM_THU_RELEASE_2026_11_20.md); [phiếu nguồn hiện hành](../docs/YEU_CAU_NGUON_56_HIEN_HANH.md). Chưa xác nhận toàn bộ luồng UI nộp nguồn hợp lệ, nộp/khóa nhãn, đổi snapshot và duyệt thành công; các mục cần con người/nguồn thật vẫn chưa tích xong.

- [Nghiệm thu API ba tài khoản ngày 20/11](../docs/a8-results/api-acceptance-2026-11-20.json): 39 bước đạt, chưa kiểm thử toàn GUI.

- [Phiếu yêu cầu nguồn theo nhóm](../docs/source-requests/README.md): dự thảo giao nhóm bổ sung hồ sơ.

- [Kiểm tra nội dung nguồn trước đánh giá](../docs/KIEM_TRA_NOI_DUNG_NGUON.md): chính sách kỹ thuật, hành vi và giới hạn.
- [Theo dõi thay đổi doanh nghiệp](../docs/LICH_SU_DOANH_NGHIEP.md): xem trước, kiểm tra snapshot và lịch sử.
- [Thu nguồn gốc trên web cho 56 control](../docs/THU_NGUON_WEB_56.md): cách nộp nguồn, tải bản gốc và tiếp tục đánh giá.
- [Điều kiện hồ sơ và trình duyệt SoA](../docs/DIEU_KIEN_DUYET_SOA_56.md): phần còn thiếu, hạn kế hoạch, thẩm định và chính sách duyệt mới.
- [Đánh giá theo lô trên server](../docs/DANH_GIA_THEO_LO_TREN_SERVER.md): vận hành, khóa, dừng và giới hạn.
- [Kết quả đánh giá lại 18 nguồn A.8](../docs/KET_QUA_DANH_GIA_NGUON_18_2026_11_18.md): bảng kết quả và dữ liệu job/evaluation/audit trail, giữ các lần lỗi. Chỉ đo thực thi, chưa phải benchmark độc lập.
- Trạng thái kiểm tra ngày 18/11: 19/56 control có nguồn ngoài preset, 18 qua kiểm tra nội dung tối thiểu; 37 còn thiếu nguồn và A.6.2 cần thay nguồn. Chưa có thẩm định hiện hành/quyết định tính áp dụng; rubric và SoA chưa được phê duyệt.

Tài liệu bàn giao từ tuần trước:

- [Nhật ký tuần 5](TUAN_05.md).
- [Bàn giao nghiệm thu, phiếu xác nhận và checklist UI](../docs/HOAN_THIEN_NGHIEM_THU_2026_11_15.md).
- [Rà soát nguồn kiểm định trong project](../docs/RA_SOAT_NGUON_KIEM_DINH_2026_11_15.md).
- [Hướng dẫn chấm tương tác](../docs/HUONG_DAN_CHAM_THAT_A8.md).

## Vướng mắc và giới hạn

- Thiếu nguồn và xác nhận chuyên môn thực tế; công cụ không thể tự tạo phê duyệt hoặc nhãn độc lập thay con người.
- Probe lab chỉ kiểm tra tiêu chí đại diện, chưa chứng minh đầy đủ nội dung từng control hoặc toàn bộ ISMS.
- Ngày 20/11 Computer Use/native pipe vẫn chưa kết nối; đã dùng Playwright chạy Edge thực tế với ba tài khoản cho tập kịch bản đọc/xuất và từ chối tệp lỗi. Chưa bao phủ toàn bộ thao tác nộp/chấm/duyệt; cần tiếp tục trên đợt thử riêng và ghi kết quả, không coi ba kịch bản là kiểm thử toàn UI.

Cập nhật thêm khi phát sinh, kèm hướng xử lý và phần còn chờ.

## Việc chuyển tiếp sang tuần 7

Chưa xác định. Rà kết quả cuối tuần 6 rồi chốt; chưa tạo file tuần 7–10.

## Đồng bộ GitHub

Ghi gọn theo ngày/nhánh; người push: Trần Văn Toàn. Không ghi thao tác chạy/dừng hoặc chuyển nhánh.

| Ngày | Giờ (UTC+7) | Người push | Nhánh | Nội dung chính |
|---|---|---|---|---|
| 18/11/2026 | 10:32, 12:18, 12:44, 20:03 | Trần Văn Toàn | `Tuan6` | Kiểm tra chất lượng nguồn; thống nhất giao diện; xem trước/lịch sử doanh nghiệp; nộp, tải bản gốc và nối nguồn với hàng đợi đánh giá 56 control; hồ sơ tài khoản/vai trò; điều kiện duyệt SoA; lô server và báo cáo 18 control; sửa đầu vào model; 38 phiếu yêu cầu nguồn theo nhóm |
