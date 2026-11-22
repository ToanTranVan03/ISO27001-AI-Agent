# Tuần 7 — Bổ sung nguồn, đối chiếu và hoàn thiện hồ sơ nghiệm thu

- Thời gian: **23/11/2026–29/11/2026 (thứ Hai–Chủ nhật).**
- Trạng thái: **Chuẩn bị — nhận việc chuyển tiếp từ tuần 6.**
- Lập kế hoạch và cập nhật: **22/11/2026** (Chủ nhật cuối tuần 6).

## Mục tiêu và kế hoạch

Giữ phạm vi 56 control (8 A.6, 14 A.7, 34 A.8), ưu tiên thực nghiệm sâu 18 A.8. Tập trung bằng chứng, chất lượng kết luận và đối chiếu người đánh giá; không mở rộng văn phòng 3D.

Các việc dưới đây chuyển từ tuần 6, **chưa đánh dấu hoàn thành**:

- [ ] Thống nhất với giảng viên/người phụ trách rubric, phạm vi nguồn và người chấm được chấp nhận; lưu người/ngày xác nhận, phiên bản/hash và căn cứ.
- [ ] Bổ sung nguồn có nội dung cho 37 control còn thiếu, thay nguồn A.6.2 một ký tự; rà mức bao phủ của 19 control đã có nguồn.
- [ ] Chuẩn bị bộ kiểm định mới; xác nhận nguồn gốc/lịch sử tiếp xúc và chốt snapshot trước chạy/chấm. Không đổi tên hoặc sửa fixture cũ rồi gọi là tập độc lập.
- [ ] Tổ chức người chấm đọc cùng run ID/gói bằng chứng, nộp đủ control và khai đúng mức hỗ trợ/tiếp xúc; giữ riêng nhãn có AI hỗ trợ và luyện tập.
- [ ] Người đánh giá rà bất đồng và căn cứ chưa phù hợp; lưu biên bản riêng, giữ nhãn đã khóa. Tiếp tục rà 15 control lệch kết luận tổng và 19 tiêu chí lệch khóa trong bộ phát triển 38 hồ sơ.
- [ ] Chạy đánh giá trên nguồn được chấp nhận; xuất kết quả từng control, phân biệt lỗi/lần đầu/sau sửa và đo độ đúng với nhãn người đánh giá đủ điều kiện.
- [ ] Người phụ trách ghi 56 quyết định tính áp dụng và kế hoạch xử lý/duy trì; có lý do, người nhận, hạn và cách kiểm tra lại. Dùng công cụ nhập theo lô sau khi đã rà nội dung thực tế.
- [ ] Thẩm định từng tiêu chí trên nguồn hiện hành; hoàn thiện hồ sơ và trình người có trách nhiệm phê duyệt SoA khi đủ điều kiện.

Khi có thay đổi code/nguồn, chạy kiểm tra phù hợp và lưu minh chứng mới. Chỉ tích hoàn thành khi có kết quả thực tế; chạy Agent xong không đồng nghĩa control tuân thủ.

## Nền tảng bàn giao từ tuần 6

Đây là trạng thái tại mốc bàn giao **21–22/11**, không phải thành tích thực hiện tuần 7:

- Đã bổ sung [vòng đời tư vấn/khắc phục](../docs/TU_VAN_VA_KHAC_PHUC_ISO.md): profile ISMS, baseline phát hiện, đề xuất, giao việc, nguồn sau, xác minh tách vai trò và báo cáo trước–sau, PostgreSQL lưu qua restart. Đợt chính chưa có hồ sơ thật trong module mới. Cần nhập bối cảnh/phân vai, sử dụng nguồn thật; các giới hạn thư viện tiêu chuẩn, hình ảnh/OCR, risk register, thông báo và xuất XLSX/PDF server ghi trong báo cáo, chưa coi đã hoàn thành toàn bộ prompt nâng cấp.
- Bổ sung gate SoA chặn quyết định thiếu/sai kiểu tính áp dụng; 397 Python đạt. Đã kiểm Edge cho lý do khóa nút thiếu nguồn và điều hướng mở hồ sơ; giữ nguyên các mục chờ nguồn/quyết định thật.
- Đã có CLI kiểm tra trước tệp nguồn ngày 22/11, không nhập database và không gọi Agent; 387 test Python đạt. Dùng khi nhóm cung cấp nguồn mới theo [hướng dẫn](../docs/KIEM_TRA_NGUON_TRUOC_KHI_NOP.md); các mục chờ nguồn/xác nhận vẫn mở.
- Đã nối kiểm tra trước nguồn lên web, cùng kiểm quyền đợt và bộ lọc nhập thật; 388 test Python đạt. Đây là phần chuẩn bị kỹ thuật ngày 22/11, chưa thay nguồn thật hoặc phê duyệt còn thiếu.
- Đã có luồng quản lý 56 control, thu/kiểm toàn vẹn nguồn, Agent chạy lô, chấm mù, thẩm định, báo cáo và SoA dự thảo; có nhập quyết định/kế hoạch theo lô và điều hướng bốn màn hình.
- Kiểm chứng mới nhất ngày 22/11: **380 test Python, 14 JavaScript**, API 39 kiểm tra ba tài khoản và ghi thật trên database riêng đạt; 11 luồng UI cũ đạt, ca nguồn mới đạt sau sửa test, tổng 12 kịch bản qua hai lần chạy. Xem [báo cáo khóa sổ 22/11](../docs/HOAN_THIEN_TUAN_06_2026_11_22.md); không chuyển công việc này thành thành tích tuần 7.
- Đã chạy lại 18 A.8 lab và 38 hồ sơ mô phỏng ngày 22/11, không lỗi kỹ thuật cuối; bộ 38 khớp khóa phát triển 23/38, còn 15 lệch tổng và 19 lệch tiêu chí. Có công cụ so sánh hai lượt và xuất hiện trạng nguồn 56; đây vẫn là thực nghiệm phát triển, chưa phải độ đúng độc lập.
- Bổ sung ngày 22/11: thống nhất kiểm tra nội dung ở connector thư mục/web, 385 test Python đạt; quét 56 thư mục chưa có nguồn mới hợp lệ. Không chuyển phần đã làm này thành nhiệm vụ tuần 7 hoặc coi các nguồn thiếu đã được bổ sung.
- Đợt chính: 19 control có nguồn ngoài preset, 18 qua ngưỡng nội dung; 37 thiếu nguồn và A.6.2 cần thay. Có 0 quyết định áp dụng, 0 thẩm định hiện hành; rubric/SoA chưa được phê duyệt ở mốc bàn giao.
- 38 hồ sơ do trợ lý tạo và gói ứng viên kỹ thuật là dữ liệu phát triển/hồi quy; không thay bộ kiểm định độc lập hoặc nguồn được người phụ trách chấp nhận.

## Nhật ký công việc chính

Chưa phát sinh công việc trong khoảng 23–29/11. Bổ sung ngày thực hiện, ý chính, kết quả và minh chứng khi làm; không ghi trước thành việc đã hoàn thành.

## Kết quả và minh chứng

Chưa có kết quả mới của tuần 7.

Tài liệu để tiếp tục:

- [Nhật ký tuần 6](TUAN_06.md): công việc và minh chứng đã có.
- [Hướng dẫn nhóm chốt việc](../docs/HUONG_DAN_CHOT_VIEC_TUAN_06.md), [phiếu nguồn theo nhóm](../docs/CHOT_VIEC_TUAN_06_2026_11_21.md): hồ sơ và xác nhận cần cung cấp; cập nhật lại khi nguồn thay đổi.
- [Nhập quyết định/kế hoạch theo lô](../docs/NHAP_QUYET_DINH_KE_HOACH_THEO_LO.md), [điều kiện duyệt SoA](../docs/DIEU_KIEN_DUYET_SOA_56.md): thao tác và điều kiện hoàn tất.
- [Toàn vẹn nguồn](../docs/KIEM_TRA_TOAN_VEN_NGUON.md), [ma trận UI](../docs/MA_TRAN_NGHIEM_THU_UI_TUAN_06.md): phạm vi kiểm tra và giới hạn kỹ thuật.

## Vướng mắc và giới hạn

- Nhóm chưa cung cấp nguồn mới, bộ kiểm định hoặc xác nhận chuyên môn ở mốc bàn giao; không tự tạo phê duyệt hay nhãn độc lập thay người thật.
- Probe lab chỉ kiểm tra tiêu chí đại diện; hash khớp không chứng minh nguồn thật hoặc đủ nội dung control.
- Chốt kiểm thử các luồng UI chính không đồng nghĩa bao phủ mọi ngoại lệ hoặc nghiệm thu chuyên môn. Giữ lịch sử lỗi, nhãn khóa và tách dữ liệu thử khỏi đợt chính.

## Việc chuyển tiếp sang tuần 8

Chưa chốt. Rà kết quả cuối tuần 7 rồi xác định; chưa tạo trước nhật ký tuần 8–10.

## Đồng bộ GitHub

Chưa có lần push ghi nhận cho tuần 7. Khi push thực tế, ghi gọn ngày, giờ UTC+7, người push, nhánh và ý chính; không ghi thao tác chạy/dừng hoặc chuyển nhánh.
