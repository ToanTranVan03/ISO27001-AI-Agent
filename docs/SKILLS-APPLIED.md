# Các skill áp dụng trong đồ án HiveFive

Các skill dưới đây hướng dẫn quá trình phát triển bằng Codex. Chúng không
phải dependency ứng dụng hoặc bằng chứng tuân thủ ISO của doanh nghiệp.
Người dùng yêu cầu áp dụng skill vào đồ án ngày 2026-10-30.

## Áp dụng vào quá trình xây dựng

| Skill | Cách áp dụng | Minh chứng trong dự án |
|---|---|---|
| Ponytail | Dùng Python/FastAPI sẵn có, thư viện chuẩn để gọi Ollama; tránh tạo frontend riêng | `agent_core/simulation.py`, `backend/static/` |
| Using Agent Skills | Chọn workflow phù hợp, công khai giả định doanh nghiệp mẫu và phạm vi | `docs/SPEC-people-simulation.md` |
| Spec-Driven Development | Viết yêu cầu, giới hạn và tiêu chí nghiệm thu trước khi triển khai; người dùng đã duyệt | `docs/SPEC-people-simulation.md` |
| Git Workflow and Versioning | Kiểm tra trạng thái, giữ thay đổi theo phạm vi, kiểm tra diff; không thay thế mã benchmark hiện có | Diff trong `backend/main.py`, `git diff --check` |
| Incremental Implementation | Làm phần đánh giá trước, sau đó API và giao diện; chạy kiểm thử mỗi bước | `tasks/plan.md`, `tests/` |
| Test-Driven Development | Viết test trước module mô phỏng, xác nhận lỗi thiếu module, sau đó triển khai và chạy đạt | `tests/test_simulation.py`; API có test hồi quy bổ sung |
| Frontend UI Engineering | Giao diện tiếng Việt, nhãn biểu mẫu, thao tác bàn phím, trạng thái tải/lỗi, bố cục responsive | `backend/static/index.html`, `style.css`, `app.js` |
| API and Interface Design | Tách danh mục và lần chạy; chế độ đầu vào có giới hạn, mã lỗi 404/422/503; giữ hợp đồng API cũ | `backend/main.py`, `tests/test_api.py` |
| Browser Testing with DevTools | Áp dụng kiểm tra bằng trình duyệt thật; môi trường không có Chrome DevTools MCP nên dùng Playwright với Edge | `tests/browser_smoke.cjs` |
| Code Review and Quality | Tự rà soát tính đúng, sự đơn giản, hợp đồng API, lỗi kết nối, cách hiển thị dữ liệu AI | Kiểm thử API, hiển thị bằng `textContent`, giữ trạng thái kiểm soát do quy tắc quyết định |

## Năng lực của agent trong bản mô phỏng

Các năng lực được thực hiện bằng hàm và dữ liệu rõ ràng, chưa dùng hệ thống
nạp skill động:

1. **Lập phạm vi kiểm tra**: xác định tình huống và tám kiểm soát con người.
2. **Thu thập bằng chứng mô phỏng**: lấy hồ sơ nhân sự, tài khoản và thiết bị;
   gắn mã nguồn và hash nội dung.
3. **Đánh giá hồ sơ**: thẩm tra, cam kết lao động, NDA, đào tạo, phổ biến quy
   trình xử lý vi phạm và kênh báo cáo sự kiện.
4. **Kiểm tra nghỉ việc**: liên kết người nghỉ việc với quyền còn mở và
   thiết bị chưa bàn giao.
5. **Kiểm tra làm việc từ xa**: đối chiếu chính sách, mã hóa laptop và MFA VPN.
6. **Đề xuất xử lý**: nêu HR/IT/SecOps phụ trách, lý do và hồ sơ cần xem.
7. **Giải thích bằng AI**: Ollama `qwen2.5:7b` viết đề xuất từ các phát hiện;
   không được thay thế trạng thái đã tính từ bằng chứng.

## Mô hình doanh nghiệp 3D theo video tham khảo

- Từ video, lấy cấu trúc góc nhìn xiên, nhân vật hoạt hình, bảng nhiệm vụ và
  trạng thái nổi phía trên nhân vật. Không sử dụng thương hiệu của video.
- Theo điều chỉnh của người dùng: một tòa nhà trên Trái Đất, có ba tầng,
  khuôn viên cây xanh, mặt kính và vườn mái; không dùng bối cảnh sao Hỏa.
- Dùng Three.js 0.170.0 và OrbitControls phục vụ từ thư mục `static/vendor`,
  có giấy phép MIT đi kèm. Không cần kết nối CDN khi mở ứng dụng.
- `campus.js` nhận cùng dữ liệu mô phỏng với bảng nhân sự. Phát hiện được gắn
  đúng nhân vật theo mã `HF-xxx`, có xem hồ sơ tài khoản và thiết bị.
- Kiểm thử WebGL thực tế: chọn nhân vật qua danh sách, chuyển tầng/phòng ban,
  bật/tắt nội thất, 8 nhân sự được làm nổi bật trong tình huống đào tạo.
- Sau phản hồi giao diện rối, áp dụng Frontend UI Engineering để giảm thông
  tin hiển thị: một phòng, một nhãn nhân vật, luồng ba bước và chi tiết thu gọn.
- Áp dụng TDD cho tìm đường tránh bàn và biên phòng trong `navigation.mjs`;
  kiểm thử trình duyệt xác nhận nhân vật đi được bằng WASD và click trên sàn.

## Cách trình bày trong báo cáo đồ án

“Đồ án vận dụng các skill phát triển phần mềm của Codex để xác định yêu cầu,
triển khai từng phần, kiểm thử và kiểm tra giao diện. Agent HiveFive sử dụng
quy tắc đối chiếu bằng chứng cho nhóm kiểm soát con người A.6, kết hợp mô hình
ngôn ngữ chạy cục bộ để giải thích hành động khắc phục. Kết quả được truy vết
đến hồ sơ giả lập; thiếu bằng chứng không được coi là tuân thủ.”

Không dùng kết quả kiểm thử phần mềm hoặc kết quả benchmark cũ để tuyên bố
độ chính xác kiểm toán thực tế hoặc doanh nghiệp đã được chứng nhận ISO.

## Bổ sung Agent điều phối công cụ theo mục tiêu

- Áp dụng Incremental Implementation và TDD: kiểm thử phát hiện hỗn hợp,
  nhánh kiểm tra sâu theo bằng chứng, lưu việc không trùng, kiểm tra lại khi
  nguồn thay đổi, lỗi model và từ chối công cụ ngoài danh sách cho phép.
- API and Interface Design: endpoint NDJSON phân biệt action/tool_result
  với complete/error; goal có giới hạn, mode AI và workflow riêng biệt.
- Frontend UI Engineering: mục tiêu là điểm bắt đầu chính, nhật ký thực tế,
  công việc và phạm vi thu gọn; diễn tập thủ công trở thành phần tùy chọn.
- Ponytail: dùng Ollama và SQLite có sẵn, không thêm framework agent hoặc
  dependency; mô hình chỉ quyết định công cụ, quy tắc vẫn xác minh bằng chứng.

Mô tả cập nhật cho báo cáo: “Agent chuyên biệt HiveFive dùng LLM cục bộ để
chọn công cụ trong vòng lặp mục tiêu–hành động–quan sát. Bộ công cụ kiểm tra
con người liên kết nhân sự với tài khoản và thiết bị, mở kiểm tra sâu theo
phát hiện, lưu công việc đề xuất và tái kiểm tra bằng chứng. Quyền tự chủ
được giới hạn trong mô phỏng; chưa vận hành hệ thống HR/IAM thực tế.”

## Giám sát theo sự kiện và thiết kế mô hình

Theo yêu cầu không bấm nút chạy Agent, mở rộng bằng worker máy chủ tự nhận
sự kiện nghiệp vụ. Áp dụng TDD cho xử lý nền, thay đổi trong lúc xử lý,
chống sự kiện trùng và khắc phục/tái kiểm tra. Khi kiểm thử thực tế phát hiện
VPN đã thu hồi của người nghỉ việc gây thiếu bằng chứng remote giả, đã sửa
điều kiện áp dụng A.6.7 và bổ sung kiểm thử hồi quy.

Frontend UI Engineering được dùng để đưa mô hình lên trước, nghiệp vụ cạnh
nhân vật, phát hiện và cách xử lý tự hiển thị; chi tiết kỹ thuật thu gọn.
Thiết kế vật liệu oak/sage, sàn có texture, nội thất bo cạnh, cửa kính và
nhân vật có chi tiết, có điều chỉnh ánh sáng và giới hạn zoom. Thiết kế
kiến trúc, ma trận kiểm soát và phương pháp thực nghiệm được ghi riêng trong
`THIET-KE-DO-AN.md`; không tuyên bố số liệu độ chính xác chưa đo.
# Bổ sung cho nâng cấp học thuật

Planning and Task Breakdown và Incremental Implementation được áp dụng qua
`tasks/plan.md`, `tasks/todo.md`, triển khai/tái kiểm thử từng phần. Frontend
UI Engineering được áp dụng cho hồ sơ sự việc, vòng đời xử lý, bảng trước/sau
và thẻ nhân sự/tài sản ngay trên cảnh 3D. Kiểm tra DOM, console và tương tác
trình duyệt thực qua công cụ browser có sẵn; không cài thêm Chrome DevTools.
Ponytail được áp dụng để dùng lại API nghiệp vụ và evaluator, không thêm
framework hoặc dependency. Kết quả nghiên cứu không được tạo từ số giả định;
chạy Ollama thật và ghi rõ dữ liệu tổng hợp, tập AI nhỏ và giới hạn suy luận.


## Ngữ cảnh nghiệp vụ và nghiên cứu ghép cặp

Tiếp tục dùng Planning/Incremental Implementation cho checklist và các lát
nghiệp vụ có thể kiểm chứng; Frontend UI Engineering cho nhóm thao tác,
bằng chứng mâu thuẫn và khắc phục theo vai trò. Debugging được dùng để xử lý
mâu thuẫn hai chiều, kiểm tra ngoại lệ đúng phạm vi và ngày mô phỏng tái lập.
Ponytail giữ nguyên SQLite/Ollama và bộ công cụ chuyên biệt. Kết quả ghép cặp
được chạy thực tế, ghi hash và độ phân tán; giới hạn suy luận được nêu trong
NGHIEN-CUU-VA-DANH-GIA.md. Không có thí nghiệm người dùng chưa được thu thập.
