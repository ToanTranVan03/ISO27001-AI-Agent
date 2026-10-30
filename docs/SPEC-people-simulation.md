# Đặc tả mô phỏng doanh nghiệp ISO 27001 — trọng tâm con người

Trạng thái: được người dùng duyệt ngày 2026-10-30; triển khai theo kế hoạch trong `tasks/plan.md`.

Bổ sung được người dùng yêu cầu trong lúc triển khai: văn phòng 3D tương tác,
có xoay/phóng to, chọn nhân sự xem tài khoản và thiết bị; trạng thái phát hiện
được đồng bộ với kết quả tình huống. Dùng Three.js bản ghim, phục vụ local,
kèm giấy phép MIT. Bảng nhân sự vẫn là cách truy cập thay thế cho cảnh 3D.
Tham khảo video người dùng cung cấp về góc nhìn và nhân vật hoạt hình; theo
điều chỉnh của người dùng, bối cảnh là Trái Đất với một tòa nhà văn phòng đẹp,
không dùng sao Hỏa. Tòa nhà ba tầng, mặt kính, sân vườn và vườn mái; có chế độ
ngoại thất/nội thất và chọn phòng ban để xem tầng phù hợp.

Điều chỉnh sau phản hồi giao diện bị rối: mặc định xem một phòng theo phối
cảnh game văn phòng; toàn tòa nhà là chế độ tham khảo. Chọn nhân vật và bấm
sàn để đi theo đường tránh bàn, hoặc dùng WASD/phím mũi tên/nút trên màn hình.
Không ra ngoài biên phòng. Di chuyển là minh họa, không thay đổi bằng chứng
hoặc kết quả đánh giá. Luồng diễn tập ba bước: Sự việc → Agent kiểm tra →
Cách xử lý. Bảng 50 người, kiểm soát không có phát hiện và dữ liệu kỹ thuật
được thu gọn mặc định. Chỉ nhân vật đang chọn có nhãn nổi để tránh chồng chữ.

## Mục tiêu và giả định

Điều chỉnh mới: người dùng thao tác nghiệp vụ, Agent phải tự phản ứng thay
vì đợi nút kiểm tra. Nguồn sống bắt đầu đầy đủ hồ sơ, lưu sự kiện và phiên
bản trong SQLite; worker nhận phiên bản chưa xử lý trên máy chủ, tự gọi
Agent và tái kiểm tra sau thao tác khắc phục. Bằng chứng được đối chiếu ngay,
trạng thái xác minh AI tách riêng. Không mất thay đổi trong lúc Agent chạy.
Mô hình là điểm bắt đầu chính, bảng nghiệp vụ cạnh phòng trên desktop và
Trạm giám sát hiển thị bằng chứng, kiểm soát, cách xử lý không cần chuyển bước.

Bổ sung theo phản hồi “chưa Agent, quá thủ công”: thêm chế độ nhận mục tiêu,
điều phối công cụ theo vòng lặp quan sát → chọn công cụ → thực thi → kiểm tra.
Ollama chọn hành động từ danh sách công cụ hợp lệ; có chế độ workflow quy tắc
riêng được ghi rõ. Không cần chọn tình huống trước. Agent đọc trạng thái
doanh nghiệp giả lập có nhiều vấn đề đồng thời, đánh giá phần đã có công cụ,
đối chiếu phạm vi 56 kiểm soát, tạo công việc nội bộ và lưu lịch sử SQLite.
Khi phát hiện tài khoản người nghỉ việc hoặc remote không an toàn, tự gọi
công cụ kiểm tra sâu tương ứng. Các công việc là đề xuất trong mô phỏng,
không gửi cho nhân sự thật. Chạy lại dùng trạng thái mới và cập nhật công
việc theo bằng chứng; không tự xác nhận đã đào tạo/ký NDA. Các kiểm soát chưa
có evaluator/connector phải ghi rõ chưa đánh giá, không tính là đã bao phủ.

Mở rộng ngay dự án hiện tại, dùng HiveFive (50 nhân viên, bốn phòng IT,
Ops, Finance, Sales) làm doanh nghiệp giả lập. Một chức năng xuyên suốt:
chạy tình huống nhân sự → thu thập bằng chứng → đánh giá → đề xuất khắc phục.
Phần mềm và phần cứng là tài sản liên kết với nhân sự trong cùng mô phỏng.

Giữ Python, FastAPI, LangGraph và Ollama hiện có. Giao diện và báo cáo bằng
tiếng Việt. Không dùng dữ liệu nhân sự thật trong bản đầu.

## Phạm vi bản đầu

- Hồ sơ nhân sự giả lập: phòng ban, vai trò, trạng thái làm việc, thẩm tra,
  cam kết bảo mật, đào tạo, nhận thức báo cáo sự kiện và làm việc từ xa.
- Phần mềm: tài khoản HR, email, VPN, hệ thống nghiệp vụ; quyền truy cập
  và trạng thái tài khoản gắn với người sở hữu.
- Phần cứng: laptop và thiết bị làm việc được cấp; người giữ tài sản,
  tình trạng mã hóa và bàn giao.
- Bao phủ A.6.1–A.6.8 bằng bằng chứng và rubric của dự án. Đối chiếu các
  tài khoản, thiết bị khi đánh giá nghỉ việc và làm việc từ xa.
- Tình huống có thể chạy lại: nhân viên mới thiếu NDA; đào tạo chưa hoàn tất;
  nhận email đáng ngờ và báo cáo; nghỉ việc còn tài khoản hoặc chưa trả laptop;
  làm việc từ xa bằng thiết bị chưa đáp ứng chính sách.
- Kết quả mỗi lần chạy: mã tình huống, bằng chứng nguồn, kiểm soát liên quan,
  phát hiện, mức ưu tiên xử lý, lý do và hành động đề xuất cho HR/IT/quản lý.
- Trang web nội bộ đơn giản phục vụ qua FastAPI: xem doanh nghiệp, chọn
  tình huống, chạy agent và đọc kết quả. Không cần một dự án frontend riêng.
- Có chế độ quy tắc để chạy mô phỏng khi Ollama không sẵn sàng. Ghi rõ chế độ
  đánh giá; không trình bày kết quả quy tắc như kết quả từ mô hình AI.

## Luồng xử lý và nguyên tắc

Tạo bản sao dữ liệu mẫu cho mỗi lần chạy → áp dụng tình huống → lập kế hoạch
kiểm tra → thu thập bằng chứng → đối chiếu quy tắc → AI giải thích khi được
chọn và khả dụng → xác minh → báo cáo. Các lần chạy độc lập, không làm thay
đổi fixture gốc. Không dùng nhãn đáp án benchmark để thay thế việc đánh giá
bằng chứng của mô phỏng mới.

Thiếu bằng chứng phải trả `Insufficient Evidence`; không coi không có dữ liệu
là tuân thủ. Kết quả truy vết được đến hồ sơ giả lập. Điểm và ngưỡng là quy
ước mô phỏng/chính sách nội bộ, không tuyên bố là ngưỡng bắt buộc của ISO.
Không suy ra chứng nhận hoặc tuân thủ toàn bộ ISO 27001 từ nhóm A.6.

## Cấu trúc và phong cách mã

- `agent_core/`: dữ liệu, xử lý tình huống và đánh giá mô phỏng.
- `backend/main.py`: giữ API cũ, bổ sung API mô phỏng và trang giao diện.
- `backend/static/`: giao diện HTML/CSS/JavaScript tối thiểu.
- `tests/`: kiểm thử bằng `unittest` của Python.
- `docs/`: đặc tả, hướng dẫn chạy và giới hạn.

Hàm dùng snake_case và trả cấu trúc dữ liệu rõ ràng, ví dụ:
`run_simulation(scenario_id, mode="rules")`.
Kiểm tra đầu vào tại API; mã tình huống không tồn tại trả lỗi có ý nghĩa.
Không thêm dependency nếu thư viện hiện tại hoặc thư viện chuẩn đáp ứng.

## Lệnh dự kiến

Chạy tại `D:\ISO27001-AI-Agent`:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
python -m unittest discover -s tests -v
```

Chế độ AI cần Ollama và model `qwen2.5:7b` hiện có. Khi lỗi kết nối, giao diện
phải giải thích được lỗi và cho phép chạy lại bằng quy tắc. Không tự tải model.

## Tiêu chí nghiệm thu và kiểm thử

1. Mở được giao diện local, thấy nhân sự cùng phần mềm và thiết bị liên quan.
2. Chạy được các tình huống trên; có bằng chứng, lý do và đề xuất xử lý.
3. Kiểm thử phát hiện đào tạo thiếu, NDA thiếu và tài khoản còn mở sau nghỉ việc.
4. Kiểm thử thiếu bằng chứng, mã tình huống sai và tính độc lập giữa các lần chạy.
5. Chế độ quy tắc chạy không cần model; chế độ AI phân biệt được lỗi kết nối.
6. API `/api/evaluate` hiện tại vẫn giữ hợp đồng đầu vào/đầu ra.
7. Kiểm tra API và trình duyệt thực tế nếu môi trường cho phép; ghi rõ phần
   nào đã kiểm tra và phần nào chưa kiểm tra.

## Ranh giới

- Luôn: dữ liệu giả lập, truy vết bằng chứng, kiểm tra đầu vào và kiểm thử logic.
- Cần thống nhất riêng: đưa dữ liệu nhân sự thật vào, tích hợp hệ thống doanh
  nghiệp hoặc triển khai cho nhiều người dùng qua mạng.
- Không thực hiện: tự khóa tài khoản, gửi email lừa đảo, xử lý kỷ luật tự động,
  thay đổi thiết bị thật, công bố chứng nhận ISO hoặc đưa bí mật vào Git.

## Điểm cần xác nhận

Đề xuất bắt đầu với giao diện web local, doanh nghiệp HiveFive hiện có và
mô phỏng A.6.1–A.6.8 như trên. Tích hợp HR/IAM thật, xác thực nhiều người dùng
và lưu lịch sử vào cơ sở dữ liệu nằm ngoài bản đầu.
