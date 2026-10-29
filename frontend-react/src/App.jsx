import { useCallback, useEffect, useState } from "react";
import { Bot, KeyRound, LogIn, ShieldCheck, UserRound } from "lucide-react";
import SpaceBaseDashboard from "./SpaceBaseDashboard";
import ISOAgentCity from "./ISOAgentCity";
import { ApiError, apiRequest } from "./api";
import AutonomousAuditDemo from "./AutonomousAuditDemo";
const SESSION_KEY = "iso_team_token"; // Compatible with existing /workspace session.

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(SESSION_KEY) || "");
  const [user, setUser] = useState(null);
  const [assessment, setAssessment] = useState(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
const [demoMode, setDemoMode] = useState(true);
  const clearSession = useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY);
    setToken("");
    setUser(null);
    setAssessment(null);
  }, []);

  // Restore existing session and verify against the database.
  useEffect(() => {
    let cancelled = false;
    async function restore() {
      if (!token) { setLoading(false); return; }
      try {
        const [profile, campaigns] = await Promise.all([
          apiRequest("/api/auth/me", token),
          apiRequest("/api/assessments", token),
        ]);
        if (cancelled) return;
        if (!campaigns.length) throw new ApiError("Tài khoản chưa thuộc đợt đánh giá nào.", 403);
        setUser(profile);
        setAssessment(campaigns[0]);
      } catch (err) {
        if (!cancelled) {
          if (err.status === 401) clearSession();
          else setError(err.message);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    restore();
    return () => { cancelled = true; };
  }, [token, clearSession]);

  const request = useCallback(async (path, options = {}) => {
    try {
      return await apiRequest(path, token, options);
    } catch (err) {
      if (err.status === 401) clearSession();
      throw err;
    }
  }, [token, clearSession]);

  async function login(event) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const session = await apiRequest("/api/auth/login", "", {
        method: "POST", body: JSON.stringify({ username: username.trim(), password }),
      });
      if (!session.access_token) throw new Error("API không trả access_token.");
      // Verify membership before making the authenticated dashboard visible.
      const campaigns = await apiRequest("/api/assessments", session.access_token);
      if (!campaigns.length) throw new Error("Tài khoản chưa được thêm vào đợt đánh giá.");
      setPassword("");
      sessionStorage.setItem(SESSION_KEY, session.access_token);
      setToken(session.access_token);
      setUser(session.user);
      setAssessment(campaigns[0]);
    } catch (err) {
      setError(err.message || "Không thể đăng nhập.");
    } finally {
      setBusy(false);
      setLoading(false);
    }
  }

  async function logout() {
    try { await request("/api/auth/logout", { method: "POST" }); }
    catch { /* Always clear local session, even if the network is unavailable. */ }
    clearSession();
  }

  if (loading) return (
    <div className="flex min-h-screen items-center justify-center bg-[#172337] text-[#FFE4C7]">
      <Bot className="mr-3 animate-pulse"/> Đang kiểm tra phiên đăng nhập...
    </div>
  );


if (user && assessment && token) {
  return (
    <>
      {/* Thanh chuyển chế độ để kiểm thử */}
      <div className="fixed right-4 top-3 z-[100] flex gap-2">
        <button
          type="button"
          onClick={() => setDemoMode(value => !value)}
          className="rounded-full bg-[#FF914D] px-4 py-2 text-xs font-bold text-white shadow-lg"
        >
          {demoMode
          ? "Xem Dashboard 3D cũ"
          : "Xem ISO Agent City"}
        </button>

        <button
          type="button"
          onClick={logout}
          className="rounded-full bg-[#34465B] px-4 py-2 text-xs font-bold text-white shadow-lg"
        >
          Đăng xuất
        </button>
      </div>

      
      {demoMode ? (
        <ISOAgentCity
          user={user}
          assessment={assessment}
          request={request}
          onLogout={logout}
        />
      ) : (
        <SpaceBaseDashboard
          key={assessment.assessment_id}
          user={user}
          assessment={assessment}
          request={request}
          onLogout={logout}
        />
      )}
    </>
  );
}


  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#172337] px-4 py-12 text-white">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_100%,#c17c53_0%,#35465a_45%,#172337_83%)] opacity-70"/>
      <section className="relative w-full max-w-[440px] rounded-[32px] border border-white/15 bg-[#223449]/95 p-7 shadow-2xl sm:p-9">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-[22px] bg-[#FF914D] text-white">
          <Bot className="h-10 w-10"/>
        </div>
        <div className="mb-7 text-center">
          <div className="text-[11px] font-bold tracking-[.18em] text-[#FFBD88]">ISO ENTERPRISE LAB · MARS TYCOON</div>
          <h1 className="mt-2 text-2xl font-black">Đăng nhập căn cứ 3D</h1>
          <p className="mt-2 text-sm text-[#C2CEDA]">Dùng tài khoản Admin hoặc thành viên đã tạo trong hệ thống PostgreSQL.</p>
        </div>
        <form onSubmit={login} className="space-y-4">
          <label className="block text-sm font-bold">Tên đăng nhập
            <div className="mt-2 flex items-center rounded-2xl border border-white/15 bg-[#142335] px-4 focus-within:border-[#FF914D]">
              <UserRound className="h-4 w-4 text-[#FFBC91]"/>
              <input required autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} className="w-full bg-transparent p-3.5 outline-none" placeholder="admin"/>
            </div>
          </label>
          <label className="block text-sm font-bold">Mật khẩu
            <div className="mt-2 flex items-center rounded-2xl border border-white/15 bg-[#142335] px-4 focus-within:border-[#FF914D]">
              <KeyRound className="h-4 w-4 text-[#FFBC91]"/>
              <input required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-transparent p-3.5 outline-none" placeholder="Nhập mật khẩu"/>
            </div>
          </label>
          {error && <p role="alert" className="rounded-xl bg-red-500/15 p-3 text-sm text-red-200">{error}</p>}
          <button disabled={busy} type="submit" className="flex w-full items-center justify-center gap-2 rounded-full bg-[#FF842F] px-5 py-4 font-black text-white shadow-[0_4px_0_#D66222] hover:bg-[#FA913E] disabled:opacity-60">
            {busy ? "Đang đăng nhập..." : <><LogIn className="h-5 w-5"/> ĐĂNG NHẬP VÀO CĂN CỨ</>}
          </button>
        </form>
        <p className="mt-6 flex items-center justify-center gap-2 text-xs text-[#B9C6D2]"><ShieldCheck className="h-4 w-4"/> Xác thực qua FastAPI · Tiến độ chia sẻ qua PostgreSQL</p>
      </section>
    </main>
  );
}
