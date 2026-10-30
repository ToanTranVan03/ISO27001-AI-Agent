import { useCallback, useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Building2, CheckCircle2, Cpu, HardDrive, Loader2, RotateCw, Shield, Users } from "lucide-react";

const DOMAIN_INFO = {
  people: { label: "Con người", icon: Users, color: "#f6bd75" },
  hardware: { label: "Phần cứng", icon: HardDrive, color: "#7dd3fc" },
  software: { label: "Phần mềm", icon: Cpu, color: "#c4b5fd" },
};

const severityLabel = { HIGH: "Cao", MEDIUM: "Trung bình", LOW: "Thấp", CRITICAL: "Nghiêm trọng" };

export default function EnterpriseIncidentLab({ assessment, request, user }) {
  const [scenarios, setScenarios] = useState([]);
  const [incidents, setIncidents] = useState([]);
  const [domain, setDomain] = useState("people");
  const [selected, setSelected] = useState(null);
  const [latest, setLatest] = useState(null);
  const [busy, setBusy] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const base = `/api/assessments/${encodeURIComponent(assessment.assessment_id)}/enterprise`;

  const refresh = useCallback(async () => {
    setError("");
    try {
      const [catalog, history] = await Promise.all([
        request(`${base}/scenarios`),
        request(`${base}/incidents?limit=50`),
      ]);
      setScenarios(catalog.scenarios || []);
      setIncidents(history || []);
      setLatest((previous) => previous || history?.[0] || null);
      setSelected((previous) => catalog.scenarios?.find((item) => item.control_id === previous?.control_id) || catalog.scenarios?.[0] || null);
    } catch (e) {
      setError(e.message || "Không tải được dữ liệu mô phỏng.");
    } finally {
      setLoading(false);
    }
  }, [base, request]);

  useEffect(() => { refresh(); }, [refresh]);

  const filtered = useMemo(() => scenarios.filter((item) => item.domain === domain), [scenarios, domain]);
  const counts = useMemo(() => Object.fromEntries(Object.keys(DOMAIN_INFO).map((key) => [key, scenarios.filter((s) => s.domain === key).length])), [scenarios]);

  async function simulate(item) {
    if (!item) return;
    setBusy(item.control_id);
    setError("");
    try {
      const result = await request(`${base}/controls/${encodeURIComponent(item.control_id)}/simulate`, { method: "POST" });
      setLatest(result);
      await refresh();
    } catch (e) {
      setError(e.message || "Agent chưa xử lý được tình huống.");
    } finally {
      setBusy("");
    }
  }

  function showIncident(incident) {
    setLatest(incident);
    const scenario = scenarios.find((item) => item.control_id === incident.control_id);
    if (scenario) { setDomain(scenario.domain); setSelected(scenario); }
  }

  if (loading) return <div className="flex min-h-screen items-center justify-center bg-[#101827] text-slate-200"><Loader2 className="mr-3 animate-spin"/>Đang tải doanh nghiệp giả lập…</div>;

  return (
    <main className="min-h-screen bg-[#101827] px-4 pb-10 pt-20 text-slate-100 sm:px-7">
      <div className="mx-auto max-w-[1500px]">
        <section className="mb-6 rounded-3xl border border-white/10 bg-gradient-to-br from-[#20334a] to-[#172337] p-6 shadow-xl sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-5">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs font-bold text-emerald-200"><Building2 size={14}/> DOANH NGHIỆP GIẢ LẬP · LAB AN TOÀN</div>
              <h1 className="text-2xl font-black sm:text-3xl">Việt Tín Logistics</h1>
              <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-300">Chạy tình huống sự cố, để AI Agent chọn công cụ được phép, cập nhật tài sản mô phỏng và tạo biên nhận xử lý có mã kiểm tra.</p>
            </div>
            <button onClick={refresh} className="inline-flex items-center gap-2 rounded-xl border border-white/15 px-4 py-2 text-sm font-bold hover:bg-white/10"><RotateCw size={15}/> Làm mới</button>
          </div>
          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            {Object.entries(DOMAIN_INFO).map(([key, info]) => {
              const Icon = info.icon;
              return <button key={key} onClick={() => setDomain(key)} className={`rounded-2xl border p-4 text-left transition ${domain === key ? "border-white/30 bg-white/10" : "border-white/10 bg-black/10 hover:bg-white/5"}`}>
                <span className="flex items-center justify-between"><span className="flex items-center gap-2 font-bold" style={{ color: info.color }}><Icon size={18}/>{info.label}</span><span className="text-xl font-black">{counts[key] || 0}</span></span>
                <span className="mt-1 block text-xs text-slate-400">tình huống trong phạm vi đồ án</span>
              </button>;
            })}
          </div>
        </section>

        {error && <div role="alert" className="mb-5 flex items-start gap-3 rounded-2xl border border-red-300/20 bg-red-400/10 p-4 text-sm text-red-100"><AlertTriangle className="mt-0.5 shrink-0" size={18}/>{error}</div>}

        <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,.85fr)]">
          <section className="rounded-3xl border border-white/10 bg-[#172337] p-4 sm:p-5">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div><h2 className="text-lg font-extrabold">Danh mục tình huống</h2><p className="mt-1 text-xs text-slate-400">{filtered.length} kiểm soát thuộc nhóm {DOMAIN_INFO[domain].label.toLowerCase()}</p></div>
              <span className="rounded-full bg-white/5 px-3 py-1 text-xs text-slate-300">{scenarios.length}/56</span>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {filtered.map((item) => {
                const active = selected?.control_id === item.control_id;
                return <button key={item.control_id} onClick={() => setSelected(item)} className={`rounded-2xl border p-4 text-left transition ${active ? "border-sky-300/60 bg-sky-300/10" : "border-white/10 bg-[#101827] hover:border-white/25"}`}>
                  <div className="flex items-start justify-between gap-3"><span className="rounded-lg bg-white/10 px-2 py-1 font-mono text-xs font-bold text-sky-200">{item.control_id}</span><span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase ${item.severity === "high" ? "bg-red-400/15 text-red-200" : "bg-amber-300/10 text-amber-100"}`}>Rủi ro {item.severity === "high" ? "cao" : "trung bình"}</span></div>
                  <h3 className="mt-3 font-bold leading-5">{item.title}</h3>
                  <p className="mt-2 line-clamp-3 text-xs leading-5 text-slate-400">{item.event}</p>
                  <div className="mt-3 flex items-center justify-between gap-2 text-[11px] text-slate-500"><span className="truncate">{item.target.name}</span><span>{item.department}</span></div>
                </button>;
              })}
            </div>
          </section>

          <div className="space-y-5">
            <section className="rounded-3xl border border-white/10 bg-[#172337] p-5">
              <div className="flex items-start justify-between gap-4"><div><p className="font-mono text-xs font-bold text-sky-200">{selected?.control_id || "Chọn tình huống"}</p><h2 className="mt-2 text-xl font-black">{selected?.title || "Chưa có tình huống"}</h2></div><Activity className="shrink-0 text-emerald-300" size={22}/></div>
              {selected && <>
                <p className="mt-4 text-sm leading-6 text-slate-300">{selected.event}</p>
                <div className="mt-4 rounded-2xl bg-black/20 p-4 text-sm"><div className="text-xs uppercase tracking-wide text-slate-500">Tài sản bị ảnh hưởng</div><div className="mt-1 font-bold">{selected.target.name}</div><div className="mt-1 font-mono text-xs text-slate-400">{selected.target.asset_id} · {selected.target.type}</div><div className="mt-3 text-xs text-slate-400">Trạng thái mô phỏng: <span className="font-mono text-slate-200">{JSON.stringify(selected.current_state || {})}</span></div></div>
                <div className="mt-4"><div className="mb-2 text-xs font-bold uppercase tracking-wide text-slate-500">Công cụ Agent được phép</div><div className="flex flex-wrap gap-2">{selected.available_actions.map((action) => <span key={action.id} className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-300">{action.label}</span>)}</div></div>
                <button disabled={Boolean(busy)} onClick={() => simulate(selected)} className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-4 py-3 font-extrabold text-[#102116] transition hover:bg-emerald-300 disabled:cursor-wait disabled:opacity-60">{busy === selected.control_id ? <><Loader2 className="animate-spin" size={17}/> Agent đang xử lý…</> : <><Shield size={17}/> Chạy sự cố với AI Agent</>}</button>
                <p className="mt-3 text-center text-[11px] leading-5 text-slate-500">Chỉ thay đổi database lab; không khóa thiết bị hoặc tài khoản thật.</p>
              </>}
            </section>

            {latest && <section className="rounded-3xl border border-emerald-300/20 bg-[#14261f] p-5">
              <div className="flex items-center justify-between gap-3"><h2 className="flex items-center gap-2 font-extrabold"><CheckCircle2 className="text-emerald-300" size={19}/>Kết quả xử lý</h2><span className="rounded-full bg-emerald-300/10 px-3 py-1 text-xs font-bold text-emerald-200">{latest.status || "RESOLVED"}</span></div>
              <p className="mt-3 text-sm font-bold">{latest.title}</p>
              <p className="mt-2 text-sm leading-6 text-slate-300">{latest.agent_rationale}</p>
              <div className="mt-4 space-y-2">{(latest.actions || []).map((action, index) => <div key={`${action.action_id || action.tool_id}-${index}`} className="rounded-xl border border-white/5 bg-black/20 p-3"><div className="flex items-center justify-between gap-2"><span className="text-sm font-bold">{action.label}</span><span className="text-[10px] font-bold text-emerald-300">{action.status}</span></div><p className="mt-1 text-xs text-slate-400">{action.result}</p><p className="mt-2 font-mono text-[10px] text-slate-500">{JSON.stringify(action.before_state)} → {JSON.stringify(action.after_state)}</p></div>)}</div>
              <div className="mt-4 break-all rounded-xl bg-black/20 p-3 text-[11px] text-slate-400">AI: {latest.model || "—"}<br/>Evidence: {latest.evidence_id || "—"}<br/>SHA-256: {latest.sha256_hash || "—"}</div>
            </section>}

            <section className="rounded-3xl border border-white/10 bg-[#172337] p-5">
              <h2 className="mb-3 font-extrabold">Nhật ký sự cố gần đây</h2>
              {incidents.length === 0 ? <p className="text-sm text-slate-500">Chưa có sự cố nào được chạy.</p> : <div className="max-h-[360px] space-y-2 overflow-auto">{incidents.map((incident) => <button onClick={() => showIncident(incident)} key={incident.incident_id} className="w-full rounded-xl border border-white/5 bg-black/15 p-3 text-left hover:bg-white/5"><div className="flex items-center justify-between gap-2"><span className="font-mono text-xs text-sky-200">{incident.control_id}</span><span className="text-[10px] text-slate-500">{new Date(incident.created_at).toLocaleString()}</span></div><div className="mt-1 text-sm font-bold">{incident.title}</div><div className="mt-1 text-xs text-slate-400">{incident.actions?.length || 0} hành động · {severityLabel[incident.severity] || incident.severity}</div></button>)}</div>}
            </section>
          </div>
        </div>
      </div>
    </main>
  );
}
