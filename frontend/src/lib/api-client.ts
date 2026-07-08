import type { DashboardSummary, FrontendContract } from "./types";

export const DAMA_API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${DAMA_API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    },
    cache: "no-store"
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(JSON.stringify(data));
  }

  return data as T;
}

export const damaApi = {
  dashboardSummary(): Promise<DashboardSummary> {
    return requestJson<DashboardSummary>("/dashboard/summary");
  },

  frontendContract(): Promise<FrontendContract> {
    return requestJson<FrontendContract>("/developer/frontend-contract");
  },

  endpointMap(): Promise<unknown> {
    return requestJson<unknown>("/developer/endpoint-map");
  },

  runbook(): Promise<unknown> {
    return requestJson<unknown>("/developer/runbook");
  }
};
