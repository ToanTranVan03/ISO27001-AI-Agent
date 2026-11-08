# Tuần 4 — Doanh nghiệp dùng chung, Agent và văn phòng tương tác 3D

- Thời gian: **02/11/2026–08/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Tổng kết tiến độ đến cuối tuần 4; còn việc chuyển tiếp sang tuần 5.**
- Cập nhật: **08/11/2026**.
- Lịch đồ án: 12/10/2026–20/12/2026, tổng cộng 10 tuần.

## Mục tiêu

Phát triển doanh nghiệp giả lập phục vụ đánh giá tuân thủ ISO/IEC 27001: nhân viên nhận lệnh riêng, hành động tạo dấu vết để SOC kiểm tra; Agent thực hiện nhiệm vụ có công việc con, kết quả và người duyệt. Thống nhất dữ liệu giữa văn phòng, Agent và Hồ sơ ISO.

## Công việc và tiến độ cuối tuần

| Công việc | Kết quả đến ngày 08/11/2026 | Trạng thái |
|---|---|---|
| Tham khảo video và xác định cách tương tác | Bình luận nhắm một nhân viên hoặc một vai trò; kết quả dựa trên thực thi backend | Đã triển khai trong lab |
| Doanh nghiệp dùng chung | PostgreSQL theo đợt đánh giá; 50 nhân viên, 50 máy văn phòng riêng, 202 tài khoản và 70 thiết bị phần cứng tại lượt kiểm chứng | Đã triển khai và kiểm tra API |
| Văn phòng tương tác 3D | Three.js, 4 khu nhân viên, 4 phòng theo vai trò; chọn người/máy/phòng, camera và di chuyển tránh vật cản; giữ lựa chọn 2D | Đã triển khai; đã xem ảnh WebGL desktop/mobile |
| Bình luận điều khiển nhân viên | Lệnh cá nhân; chuẩn bị vào ca/về bàn cho USB/app/rời máy khi đủ điều kiện; lưu từng bước và chống trùng yêu cầu | Đã triển khai và kiểm tra API/unit test |
| Phát hiện và xử lý vi phạm | Rời máy không khóa, USB chưa đăng ký, cài ứng dụng chưa duyệt; liên kết người, máy, sự kiện và sự cố | Đã triển khai trong lab; còn kiểm thử đầy đủ ba luồng qua UI |
| Điều phối Agent | Bốn vai trò chung bộ điều phối; Qwen2.5:7b lập kế hoạch JSON, kiểm tra công cụ/thứ tự/phạm vi; công việc con, phản hồi, memory từ hồ sơ có nhận xét | Đã triển khai và kiểm tra nhiệm vụ thực |
| Liên kết Agent với văn phòng | Chọn người làm mục tiêu; trạng thái/SOC theo đúng máy; mở kết quả và hồ sơ liên quan | Đã nối backend và giao diện; chưa kiểm thử bấm toàn bộ UI |
| Hồ sơ ISO và bằng chứng | Xem tiêu chí, kết luận, lịch sử, tái đánh giá, xuất JSON; bằng chứng gắn định danh và hash; cảnh báo khi nguồn đổi | Đã triển khai và kiểm tra API |
| Kiểm chứng và hiệu chỉnh báo cáo | Có benchmark 8 ca tổng hợp, phân biệt luật/LLM/phục hồi; sửa các tuyên bố chưa có bằng chứng | Đã có kết quả giới hạn; cần đánh giá rộng hơn |
| Kiểm thử giao diện có đăng nhập | Đã build và xem ảnh dựng; công cụ điều khiển trình duyệt chưa kết nối | Chưa hoàn tất, chuyển tuần 5 |

## Nhật ký công việc chính

Không bổ sung công việc cho ngày chưa có ghi chép. Số lượng và kết quả dưới đây phản ánh từng mốc triển khai, không cộng dồn số test giữa các phiên bản.

| Ngày | Công việc thực hiện | Kết quả chính |
|---|---|---|
| 05/11/2026 | Đối chiếu video tương tác; bổ sung văn phòng và bình luận cá nhân | Bản đầu có 14 người và 14 máy riêng; hành động của người được chọn không đổi máy người khác. Cuối tuần đã mở rộng lên 50 người |
| 05/11/2026 | Bổ sung nhiệm vụ liên phòng và kiểm tra lưu hồ sơ | Điều phối → Tài sản & nhân sự → SOC → Kiểm soát nội bộ → người duyệt; USB có xử lý/xác minh và ID sự cố; hồ sơ giữ sau restart. SOC lượt thử dùng policy-fallback |
| 05/11/2026 | Kiểm thử phiên bản ban đầu | 143 test Python, 6 test JavaScript và build đạt |
| 06/11/2026 | Tổ chức kế hoạch, nhật ký 10 tuần; phân tích thêm video về Agent | Xác định tuần 4 từ 02–08/11; phân biệt LLM, công cụ, memory, điều phối và kết quả thực thi |
| 06/11/2026 | Bổ sung lập kế hoạch có ràng buộc, memory, trace và xử lý lỗi | Kiểm tra kế hoạch JSON và công cụ được phép; truy xuất tối đa ba hồ sơ có nhận xét; fallback có tùy chọn; kiểm tra phiên bản hồ sơ khi duyệt |
| 06/11/2026 | Phát triển Agent Workspace và nối với văn phòng | Giao việc theo vai trò/mục tiêu, hiển thị công việc con và phản hồi; từ kết quả quay về nhân viên/hồ sơ; mục tiêu sai bị từ chối, sự kiện đã xử lý không tạo sự cố trùng |
| 06/11/2026 | Củng cố đánh giá tuân thủ và Hồ sơ ISO | Chốt phạm vi/tiêu chí/nguồn bằng chứng; bổ sung lịch sử, tái đánh giá, xuất JSON; sửa lỗi Unicode Windows và định dạng JSON với Ollama SDK; hiệu chỉnh tuyên bố khảo sát/hiệu quả chưa được kiểm chứng |
| 06/11/2026 | Chạy benchmark có nhãn tổng hợp | 8 ca × 3 chế độ đều khớp 8/8; luật/workflow nhanh hơn AI. 8 ca cố ý gây lỗi model được chạy phục hồi riêng; không coi đây là tỷ lệ fallback vận hành |
| 06/11/2026 | Thống nhất nguồn dữ liệu doanh nghiệp | PostgreSQL theo đợt; EMP là định danh chính, HF là mã nhập tương thích; 50 người/4 khu, 202 tài khoản, 70 thiết bị; thêm màn hình Doanh nghiệp, entity_refs và snapshot_hash |
| 06/11/2026 | Kiểm tra dữ liệu chung và hồ sơ | Luồng đào tạo → đánh giá → thay đổi dữ liệu → cảnh báo/tái đánh giá; 8 job A.6 hoàn tất; migration không nhân đôi; kiểm tra quyền truy cập và máy EMP-050. SOC lượt thử dùng policy-fallback |
| 08/11/2026 | Đối chiếu video doanh nghiệp Agent và phát triển văn phòng 3D | Phòng kính, nhân vật, khu nghỉ, camera, tìm đường; SOC bám mục tiêu máy; bảng bình luận giao việc nối API nhiệm vụ và hồ sơ chờ duyệt |
| 08/11/2026 | Kiểm tra bình luận và nhiệm vụ mục tiêu | EMP-045 từ ngoài ca tạo bước vào ca và USB; gửi lại request_id không nhân đôi. Nhiệm vụ dùng Qwen2.5:7b lập kế hoạch thật, hoàn tất bước và chờ duyệt; SOC xử lý USB bằng policy-fallback |
| 08/11/2026 | Tổng hợp cuối tuần và kế hoạch chuyển tiếp | Rà lại kết quả, giới hạn, vướng mắc; lập các việc dự kiến cho tuần 5, chưa ghi là đã thực hiện |

## Bổ sung cuối ngày 08/11/2026 — Công việc chung và tiếp tục tự động

- Bổ sung tiến độ chung trong Hồ sơ ISO: người phụ trách, thời điểm, đang xử lý, chờ bằng chứng/duyệt, đã kiểm tra và cần tái đánh giá; kết luận tuân thủ được hiển thị riêng.
- Dùng lại kết quả còn mới, theo dõi job chung khi người khác đã chạy; bổ sung khóa chọn/claim và giữ bảo vệ nguyên tử theo đợt/kiểm soát của hệ thống.
- Thêm lượt tiếp tục tự động tối đa 12 kiểm soát có collector khi trang đang mở; bỏ qua kết quả mới và hồ sơ chờ xử lý thủ công, dừng khi lỗi. Chưa phải scheduler nền hoặc đánh giá tăng dần theo nhân viên.
- 210 test Python và build đạt; API thật bốn yêu cầu đồng thời A.6.1 chỉ tạo một job, hoàn tất rồi dùng lại kết quả. Chưa kiểm thử toàn bộ luồng tự động qua UI.
- Minh chứng và giới hạn: [Công việc chung Agent](../docs/CONG_VIEC_CHUNG_AGENT.md).

## Kết quả và minh chứng

### Kết quả kiểm chứng đã có

- Bản cuối được ghi nhận **195 test Python, 25 test JavaScript và build frontend đạt** ở mốc văn phòng 3D (trước phần công việc chung). Đây là kết quả lượt triển khai trước, không phải một lượt chạy lại khi chỉnh nhật ký. Lint còn cảnh báo và build còn cảnh báo kích thước chunk Three.js.
- API đã kiểm tra mục tiêu nhân viên/máy, chống trùng yêu cầu, liên kết sự cố, nhiệm vụ chờ duyệt, dữ liệu chung và tái đánh giá. Các lượt SOC được viện dẫn ở trên dùng `policy-fallback`; không tính là LLM xử lý thành công.
- Lượt nhiệm vụ 08/11 có nguồn lập kế hoạch `ollama_plan_and_execute` thật. Bốn phòng vẫn là bốn vai trò dùng chung bộ điều phối, không phải bốn mô hình độc lập.
- Benchmark ngày 06/11 gồm 8 ca tổng hợp tự xây dựng, mỗi ca một lần lặp. Ba chế độ cùng evaluator và đều khớp 8/8; không chứng minh LLM phân loại tốt hơn luật, chưa đủ kết luận thống kê hoặc hiệu quả trên doanh nghiệp thật.
- Đã xem ảnh WebGL desktop/mobile bằng Edge headless. Ảnh QA 3D dùng fixture để kiểm tra bố cục; không phải chứng cứ vận hành hoặc thay thế thao tác đầy đủ trên UI có đăng nhập.

### Tài liệu và mã nguồn đối chiếu

- [Bình luận và quy tắc trạng thái](../docs/BINH_LUAN_DIEU_KHIEN.md), [xử lý lệnh](../backend/employee_commands.py), [điều kiện chuyển trạng thái](../backend/office_logic.py).
- [Kiến trúc áp dụng từ video](../docs/KIEN_TRUC_AGENT_TU_VIDEO.md), [trụ sở điều phối](../docs/TRU_SO_DIEU_PHOI.md), [lập kế hoạch](../backend/mission_planner.py), [nhiệm vụ liên phòng](../backend/enterprise_missions.py).
- [Doanh nghiệp dùng chung](../docs/DOANH_NGHIEP_DUNG_CHUNG.md), [văn phòng Agent 3D và kiểm chứng](../docs/VAN_PHONG_AGENT_3D.md).
- [Phạm vi đánh giá](../docs/PHAM_VI_DANH_GIA.md), [kết quả benchmark và giới hạn](../docs/KIEM_CHUNG_DANH_GIA.md).

## Vướng mắc chưa giải quyết

| Vướng mắc | Ảnh hưởng | Hướng xử lý tiếp |
|---|---|---|
| Công cụ điều khiển trình duyệt không kết nối được native pipe Windows | Chưa kiểm thử bấm toàn bộ UI có đăng nhập, dù API/build và ảnh dựng đã được kiểm tra | Khôi phục công cụ hoặc kiểm tra thủ công theo checklist desktop/mobile |
| Chưa kiểm chứng đầy đủ ba luồng vi phạm qua UI 3D và tình huống đồng thời | Chưa đủ cơ sở kết luận mọi tương tác trực quan đều đúng trong mọi trạng thái | Kiểm tra từng luồng, lệnh trùng/sai điều kiện và nhiều nhân viên độc lập |
| Đánh giá chất lượng còn nhỏ, chưa có nhãn chuyên gia hoặc khảo sát người thật | Chưa kết luận độ chính xác tổng quát, lợi ích sử dụng hay hiệu quả vận hành | Mở rộng ca có nhãn, lặp đo, ghi nguồn luật/LLM/fallback và lỗi |

## Giới hạn phạm vi hiện tại

- Dữ liệu, telemetry và hành động là mô phỏng lab; chưa tích hợp HR/IAM/EDR thật. Nhận diện vi phạm dựa trên dấu vết sự kiện, không phải nhận diện người qua camera.
- Danh mục 56 kiểm soát không đồng nghĩa tự động đánh giá đủ 56. Hiện có 12 collector được hỗ trợ: A.6.1–A.6.8 và bốn collector lab A.7.1, A.8.5, A.8.13, A.8.20. Ba dấu hiệu văn phòng chỉ phản ánh một phần các kiểm soát liên quan; xử lý sự cố không đồng nghĩa chứng nhận tuân thủ ISO.
- Bốn vai trò dùng chung bộ điều phối có giới hạn; kết quả luật, LLM và `policy-fallback` phải được ghi riêng. Agent không tự phê duyệt hồ sơ.
- Chưa tích hợp bình luận TikTok hoặc tự tạo nhân vật từ danh tính người bình luận.
- Snapshot đổi có thể khiến nhiều kiểm soát cần đánh giá lại; chưa tối ưu phụ thuộc theo từng trường dữ liệu. Dữ liệu CLI/benchmark lịch sử được giữ riêng, không tự trộn vào doanh nghiệp web.

## Việc dự kiến chuyển sang tuần 5

Dự kiến tại ngày **08/11/2026**, cuối tuần 4. Tuần 5 diễn ra từ **09/11/2026–15/11/2026**; các mục dưới đây chưa được tính là đã hoàn thành.

| Ưu tiên | Công việc chuyển tiếp | Kết quả cần đạt |
|---|---|---|
| 1 | Gỡ vướng kiểm thử giao diện; kiểm tra luồng có đăng nhập trên desktop và điện thoại | Có checklist thao tác và lỗi thực tế; kiểm tra chọn nhân viên, bình luận, giao việc, theo dõi Agent và mở hồ sơ |
| 2 | Kiểm chứng trọn luồng ba hành vi vi phạm trong văn phòng 3D | Bình luận → đúng người/máy → dấu vết → SOC phát hiện/xử lý/xác minh → hồ sơ; thử lệnh trùng, sai điều kiện và nhiều người độc lập |
| 3 | Kiểm tra tính nhất quán dữ liệu và điều kiện duyệt | Văn phòng, Agent và Hồ sơ ISO cùng tham chiếu nhân viên/thiết bị/bằng chứng; dữ liệu đổi phải cảnh báo kết luận cũ; không duyệt khi còn sự cố hoặc hồ sơ không hợp lệ |
| 4 | Bổ sung lượt đo đánh giá có nhãn chuẩn | Ghi thời gian, kết quả đúng/sai, nguồn luật/LLM/fallback và trường hợp lỗi; chỉ báo cáo số liệu đã đo, nêu rõ phạm vi lab |
| 5 | Hoàn thiện báo cáo và kịch bản bảo vệ | Tổng hợp kiến trúc, phạm vi kiểm soát, minh chứng, kết quả và giới hạn; cập nhật nhật ký theo công việc thực tế |

Chỉ xem xét mở rộng hành vi hoặc tích hợp bình luận bên ngoài sau khi các luồng cốt lõi ổn định. Chi tiết kế hoạch dự kiến tại [Tuần 5](TUAN_05.md).
