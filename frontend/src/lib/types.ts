export type DamaError = {
  error: {
    type: "http_error" | "validation_error";
    status_code: number;
    message: string;
    path: string;
    details?: unknown[];
  };
};

export type Project = {
  id: string;
  name: string;
  slug?: string;
  project_type: string;
  language?: string;
  description?: string;
  status: string;
  content_types?: string[];
  created_at?: string;
  updated_at?: string;
};

export type ContentAsset = {
  id: string;
  project_id: string;
  content_type: string;
  title: string;
  body?: string;
  status: string;
  source: string;
  metadata?: Record<string, unknown>;
  created_at?: string;
  updated_at?: string;
};

export type ProjectSummary = {
  project: Project;
  total_assets: number;
  assets_by_status: Record<string, number>;
  assets_by_content_type: Record<string, number>;
  recent_assets: ContentAsset[];
};

export type ProjectContentAssetsResponse = {
  project_id: string;
  content_assets: ContentAsset[];
};

export type PlannedOutput = {
  order: number;
  project_id: string;
  content_type: string;
  title: string;
  workflow_stage: string;
  recommended_status: string;
  generation_topic: string;
};

export type OutputPlanResponse = {
  project_id: string;
  planned_outputs: PlannedOutput[];
};

export type MaintenanceStatus = {
  database: {
    path: string;
    exists: boolean;
    size_bytes: number;
    tables: Record<string, number>;
  };
  exports: {
    path: string;
    exists: boolean;
    file_count: number;
    total_size_bytes: number;
    recent: Array<{
      file_name: string;
      file_path: string;
      size_bytes: number;
    }>;
  };
  backups: {
    path: string;
    exists: boolean;
    file_count: number;
    total_size_bytes: number;
    recent: Array<{
      file_name: string;
      file_path: string;
      size_bytes: number;
    }>;
  };
  maintenance_ready: boolean;
  generated_at: string;
};

export type DashboardSummary = {
  system: Record<string, unknown>;
  projects: {
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    recent: Project[];
  };
  content_assets: {
    total: number;
    by_status: Record<string, number>;
    by_content_type: Record<string, number>;
    by_source: Record<string, number>;
    recent: ContentAsset[];
  };
  exports: {
    total_markdown_files: number;
    export_root: string;
    recent: Array<{
      file_name?: string;
      file_path?: string;
      size_bytes?: number;
    }>;
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
