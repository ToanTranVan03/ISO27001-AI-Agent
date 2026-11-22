import AccountProfile from './AccountProfile';
import { useCallback, useEffect, useState, useRef, useLayoutEffect } from "react";
import {readNavigation,navigationHash,mergeNavigation} from './navigation';
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
  const [campaigns,setCampaigns]=useState([]);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [navigation,setNavigation]=useState(()=>readNavigation(window.location.hash));
  const [focusDetails,setFocusDetails]=useState(false);
  useLayoutEffect(()=>{const previous=window.history.scrollRestoration;window.history.scrollRestoration='manual';window.scrollTo({top:0,behavior:'instant'});return()=>{window.history.scrollRestoration=previous;};},[]);
  const navigationRef=useRef(navigation);
  const view=navigation.view;
  const navigate=useCallback((patch,replace=false)=>{
    const next=mergeNavigation(navigationRef.current,patch);
    const hash=navigationHash(next);
    const changedView=next.view!==navigationRef.current.view;
    if(hash===navigationHash(navigationRef.current))return;
    if(!replace)setFocusDetails(!!(patch?.controlId||patch?.employeeId));
    navigationRef.current=next;setNavigation(next);
    window.history[replace?'replaceState':'pushState'](null,'',window.location.pathname+window.location.search+hash);
    if(changedView)window.scrollTo({top:0,behavior:'instant'});
  },[]);
  const updateContext=useCallback(patch=>navigate({assessmentId:assessment?.assessment_id,...patch},true),[navigate,assessment?.assessment_id]);
  useEffect(()=>{
    const update=()=>{setFocusDetails(false);const next=readNavigation(window.location.hash);navigationRef.current=next;setNavigation(next);};
    window.addEventListener('popstate',update);window.addEventListener('hashchange',update);
    return()=>{window.removeEventListener('popstate',update);window.removeEventListener('hashchange',update);};
  },[]);
  useEffect(()=>{
    if(!assessment||!navigation.assessmentId||navigation.assessmentId===assessment.assessment_id)return;
    const previousCampaign=campaigns.find(c=>c.assessment_id===navigation.assessmentId);
    const frame=requestAnimationFrame(()=>{if(previousCampaign)setAssessment(previousCampaign);else navigate({...readNavigation(''),assessmentId:assessment.assessment_id},true);});
    return()=>cancelAnimationFrame(frame);
  },[assessment,navigation.assessmentId,navigate,campaigns]);
  const clearSession = useCallback(() => {
    sessionStorage.removeItem(SESSION_KEY);
    sessionStorage.removeItem("iso_team_assessment");
    setToken("");
    setUser(null);
    setAssessment(null);
    const empty=readNavigation('');navigationRef.current=empty;setNavigation(empty);
    window.history.replaceState(null,'',window.location.pathname+window.location.search);
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
        setUser(profile);setCampaigns(campaigns);
        const target=campaigns.find(c=>c.assessment_id===navigationRef.current.assessmentId)||campaigns[0];
        setAssessment(target);
        if(navigationRef.current.assessmentId&&navigationRef.current.assessmentId!==target.assessment_id){
          navigationRef.current=readNavigation('');setNavigation(navigationRef.current);
          window.history.replaceState(null,'',window.location.pathname+window.location.search);
        }else navigate({assessmentId:target.assessment_id},true);
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
  }, [token, clearSession,navigate]);

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
      setUser(session.user);setCampaigns(campaigns);
      const target=campaigns.find(c=>c.assessment_id===navigationRef.current.assessmentId)||campaigns[0];
      setAssessment(target);
      if(navigationRef.current.assessmentId&&navigationRef.current.assessmentId!==target.assessment_id)navigate({...readNavigation(''),assessmentId:target.assessment_id},true);
      else navigate({assessmentId:target.assessment_id},true);
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
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-2 px-4 py-3 lg:flex-nowrap lg:gap-3"><div className="mr-auto flex shrink-0 items-center gap-2 lg:mr-0 lg:gap-3"><span className="rounded-xl bg-teal-400/10 p-2 text-teal-300"><ShieldCheck size={24}/></span><span className="text-sm font-bold">ISO 27001<span className="block text-[8px] font-normal tracking-wider text-slate-400 sm:text-[10px]">AI AGENT · ĐÁNH GIÁ TUÂN THỦ</span></span></div>
        <nav aria-label="Điều hướng chính" className="order-last flex w-full min-w-0 gap-1 overflow-x-auto lg:order-none lg:w-auto lg:flex-1">{[
          ['scope56','Tổng quan 56 control',LayoutDashboard],['a8','Thực nghiệm A.8',FlaskConical],['company','Doanh nghiệp',Building2],['dossier','Hồ sơ ISO',FolderCheck]
        ].map(([id,label,Icon])=><button key={id} type="button" onClick={()=>navigate({view:id,assessmentId:assessment.assessment_id})} aria-current={view===id?'page':undefined} className={`flex shrink-0 items-center gap-2 whitespace-nowrap rounded-xl px-3 py-3 text-xs font-semibold transition ${view===id?'bg-teal-400/15 text-teal-200 ring-1 ring-teal-400/30':'text-slate-400 hover:bg-slate-800 hover:text-white'}`}><Icon size={16}/>{label}</button>)}</nav>
        {campaigns.length>1&&<label className="text-[10px] text-slate-400">Đợt đang làm<select aria-label="Chọn đợt đánh giá" className="ml-1 max-w-40 rounded bg-slate-900 p-2 text-xs" value={assessment.assessment_id} onChange={e=>{const next=campaigns.find(c=>c.assessment_id===e.target.value);setAssessment(next);navigate({...readNavigation(''),assessmentId:next.assessment_id});}}>{campaigns.map(c=><option key={c.assessment_id} value={c.assessment_id}>{c.name}</option>)}</select></label>}
        <AccountProfile user={user} assessment={assessment} request={request} onSaved={setUser}/><button type="button" onClick={logout} aria-label="Đăng xuất" title="Đăng xuất" className="rounded-xl p-3 text-slate-400 hover:bg-slate-800 hover:text-white"><LogOut size={18}/></button></div>
      </header>

      <div key={assessment.assessment_id}>{view === "scope56" ? <Scope56 focusDetails={focusDetails} canManage={user.role==='admin'} assessment={assessment} request={request} controlId={navigation.controlId} employeeId={navigation.employeeId} runId={navigation.runId} onContext={updateContext} onOpenA8={context=>navigate({view:'a8',...context})} onOpenDossier={context=>navigate({view:'dossier',...context})} onOpenCompany={context=>navigate({view:'company',...context})}/> : view === "company" ? <CompanyInventory onCampaignsChanged={async()=>setCampaigns(await request("/api/assessments"))} focusDetails={focusDetails} assessment={assessment} request={request} employeeId={navigation.employeeId} onContext={updateContext} onOpenDossier={context=>navigate({view:'dossier',...context})}/> : view === "dossier" ? <ComplianceDossier focusDetails={focusDetails} user={user} assessment={assessment} request={request} controlId={navigation.controlId} employeeId={navigation.employeeId} onContext={updateContext} onOpenDashboard={context=>navigate({view:'scope56',...context})} onOpenCompany={context=>navigate({view:'company',...context})} onOpenA8={context=>navigate({view:'a8',...context})}/> : (
        <A8ComplianceStudy assessment={assessment} request={request} controlId={navigation.controlId} runId={navigation.runId} onContext={updateContext} onOpenDashboard={context=>navigate({view:'scope56',...context})}/>
      )}</div>
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
