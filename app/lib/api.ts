// Typed client for the praxis-server FastAPI app.
//
// Set NEXT_PUBLIC_API_URL=http://localhost:8000 to point the UI at a live
// backend. When unset, `apiBaseUrl()` returns null and pages should fall
// back to deterministic seeded demo data — both render paths are valid;
// neither lies to the operator.

export type Metrics = {
  sharpe?: number;
  sortino?: number;
  calmar?: number;
  max_drawdown?: number;
  total_return?: number;
  hit_rate?: number;
  n_periods?: number;
  [k: string]: number | string | undefined;
};

export type RunSummary = {
  id: string;
  metrics: Metrics;
};

export type Decision = {
  ts?: string;
  regime?: string;
  signals?: Record<string, number>;
  target_weights?: Record<string, number>;
  notes?: string;
  [k: string]: unknown;
};

export type RunDetail = {
  id: string;
  metrics?: Metrics;
  config_yaml?: string;
  decisions?: Decision[];
};

export type EquityPoint = {
  ts: string;
  equity: number;
};

export function apiBaseUrl(): string | null {
  const url = process.env.NEXT_PUBLIC_API_URL;
  if (!url) return null;
  return url.replace(/\/$/, "");
}

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const base = apiBaseUrl();
  if (!base) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set; pages should call this only after isApiConfigured() === true",
    );
  }
  const response = await fetch(`${base}${path}`, {
    ...init,
    cache: "no-store",
    headers: { Accept: "application/json", ...(init?.headers ?? {}) },
  });
  if (!response.ok) {
    throw new Error(`praxis-server ${path} → ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}

export const api = {
  isConfigured(): boolean {
    return apiBaseUrl() !== null;
  },
  health: () => getJson<{ status: string }>("/health"),
  version: () => getJson<{ version: string }>("/version"),
  strategies: () => getJson<string[]>("/strategies"),
  runs: () => getJson<RunSummary[]>("/runs"),
  run: (id: string) => getJson<RunDetail>(`/runs/${encodeURIComponent(id)}`),
  equity: (id: string) => getJson<EquityPoint[]>(`/runs/${encodeURIComponent(id)}/equity`),
};
