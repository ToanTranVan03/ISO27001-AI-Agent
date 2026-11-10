> **Phạm vi đồ án là 56 control.** Tài liệu này chỉ mô tả nhóm 18 A.8 ưu tiên thực nghiệm, không thay thế phần con người/phần cứng/phần mềm còn lại. SoA 18 A.8 là báo cáo con; màn hình Phạm vi 56 xuất SoA tổng thể. Xem [ma trận 56 control](MA_TRAN_56_CONTROL.md).

> **Cập nhật raw v2:** luồng hiện tại đọc cấu hình/log gốc và hỗ trợ Docker cô lập, 108 ca, đánh giá mù và phê duyệt SoA có kiểm tra điều kiện. Xem [quy trình nghiệm thu v2](QUY_TRINH_NGHIEM_THU_A8.md). Nội dung v1 và số liệu 97,22% bên dưới được giữ làm lịch sử, không mô tả đầy đủ bản hiện tại.

# Trọng tâm đề tài từ 10/11/2026: đánh giá tuân thủ kỹ thuật A.8

## Yêu cầu và phạm vi

Dừng phát triển văn phòng 3D và điều khiển nhân viên bằng bình luận. Màn hình mặc định và điều hướng hiện tại tập trung vào đánh giá bằng chứng A.8. Mã mô phỏng cũ được giữ làm lịch sử, không xem là đầu ra nghiên cứu chính.

Mục tiêu: Agent kết luận từ bằng chứng thu tự động trong doanh nghiệp giả lập; so sánh với đáp án thiết kế và kết luận người đánh giá; sinh dự thảo Statement of Applicability (SoA).

**18 control:** A.8.1, A.8.2, A.8.3, A.8.5, A.8.7, A.8.8, A.8.9, A.8.10, A.8.12, A.8.13, A.8.15, A.8.16, A.8.17, A.8.19, A.8.20, A.8.22, A.8.24, A.8.32. Tiêu chí cụ thể và đơn vị phụ trách ở `lab_a8/catalog.json`; xem [ma trận A.8](MA_TRAN_A8.md).

Tên tham chiếu theo cấu trúc nhóm công nghệ; ISO/IEC 27001 quy định yêu cầu ISMS và ISO/IEC 27002 cung cấp hướng dẫn kiểm soát: [ISO/IEC 27002:2022](https://www.iso.org/standard/75652.html). Hai thuộc tính mỗi control là rubric thử nghiệm do nhóm lựa chọn, không phải toàn bộ yêu cầu hoặc nguyên văn tiêu chuẩn. Cần giảng viên/người đánh giá duyệt rubric trước khi kết luận nghiên cứu.

## Thu bằng chứng: đã có và chưa có

Collector đọc tự động các file JSON export trong `lab_a8/sources`, kiểm tra định danh, kiểu dữ liệu, chỉ lấy các trường trong allowlist, lưu SHA-256 của nguồn và thời điểm thu thập. Các nguồn giả lập đại diện endpoint, IAM, vulnerability, configuration, DLP, backup, logging, monitoring, time, software, network, crypto và change.

**Đây là thu tự động từ file export lab, không phải collector truy vấn trực tiếp Docker/Linux/EDR/IAM thật.** Các thuộc tính đầu vào hiện đã được chuẩn hóa dạng true/false/null. Chưa chứng minh khả năng suy luận từ cấu hình thô hoặc log mâu thuẫn; cần phát triển bộ chuyển đổi từ cấu hình/log thực tế và thêm ca khó để đánh giá có ý nghĩa hơn.

Mỗi control có bốn hồ sơ: conforming, mixed, nonconforming, incomplete. Tổng **72 ca**; nhãn thiết kế nằm riêng ở `lab_a8/reference/designer_labels.json`. Tên profile, đường dẫn chứa profile và đáp án không được gửi cho LLM. Model chỉ nhận rubric chung, định danh control và evidence được cho phép.

## Engine và đối chiếu

- `rules`: baseline xác định, không gọi LLM.
- `llm`: gọi Ollama theo từng control; schema Pydantic, viện dẫn đúng ID; lỗi API/timeout/JSON/viện dẫn ghi lỗi, không fallback sang luật.
- Rubric v1: thiếu thuộc tính => Insufficient Evidence; tất cả true => Compliant; tất cả false => Non-Compliant; hỗn hợp => Partially Compliant. Kết luận chỉ có giá trị trong phạm vi rubric lab.
- Chạy kiểm tra không đồng nghĩa đã đáp ứng ISO. 72 ca đơn giản và cùng mẫu rubric chỉ là kiểm chứng ban đầu, không phải benchmark độc lập có độ khó cao.

Bảng theo từng control ghi số mẫu, số đúng, lỗi, accuracy và confusion matrix. Lỗi engine tính là không khớp trên mẫu có nhãn. Bảng đối chiếu đáp án nhóm tách hoàn toàn khỏi bảng người đánh giá. Chưa có người nhập nhãn thì cột người đánh giá là **Chưa đo**, không mặc định bằng đáp án nhóm.

Có [mẫu phiếu gán nhãn trống](../lab_a8/reference/human_review_template.tsv) để chuẩn bị đánh giá ngoài hệ thống; mẫu này chưa được tự nhập vào API hoặc tính điểm. Người đánh giá phải dùng tài khoản khác người khởi chạy. Nhãn lưu người nhập, thời điểm, lý do, hash bằng chứng/hash báo cáo. Bản chỉnh sửa giữ trong lịch sử, kết quả tổng hợp dùng nhãn mới nhất mỗi ca. Giao diện hiện cho xem kết quả Agent: đây là đối chiếu **không mù**, có nguy cơ thiên lệch. Chưa có chuyên gia thực sự tham gia hoặc xác nhận nhãn; kiểm thử nhập nhãn chỉ là test phần mềm.

## SoA tự sinh

Sinh từ catalog về tính áp dụng và kết quả đánh giá; không suy không áp dụng từ thất bại kiểm tra. SoA chứa control, lý do đưa vào, tính áp dụng đề xuất, trạng thái triển khai trong lab, người phụ trách, lý do kết luận, ID/hash nguồn bằng chứng và hash báo cáo. Xuất JSON hoặc Markdown.

Luôn là **DRAFT_NOT_APPROVED**, chỉ 18 control thuộc phạm vi. Các control ngoài phạm vi chưa được đánh giá tính áp dụng, không tự loại bỏ. Muốn có SoA đầy đủ cần bối cảnh ISMS, đánh giá rủi ro, quyết định áp dụng/loại trừ và phê duyệt người có thẩm quyền.

## Chạy và kiểm chứng

Khởi động theo `CHAY_LOCAL.md`; đăng nhập, mở **Đánh giá A.8**. Chọn hồ sơ, engine, bấm thu bằng chứng/đánh giá. Mỗi lượt thu 18 control, lưu trên server theo assessment_id trong `data/a8-study`. UI tự theo dõi đến khi hoàn tất. Đổi người đăng nhập để nhập kết luận đối chiếu; xuất CSV và báo cáo SoA.

```powershell
.venv\Scripts\python.exe -m agent_core.a8_benchmark --mode rules --output docs/a8-results/baseline-rules.json
.venv\Scripts\python.exe -m agent_core.a8_benchmark --mode llm --output docs/a8-results/ollama-judgments.json
.venv\Scripts\python.exe -m pytest tests -q
```

CLI chạy cả 4 hồ sơ và ghi bảng accuracy theo control thành CSV bên cạnh JSON. Kết quả người đánh giá trong CLI mặc định chưa có nhãn; dùng giao diện để thu đối chiếu có danh tính, không sửa nhãn nhóm thành nhãn chuyên gia.

Giới hạn triển khai: worker và khóa API nội tiến trình, chỉ hỗ trợ một tiến trình Uvicorn; API restart đánh dấu lượt đang chạy bị gián đoạn. Hồ sơ và review lưu file local theo đợt, chưa chuyển vào PostgreSQL/migration/queue phân tán. Không chạy nhiều worker Uvicorn cho module này.

## Việc còn cần để nghiệm thu nghiên cứu

1. Giảng viên/người đánh giá rà soát phạm vi và rubric 18 control.
2. Bổ sung collector đọc cấu hình/log gốc và ca thiếu/mâu thuẫn/hết hạn bằng chứng; không chỉ các cờ Boolean đã chuẩn hóa.
3. Người đánh giá thực sự gán nhãn độc lập; bổ sung chế độ đánh giá mù nếu dùng cho nghiên cứu.
4. Đo lặp nhiều lần, báo cáo lỗi, accuracy/precision/recall theo control và thời gian, giữ riêng baseline/LLM.
5. Xác nhận bối cảnh, rủi ro và tính áp dụng để phê duyệt SoA.

## Kết quả đo ban đầu

Ngày 10/11/2026: [bảng kết quả A.8](a8-results/KET_QUA_A8.md) ghi 70/72 ca LLM khớp đáp án nhóm, baseline 72/72, chưa có nhãn người đánh giá. Hai ca sai được giữ nguyên; 227 test Python và build đạt. Không ghi nội dung này vào nhật ký tuần theo yêu cầu.
