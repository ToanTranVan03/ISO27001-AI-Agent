# Rà rubric và chuẩn bị xác nhận phạm vi — 22/11/2026

Trạng thái: **RÀ KỸ THUẬT, CHƯA PHÊ DUYỆT CHUYÊN MÔN**. Báo cáo do trợ lý AI tạo từ mã, catalog và minh chứng đã lưu. Không thay chữ ký/xác nhận của giảng viên hay người phụ trách.

## Phiên bản và tính nhất quán

- Phạm vi: 56 control = 8 A.6 + 14 A.7 + 34 A.8; 113 tiêu chí hồ sơ. Đủ 56 mục rubric JSON; không thiếu ID thuộc phạm vi.
- Hash rubric toàn phạm vi (đúng thuật toán `backend/scope56.py`): `dbf106d4cc9cf939e8bd3aba2cc7bf61c605b4c0e0068d6f113a14c942087c9c`.
- Catalog raw A.8: `b7b102b86e746543451b11f87ac52890f678c84b121f899c733cd4dc1657d3a4`; phiên bản báo cáo `a8-raw-v2`.
- Catalog runtime live: `135424a5cad9a5a55ac88337b7b2efe375c1edd731b5b3f47708098bf062f09f`; phiên bản `a8-live-v2-active`.
- Nhóm sâu 18 A.8 có 36 phép kiểm tra đại diện. Hai rubric raw/live có ý nghĩa nguồn khác nhau; không gộp kết quả khi hash/phiên bản/transport khác nhau.
- `agent_core/graph_builder.py` lấy rubric qua `backend/database.py:get_rubric`; hàm này đọc chính JSON được scope56 băm, tránh rubric PostgreSQL seed cũ. `docs/ISO_27001_Rubric.xlsx` không phải đầu vào runtime hoặc căn cứ tự phê duyệt.
- Chấm thiếu nguồn: Graph có nhãn `Insufficient Evidence`; nhánh A.8 có điều kiện missing/unknown theo từng phép kiểm tra. Không suy đạt từ loại tài liệu hay số ký tự.

## A.6.2: một ký tự là lỗi chất lượng, không phải ngưỡng chấp nhận

- Audit nguồn ngày 21/11 ghi `bc.docx`, evidence ID `c6e06211-2486-492e-82a4-8673bbe80d45`, 1 ký tự chữ/số, `too_little_extracted_text`, toàn vẹn `not_verifiable`.
- `text-usability-v1` yêu cầu tối thiểu 20 ký tự chữ/số và loại nội dung lặp. Đây là ngưỡng kỹ thuật của đồ án, không phải yêu cầu ISO. Không hạ ngưỡng xuống một ký tự/từ để cho nguồn qua.
- `document_parser.py` đọc đoạn văn/bảng DOCX, trích text PDF; không có OCR tự động cho ảnh scan. Cần bản gốc có điều khoản/trách nhiệm, chữ ký và phạm vi liên quan; nếu ảnh scan thì nhóm cần cung cấp bản trích có kiểm tra với bản gốc.
- Chưa xác định nguyên nhân một ký tự là tệp thật quá ít nội dung hay nội dung nằm trong ảnh vì chưa đối chiếu được bản gốc cũ. Không tái tạo hoặc sửa tài liệu thay nhóm.

## Ma trận bàn giao cho người xác nhận

Mốc nguồn bên dưới lấy từ [audit 21/11](a8-results/source-integrity-audit-2026-11-21.json), không phải phép đọc database mới ngày 22/11. Có nguồn chỉ cho biết có bản lưu; bao phủ chuyên môn vẫn chờ xác nhận. Có 19 control có nguồn (18 A.8 + A.6.2), 37 control thiếu nguồn; A.6.2 cần thay. Bộ 38 hồ sơ trợ lý tạo là dữ liệu phát triển, không lấp các chỗ thiếu chính thức.

| Control | Sâu A.8 | Tiêu chí hồ sơ | Loại nguồn đề nghị | Mốc nguồn 21/11 |
|---|---|---|---|---|
| A.6.1 | Không | 2 | EVID_PPL_HR_RECORD | Thiếu nguồn ngoài preset |
| A.6.2 | Không | 2 | EVID_PPL_CONTRACT_NDA | Cần thay nguồn một ký tự |
| A.6.3 | Không | 2 | EVID_PPL_TRAINING, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.6.4 | Không | 2 | EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.6.5 | Không | 2 | EVID_PPL_HR_RECORD | Thiếu nguồn ngoài preset |
| A.6.6 | Không | 2 | EVID_PPL_CONTRACT_NDA | Thiếu nguồn ngoài preset |
| A.6.7 | Không | 2 | EVID_DOC_POLICY, EVID_TECH_ENDPOINT_AV | Thiếu nguồn ngoài preset |
| A.6.8 | Không | 2 | EVID_PPL_HR_RECORD, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.7.1 | Không | 2 | EVID_PHY_CHECKLIST | Thiếu nguồn ngoài preset |
| A.7.2 | Không | 2 | EVID_PHY_ACCESS_LOG | Thiếu nguồn ngoài preset |
| A.7.3 | Không | 2 | EVID_PHY_CHECKLIST, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.7.4 | Không | 2 | EVID_PHY_ASSET_INV | Thiếu nguồn ngoài preset |
| A.7.5 | Không | 2 | EVID_PHY_CHECKLIST | Thiếu nguồn ngoài preset |
| A.7.6 | Không | 2 | EVID_PHY_ACCESS_LOG, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.7.7 | Không | 2 | EVID_PHY_CHECKLIST, EVID_TECH_ENDPOINT_AV | Thiếu nguồn ngoài preset |
| A.7.8 | Không | 2 | EVID_PHY_ASSET_INV | Thiếu nguồn ngoài preset |
| A.7.9 | Không | 2 | EVID_PHY_ASSET_INV, EVID_TECH_ENDPOINT_AV | Thiếu nguồn ngoài preset |
| A.7.10 | Không | 2 | EVID_PHY_ASSET_INV, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.7.11 | Không | 2 | EVID_PHY_CHECKLIST | Thiếu nguồn ngoài preset |
| A.7.12 | Không | 2 | EVID_PHY_CHECKLIST | Thiếu nguồn ngoài preset |
| A.7.13 | Không | 2 | EVID_PHY_MAINT_DISP | Thiếu nguồn ngoài preset |
| A.7.14 | Không | 2 | EVID_PHY_MAINT_DISP | Thiếu nguồn ngoài preset |
| A.8.1 | Có | 3 | EVID_TECH_ENDPOINT_AV | Có bản thu lab; chờ rà bao phủ |
| A.8.2 | Có | 2 | EVID_TECH_IAM_AUTH | Có bản thu lab; chờ rà bao phủ |
| A.8.3 | Có | 2 | EVID_TECH_IAM_AUTH, EVID_DOC_POLICY | Có bản thu lab; chờ rà bao phủ |
| A.8.4 | Không | 2 | EVID_TECH_SDLC_REPORT | Thiếu nguồn ngoài preset |
| A.8.5 | Có | 3 | EVID_TECH_IAM_AUTH | Có bản thu lab; chờ rà bao phủ |
| A.8.6 | Không | 2 | EVID_TECH_NET_FIREWALL | Thiếu nguồn ngoài preset |
| A.8.7 | Có | 2 | EVID_TECH_ENDPOINT_AV | Có bản thu lab; chờ rà bao phủ |
| A.8.8 | Có | 2 | EVID_TECH_VULN_CONFIG | Có bản thu lab; chờ rà bao phủ |
| A.8.9 | Có | 2 | EVID_TECH_VULN_CONFIG | Có bản thu lab; chờ rà bao phủ |
| A.8.10 | Có | 2 | EVID_TECH_VULN_CONFIG, EVID_DOC_POLICY | Có bản thu lab; chờ rà bao phủ |
| A.8.11 | Không | 2 | EVID_TECH_VULN_CONFIG, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.8.12 | Có | 2 | EVID_TECH_ENDPOINT_AV, EVID_DOC_POLICY | Có bản thu lab; chờ rà bao phủ |
| A.8.13 | Có | 2 | EVID_TECH_BACKUP_LOG | Có bản thu lab; chờ rà bao phủ |
| A.8.14 | Không | 2 | EVID_TECH_NET_FIREWALL, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.8.15 | Có | 2 | EVID_TECH_BACKUP_LOG | Có bản thu lab; chờ rà bao phủ |
| A.8.16 | Có | 2 | EVID_TECH_BACKUP_LOG, EVID_DOC_POLICY | Có bản thu lab; chờ rà bao phủ |
| A.8.17 | Có | 2 | EVID_TECH_BACKUP_LOG | Có bản thu lab; chờ rà bao phủ |
| A.8.18 | Không | 2 | EVID_TECH_IAM_AUTH | Thiếu nguồn ngoài preset |
| A.8.19 | Có | 2 | EVID_TECH_ENDPOINT_AV, EVID_DOC_POLICY | Có bản thu lab; chờ rà bao phủ |
| A.8.20 | Có | 2 | EVID_TECH_NET_FIREWALL | Có bản thu lab; chờ rà bao phủ |
| A.8.21 | Không | 2 | EVID_TECH_NET_FIREWALL, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.8.22 | Có | 2 | EVID_TECH_NET_FIREWALL | Có bản thu lab; chờ rà bao phủ |
| A.8.23 | Không | 2 | EVID_TECH_NET_FIREWALL | Thiếu nguồn ngoài preset |
| A.8.24 | Có | 2 | EVID_TECH_VULN_CONFIG, EVID_DOC_POLICY | Có bản thu lab; chờ rà bao phủ |
| A.8.25 | Không | 2 | EVID_TECH_SDLC_REPORT, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.8.26 | Không | 1 | EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.8.27 | Không | 2 | EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.8.28 | Không | 2 | EVID_TECH_SDLC_REPORT, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.8.29 | Không | 2 | EVID_TECH_SDLC_REPORT | Thiếu nguồn ngoài preset |
| A.8.30 | Không | 2 | EVID_DOC_POLICY, EVID_TECH_SDLC_REPORT | Thiếu nguồn ngoài preset |
| A.8.31 | Không | 2 | EVID_TECH_NET_FIREWALL, EVID_TECH_IAM_AUTH | Thiếu nguồn ngoài preset |
| A.8.32 | Có | 2 | EVID_TECH_SDLC_REPORT, EVID_DOC_POLICY | Có bản thu lab; chờ rà bao phủ |
| A.8.33 | Không | 2 | EVID_TECH_VULN_CONFIG, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |
| A.8.34 | Không | 2 | EVID_TECH_IAM_AUTH, EVID_DOC_POLICY | Thiếu nguồn ngoài preset |

## Phiếu xác nhận — để người có trách nhiệm thực hiện

- [ ] Người phụ trách rà từng `pass_criteria`, nguồn cần chấp nhận và mức đại diện trong [catalog 56](56_controls_scope.json), [rubric kết luận](compliance_rubrics.json) và [giới hạn live A.8](LIVE_A8_V2.md).
- [ ] Ghi người xác nhận, vai trò, ngày, hash rubric, kỳ kiểm tra, phần không bao phủ và căn cứ xác nhận thực tế.
- [ ] Thống nhất người chấm và phương pháp với giảng viên; ghi tự đọc/AI hỗ trợ/trao đổi và mức tiếp xúc đáp án đúng thực tế.
- [ ] Admin chỉ ghi xác nhận trên giao diện sau khi đã có rà thực tế. API `POST /api/assessments/{assessment_id}/enterprise/scope56/rubric/approval` yêu cầu `rubric_sha256` và `note`; hash cũ bị trả 409, tài khoản không admin bị 403. Không gọi API này để hoàn thành checklist thay người phụ trách.
- [ ] Với bộ kiểm định mới: chốt snapshot/hash trước chạy/chấm, ghi lịch sử tiếp xúc; giữ tập mô phỏng/fixture đã biết ở nhóm riêng.
- [ ] Với hồ sơ SoA: ghi 56 quyết định áp dụng và kế hoạch; thẩm định tiêu chí trên nguồn hiện hành rồi mới trình duyệt.

## Phần chưa có cơ sở xác nhận

Chưa có nguồn mới cho 37 control, bản thay A.6.2, tập kiểm định độc lập, nhãn đủ điều kiện hoặc quyết định chuyên môn mới trong báo cáo này. Không đánh dấu xong các mục tương ứng. Tham chiếu [điều kiện duyệt SoA](DIEU_KIEN_DUYET_SOA_56.md) và [kế hoạch xử lý](KE_HOACH_XU_LY_VA_KIEM_TRA_LAI.md).
