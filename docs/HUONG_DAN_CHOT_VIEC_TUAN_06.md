# Hoàn tất các mục còn chờ của tuần 6

Cập nhật 21/11/2026. Đây là hướng dẫn thao tác và phân công **đề xuất**, không phải biên bản xác nhận đã làm. Phạm vi 56 control và thực nghiệm sâu 18 A.8 được giữ nguyên.

## Phần trợ lý đã làm được

- Công cụ thu/lưu bản gốc, kiểm chất lượng nguồn, đánh giá lô, chấm mù, báo cáo và điều kiện duyệt SoA.
- Bộ lọc chất lượng căn cứ, sổ xử lý bất đồng riêng; giữ nhãn khóa và các lần lỗi.
- Bảng **Cần làm gì để hoàn tất?** ở Tổng quan 56 control: đọc dữ liệu hiện hành, phân bước/vai trò, mở đúng control và xuất checklist JSON/Markdown. Checklist không được nạp lại làm bằng chứng tuân thủ.
- Kiểm thử API và trình duyệt; phần nộp nguồn/thẩm định/quyết định dùng dữ liệu thử cô lập phải được ghi riêng với thao tác trên hồ sơ thật.

## 1. Toàn: chốt phương pháp với thầy/người phụ trách

Mang theo rubric hiện hành, ma trận 56 control và một gói artifact A.8 để thống nhất:

1. 18 control A.8 đang kiểm tra phần nào; tiêu chí lab có được chấp nhận cho thực nghiệm không, phần nào còn ngoài phạm vi probe?
2. Có chấp nhận Khoa/Tú là người đánh giá nội bộ khi tham gia phát triển không? Nếu cần người khác/năng lực khác, thống nhất ai và cách chấm.
3. Thầy chấp nhận cách tách tập phát triển/kiểm định, số ca và phương pháp so sánh nào?

Lưu kết quả trao đổi: người xác nhận, ngày, phiên bản/hash rubric, nội dung đồng ý và điều chỉnh. Không tự khai thầy đã duyệt nếu chưa trao đổi.

Sau khi thực sự rà rubric, admin mở **Tổng quan 56 → Quản lý nguồn, tiêu chí và hồ sơ bàn giao → Tiêu chí toàn phạm vi 56**, ghi căn cứ thực tế rồi xác nhận. Xác nhận rubric A.8 theo nguồn ở **Thực nghiệm A.8 → Phạm vi, rubric và phê duyệt** là một hồ sơ riêng; không nhầm hai phạm vi.

## 2. Nhóm: bổ sung nguồn của doanh nghiệp lab

Không bắt buộc doanh nghiệp production. Cần artifact/hồ sơ thực sự có nội dung của mô hình lab đã dựng, không dùng bảng đáp án, mẫu yêu cầu trống hoặc cờ đúng/sai thay cấu hình/log gốc.

Đề xuất chia thu nguồn (cần nhóm đồng ý, chưa phải giao việc đã xác nhận):

| Người | Nhóm việc đề xuất | Sản phẩm cần giao |
|---|---|---|
| Trần Văn Toàn | Điều phối, nguồn A.6 và rà A.6.2 | Hồ sơ HR lab đúng đối tượng/kỳ kiểm tra, nguồn A.6.2 đọc được và kết quả rà phạm vi |
| Lê Đăng Khoa | Nguồn A.7 | Hồ sơ/nhật ký kiểm soát vật lý lab theo từng tiêu chí; mô tả rõ phần mô phỏng |
| Lê Đoàn Văn Tú | Nguồn A.8 còn thiếu, phối hợp bộ nguồn mới | Cấu hình/log/export và bằng chứng phép thử gốc, có phạm vi/giới hạn |

Thao tác cho từng control:

1. Mở **Tổng quan 56 → Cần làm gì để hoàn tất? → Bổ sung nguồn**, bấm mã control.
2. Đọc tiêu chí và loại bằng chứng trước khi tìm/nộp nguồn. Với A.6.2, tải/đọc bản gốc nếu có; thay nguồn một ký tự bằng tài liệu đúng có nội dung trích xuất được. Không tự viết kết luận đạt thay hồ sơ.
3. Trong **Đọc tiêu chí & bổ sung bằng chứng**, chọn loại nguồn đúng, ghi xuất xứ, thời điểm quan sát nếu biết và giới hạn mẫu; nộp bản gốc. PDF scan không đọc được cần bản văn bản/OCR được chủ nguồn đối chiếu.
4. Đọc lại nội dung đã thu, kiểm tra hash và đối tượng. Chạy **Agent đánh giá hồ sơ đã thu**; có nhiều control thì dùng lô tại **Hồ sơ ISO**.
5. Rà kết luận/viện dẫn và phần còn thiếu. Nguồn qua ngưỡng văn bản chỉ là đủ đầu vào kỹ thuật, không tự chứng minh đủ control.

Danh sách nguồn: [phiếu hiện hành ngày 20/11](YEU_CAU_NGUON_56_HIEN_HANH.md). Khi dữ liệu đổi, xuất bản mới từ giao diện thay vì dựa mãi vào số 37/19.

## 3. Bộ kiểm định mới: nhóm cung cấp, trợ lý hỗ trợ đóng gói

Người cung cấp chuẩn bị cấu hình/log/hồ sơ mới, có tình huống đạt/sai/thiếu có chủ đích và đáp án thiết kế tách khỏi đầu vào Agent. Không đổi tên, thêm khoảng trắng hoặc sao chép fixture cũ rồi gọi là tập mới.

Ghi ai tạo, lúc nào, hệ thống nguồn, ai đã xem và nguồn có từng dùng chỉnh code/prompt chưa. Chốt tập trước khi xem dự đoán. Nếu đã dùng để sửa hệ thống, ghi đúng là tập phát triển/kiểm tra lại.

Với A.8, thư mục ứng viên theo `<root>/<profile>/A.8.x/<artifact>` trong [ma trận nguồn](MA_TRAN_A8.md). Sau khi bạn cung cấp thư mục, trợ lý có thể kiểm cấu trúc, đóng gói và chạy preflight:

```powershell
.venv\Scripts\python.exe -m agent_core.a8_protocol prepare --profile mixed --transport files --raw-root data/a8-validation/nguon-moi --coordinator "Tran Van Toan" --objective "Candidate awaiting verification" --output work/plan-kiem-dinh-moi.json
```

Lệnh trên chỉ chạy khi thư mục thật đã có; không tự tạo nguồn hoặc xác nhận độc lập. Admin nhập JSON ở **Thực nghiệm A.8 → Nhập gói nguồn ứng viên đã chốt**, kiểm tra trước, sau đó mới quyết định chạy. Dò hash không chứng minh độc lập; cần xác nhận phương pháp riêng.

## 4. Khoa/Tú: chấm phù hợp trên cùng lượt mới

Chỉ thực hiện sau khi thống nhất người chấm/phương pháp. Admin cung cấp cùng run ID và giữ nguyên snapshot.

1. Mỗi người dùng tài khoản riêng, mở **Thực nghiệm A.8 → Mở lượt đánh giá đã lưu**, chọn đúng run ID.
2. Đọc gói mù, rubric và artifact của từng control; tự ghi căn cứ và chọn kết luận.
3. Nếu tự chấm chưa xem đáp án, khai đúng hai lựa chọn đó. Nếu có AI hỗ trợ, trao đổi kết luận hoặc đã xem Agent/đáp án, khai đúng thực tế; không chọn độc lập để tăng số liệu.
4. Nộp và khóa từng nhãn, hoàn tất 18/18. Trợ lý có thể giải thích thao tác/nguồn, nhưng nếu cung cấp kết luận/căn cứ thì phải ghi nhận mức hỗ trợ.
5. Admin mở đúng lượt để xem tiến độ từng người, chất lượng căn cứ và xuất đối chiếu. Không sửa nhãn cũ; lượt cũ có hỗ trợ tiếp tục là lịch sử.

## 5. Toàn và người đánh giá: xử lý bất đồng, thẩm định và SoA

- Mở **Sổ xử lý bất đồng & căn cứ cần rà**, đối chiếu artifact/rubric của từng điểm lệch. Admin lưu nội dung trao đổi thật, hướng xử lý và phần chưa rõ. Không dùng ghi chú để thay nhãn hoặc xóa cảnh báo. Xem [hướng dẫn sổ](SO_XU_LY_BAT_DONG_A8.md).
- Tại **Tổng quan 56 → chọn control → Thẩm định kết luận**, người được phân công đọc từng tiêu chí, chọn đạt/không đạt/chưa rõ, ghi căn cứ và chọn nguồn viện dẫn. Kết luận tổng phải khớp rubric; thiếu nguồn giữ chưa rõ. Đây là thẩm định hồ sơ, không phải chấm mù nghiên cứu.
- Người phụ trách mở **Tính áp dụng & kế hoạch xử lý**: ghi lý do, xử lý/duy trì, người nhận thực tế, hạn/kỳ rà và cách thu lại nguồn xác minh. Không loại trừ chỉ vì thiếu hồ sơ; không tự gán người/hạn chưa thống nhất.
- Sau khi đủ điều kiện, người có trách nhiệm kiểm tra bảng **Hồ sơ nào còn chặn trình duyệt?**, xuất SoA để đọc, ghi căn cứ rồi duyệt fingerprint hiện hành. Không cần biến mọi kết luận thành “tuân thủ”; không đạt/thiếu bằng chứng cần được báo cáo trung thực và có kế hoạch phù hợp.

## Bạn cần gửi lại gì để trợ lý làm tiếp?

1. Kết quả thống nhất rubric/phương pháp/người chấm với thầy: nội dung thực tế, người và ngày xác nhận.
2. Đường dẫn thư mục hồ sơ lab có nội dung cần thu và thư mục bộ kiểm định mới; kèm phạm vi/nguồn gốc/lịch sử đã dùng.
3. Sau khi nhóm tự chấm: run ID; trợ lý kiểm tra liên kết hash, phân loại mức hỗ trợ, tính số liệu và hỗ trợ phân tích bất đồng.
4. Quyết định thật về tính áp dụng, người xử lý/hạn và người có trách nhiệm thẩm định/duyệt. Không cần gửi mật khẩu hoặc yêu cầu giả danh người phê duyệt.

Trợ lý có thể xử lý đóng gói, kiểm tra kỹ thuật, chạy Agent, báo cáo và hướng dẫn giao diện. Việc xác nhận chuyên môn, tự chấm và phê duyệt cần đúng người thực hiện; không đóng các mục này bằng dữ liệu thử.
