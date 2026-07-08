import type {
  BatchGenerateDryRunInput,
  BatchGenerateResponse,
  ContentAsset,
  CreateContentAssetInput,
  CreateProjectInput,
  DashboardSummary,
  FrontendContract,
  MaintenanceStatus,
  OutputPlanResponse,
  Project,
  ProjectContentAssetsResponse,
  ProjectSummary
} from "./types";

export const DAMA_API_BASE_URL =
  process.env.NEXT_PUBLIC_DAMA_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
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

function normalizeListResponse<T>(data: unknown, possibleKeys: string[]): T[] {
  if (Array.isArray(data)) {
    return data as T[];
  }

  if (data && typeof data === "object") {
    const record = data as Record<string, unknown>;

    for (const key of possibleKeys) {
      const value = record[key];

      if (Array.isArray(value)) {
        return value as T[];
      }
    }
  }

  return [];
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
  },

  maintenanceStatus(): Promise<MaintenanceStatus> {
    return requestJson<MaintenanceStatus>("/maintenance/status");
  },

  async projects(): Promise<Project[]> {
    const data = await requestJson<unknown>("/projects");
    return normalizeListResponse<Project>(data, ["projects", "items", "results"]);
  },

  createProject(input: CreateProjectInput): Promise<Project> {
    return requestJson<Project>("/projects", {
      method: "POST",
      body: JSON.stringify(input)
    });
  },

  project(projectId: string): Promise<Project> {
    return requestJson<Project>(`/projects/${projectId}`);
  },

  projectSummary(projectId: string): Promise<ProjectSummary> {
    return requestJson<ProjectSummary>(`/projects/${projectId}/summary`);
  },

  projectContentAssets(projectId: string): Promise<ProjectContentAssetsResponse> {
    return requestJson<ProjectContentAssetsResponse>(
      `/projects/${projectId}/content-assets`
    );
  },

  projectOutputPlan(projectId: string): Promise<OutputPlanResponse> {
    return requestJson<OutputPlanResponse>(
      `/workflows/projects/${projectId}/output-plan`
    );
  },

  batchGenerateDryRun(
    projectId: string,
    input: BatchGenerateDryRunInput
  ): Promise<BatchGenerateResponse> {
    return requestJson<BatchGenerateResponse>(
      `/workflows/projects/${projectId}/batch-generate`,
      {
        method: "POST",
        body: JSON.stringify(input)
      }
    );
  },

  async contentAssets(): Promise<ContentAsset[]> {
    const data = await requestJson<unknown>("/content-assets");
    return normalizeListResponse<ContentAsset>(data, [
      "content_assets",
      "assets",
      "items",
      "results"
    ]);
  },

  createContentAsset(input: CreateContentAssetInput): Promise<ContentAsset> {
    return requestJson<ContentAsset>("/content-assets", {
      method: "POST",
      body: JSON.stringify(input)
    });
  }
};
