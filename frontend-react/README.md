# Frontend đánh giá tuân thủ — phạm vi 56 control

React/Vite cho phạm vi 56 control con người/phần cứng/phần mềm, quản lý bằng chứng, tiến độ và SoA tổng thể. Nhóm 18 A.8 là luồng raw/thực nghiệm/chấm mù ưu tiên riêng. Mã văn phòng/bình luận/mission cũ đã được gỡ; thư mục src chỉ giữ các màn hình đánh giá hiện hành.

## Chạy

Chuẩn bị PostgreSQL, Ollama và container `iso-a8-lab` theo [CHAY_LOCAL.md](../CHAY_LOCAL.md), rồi từ thư mục này:

```powershell
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Giao diện: http://127.0.0.1:5173. Proxy API đến cổng 8000 trong `vite.config.js`.

## Module chính

- `src/App.jsx`: xác thực, điều hướng mặc định Phạm vi 56 control.
- `src/Scope56.jsx`: bảng đủ 56 control, nộp tài liệu, đánh giá và SoA toàn phạm vi.
- `src/A8ComplianceStudy.jsx`: chọn nguồn/hồ sơ/engine, theo dõi job, chấm mù, đối chiếu và phê duyệt SoA.
- `src/api.js`: request và Bearer token.
- `src/ComplianceDossier.jsx`, `src/CompanyInventory.jsx`: hồ sơ và dữ liệu doanh nghiệp hiện hữu.

```powershell
npm run lint
npm run build
```

Xem [quy trình nghiệm thu raw v2](../docs/QUY_TRINH_NGHIEM_THU_A8.md). Chưa có người thật đánh giá thì không hiển thị độ đúng human; không tự tạo phê duyệt. Thư mục `dist/`, `node_modules/` và thông tin đăng nhập không đưa vào Git.
