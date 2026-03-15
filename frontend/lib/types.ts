export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  company_id: string;
  role: string;
  email_verified: boolean;
}

export interface Company {
  id: string;
  name: string;
  plan: string;
  created_at: string;
}

export interface BillingInfo {
  plan: string;
  subscription_status: string | null;
  ls_subscription_id: string | null;
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

export interface ScoreHistoryPoint {
  score: number;
  ts: string;
}

export interface EvidenceActivityPoint {
  day: string;
  count: number;
}

export interface AuditLog {
  id: string;
  company_id: string;
  user_id: string | null;
  user_email: string | null;
  action: string;
  action_label: string;
  resource_type: string | null;
  resource_id: string | null;
  metadata_: Record<string, unknown> | null;
  ip_address: string | null;
  created_at: string;
}

export interface ManualControl {
  control_id: string;
  name: string;
  description: string;
  status: "pending" | "compliant" | "not_applicable";
  notes: string | null;
  updated_at: string | null;
  owner_user_id: string | null;
  owner_name: string | null;
}

export interface AuditSession {
  id: string;
  token: string;
  label: string | null;
  expires_at: string | null;
  created_at: string;
}

export interface PublicControlScore {
  name: string;
  score: number;
  status: string;
}

export interface PublicFrameworkView {
  framework: string;
  label: string;
  overall_score: number;
  controls: PublicControlScore[];
}

export interface PublicAuditView {
  company_name: string;
  session_label: string | null;
  generated_at: string;
  frameworks: PublicFrameworkView[];
}

export interface Risk {
  id: string;
  company_id: string;
  title: string;
  description: string | null;
  category: string;
  likelihood: number;
  impact: number;
  status: "open" | "mitigated" | "accepted";
  owner_user_id: string | null;
  owner_name: string | null;
  notes: string | null;
  risk_level: "critical" | "high" | "medium" | "low";
  created_at: string;
  updated_at: string;
}

export interface Policy {
  slug: string;
  title: string;
  category: string;
  content: string;
  updated_at: string | null;
}

export interface QuestionnaireType {
  id: string;
  name: string;
}

export interface QuestionnaireAnswer {
  id: string;
  question: string;
  answer: string;
}

export interface QuestionnaireResult {
  questionnaire_type: string;
  name: string;
  company_name: string;
  generated_at: string;
  answers: QuestionnaireAnswer[];
}
