import * as React from "react";
import { getJSON } from "../../lib/api";

type Svc = "orchestrator" | "docs" | "search" | "llm" | "graphrag";
type Entry = { name: string; path: string; key: Svc };

const SERVICES: Entry[] = [
  { key: "orchestrator", name: "Orchestrator", path: "/orch/health" },
  { key: "docs",         name: "SQL Docs Service", path: "/docs/health" },
  { key: "search",       name: "Search Service",   path: "/search/health" },
  { key: "llm",          name: "LLM Service",      path: "/llm/health" },
  { key: "graphrag",     name: "GraphRAG Service", path: "/graphrag/health" },
];

export default function ServiceHealth() {
  const [rows, setRows] = React.useState<{[k in Svc]: {status: "ok"|"down"|"error"; code: number; info?: string; latency?: number; }}>({
    orchestrator:{status:"error",code:0}, docs:{status:"error",code:0},
    search:{status:"error",code:0}, llm:{status:"error",code:0}, graphrag:{status:"error",code:0}
  });
  const [updated, setUpdated] = React.useState<Date | null>(null);

  async function refresh() {
    const results = await Promise.all(SERVICES.map(async s => {
      const t0 = performance.now();
      const r = await getJSON(s.path, 7000);
      const t1 = performance.now();
      const latency = Math.max(1, Math.round(t1 - t0));
      const status: "ok"|"down"|"error" =
        r.ok ? "ok" : (r.status === 404 || r.status === 0 ? "error" : "down");
      const info = r.data?.status || r.data?.message || r.error;
      return [s.key, { status, code: r.status, latency, info }] as const;
    }));
    setRows(prev => ({...prev, ...Object.fromEntries(results)} as any));
    setUpdated(new Date());
  }

  React.useEffect(() => { refresh(); }, []);

  const online = Object.values(rows).filter(x => x.status === "ok").length;
  const pct = Math.round((online / SERVICES.length) * 100);

  return (
    <div style={{border:"1px solid #dcdcdc", borderRadius:12, padding:12}}>
      <div style={{display:"flex", alignItems:"center", justifyContent:"space-between"}}>
        <h2 style={{margin:0}}>System Health</h2>
        <button onClick={refresh} style={{padding:"6px 10px", borderRadius:8, border:"1px solid #ccc", cursor:"pointer"}}>Refresh</button>
      </div>

      <div style={{marginTop:10, height:8, background:"#eee", borderRadius:6}}>
        <div style={{width:`${pct}%`, height:"100%", background: pct===100 ? "#16a34a" : "#f59e0b", borderRadius:6}} />
      </div>
      <div style={{fontSize:12, color:"#555", marginTop:6}}>
        {online}/{SERVICES.length} Services Online · {updated ? updated.toLocaleTimeString() : "—"}
      </div>

      <div style={{display:"grid", gridTemplateColumns:"repeat(2, minmax(0,1fr))", gap:10, marginTop:12}}>
        {SERVICES.map(s => {
          const r = rows[s.key];
          const color = r.status === "ok" ? "#dcfce7" : "#fee2e2";
          const pill  = r.status === "ok" ? "🟢 Healthy" : "🔴 Down";
          return (
            <div key={s.key} style={{background:color, border:"1px solid #e5e7eb", borderRadius:10, padding:12}}>
              <div style={{display:"flex", justifyContent:"space-between", alignItems:"center"}}>
                <strong>{s.name}</strong>
                <span style={{fontSize:12}}>{pill}</span>
              </div>
              <div style={{fontSize:12, color:"#444", marginTop:6}}>
                Latency: {r.latency ?? "—"} ms · HTTP {r.code || "—"} {r.info ? "· " + String(r.info) : ""}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}