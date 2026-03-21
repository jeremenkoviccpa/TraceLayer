export interface User {
  id: string;
  email: string;
  full_name?: string | null;
  company_id: string;
  role: string;
  email_verified: boolean;
  totp_enabled?: boolean;
}

export interface Company {
  id: string;
  name: string;
  plan: string;
  created_at: string;
  onboarding_completed: boolean;
  is_partner_account: boolean;
}

export interface PartnerClient {
  id: string;
  name: string;
  plan: string;
  created_at: string;
  trust_page_slug: string | null;
  trust_page_enabled: boolean | null;
}

export interface PartnerSwitchResponse {
  access_token: string;
  client_company_id: string;
  client_name: string;
}

export interface PartnerTrustCenterInfo {
  slug: string;
  public_url: string;
  is_enabled: boolean;
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
  auto_detected: boolean;
  detection_key: string | null;
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

export interface AutofillAnswerItem {
  question: string;
  answer: string;
}

export interface AutofillContextSummary {
  integrations_count: number;
  policies_count: number;
  vendors_count: number;
  assets_count: number;
  incidents_count: number;
  vulnerabilities_count: number;
  pen_test: boolean;
  training_count: number;
  risks_count: number;
  soa_count: number;
  ropa_count: number;
  breaches_count: number;
  subject_requests_count: number;
  bcp_count: number;
  management_review: boolean;
  detected_type: string;
}

export interface AutofillResult {
  company_name: string;
  generated_at: string;
  detected_type: string;
  context: AutofillContextSummary;
  answers: AutofillAnswerItem[];
}

export interface TrainingRecord {
  id: string;
  company_id: string;
  assignee_email: string;
  assignee_name: string | null;
  title: string;
  description: string | null;
  due_date: string | null;
  completed_at: string | null;
  status: "pending" | "completed" | "overdue";
  annual: boolean;
  notes: string | null;
  auto_detected: boolean;
  detection_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface PenTest {
  id: string;
  company_id: string;
  vendor_name: string;
  status: "scheduled" | "in_progress" | "completed" | "remediated";
  scope: string | null;
  conducted_at: string | null;
  next_scheduled_at: string | null;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  summary: string | null;
  file_url: string | null;
  remediation_notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface Vendor {
  id: string;
  company_id: string;
  name: string;
  category: string;
  risk_level: "low" | "medium" | "high" | "critical";
  website: string | null;
  contact_email: string | null;
  soc2_certified: boolean;
  iso27001_certified: boolean;
  hipaa_certified: boolean;
  review_date: string | null;
  notes: string | null;
  report_file_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface AccessReview {
  id: string;
  company_id: string;
  title: string;
  period: string;
  reviewer_user_id: string | null;
  reviewer_name: string | null;
  status: "open" | "in_progress" | "completed";
  due_date: string | null;
  completed_at: string | null;
  users_reviewed: number;
  access_changes: number;
  scope: string | null;
  findings: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReadinessData {
  framework: string;
  readiness_score: number;
  automated_score: number;
  manual_score: number;
  weeks_estimate: number;
  stage: string;
  manual_total: number;
  manual_compliant: number;
  controls_passing: number;
  controls_failing: number;
  controls_no_evidence: number;
  controls_total: number;
}

export interface TrustPageSettings {
  is_enabled: boolean;
  slug: string;
  show_score: boolean;
  show_policies: boolean;
  show_integrations: boolean;
  custom_headline: string | null;
  custom_message: string | null;
  frameworks: string[];
}

export interface PublicTrustControlScore {
  name: string;
  score: number;
  status: string;
}

export interface PublicTrustFramework {
  framework: string;
  label: string;
  overall_score: number;
  controls: PublicTrustControlScore[];
}

export interface PublicTrustPolicy {
  slug: string;
}

export interface Document {
  id: string;
  resource_type: string;
  resource_id: string | null;
  filename: string;
  file_size: number;
  mime_type: string;
  uploader_email: string | null;
  created_at: string;
}

export interface Incident {
  id: string;
  company_id: string;
  title: string;
  description: string | null;
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'investigating' | 'resolved' | 'closed';
  detected_at: string | null;
  resolved_at: string | null;
  affected_systems: string | null;
  root_cause: string | null;
  lessons_learned: string | null;
  reporter_user_id: string | null;
  reporter_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface Asset {
  id: string;
  company_id: string;
  name: string;
  asset_type: 'hardware' | 'software' | 'cloud' | 'data' | 'other';
  owner_user_id: string | null;
  owner_name: string | null;
  environment: 'production' | 'staging' | 'development' | 'other';
  classification: 'public' | 'internal' | 'confidential' | 'restricted';
  status: 'active' | 'retired' | 'disposed';
  vendor: string | null;
  version: string | null;
  ip_address: string | null;
  location: string | null;
  description: string | null;
  last_reviewed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Vulnerability {
  id: string;
  company_id: string;
  title: string;
  cve_id: string | null;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'info';
  status: 'open' | 'in_remediation' | 'resolved' | 'accepted_risk';
  affected_system: string | null;
  discovered_at: string | null;
  due_date: string | null;
  resolved_at: string | null;
  description: string | null;
  remediation_notes: string | null;
  owner_user_id: string | null;
  owner_name: string | null;
  created_at: string;
  updated_at: string;
}

export interface BcpRecord {
  id: string;
  company_id: string;
  title: string;
  record_type: 'bcp' | 'drp' | 'both';
  status: 'not_tested' | 'scheduled' | 'tested' | 'passed' | 'failed';
  last_tested_at: string | null;
  next_test_due: string | null;
  rto_minutes: number | null;
  rpo_minutes: number | null;
  test_results: string | null;
  scope: string | null;
  notes: string | null;
  owner_user_id: string | null;
  owner_name: string | null;
  file_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface BackgroundCheck {
  id: string;
  company_id: string;
  employee_name: string;
  employee_email: string | null;
  check_type: 'standard' | 'enhanced' | 'international';
  vendor: string | null;
  status: 'pending' | 'in_progress' | 'completed' | 'failed' | 'expired';
  initiated_at: string | null;
  completed_at: string | null;
  valid_until: string | null;
  notes: string | null;
  auto_detected: boolean;
  detection_key: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChecklistItem {
  item: string;
  done: boolean;
}

export interface Offboarding {
  id: string;
  company_id: string;
  employee_name: string;
  employee_email: string | null;
  last_day: string | null;
  department: string | null;
  status: 'pending' | 'in_progress' | 'completed';
  checklist: ChecklistItem[];
  completed_by_user_id: string | null;
  completed_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface AppNotification {
  id: string;
  type: 'info' | 'warning' | 'error' | 'success';
  title: string;
  message: string;
  read: boolean;
  resource_type?: string;
  resource_id?: string;
  created_at: string;
}

export interface NotificationPrefs {
  training_overdue: boolean;
  access_review_overdue: boolean;
  vendor_needs_review: boolean;
  evidence_stale: boolean;
  weekly_digest: boolean;
}

export interface NotificationSettings {
  prefs: NotificationPrefs;
  slack_webhook_url: string | null;
}

export interface PublicTrustPageView {
  company_name: string;
  slug: string;
  custom_headline: string | null;
  custom_message: string | null;
  show_score: boolean;
  show_policies: boolean;
  show_integrations: boolean;
  frameworks: PublicTrustFramework[];
  policies: PublicTrustPolicy[] | null;
  integrations: string[] | null;
  generated_at: string;
}

export interface SoaItem {
  id: string;
  annex_ref: string;
  annex_theme: string;
  title: string;
  included: boolean;
  justification?: string | null;
  implementation_status: string;
  implementation_notes?: string | null;
}

export interface RopaRecord {
  id: string;
  name: string;
  role: string;
  purpose?: string | null;
  legal_basis?: string | null;
  data_categories?: string | null;
  data_subjects?: string | null;
  recipients?: string | null;
  third_country_transfers?: string | null;
  retention_period?: string | null;
  security_measures?: string | null;
  dpa_url?: string | null;
  notes?: string | null;
}

export interface DataBreach {
  id: string;
  title: string;
  occurred_at?: string | null;
  discovered_at?: string | null;
  breach_type: string;
  severity: string;
  status: string;
  affected_records?: number | null;
  affected_systems?: string | null;
  description?: string | null;
  notification_required: boolean;
  dpa_notified_at?: string | null;
  individuals_notified_at?: string | null;
  root_cause?: string | null;
  remediation?: string | null;
  reporter_name?: string | null;
}

export interface SubjectRequest {
  id: string;
  requester_name: string;
  requester_email?: string | null;
  request_type: string;
  received_at: string;
  due_at?: string | null;
  status: string;
  response_notes?: string | null;
  completed_at?: string | null;
  regulation: string;
}

export interface ManagementReview {
  id: string;
  review_date: string;
  attendees?: string | null;
  inputs_summary?: string | null;
  decisions?: string | null;
  action_items: Array<{ item: string; owner: string; due_date: string | null; done: boolean }>;
  next_review_date?: string | null;
  outcome: string;
  notes?: string | null;
}
