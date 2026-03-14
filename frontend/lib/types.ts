export interface User {
  id: string;
  email: string;
  company_id: string;
  role: string;
}

export interface Company {
  id: string;
  name: string;
  created_at: string;
}

export interface Integration {
  id: string;
  integration_type: string;
  status: string;
  last_collected_at: string | null;
  last_error: string | null;
  created_at: string;
}

export interface Evidence {
  id: string;
  integration: string;
  control: string;
  evidence_type: string;
  source_id: string;
  timestamp: string;
  data: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Report {
  id: string;
  framework: string;
  report_type: string;
  fmt: string;
  status: string;
  file_url: string | null;
  file_name: string | null;
  mime_type: string | null;
  file_size: number | null;
  generated_at: string | null;
  created_at: string;
}

export interface DownloadResponse {
  url: string;
  expires_in: number;
  file_name: string | null;
  mime_type: string | null;
  file_size: number | null;
}

export interface Member {
  id: string;
  email: string;
  role: string;
}

export interface Invitation {
  id: string;
  email: string;
  role: string;
  invite_url: string;
  accepted_at: string | null;
  created_at: string;
}

export interface ControlScore {
  category: string;
  name: string;
  score: number;
  status: "passing" | "warning" | "failing" | "no_evidence";
  evidence_count: number;
  covered_types: string[];
  missing_types: string[];
  last_collected: string | null;
}

export interface ComplianceScore {
  framework: string;
  overall_score: number;
  evaluated_at: string;
  controls: ControlScore[];
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
