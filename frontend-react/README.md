# Frontend doanh nghiệp AI Agent

Giao diện React/Vite của đồ án đánh giá tuân thủ ISO/IEC 27001: văn phòng 3D, giao nhiệm vụ Agent, danh mục doanh nghiệp và Hồ sơ ISO.

## Chạy local

Làm theo [CHAY_LOCAL.md](../CHAY_LOCAL.md) để chuẩn bị PostgreSQL, backend và Ollama. Từ thư mục `frontend-react`:

```powershell
npm install
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Truy cập http://127.0.0.1:5173. Cấu hình API xem [vite.config.js](vite.config.js) và [src/api.js](src/api.js).

## Kiểm tra và build

```powershell
npm run lint
npm run build
```

Bản build nằm trong `dist/`. Không đưa `node_modules/`, `dist/` hoặc thông tin đăng nhập vào Git.

## Thành phần chính

- `src/App.jsx`: đăng nhập và điều hướng.
- `src/EnterpriseIncident3D.jsx`: tích hợp văn phòng và nhiệm vụ.
- `src/OfficeInteractive3D.jsx`, `src/office3dEngine.js`: giao diện và cảnh Three.js.
- `src/AgentOfficeConsole.jsx`, `src/EnterpriseMissionControl.jsx`: giao việc và theo dõi thực thi.
- `src/CompanyInventory.jsx`, `src/ComplianceDossier.jsx`: dữ liệu doanh nghiệp và hồ sơ đánh giá.

Phạm vi và giới hạn: [README đồ án](../README.md), [văn phòng Agent 3D](../docs/VAN_PHONG_AGENT_3D.md).
