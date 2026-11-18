import AccountProfile from './AccountProfile';
import { useCallback, useEffect, useState } from "react";
import { Bot, KeyRound, LogIn, ShieldCheck, UserRound, LayoutDashboard, FlaskConical, Building2, FolderCheck, LogOut } from "lucide-react";
import { ApiError, apiRequest } from "./api";
import A8ComplianceStudy from "./A8ComplianceStudy";
import Scope56 from "./Scope56";
import ComplianceDossier from "./ComplianceDossier";
import CompanyInventory from "./CompanyInventory";
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
const [view, setView] = useState("scope56");
  const clearSession = useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem("iso_team_assessment");
    setToken("");
    setUser(null);
    setAssessment(null);
  }, []);

  useEffect(() => {
    if (assessment?.assessment_id) sessionStorage.setItem('iso_team_assessment', assessment.assessment_id);
  }, [assessment]);

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
      setView("scope56");
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
    <div className="flex min-h-screen items-center justify-center bg-[#080f1d] text-[#99f6e4]">
      <Bot className="mr-3 animate-pulse"/> Đang kiểm tra phiên đăng nhập...
    </div>
  );


if (user && assessment && token) {
  return (
    <>
      <header className="fixed inset-x-0 top-0 z-[100] border-b border-slate-700/70 bg-slate-950/95 text-white shadow-lg backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center gap-3 px-4 py-3"><div className="hidden shrink-0 items-center gap-3 lg:flex"><span className="rounded-xl bg-teal-400/10 p-2 text-teal-300"><ShieldCheck size={24}/></span><span className="text-sm font-bold">ISO 27001<span className="block text-[10px] font-normal tracking-wider text-slate-400">AI AGENT · ĐÁNH GIÁ TUÂN THỦ</span></span></div>
        <nav aria-label="Điều hướng chính" className="flex min-w-0 flex-1 gap-1 overflow-x-auto">{[
          ['scope56','Tổng quan 56 control',LayoutDashboard],['a8','Thực nghiệm A.8',FlaskConical],['company','Doanh nghiệp',Building2],['dossier','Hồ sơ ISO',FolderCheck]
        ].map(([id,label,Icon])=><button key={id} type="button" onClick={()=>{setView(id);window.scrollTo({top:0,behavior:'instant'});}} aria-current={view===id?'page':undefined} className={`flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl px-3 py-3 text-xs font-semibold transition ${view===id?'bg-teal-400/15 text-teal-200 ring-1 ring-teal-400/30':'text-slate-400 hover:bg-slate-800 hover:text-white'}`}><Icon size={16}/>{label}</button>)}</nav>
        <AccountProfile user={user} assessment={assessment} request={request} onSaved={setUser}/><button type="button" onClick={logout} aria-label="Đăng xuất" title="Đăng xuất" className="rounded-xl p-3 text-slate-400 hover:bg-slate-800 hover:text-white"><LogOut size={18}/></button></div>
      </header>

      {view === "scope56" ? <Scope56 assessment={assessment} request={request} onOpenA8={()=>setView("a8")} /> : view === "company" ? <CompanyInventory assessment={assessment} request={request} onOpenDossier={() => setView("dossier")} /> : view === "dossier" ? <ComplianceDossier assessment={assessment} request={request} onOpenDashboard={()=>{setView("scope56");window.scrollTo({top:0,behavior:"instant"});}} onOpenCompany={() => setView("company")} /> : (
        <A8ComplianceStudy assessment={assessment} request={request} />
      )}
    </>
  );
}


  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#080f1d] px-4 py-12 text-white">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_100%,#0f766e_0%,#152b3c_45%,#080f1d_83%)] opacity-70"/>
      <section className="relative w-full max-w-[440px] rounded-[32px] border border-white/15 bg-[#111e30]/95 p-7 shadow-2xl sm:p-9">
        <div className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-[22px] bg-[#14b8a6] text-white">
          <Bot className="h-10 w-10"/>
        </div>
        <div className="mb-7 text-center">
          <div className="text-[11px] font-bold tracking-[.18em] text-[#5eead4]">ISO/IEC 27001 · ĐÁNH GIÁ TUÂN THỦ</div>
          <h1 className="mt-2 text-2xl font-black">Đăng nhập hệ thống đánh giá</h1>
          <p className="mt-2 text-sm text-[#C2CEDA]">Theo dõi bằng chứng, kết luận của Agent và hồ sơ đánh giá trong cùng một hệ thống.</p>
        </div>
        <form onSubmit={login} className="space-y-4">
          <label className="block text-sm font-bold">Tên đăng nhập
            <div className="mt-2 flex items-center rounded-2xl border border-white/15 bg-[#142335] px-4 focus-within:border-[#14b8a6]">
              <UserRound className="h-4 w-4 text-[#5eead4]"/>
              <input required autoComplete="username" value={username} onChange={e => setUsername(e.target.value)} className="w-full bg-transparent p-3.5 outline-none" placeholder="admin"/>
            </div>
          </label>
          <label className="block text-sm font-bold">Mật khẩu
            <div className="mt-2 flex items-center rounded-2xl border border-white/15 bg-[#142335] px-4 focus-within:border-[#14b8a6]">
              <KeyRound className="h-4 w-4 text-[#5eead4]"/>
              <input required type="password" autoComplete="current-password" value={password} onChange={e => setPassword(e.target.value)} className="w-full bg-transparent p-3.5 outline-none" placeholder="Nhập mật khẩu"/>
            </div>
          </label>
          {error && <p role="alert" className="rounded-xl bg-red-500/15 p-3 text-sm text-red-200">{error}</p>}
          <button disabled={busy} type="submit" className="flex w-full items-center justify-center gap-2 rounded-full bg-[#0f766e] px-5 py-4 font-black text-white shadow-[0_4px_0_#115e59] hover:bg-[#0d9488] disabled:opacity-60">
            {busy ? "Đang đăng nhập..." : <><LogIn className="h-5 w-5"/> ĐĂNG NHẬP HỆ THỐNG</>}
          </button>
        </form>
        <p className="mt-6 flex items-center justify-center gap-2 text-xs text-[#B9C6D2]"><ShieldCheck className="h-4 w-4"/> Tài khoản riêng · Hồ sơ và tiến độ dùng chung</p>
      </section>
    </main>
  );
}
