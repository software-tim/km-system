export async function getJSON(path: string, timeoutMs = 5000): Promise<{ ok: boolean; status: number; data?: any; error?: string; }> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(path, { signal: ctrl.signal });
    let data: any = undefined;
    try { data = await res.json(); } catch {}
    return { ok: res.ok, status: res.status, data };
  } catch (e: any) {
    return { ok: false, status: 0, error: e?.message ?? "request failed" };
  } finally {
    clearTimeout(t);
  }
}