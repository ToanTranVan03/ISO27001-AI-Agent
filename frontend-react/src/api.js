/** Centralized request helper; backend requires Bearer tokens on private APIs. */
export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

export async function apiRequest(path, token = "", options = {}) {
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  let response;
  try {
    response = await fetch(path, { ...options, headers });
  } catch {
    throw new ApiError("Không kết nối được FastAPI. Hãy khởi động server cổng 8000.", 0);
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(typeof data.detail === "string" ? data.detail : `Lỗi HTTP ${response.status}`, response.status);
  }
  return data;
}
