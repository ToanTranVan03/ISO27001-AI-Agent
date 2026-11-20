/** Centralized request helper; backend requires Bearer tokens on private APIs. */
export class ApiError extends Error {
  constructor(message, status, detail = null) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

function errorMessage(detail, status) {
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(item => {
    const field = Array.isArray(item?.loc) ? item.loc.filter(x => x !== 'body').join('.') : '';
    return typeof item?.msg === 'string' ? `${field ? field + ': ' : ''}${item.msg}` : '';
  }).filter(Boolean).join('; ') || `Lỗi HTTP ${status}`;
  if (detail && typeof detail.message === 'string') {
    const pending = Array.isArray(detail.pending_controls) ? detail.pending_controls.filter(x => typeof x === 'string') : [];
    return detail.message + (pending.length ? ` Control cần bổ sung: ${pending.join(', ')}.` : '');
  }
  return `Lỗi HTTP ${status}`;
}

export async function apiRequest(path, token = "", options = {}) {
  const {responseType,...fetchOptions}=options;
  const headers = new Headers(options.headers || {});
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  let response;
  try {
    response = await fetch(path, { ...fetchOptions, headers });
  } catch {
    throw new ApiError("Không kết nối được FastAPI. Hãy khởi động server cổng 8000.", 0);
  }
  if (response.ok && responseType === 'blob') return response.blob();
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(errorMessage(data.detail, response.status), response.status, data.detail);
  }
  return data;
}
