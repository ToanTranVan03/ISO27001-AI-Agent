# Bàn giao nghiệm thu khắc phục Linux và hồ sơ 56 control

| Góp ý | Kết quả |
|---|---|
| Cùng đối tượng trước và sau | Nguồn đầu được thu theo môi trường đã chọn. Phát hiện lưu mã đợt, môi trường, ứng dụng, phiên bản và mã nguồn đầu. Đầu việc lấy đích từ phát hiện. Backend chặn yêu cầu khác đích, rồi kiểm lại ngay trong công cụ trước khi đổi gói. |
| Đúng bằng chứng và quyền | Chỉ nhận nguồn lab do server tạo cho bước ràng buộc. Nguồn sau gắn với đúng đầu việc và đích. Dùng quyền và khóa phiên bản hiện có. Hồ sơ cũ vẫn đọc được. Muốn chạy lại ca cũ thiếu định danh phải thu nguồn đầu và tạo phát hiện mới. |
| Việc nhân viên và chuyên viên | Nhân viên thao tác trên thẻ đầu việc, gắn nguồn đúng đích và gửi. Chuyên viên xác minh riêng. Ca A.8.8 ghi cải thiện một phần vì biên nhận ứng dụng mẫu chưa chứng minh tiêu chí bản vá hệ điều hành. |
| Báo cáo và hồ sơ phạm vi | PDF/Excel giữ biên nhận trước–sau và lịch sử. Đã xuất ma trận 56 control, SoA dự thảo và báo cáo đối chiếu theo đợt. |
| Chấm độc lập và phê duyệt | Báo cáo có 17 lượt thử được lưu. Chưa có người chấm đủ điều kiện đối chiếu độc lập trong báo cáo đã xuất. SoA còn chờ rubric, quyết định áp dụng và thẩm định của người phụ trách. |
| Nhiều thiết bị và hệ điều hành | Đã kiểm Windows tại backend và Debian 12 trong container cô lập. Container là đích thử ứng dụng tổng hợp. Tên thiết bị ở khoảng 08:43–09:35 của bản ghi chưa đủ rõ để chọn lab khác. |

## Kịch bản trình bày 7–10 phút

1. **Doanh nghiệp** (`#view=company`): chọn đợt demo riêng và giải thích đối tượng thử. Tài khoản tư vấn quản lý phạm vi. Ca tự động dùng cấu hình tổng hợp, không dùng danh mục doanh nghiệp thật.
2. **Tổng quan 56 control** (`#view=scope56&control=A.8.8`): trong Tư vấn & khắc phục chọn Linux Debian ở phần thu nguồn, thu phiên bản 1.0.0, tạo phát hiện A.8.8 chọn nguồn đầu đó. Lập kế hoạch, duyệt và giao cho nhân viên. Kiểm mã nguồn và đích đã khóa trên thẻ. Tư vấn chạy công cụ và lưu nguồn sau. Phiên bản quan sát 1.1.0, hash khớp.
3. **Hồ sơ ISO** (`#view=dossier&control=A.8.8`): xem nguồn trong đúng đợt và control. Nhân viên quay lại đầu việc, hoàn thành các bước, gắn biên nhận sau và gửi xác minh. Tư vấn đọc nguồn và kết luận mức cải thiện của đầu việc, giữ phần OS chưa có nguồn.
4. **Thực nghiệm A.8** (`#view=a8&control=A.8.8`): minh họa khác biệt giữa một lượt probe kỹ thuật và hồ sơ khắc phục. Chỉ mở lượt A.8 đã lưu khi có liên kết nguồn phù hợp. Ca cập nhật ứng dụng có mã phát hiện dùng chung ở bốn màn hình. Lượt thử A.8 chỉ liên kết khi có nguồn phù hợp.
5. Quay về **Tư vấn & khắc phục**, tải PDF/Excel, chỉ mã phát hiện, mã môi trường, nguồn đầu, phiên bản trước/sau, người duyệt/chạy/xác minh và kết quả còn thiếu.

Lượt hồi quy dùng tài khoản thử do runner tạo. Bản mới đã tạo phát hiện chính, duyệt giao và chuyển bốn màn hình qua Edge. Phép thử quyền và bước tạo phát hiện đối chứng được thực hiện qua API.

## Chạy lại và tệp liên quan

```powershell
npm --prefix frontend-react run build
$env:ISO_TEST_LINUX_LAB='1'
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --remediation-only --output work/linux-nghiem-thu-moi.json
```

Linux cần Docker và image cục bộ iso-a8-live-lab:v2. Dùng giá trị 0 cho biến kiểm thử Linux để chọn backend Windows. Biên nhận dùng dữ liệu thử, runner giữ kết quả và dọn database riêng.

Thay đổi ở backend/remediation_api.py, backend/compliance_report.py và evidence_collectors/control_packages.py để ràng buộc, lưu và đọc định danh nguồn lab. lab_a8/software_update_demo.py kiểm đích trong ca chạy. frontend-react/src/RemediationWorkspace.jsx chọn môi trường khi thu nguồn và giữ đích đã chọn ở phát hiện. frontend-react/tests/live-remediation-mfa.spec.js kiểm hồi quy. Dùng cột xuất xứ nguồn và JSONB sẵn có nên không cần migration mới.

Mốc đợt chính đã xuất: 19/56 có nguồn ngoài preset, 18 có nội dung dùng được, 0 quyết định áp dụng và 0 thẩm định hiện hành. Cần nguồn cho 37 control thiếu, chỉnh nguồn không dùng được, xác nhận rubric, tập kiểm định và người chấm độc lập. SoA đang ở dạng dự thảo. Phê duyệt cần người có thẩm quyền.


## Minh chứng đã kiểm

- [Linux qua Edge](../work/linux-nghiem-thu-2026-11-28.json), [Windows hồi quy](../work/windows-bound-2026-11-28.json), [bàn giao laptop](../work/ban-giao-hoi-quy-2026-11-28.json). MFA cũng chạy trong bộ Linux và Windows. Linux và bàn giao có kiểm sau restart. Database thử đã dọn.
- Phát hiện Linux `77c63f0d-8cd8-4bf7-8506-346484795a89` truy vết trong biên nhận và Excel sau khi database thử được dọn. [Mã phát hiện](../work/ban-giao-nghiem-thu-2026-11-28/ma-phat-hien-linux.json). PDF đã đối chiếu môi trường, ứng dụng, phiên bản và kết quả một phần. Dùng Excel hoặc JSON để tra UUID phát hiện.
- [PDF trước–sau](../work/ban-giao-nghiem-thu-2026-11-28/khoi-phuc-linux.pdf), [Excel trước–sau](../work/ban-giao-nghiem-thu-2026-11-28/khoi-phuc-linux.xlsx).
- [Ma trận nguồn 56](../work/ban-giao-nghiem-thu-2026-11-28/ma-tran-nguon-56.xlsx), [SoA dự thảo](../work/ban-giao-nghiem-thu-2026-11-28/soa-du-thao.json), [Đối chiếu người đánh giá theo từng lượt](../work/ban-giao-nghiem-thu-2026-11-28/doi-chieu-giang-vien.json).
- 38 test Python liên quan đạt, frontend lint/build đạt. Hai lần kiểm thử Edge ban đầu vấp vì phép kiểm checkbox chưa chờ API và phép đợi phản hồi bắt nhầm yêu cầu gắn nguồn. Đã chỉnh phép kiểm, chạy lại đạt. Windows chạy ca ràng buộc nguồn và công cụ trước khi bổ sung kiểm thao tác nhân viên ở bản Linux cuối.

## Bổ sung nghiệm thu ngày 28/11/2026

- Edge đã tạo phát hiện A.8.8 từ nguồn đo Linux, lập kế hoạch, duyệt và giao trên giao diện. Cùng mã `8f9cbd48-caf6-47dc-92a0-cf3cf866f57e` xuất hiện ở Doanh nghiệp, Thực nghiệm A.8, Hồ sơ ISO và Tổng quan 56 control, kể cả sau tải lại. Màn Thực nghiệm A.8 hiển thị ngữ cảnh phát hiện. Lượt đo kỹ thuật A.8 vẫn có nguồn và kết quả riêng.
- Trên Edge, chuyên viên chạy công cụ lab, lưu biên nhận, nhân viên gắn nguồn sau và gửi xác minh, chuyên viên ghi cải thiện một phần. Ứng dụng mẫu `iso-demo-inventory` chuyển từ 1.0.0 lên 1.1.0 trên Linux. Phạm vi vá hệ điều hành còn thiếu bằng chứng. Các phép thử quyền và thao tác trước duyệt trong kịch bản dùng API.
- Edge kết nối FastAPI và PostgreSQL thật trên database thử riêng. Runner kiểm tra dữ liệu sau khi khởi động lại API, dọn database thử và xác nhận số dòng các bảng được theo dõi của database chính giữ nguyên. Hồ sơ thử dùng chung với ca MFA và phần khai phạm vi mẫu đang mô tả MFA; khi demo riêng Linux, khai phạm vi ứng dụng và đích Linux ngay ở bước đầu.
- [Biên nhận lượt đạt](../work/linux-bon-man-lai-2026-11-28.json), [lượt đầu lỗi định vị ô nhập](../work/linux-bon-man-2026-11-28.json), [PDF mới](../work/ban-giao-nghiem-thu-2026-11-28/linux-bon-man.pdf), [Excel mới](../work/ban-giao-nghiem-thu-2026-11-28/linux-bon-man.xlsx). Đã đọc lại hai file và kiểm UUID trong PDF và Excel, phiên bản trước/sau và nhãn tiếng Việt trong PDF.
- Không cần migration. Luồng điều hướng dùng mã phát hiện trong URL và đọc hồ sơ qua API có phân quyền hiện hành. Mốc này bổ sung cho ca đã ghi ở trên.

Chạy lại bằng lệnh ở trên với tên tệp kết quả mới. Phần còn chờ gồm hồ sơ ngoài preset cho 37 control, thay một nguồn chưa dùng được, đối chiếu độc lập, thẩm định và duyệt SoA. Cần xác nhận tên thiết bị trong ghi âm trước khi chọn môi trường thử tương ứng.

## Đối chiếu hai yêu cầu nghiệm thu

| Hạng mục | Trạng thái | Căn cứ |
| --- | --- | --- |
| Nhận diện đúng môi trường từ nguồn đầu đến đo lại | Đạt trong lab Linux và ca Windows hồi quy | Ràng buộc đợt, môi trường, ứng dụng và mã nguồn đầu trong phát hiện; phiên bản 1.0.0 → 1.1.0 trong biên nhận. |
| Tạo phát hiện và duyệt giao qua React | Đạt | Lượt Edge trên PostgreSQL riêng chờ phản hồi tạo và duyệt ngay sau thao tác bấm; người thực hiện dùng phiên đăng nhập riêng. |
| Bốn màn hình, tải lại và mở liên kết trực tiếp | Đạt | Ca Edge dùng hai UUID cùng A.8.8, kiểm tra chỉ đúng hồ sơ xuất hiện sau tra mã và mở URL. Tra mã phát hiện MFA từ A.8.8 chuyển đồng thời về đúng A.8.5. |
| Quan hệ với lượt đo Thực nghiệm A.8 | Một phần | Đã có ngữ cảnh phát hiện và đường về hồ sơ. Probe A.8.8 của lượt kỹ thuật đọc inventory và cấu hình quét; nguồn Linux này ghi phiên bản ứng dụng mẫu. Chưa có lượt kỹ thuật thu đúng quan sát của ứng dụng để liên kết theo mã nguồn. |
| Báo cáo trước–sau | Đạt cho ca ứng dụng | PDF, Excel và JSON cùng chứa hai UUID riêng. Hồ sơ có hành động ghi biên nhận, nguồn sau và thẩm định một phần. |
| Phân vai và hành động theo phạm vi | Đạt trong ca đại diện | Tư vấn duyệt và khởi chạy công cụ lab; nhân viên đánh dấu tiến độ, gắn nguồn, gửi xác minh; tư vấn xác minh. Phép thử tự xác minh, chạy trước duyệt và gửi nguồn sai chạy qua API. |
| Hồi quy | Đạt theo phạm vi ca đã lưu | Linux/MFA và Windows chạy lại; xem biên nhận hồi quy dưới đây. |
| Bản vá hệ điều hành và thiết bị trong ghi âm | Chờ đầu vào | Cần chốt tên/model thiết bị, hệ điều hành và máy thử được chỉ định. Xem bảng bên dưới. |
| Nguồn, chấm độc lập và SoA | Một phần | Ma trận và báo cáo đã xuất; các quyết định nghiệp vụ cần nguồn và người xác nhận. |

### Báo cáo cùng lượt Edge

- Phát hiện có đầu việc: `dc8ed051-9ca9-4740-a7a2-14320ee897ad`. Nguồn đầu `WEB-397d6a4877958baf07457d1d025baeb8`, nguồn sau `WEB-ffbc71a51eeca319d68b60dec4e2046f`. Đích `linux_lab`, ứng dụng `iso-demo-inventory`.
- Phát hiện đối chứng cùng control `3980b9ea-464b-4154-83f0-477e640c49c8` được tạo qua API để thử điều hướng. Trong giao diện, vào Tổng quan 56 control → Tư vấn & khắc phục → dán mã từ PDF vào ô **Mã phát hiện từ báo cáo** → **Mở theo mã phát hiện**. Các mã trong gói này thuộc cơ sở dữ liệu kiểm thử đã dọn, nên cần tạo ca mới để thao tác với dữ liệu đang chạy.
- [PDF](../work/ban-giao-nghiem-thu-2026-11-28/linux-doi-chieu-final.pdf), [Excel](../work/ban-giao-nghiem-thu-2026-11-28/linux-doi-chieu-final.xlsx), [JSON](../work/ban-giao-nghiem-thu-2026-11-28/linux-doi-chieu-final.json), [biên nhận kiểm thử](../work/linux-doi-chieu-final-2026-11-28.json).

### Thiết bị, cách đo và ca chờ

| Đích | Loại | Đo và hành động đã kiểm | Điều kiện để mở rộng |
| --- | --- | --- | --- |
| Windows, đích local của backend | Máy chạy ca thử Windows | Đọc thông tin nền tảng và phiên bản ứng dụng mẫu, cập nhật trong thư mục thử, kiểm lại phiên bản và hash | Muốn kiểm bản vá cần máy ảo thử riêng, tài sản định danh rõ và người phê duyệt |
| Debian 12, `linux_lab` | Container cô lập | Đọc từ container, chạy lại ứng dụng mẫu sau cập nhật và kiểm hash | Bản vá hệ điều hành cần máy thử có vòng đời reboot và khả năng phục hồi phù hợp |
| Laptop bàn giao | Tài sản mô phỏng | Nhân viên và người tiếp nhận đối chiếu mã tài sản, người xác minh thẩm định biên nhận | Muốn áp dụng thật cần danh mục tài sản và biên bản có người chịu trách nhiệm xác nhận |
| Thiết bị đoạn 08:43–09:35 | Chưa xác định | Bản chép có các chuỗi nghe thành SEBA, Doutor và Sougwick, chưa đủ để định danh | Nhờ nhóm xác nhận tên/model và hệ điều hành từng thiết bị trước khi gán đích |

**Ca vá hệ điều hành chờ máy thử.** Tạo phát hiện riêng cho tiêu chí Patch OS ở A.8.8, ghi mã máy và build ban đầu vào nguồn trước. Chuyên viên duyệt đầu việc với mã bản vá, cửa sổ thực hiện và điều kiện hồi phục; người được giao thực hiện trên máy thử được cấp quyền. Đính kèm nguồn bản vá đã áp dụng và phép đo riêng sau thao tác gồm mã máy, build/gói, thời điểm và trạng thái khởi động lại nếu áp dụng. Chuyên viên đối chiếu hai lần đo trước khi ghi kết quả. Có thể dùng ngay đường nộp nguồn, giao việc và thẩm định hiện có. Trạng thái ca này vẫn chờ thực thi.

### Việc cần người phụ trách xử lý

- Đợt chính có 19/56 control có nguồn ngoài preset, 18 có nội dung dùng được ở ngưỡng kỹ thuật, 37 thiếu nguồn. A.6.2 có tệp DOCX chỉ trích xuất 1 ký tự chữ/số. Nhân sự/pháp chế cần nộp bản đọc được, trích phần điều khoản ATTT liên quan và nêu phạm vi áp dụng. Các dòng khác có yêu cầu nguồn và vai trò phụ trách trong [gói yêu cầu 56 control](../work/ban-giao-nghiem-thu-2026-11-28/nguon-56/handoff.json).
- Trong 17 lượt đã xuất, 14 dùng LLM, 3 dùng luật, 14 có đủ metadata, 8 có nguồn cho cả 18 control, 6 có nguồn cho 5 control và 3 có độ bao phủ ghi nhận bằng 0. Có 6 lỗi cuối trên 5 lượt. Cả 17 đang chờ đối chiếu độc lập, nên độ đúng độc lập chưa có mẫu số. Với lượt chấm mới, thống nhất người chấm và phạm vi, chốt report hash và rubric của cùng bộ nguồn, giao qua tài khoản chấm mù và lưu nhãn riêng của từng người. [Báo cáo đối chiếu](../work/ban-giao-nghiem-thu-2026-11-28/doi-chieu-giang-vien.json).
- SoA mốc xuất có 56 dòng, 0 quyết định áp dụng và 0 thẩm định hiện hành. Người phụ trách ghi quyết định, lý do, nguồn, rồi thẩm định trước khi trình duyệt theo [điều kiện SoA](DIEU_KIEN_DUYET_SOA_56.md).

### Kiểm thử đợt bổ sung

- 488 test Python đã theo dõi trong Git đạt. Chạy pytest không giới hạn đường dẫn còn vướng 10 tệp chưa được Git theo dõi, thuộc cây kỹ thuật riêng, thiếu dependency/import trong venv hiện tại.
- 15 test JavaScript đã theo dõi trong Git và một phép đối chiếu mới cho 56 mẫu khắc phục đạt. Phép kiểm đối chiếu mã với catalog và kiểm trường bộ phận, bước làm, nguồn, cách kiểm lại và điều kiện nghiệm thu. Lint và build frontend đạt; build cảnh báo kích thước chunk.
- Edge với FastAPI/PostgreSQL thật đạt, giữ dữ liệu sau restart API, runner dọn database thử. Không có migration mới. Chạy lại lệnh ở trên và dùng tên file JSON mới.

Hồi quy bổ sung ngày 28/11/2026 đạt cho [Windows và MFA](../work/windows-doi-chieu-2026-11-28.json) và [bàn giao laptop](../work/ban-giao-doi-chieu-final-2026-11-28.json), có kiểm giữ dữ liệu sau restart. Lượt bàn giao chạy kèm phép kiểm gián đoạn lô đánh giá trả HTTP 409 ở phần lô; trình duyệt và kiểm giữ hồ sơ bàn giao đã đạt. Lượt chuyên biệt bàn giao chạy lại đạt với lệnh:

```powershell
.venv\Scripts\python.exe run_isolated_acceptance.py --execute --remediation --governance --clients --employee-workflows --handover-only --output work/ban-giao-moi.json
```
