# Tuần 4 — Văn phòng tương tác và trụ sở điều phối

- Trạng thái: **Tuần hiện tại — đang thực hiện.**
- Cập nhật: 06/11/2026.
- Nhánh làm việc: `Toant3`.
- Thời gian: **02/11/2026–08/11/2026 (thứ Hai–Chủ nhật).**
- Lịch đồ án: 12/10/2026–20/12/2026, tổng cộng 10 tuần.

## Mục tiêu

Hoàn thiện doanh nghiệp giả lập có nhiều nhân vật hoạt động riêng; bình luận tạo
hành vi và dấu vết để Agent kiểm tra. Bổ sung luồng giao nhiệm vụ liên phòng,
bàn giao đầu ra và người phụ trách duyệt hồ sơ.

## Kế hoạch và tiến độ

| Công việc | Đầu ra / tiêu chí | Trạng thái |
|---|---|---|
| Tham khảo các video người dùng cung cấp | Xác định cơ chế bình luận cá nhân, không lấy lệnh đồng loạt làm luồng chính | Đã thực hiện |
| Văn phòng tương tác | 14 nhân vật, 14 máy riêng, trạng thái lưu trong PostgreSQL | Đã thực hiện |
| Bình luận điều khiển | Chọn người, nhận lệnh riêng, hiển thị lời thoại và kết quả | Đã thực hiện |
| Tham gia ca bằng một lệnh | `đi làm` cho người chưa vào ca; giữ biện pháp bảo vệ của Agent | Đã thực hiện |
| Phát hiện và xử lý vi phạm | Ba hành vi: rời máy mở màn hình, USB chưa đăng ký, cài app chưa duyệt | Đã thực hiện trong lab |
| Trụ sở điều phối | Bốn phòng, tiến độ thực, đầu ra bàn giao, hồ sơ chờ duyệt | Đã thực hiện |
| Lưu và xuất hồ sơ | Giữ qua restart, lịch sử nhiệm vụ và xuất JSON | Đã thực hiện |
| Kiểm tra UI trực tiếp | Kiểm tra thao tác, bố cục và lỗi hiển thị trên trình duyệt | Còn cần hoàn thiện |
| Đo hiệu năng / chất lượng AI hiện tại | Có dữ liệu đo mới và phân biệt AI với fallback | Chưa hoàn thành |

## Nhật ký

| Ngày | Công việc thực hiện | Kết quả / minh chứng |
|---|---|---|
| 05/11/2026 | Đối chiếu bốn video đi học, đi chùa, đi tù, đi lễ online; sửa cách hiểu tương tác | Luồng một bình luận → một nhân vật → hành động riêng; xem [tài liệu bình luận](../docs/BINH_LUAN_DIEU_KHIEN.md) |
| 05/11/2026 | Bổ sung văn phòng, lệnh cá nhân và lưu trạng thái | Kiểm tra một người nghỉ, người khác làm; các máy còn lại không đổi |
| 05/11/2026 | Tham khảo video doanh nghiệp AI Agent; bổ sung nhiệm vụ liên phòng | Điều phối → Tài sản & nhân sự → SOC → Kiểm soát nội bộ → người duyệt |
| 05/11/2026 | Chạy thử nhiệm vụ thu thập và nhiệm vụ có USB lạ | Có phát hiện, xử lý, xác minh, ID sự cố; lượt thử xử lý ghi nguồn `policy-fallback` |
| 05/11/2026 | Kiểm tra sau khi restart backend | Hồ sơ vẫn lưu và ở trạng thái chờ người dùng duyệt |
| 05/11/2026 | Kiểm thử và push thay đổi lên `Toant3` | 143 test Python, 6 test tương tác JavaScript và build đạt; commit `66400a4` |
| 05/11/2026 | Chạy thử nhánh `Khoa-update`, sau đó dừng và quay lại `Toant3` | Ba container IAM/Network/SecOps trả dữ liệu; không merge nhánh thử vào `Toant3` |
| 06/11/2026 | Khởi động lại bản hiện tại | Kiểm tra đăng nhập, 14 máy và API nhiệm vụ liên phòng hoạt động |
| 06/11/2026 | Tạo thư mục kế hoạch và nhật ký tuần | Tạo hồ sơ tuần 1–4; xác định tuần 4 là tuần hiện tại |
| 06/11/2026 | Xác định lịch đồ án 10 tuần | 12/10–20/12/2026; tuần 4 từ thứ Hai 02/11 đến Chủ nhật 08/11; các tuần sau chỉ có khung |
| 06/11/2026 | Phân tích thêm ba video về văn phòng và tự động hóa Agent | Phân biệt UI, LLM, công cụ, memory, điều phối và kết quả thật; xem [kiến trúc áp dụng](../docs/KIEN_TRUC_AGENT_TU_VIDEO.md) |
| 06/11/2026 | Bổ sung AI lập kế hoạch có ràng buộc | Qwen2.5:7b trả kế hoạch JSON; backend kiểm tra công cụ/thứ tự; thực thi theo phạm vi đã giao |
| 06/11/2026 | Bổ sung memory, trace, trạng thái lỗi và kiểm tra phiên bản hồ sơ | Truy xuất tối đa ba hồ sơ đã có nhận xét; fallback có tùy chọn; duyệt đối chiếu hash; restart không để phòng hiển thị đang chạy giả |
| 06/11/2026 | Kiểm tra luồng AI trên PostgreSQL/Ollama | Có kế hoạch LLM, ngữ cảnh từ nhận xét, công cụ đọc máy, USB được phát hiện/xác minh; SOC của lượt thử dùng `policy-fallback`. Mô hình offline bị chặn trước công cụ nghiệp vụ |
| 06/11/2026 | Phát triển màn hình Agent Workspace theo video | Giao yêu cầu theo vai trò; văn phòng bốn phòng; công việc con, phản hồi và bàn giao gắn với kết quả backend |
| 06/11/2026 | Kiểm tra luồng giao việc cho SOC | 5 công việc con và 20 phản hồi/sự kiện, đầu ra và ID sự cố liên kết được; hồ sơ cuối chờ người duyệt |
| 06/11/2026 | Nối trực quan Agent Workspace với văn phòng nhân viên | Chọn người → mục tiêu người/máy; giao SOC; trạng thái và robot chung; từ kết quả quay về đúng nhân viên/hồ sơ |
| 06/11/2026 | Kiểm tra giới hạn mục tiêu và sự kiện đã xử lý | Mục tiêu sai bị từ chối; chỉ xử lý sự kiện của người đã chọn; người khác không bị tác động; kiểm tra lại liên kết hồ sơ cũ, không tạo trùng |

## Kết quả và minh chứng

- [Luồng bình luận và quy tắc trạng thái](../docs/BINH_LUAN_DIEU_KHIEN.md).
- [Trụ sở điều phối và các bước bàn giao](../docs/TRU_SO_DIEU_PHOI.md).
- [Xử lý lệnh nhân viên](../backend/employee_commands.py).
- [Trạng thái máy và điều kiện trước hành động](../backend/office_logic.py).
- [Nhiệm vụ liên phòng](../backend/enterprise_missions.py).
- [Kiểm thử nhiệm vụ](../tests/test_enterprise_missions.py).
- [Hướng dẫn chạy local](../CHAY_LOCAL.md).
- Commit đã push: `66400a4` — Bổ sung trụ sở điều phối và tương tác riêng cho từng nhân viên.

Ngày 06/11/2026 đã chạy bộ test đầy đủ: **159 test Python đạt**. Sau đó bổ sung
ca giới hạn xử lý sự cố, chạy lại nhóm planner/runtime: **17 test đạt**. Build frontend đạt;
lint không có lỗi chặn nhưng còn cảnh báo trong các component hiện có.
Lượt nâng cấp màn hình theo vai trò: **164 test Python, 11 test JavaScript và build đạt**;
đã xem ảnh dựng desktop/màn hình hẹp bằng Edge headless từ dữ liệu thực thi thật.
Các thay đổi kiến trúc và file kế hoạch/nhật ký mới được đưa vào đợt commit/push ghi ở mục bên dưới.

## Giới hạn và vướng mắc

- Dữ liệu và hành động thuộc môi trường doanh nghiệp giả lập.
- Luồng bình luận mới bao phủ ba hành vi vi phạm, chưa đủ hành vi cho cả 56 kiểm soát.
- Chưa kết nối bình luận TikTok hoặc tự tạo nhân vật theo danh tính người bình luận.
- Các phòng là vai trò của Plan-and-Execute có giới hạn; có LLM ở bước lập kế hoạch
  và cơ chế AI/công cụ ứng phó ở SOC, chưa phải bốn Agent AI độc lập.
- Luật nhận diện, mô hình và `policy-fallback` cần được phân biệt trong đánh giá.
- Công cụ kiểm tra trình duyệt chưa kết nối được ở lượt triển khai gần nhất;
  kiểm tra hình dựng từ component và API không thay thế toàn bộ kiểm thử UI.

## Việc tiếp tục trong tuần 4

- [ ] Kiểm tra trực tiếp các luồng trên trình duyệt và ghi nhận lỗi còn lại.
- [ ] Kiểm tra lần lượt cả ba vi phạm, đúng người/máy và kết quả xác minh.
- [ ] Kiểm tra hồ sơ bị chặn duyệt khi còn sự cố hoặc có dấu hiệu mới.
- [ ] Đo thời gian xử lý và tỷ lệ dùng mô hình/fallback bằng lượt chạy mới.
- [ ] Thống nhất phạm vi tiếp theo: danh tính người bình luận, nhân vật, hành vi hoặc tích hợp nguồn thật.
- [ ] Hoàn thiện nội dung báo cáo tuần với người phụ trách và lịch tuần của nhóm.

## Việc dự kiến chuyển sang tuần 5

Chưa chốt. Cuối tuần 4, rà lại các mục còn mở và chỉ chuyển những việc đã thống nhất.

## Kiểm chứng liên kết trực quan ngày 06/11/2026

- 169 test Python và 15 test JavaScript đạt; build frontend đạt, lint còn cảnh báo.
- API thực tế: mục tiêu người/máy được kiểm tra đúng, từ chối máy hoặc sự kiện không thuộc nhân viên; sự kiện của người khác không bị xử lý.
- Kiểm tra lại sự kiện đã xử lý trả hồ sơ cũ, không tạo sự cố trùng.
- Đã xem ảnh dựng giao diện từ dữ liệu thực thi thật: SOC và văn phòng cùng trạng thái, robot theo đúng nhân viên. Đây chưa thay thế kiểm thử bấm toàn bộ UI có đăng nhập.

## Nhật ký commit và push GitHub

- Thời điểm bắt đầu commit/push: **10:21:21 ngày 06/11/2026 (UTC+7)**.
- Nhánh GitHub nhận các thay đổi: **Toant3**, remote origin, kho [ISO27001-AI-Agent](https://github.com/ToanTranVan03/ISO27001-AI-Agent/tree/Toant3).
- Nội dung: bổ sung lập kế hoạch Agent, công việc con và phản hồi theo kết quả; liên kết trực quan Agent với nhân viên/máy/sự kiện/hồ sơ; thêm kiểm thử, tài liệu kiến trúc và kế hoạch/nhật ký 10 tuần.
- Thông điệp commit: **Hoàn thiện điều phối Agent và liên kết tương tác với văn phòng nhân viên**.
- Kiểm chứng trước đợt push: 169 test Python, 15 test JavaScript và build đạt; lint còn cảnh báo.
