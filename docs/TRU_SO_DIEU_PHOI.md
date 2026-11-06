# Trụ sở điều phối doanh nghiệp

Tham khảo video người dùng cung cấp `D:\doanh nghiep ai agent.mp4` (38,15 giây).
Đã xem 12 khung hình trải đều video: trụ sở chia phòng, mỗi phòng một nhiệm vụ,
giao một chủ đề, bàn giao kết quả và có bước duyệt. Giao diện video không đủ
để xác minh cách các Agent bên trong thực thi. Không sao chép hình ảnh hoặc logo.

## Cách dùng

Trong **Mô phỏng 3D**, phần **Trụ sở điều phối** nằm trên văn phòng tương tác.
Màn hình **Agent Workspace** gồm văn phòng bốn phòng, mỗi phòng có nhân vật theo vai trò.
Nhân vật về bàn và hoạt động khi công việc con thực sự ở trạng thái đang chạy;
hoàn tất/bị chặn thì đổi trạng thái theo dữ liệu backend, không tự chạy tiến độ giả.
Chọn nhân vật hoặc phòng để xem công việc và đầu ra ở bảng bên cạnh.

### Giao việc và xem phản hồi theo vai trò

1. Chọn **Agent điều phối**, **Agent tài sản**, **Agent SOC** hoặc **Agent kiểm soát**
   ở hàng **Giao yêu cầu cho**. Đây là vai trò tiếp nhận; Điều phối vẫn chia đủ
   các bước bắt buộc, không bỏ kiểm tra vì chọn trực tiếp SOC hoặc Kiểm soát.
2. Nhập mục tiêu hoặc bấm **Điền yêu cầu mẫu**, kiểm tra phạm vi và giao nhiệm vụ.
3. Bật **Theo dõi Agent đang làm** để bảng bên cạnh chuyển đến vai trò có công việc
   đang thực thi. Chọn phòng bằng tay sẽ tắt theo dõi để bạn tự xem đầu ra.
4. Mỗi công việc con có ID, người phụ trách theo vai trò, mục đích, thời điểm bắt đầu,
   kết thúc, trạng thái và tham chiếu đầu ra. Bước đọc máy là công việc riêng thuộc
   Agent tài sản, kể cả khi kế hoạch đặt bước đó sau SOC.
5. **Trao đổi và bàn giao** hiển thị yêu cầu của bạn và phản hồi từ sự kiện backend.
   Nội dung như số hồ sơ, số máy và số kết quả xác minh được tính từ đầu ra thật;
   không phải cuộc hội thoại LLM được tự tạo để trang trí.
6. Bấm **Mở kết quả bàn giao** dưới phản hồi hoặc chọn một công việc con để đọc kết quả.
   Có số liệu và danh sách dễ đọc; JSON nằm trong **Dữ liệu kỹ thuật**. Có thể tải
   riêng đầu ra của công việc hoặc toàn bộ hồ sơ.
7. Với kết quả SOC, **Mở hồ sơ sự cố** mở dữ liệu sự cố trong phần chi tiết/chat bên dưới.

Trên màn hình hẹp, các phòng nằm trong bản đồ cuộn ngang; bảng công việc chuyển xuống dưới.
Nhập chủ đề kiểm tra, chọn phạm vi con người/phần cứng/phần mềm/toàn bộ rồi
nhấn **Giao nhiệm vụ kiểm tra**. Chọn cách điều phối:

- **AI lập kế hoạch → thực thi công cụ**: Ollama đọc mục tiêu, phạm vi và tối đa ba
  hồ sơ đã có nhận xét trong cùng đợt đánh giá/phạm vi. AI trả kế hoạch JSON và tiêu chí
  gợi ý cho người duyệt; backend kiểm tra công cụ và thứ tự trước khi thực thi.
- **Quy trình cố định**: bỏ bước gọi mô hình lập kế hoạch, chạy thứ tự chuẩn.

Nếu AI lập kế hoạch không khả dụng hoặc trả JSON sai, chế độ AI mặc định báo **Bị chặn**.
Chỉ khi tích **Cho phép dùng quy trình khi AI không lập được kế hoạch** mới chuyển sang
`workflow-fallback`, có ghi lý do. Chính sách dự phòng của SOC là cơ chế riêng,
nguồn model/policy-fallback luôn nằm trong đầu ra xử lý sự cố.

1. **Điều phối** lập kế hoạch theo chế độ đã chọn, giữ nguyên phạm vi người dùng xác định.
2. **Tài sản & nhân sự** chụp danh mục từ PostgreSQL của đợt đánh giá.
3. **SOC** đọc telemetry trong phạm vi và gọi chính luồng ứng phó hiện có.
   Khóa quét được dùng chung với bộ giám sát để tránh xử lý trùng.
   Mô hình/công cụ hoặc fallback được ghi trong kết quả khi có sự cố. Một lượt xử lý
   tối đa ba dấu hiệu; dấu hiệu chưa xử lý được nêu trong báo cáo và chặn duyệt.
4. **Kiểm soát nội bộ** kiểm tra lại dấu hiệu còn mở, kết quả chưa xác minh
   và hồ sơ chưa giải quyết; lập báo cáo chờ người phụ trách duyệt.
5. Người dùng nhập nhận xét rồi **Duyệt hồ sơ kiểm tra** hoặc **Yêu cầu bổ sung**.
   Không duyệt được hồ sơ có hạng mục chặn. Khi duyệt, kiểm tra lại dấu hiệu/hồ sơ
   còn mở để không duyệt dựa vào báo cáo cũ trong khi đã có vấn đề mới. Hồ sơ mới có
   SHA-256 của tập đầu ra; API đối chiếu hash trước khi lưu nhận xét/phê duyệt.

Đầu ra mỗi phòng mở được ở **Xem đầu ra bàn giao**. **Tải hồ sơ JSON** xuất
chủ đề, phạm vi, danh mục tại thời điểm thu thập, dấu hiệu, ID sự cố, nguồn xử lý,
tiến độ, thời điểm bàn giao và nhận xét. Lưu 10 nhiệm vụ gần nhất trong giao diện;
database giữ toàn bộ. Dữ liệu tách theo đợt đánh giá và API yêu cầu đăng nhập/quyền truy cập.
Mở **Nhật ký thực thi** để xem thời gian, nguồn lập kế hoạch, điều phối công cụ,
sự kiện SOC, hoàn tất hoặc lý do bị chặn. Nhiệm vụ lỗi/gián đoạn có nút **Chạy lại
mục tiêu từ dữ liệu mới**: tạo lượt mới, giữ lịch sử cũ, không tự khôi phục kết quả đã lỗi.

## Giới hạn và tính đúng đắn

- Kiến trúc là **Plan-and-Execute có ràng buộc**, không phải hệ thống bốn mô hình AI
  độc lập hoặc vòng ReAct tổng quát. Điều phối gọi LLM lập kế hoạch; SOC dùng cơ chế
  AI/công cụ vốn có; thu thập và tổng hợp được thực hiện bằng mã xử lý xác định.
- Memory là truy xuất hồ sơ đã có nhận xét từ PostgreSQL, giới hạn cùng phạm vi và đợt
  đánh giá. Không tự huấn luyện mô hình, chưa có vector database/RAG ngữ nghĩa.
- Công cụ: `inventory`, `security`, `report` bắt buộc theo thứ tự; có thể thêm `workstations`
  trước báo cáo. Không nhận đối số lệnh shell, không cho AI tự duyệt hoặc đổi phạm vi.
- Mô hình lập kế hoạch và mô hình ứng phó có timeout 45 giây mỗi yêu cầu. Khóa quét
  chờ tối đa 15 giây. Ngân sách 240 giây được kiểm tra giữa các bước/vụ việc; không
  hủy cưỡng bức một công cụ đang thực thi. Mỗi kế hoạch có tối đa bốn lời gọi công cụ cấp phòng.
- Dữ liệu và hành động thuộc doanh nghiệp giả lập. Không kết nối ERP, mạng doanh nghiệp
  thật hoặc tự tạo bài marketing, ảnh, video như ví dụ Content OS.
- Không điều khiển đồng loạt nhân viên; nhiệm vụ liên phòng và bình luận cá nhân
  là hai luồng thao tác riêng, dùng chung dữ liệu doanh nghiệp.
- Không có dấu hiệu mới không đồng nghĩa đạt toàn bộ 56 kiểm soát.
  Duyệt hồ sơ xác nhận lượt kiểm tra này, không phải cấp chứng nhận ISO.
- Mỗi đợt đánh giá chạy một nhiệm vụ liên phòng tại một thời điểm. UUID chống tạo trùng.
  Nếu lỗi, bước sau bị chặn. Sau restart, nhiệm vụ đang chạy được đánh dấu gián đoạn;
  người dùng giao lượt kiểm tra mới từ dữ liệu hiện tại, không hiển thị tiến độ giả.

## Kiểm tra màn hình vai trò (06/11/2026)

- 164 test Python và 11 test JavaScript đạt; build frontend đạt.
- Đã chạy yêu cầu gửi cho SOC với Ollama/PostgreSQL: kế hoạch có 5 công việc con
  (gồm lập kế hoạch), 20 phản hồi/sự kiện, có ID đầu ra và bàn giao; USB được xác minh.
  Lượt này SOC dùng `policy-fallback`, hiển thị riêng với nguồn mô hình lập kế hoạch.
- Đã kiểm tra ảnh bố cục desktop/màn hình hẹp bằng Edge headless trên bản dựng tĩnh
  của component với dữ liệu chạy thật; chưa kiểm thử toàn bộ thao tác UI đã đăng nhập
  tự động bằng trình duyệt. Kiểm tra API không thay thế bước kiểm tra UI này.

## Liên kết với văn phòng nhân viên

1. Chọn một nhân viên trong bản đồ/danh sách bên dưới. Khối giao việc phía trên tự
   hiển thị người và máy đó ở **Kiểm tra nhân viên đang chọn ở văn phòng**.
2. Bấm **Giao SOC kiểm tra EMP-xxx** dưới bản đồ để cuộn lên, chọn vai trò SOC và điền
   mục tiêu kiểm tra. Kiểm tra phạm vi rồi bấm **Giao nhiệm vụ**.
3. Nhiệm vụ lưu mục tiêu tường minh: employee ID, asset ID và event ID nếu có.
   Backend kiểm tra quan hệ trong đúng đợt đánh giá; AI không được tự đổi mục tiêu.
   Bỏ tích kiểm tra nhân viên để giao một lượt kiểm tra toàn doanh nghiệp.
4. Khi SOC quét/xử lý, `current_activity` lưu đúng người, máy, sự kiện và trạng thái.
   Cả Agent Workspace và văn phòng nhân viên hiện cùng dòng trạng thái; robot giám sát
   phía dưới tới đúng nhân viên. Bộ giám sát tự động cũng dùng chung cơ chế hiển thị.
5. Trong kết quả SOC, bấm **Đến nhân viên này** hoặc **Xem nhân viên và máy ở văn phòng**
   để cuộn xuống và chọn đúng nhân vật. Khối kết quả liên kết giữ event ID/incident ID,
   cập nhật hồ sơ sau khi xử lý và có nút mở hồ sơ sự cố.
6. Nếu sự kiện đã được bộ giám sát hoặc nhiệm vụ trước xử lý, mục **Đã xử lý trước lượt
   kiểm tra này** hiển thị hồ sơ cũ. Không tạo vụ việc mới hay giả lập robot đang xử lý lại.

Chọn nhân viên mới chỉ thay đổi mục tiêu của **yêu cầu sắp giao**; mục tiêu của nhiệm vụ
đã lưu không thay đổi. Chọn hồ sơ lịch sử không được hiển thị như một lượt đang chạy.
Các tham chiếu cốt lõi: `employee_id`, `asset_id`, `event_id`, `incident_id`, `mission_id`.
