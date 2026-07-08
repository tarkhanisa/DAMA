export type DamaError = {
  error: {
    type: "http_error" | "validation_error";
    status_code: number;
    message: string;
    path: string;
    details?: unknown[];
  };
};

export type DashboardSummary = {
  system: Record<string, unknown>;
  projects: {
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    recent: unknown[];
  };
  content_assets: {
    total: number;
    by_status: Record<string, number>;
    by_content_type: Record<string, number>;
    by_source: Record<string, number>;
    recent: unknown[];
  };
  exports: {
    total_markdown_files: number;
    export_root: string;
    recent: unknown[];
  };
  readiness: {
    has_projects: boolean;
    has_content_assets: boolean;
    has_exports: boolean;
    dashboard_ready: boolean;
    workflow_ready: boolean;
    export_ready: boolean;
  };
};

export type FrontendContract = {
  name: string;
  version: string;
  backend_base_url: string;
  interactive_docs: string;
  openapi_json: string;
  recommended_frontend_sections: Array<{
    key: string;
    title: string;
    primary_endpoints: string[];
  }>;
  endpoint_count: number;
};
