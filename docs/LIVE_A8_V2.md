# Live A.8 v2 — 18 probe đại diện trong lab

Cập nhật 11/11/2026. Rubric: **`a8-live-v2-active`**. Phạm vi đồ án vẫn là 56 control; đây là nhánh thực nghiệm 18 A.8.

## Thay đổi có thể kiểm chứng

Đã bổ sung 13 probe bên cạnh 5 probe quan sát trước đây. Runtime dùng Python 3.12/Debian và OpenSSL trong container, không có mạng ngoài hoặc cổng publish, không được cấp NET_ADMIN/privileged và không mount Docker socket. Base image được pin digest trong Dockerfile. Nguồn gồm thao tác tệp/quyền, crypto, giao dịch TCP/TLS loopback và các thành phần bảo vệ ứng dụng lab có mã thực thi.

**Có probe không đồng nghĩa đã đáp ứng toàn bộ control ISO.** Một số tiêu chí đại diện mới khác raw v2 và live v1; ví dụ A.8.1 kiểm tra quyền hồ sơ và mã hóa tệp ứng dụng, không gán thành EDR hoặc mã hóa toàn ổ đĩa. Các giới hạn dưới đây thuộc phạm vi rubric, cần người phụ trách xác nhận.

| Control | Nguồn/phép thử thực hiện | Giới hạn |
|---|---|---|
| A.8.1 | `su labworker` kiểm tra quyền đọc; OpenSSL AES/PBKDF2 giải mã tệp mẫu và đối chiếu hash/bản plaintext phụ | Không phải EDR, full-disk encryption hoặc quản lý toàn bộ endpoint |
| A.8.2 | Quyền ghi cấu hình quản trị và tài khoản labadmin thực; hồ sơ review lab | Không bao phủ sudo/PAM/IAM doanh nghiệp; review không phải người thật ký |
| A.8.3 | Quyền ghi hồ sơ thực và bản ghi access review | Không chứng minh toàn bộ phân quyền doanh nghiệp |
| A.8.5 | Dịch vụ TCP lab xác thực PBKDF2 và token HMAC theo thời gian; thử sai password/thiếu yếu tố thứ hai/thông tin đúng | Token lab không phải chứng nhận chuẩn TOTP; chưa tích hợp IdP/MFA production |
| A.8.7 | Scanner tìm chữ ký thử vô hại trong tệp và chuyển vào quarantine; mtime cơ sở chữ ký | Scanner tự xây, không phải antivirus/EDR, không có phép đo phát hiện malware thực |
| A.8.8 | Truy vấn inventory dpkg hiện tại, đối chiếu advisory package/version tổng hợp | Advisory LAB, không phải CVE/feed thực; chưa bao phủ quy trình remediation |
| A.8.9 | Đọc cấu hình hiện tại, tính hash, đối chiếu baseline/CAB lab | Baseline lab chưa được người có thẩm quyền duyệt |
| A.8.10 | Retention cấu hình, biên nhận và tồn tại đối tượng | Chưa chứng minh secure erase/vòng đời mọi dữ liệu |
| A.8.12 | Giao dịch TCP chứa mẫu LAB-CONFIDENTIAL, phản hồi chặn và sự kiện audit | Bộ lọc nội dung đơn giản trong lab, chưa là DLP doanh nghiệp |
| A.8.13 | Hash backup và nội dung restore thực | Chưa chứng minh RPO/RTO, offsite hoặc lịch vận hành dài hạn |
| A.8.15 | Log ứng dụng, seal hash và quyền tệp thực | Không phải auditd/SIEM; quản trị root vẫn có thể thay cả log và seal |
| A.8.16 | Watcher phát hiện sửa tệp thử, thời gian phát hiện và biên nhận sink lab | Tác vụ ngắn trong tiến trình probe, không phải giám sát vận hành lâu dài/SIEM ngoài |
| A.8.17 | Đối chiếu nguồn thời gian ứng dụng qua TCP, HMAC/nonce, đo offset/RTT | Hai phía cùng clock container, có offset chủ đích; không chứng minh NTP hoặc OS được đồng bộ độc lập |
| A.8.19 | Quyền thư mục cài và inventory dpkg hiện tại so với danh mục lab | Chưa chặn mọi cách cài hoặc chứng minh quy trình CAB thực |
| A.8.20 | TCP từ hai địa chỉ loopback, kiểm tra source ACL và luồng được phép | ACL ứng dụng, không phải firewall kernel hay mạng vật lý |
| A.8.22 | TCP kiểm tra gate dịch vụ quản trị/nghiệp vụ từ nguồn nhân viên | Không phải VLAN, subnet, namespace hoặc cách ly mạng ở tầng hạ tầng |
| A.8.24 | Handshake TLS 1.2/1.3, xác minh cert lab; quyền đọc private key | Chứng chỉ lab tự ký được trust riêng cho phép thử; chưa chứng minh PKI/rotation toàn doanh nghiệp |
| A.8.32 | Hash release gắn bản ghi thay đổi và copy rollback, đối chiếu nội dung phục hồi | Phê duyệt CAB do lab dựng; chưa kiểm chứng toàn bộ CI/CD/quản trị thay đổi |

## Cách thu nguồn và xử lý thiếu

- `live_probe.sh` chỉ nhận 4 profile và 18 ID đã allowlist. Năm probe cũ đọc tài nguyên; 13 probe mới chạy phép thử chủ động có giới hạn trong `/lab/live-extended`, dùng tệp tạm và loopback container.
- Không nhận shell/đường dẫn tùy ý từ API. Collector không nhận Boolean đạt/sai đặt sẵn: nó đọc mã trả về, giao dịch, inventory, hash, mode, timestamp và raw JSON rồi suy ra facts.
- Gói nguồn có schema, control/asset ID, thời điểm, nội dung và hash. Sai danh tính, timestamp quá hạn, công cụ lỗi hoặc thiếu nguồn thì trả unknown. Metadata/probe lỗi không được tính thành quan sát hữu ích và không được gọi LLM để đoán.
- Bản ghi lỗi không chứa đường dẫn profile, tránh lộ hồ sơ trong gói chấm mù.
- Triển khai mới không sửa report/snapshot/nhãn của lượt trước. Hash rubric mới không kế thừa phê duyệt cũ. Tập live không dùng đáp án của bộ raw để tính accuracy.

## Kiểm chứng kỹ thuật

- [72 tình huống — 18 control × 4 profile](a8-results/live-v2-engineering.json): **72/72** khớp thiết kế tình huống, baseline không có lỗi engine. Đây là kiểm chứng lab do nhóm dựng, không phải accuracy chuyên gia.
- [Thử đổi nguồn thực và khôi phục](a8-results/live-v2-mutations.json): 5 thay đổi ở private key TLS, cơ sở chữ ký scanner, ACL dịch vụ, dữ liệu rollback và cấu hình nhận cảnh báo đều làm facts thay đổi; sau khôi phục facts trở lại. Điều này kiểm tra sự phụ thuộc vào nguồn hiện tại, không chỉ vào tên profile.
- Kết quả live v1/pilot v5 cũ vẫn được giữ riêng. Lượt live v2 dùng rubric/check mới nên không gộp tỷ lệ hoặc suy ra chất lượng tăng từ số cũ.

### Lượt Agent đã chạy trên API thật

- Lượt `67d38694-724e-4cc1-83f8-9df07f5cc3b2`, tạo **21:42:30 ngày 11/11/2026 (UTC+7)**; profile mixed, Qwen2.5:7b, rubric live v2. Gói bằng chứng được chốt trước suy luận.
- 18/18 control có quan sát. 17 phản hồi hợp lệ ngay lần đầu; A.8.3 mâu thuẫn rubric ở lần đầu và được model sửa hợp lệ ở lần hai. Cuối lượt không còn lỗi engine, cả 18 kết luận là một phần theo tiêu chí lab của hồ sơ mixed.
- Đây là một lượt pilot trên cấu hình nhóm đã thiết kế; **không phải accuracy so với người thật hoặc tập held-out**. Guard kiểm tra nhất quán theo cùng rubric nên không lấy số kết luận cuối hợp lệ làm bằng chứng độc lập về chất lượng AI.
- [Hồ sơ nguồn, phản hồi và lịch sử lỗi JSON](a8-results/live-v2-ollama-pilot.json), [bảng từng control CSV](a8-results/live-v2-ollama-pilot.csv), [SoA dự thảo](a8-results/SOA_LIVE_V2.md).
- Báo cáo và hai nhãn đã nộp của lượt cũ `2370c707…` được giữ nguyên lúc kiểm tra sau triển khai. Không chuyển nhãn sang lượt mới, không nộp nhãn hay phê duyệt thay thành viên.
- Kiểm tra phần mềm: **190 test Python, 5 test JavaScript, lint và build đạt**; còn 3 cảnh báo thư viện Python. Chưa kiểm thử bấm toàn bộ UI hoặc nghiệm thu chuyên môn.

## Dựng và kiểm tra

```powershell
docker compose -f docker-compose.a8.yml build
docker compose -f docker-compose.a8.yml up -d --no-build
.venv\Scripts\python.exe -m lab_a8.verify_live_v2 --output work/live-v2-kiem-tra-moi.json
```

Không chạy các phép sửa nguồn cùng lúc Agent đang thu chính các tài nguyên đó. Mỗi lượt chốt snapshot trước suy luận; dùng snapshot để đối chiếu engine trên đúng cùng nguồn. Chuẩn bị plan mới khi mã/rubric đổi; không ghi đè plan hoặc báo cáo cũ để vượt kiểm tra hash.

Trong UI, danh sách lượt đã sắp mới nhất trước và có rubric/ID ngắn. Người đang chấm lượt live v1 tiếp tục chính lượt đó; muốn chấm rubric live v2 phải chọn lượt mới, không mang nhãn cũ sang.

## Chưa được kết luận

- Chưa có kết quả chuyên gia độc lập/tập held-out đã xác nhận; không nhận 72/72 là độ đúng LLM.
- Chưa hoàn thiện đầy đủ nội dung 18 control hoặc tự động hóa toàn bộ 56 control.
- Hồ sơ, tính áp dụng, phê duyệt rubric/SoA và mức độc lập người đánh giá vẫn cần người có trách nhiệm xác nhận.
