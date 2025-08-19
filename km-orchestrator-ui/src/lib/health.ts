export type Status = "healthy" | "degraded" | "down" | "unknown";

export type Probe = {
  key: "orch" | "docs" | "search" | "llm" | "graphrag";
  name: string;
  path: string;        // proxied path to /health
};

export type ProbeResult = {
  key: Probe["key"];
  name: string;
  status: Status;
  latency_ms: number | null;
  uptime?: number | null;
  raw?: any;
  error?: string | null;
};

const PROBES: Probe[] = [
  { key: "orch",     name: "Orchestrator",     path: "/health" },
  { key: "docs",     name: "SQL Docs Service", path: "/docs/health" },
  { key: "search",   name: "Search Service",    path: "/search/health" },
  { key: "llm",      name: "LLM Service",       path: "/llm/health" },
  { key: "graphrag", name: "GraphRAG Service",  path: "/graphrag/health" },
];

async function withTimeout<T>(p: Promise<T>, ms = 5000): Promise<T> {
  return await Promise.race([
    p,
    new Promise<T>((_, rej) => setTimeout(() => rej(new Error("timeout")), ms))
  ]);
}

export async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { ...init, headers: { "Accept": "application/json", ...(init?.headers||{}) }});
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  // endpoints that return text/plain should still parse if JSON-like
  const text = await res.text();
  try { return JSON.parse(text) as T; } catch { return (text as any as T); }
}

export async function probeOne(p: Probe): Promise<ProbeResult> {
  const t0 = performance.now();
  try {
    const data = await withTimeout(fetchJSON<any>(p.path), 7000);
    const t1 = performance.now();
    // Guess fields if the service doesn't use a common schema
    const status: Status =
      (data?.status?.toLowerCase?.() ?? data?.health?.toLowerCase?.() ?? "") === "healthy" ? "healthy" :
      (data?.ok === true || data?.alive === true) ? "healthy" :
      (data?.status?.toLowerCase?.() === "degraded") ? "degraded" :
      (data?.status?.toLowerCase?.() === "down") ? "down" :
      "healthy"; // be optimistic if it replied OK

    const uptime = typeof data?.uptime === "number" ? data.uptime
                 : typeof data?.uptime_percent === "number" ? data.uptime_percent
                 : null;

    return {
      key: p.key,
      name: p.name,
      status,
      latency_ms: Math.round(t1 - t0),
      uptime,
      raw: data,
      error: null,
    };
  } catch (e:any) {
    const t1 = performance.now();
    return {
      key: p.key,
      name: p.name,
      status: "down",
      latency_ms: Math.round(t1 - t0),
      uptime: null,
      raw: null,
      error: e?.message ?? String(e),
    };
  }
}

export async function probeAll(): Promise<ProbeResult[]> {
  return await Promise.all(PROBES.map(probeOne));
}

export type OrchestratorSummary = {
  overall_health?: number;       // 0..100
  services_online?: number;
  total_services?: number;
  updated_at?: string;
};

export async function getOrchestratorSummary(): Promise<OrchestratorSummary | null> {
  try {
    const data = await withTimeout(fetchJSON<any>("/health"), 7000);
    return {
      overall_health: typeof data?.overall_health === "number" ? Math.round(data.overall_health) : undefined,
      services_online: data?.services_online,
      total_services: data?.total_services,
      updated_at: data?.updated_at,
    };
  } catch {
    return null;
  }
}