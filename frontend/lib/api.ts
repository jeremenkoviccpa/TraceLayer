import type { AccessReview, ActionPlan, AgencyAssignment, AgencyFinding, AgencyTask, ApiKey, AppNotification, Asset, AuditComment, AuditEngagement, AuditEngagementView, AutofillResult, AuditLog, AuditSession, BackgroundCheck, BcpRecord, BillingInfo, ChatConversation, ChatConversationWithMessages, Company, ComplianceScore, DataBreach, Device, Document, DownloadResponse, DriftEvent, Evidence, EvidenceActivityPoint, Incident, Integration, Invitation, ManagementReview, ManualControl, Member, NotificationSettings, Offboarding, Page, PartnerClient, PartnerDirectoryEntry, PartnerSwitchResponse, PartnerTrustCenterInfo, PenTest, PentestAgencyProfile, Policy, PolicyContentResponse, PolicyTaskItem, PortalTasksResponse, PublicAuditView, PublicTrustPageView, QuestionnaireComment, QuestionnaireResult, QuestionnaireSession, QuestionnaireSessionAnswer, QuestionnaireType, ReadinessData, RemediationSuggestion, Report, Risk, RopaRecord, ScoreHistoryPoint, SimulationResult, SlackConfig, SoaItem, SubjectRequest, SuperAdminCompany, SuperAdminUser, TimeMachineResult, TrainingCertificate, TrainingQuiz, TrainingQuizResult, TrainingRecord, TrustAnalytics, TrustPageSettings, User, Vendor, Vulnerability } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiClient {
  private getToken(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("access_token");
  }

  setTokens(access: string, refresh: string) {
    localStorage.setItem("access_token", access);
    localStorage.setItem("refresh_token", refresh);
  }

  clearTokens() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  private async tryRefresh(): Promise<boolean> {
    const refresh = localStorage.getItem("refresh_token");
    if (!refresh) return false;
    try {
      const res = await fetch(`${API_URL}/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refresh }),
      });
      if (!res.ok) return false;
      const data = await res.json();
      this.setTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    auth = true,
    isRetry = false,
  ): Promise<T> {
    const headers: Record<string, string> = { "Content-Type": "application/json" };
    if (auth) {
      const token = this.getToken();
      if (!token) throw new Error("Not authenticated");
      headers["Authorization"] = `Bearer ${token}`;
    }

    const res = await fetch(`${API_URL}/v1${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (res.status === 401 && auth && !isRetry) {
      const refreshed = await this.tryRefresh();
      if (refreshed) return this.request(method, path, body, auth, true);
      this.clearTokens();
      window.location.href = "/login";
      throw new Error("Session expired");
    }

    if (res.status === 204) return undefined as T;

    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(json.detail ?? "Request failed");
    return json as T;
  }

  async requestPublic<T>(method: string, path: string, body?: unknown): Promise<T> {
    return this.request<T>(method, path, body, false);
  }

  // ── Auth ────────────────────────────────────────────────────────────────

  async register(email: string, password: string, companyName: string, accountType: "company" | "partner" = "company"): Promise<void> {
    const data = await this.request<{ access_token: string; refresh_token: string }>(
      "POST", "/auth/register",
      { email, password, company_name: companyName, account_type: accountType },
      false,
    );
    this.setTokens(data.access_token, data.refresh_token);
  }

  async registerAgency(email: string, password: string, companyName: string): Promise<void> {
    const data = await this.request<{ access_token: string; refresh_token: string }>(
      "POST", "/auth/register",
      { email, password, company_name: companyName, account_type: "pentest_agency" },
      false,
    );
    this.setTokens(data.access_token, data.refresh_token);
  }

  async login(email: string, password: string): Promise<{ requires_2fa?: boolean; totp_token?: string }> {
    const data = await this.request<{ access_token: string; refresh_token: string; requires_2fa?: boolean; totp_token?: string }>(
      "POST", "/auth/login",
      { email, password },
      false,
    );
    if (data.requires_2fa) {
      return { requires_2fa: true, totp_token: data.totp_token };
    }
    this.setTokens(data.access_token, data.refresh_token);
    return {};
  }

  async verify2FA(totpToken: string, code: string): Promise<void> {
    const data = await this.request<{ access_token: string; refresh_token: string }>(
      "POST", "/auth/2fa/verify",
      { totp_token: totpToken, code },
      false,
    );
    this.setTokens(data.access_token, data.refresh_token);
  }

  async setup2FA(): Promise<{ secret: string; qr_uri: string; backup_codes: string[] }> {
    return this.request("POST", "/auth/2fa/setup");
  }

  async enable2FA(code: string): Promise<void> {
    return this.request("POST", "/auth/2fa/enable", { code });
  }

  async disable2FA(password: string): Promise<void> {
    return this.request("POST", "/auth/2fa/disable", { password });
  }

  async regenerateBackupCodes(password: string): Promise<{ secret: string; qr_uri: string; backup_codes: string[] }> {
    return this.request("POST", "/auth/2fa/backup-codes", { password });
  }

  async logout(): Promise<void> {
    const refresh = localStorage.getItem("refresh_token");
    if (refresh) {
      await this.request("POST", "/auth/logout", { refresh_token: refresh }).catch(() => {});
    }
    this.clearTokens();
  }

  async me(): Promise<User> {
    return this.request<User>("GET", "/auth/me");
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<User> {
    return this.request<User>("PATCH", "/auth/me", {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  async updateProfile(fullName: string): Promise<User> {
    return this.request<User>("PATCH", "/auth/profile", { full_name: fullName });
  }

  async forgotPassword(email: string): Promise<void> {
    return this.request("POST", "/auth/forgot-password", { email }, false);
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    return this.request("POST", "/auth/reset-password", { token, new_password: newPassword }, false);
  }

  async verifyEmail(token: string): Promise<void> {
    return this.request("POST", `/auth/verify-email?token=${encodeURIComponent(token)}`, undefined, false);
  }

  async resendVerification(): Promise<void> {
    return this.request("POST", "/auth/resend-verification");
  }

  // ── Integrations ────────────────────────────────────────────────────────

  async getIntegrations(): Promise<Integration[]> {
    return this.request<Integration[]>("GET", "/integrations");
  }

  async connectIntegration(
    integrationType: string,
    credentials: Record<string, string>,
  ): Promise<Integration> {
    return this.request<Integration>("POST", "/integrations/connect", {
      integration_type: integrationType,
      credentials,
    });
  }

  async disconnectIntegration(integrationType: string): Promise<void> {
    return this.request("DELETE", `/integrations/${integrationType}`);
  }

  async triggerCollect(integrationType: string): Promise<void> {
    return this.request("POST", `/integrations/${integrationType}/collect`);
  }

  async simulateIntegration(integrationType: string): Promise<SimulationResult> {
    return this.request<SimulationResult>("GET", `/integrations/simulate/${integrationType}`);
  }

  // ── Evidence ────────────────────────────────────────────────────────────

  async getEvidence(params?: {
    control?: string;
    integration?: string;
    page?: number;
    page_size?: number;
  }): Promise<Page<Evidence>> {
    const q = new URLSearchParams();
    if (params?.control) q.set("control", params.control);
    if (params?.integration) q.set("integration", params.integration);
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    const qs = q.toString();
    return this.request<Page<Evidence>>("GET", `/evidence${qs ? `?${qs}` : ""}`);
  }

  // ── Reports ─────────────────────────────────────────────────────────────

  async generateReport(framework = "soc2", reportType = "full", format = "json"): Promise<Report> {
    return this.request<Report>("POST", "/reports/generate", {
      framework,
      report_type: reportType,
      format,
    });
  }

  async getReports(page = 1): Promise<Page<Report>> {
    return this.request<Page<Report>>("GET", `/reports?page=${page}`);
  }

  async getReport(id: string): Promise<Report> {
    return this.request<Report>("GET", `/reports/${id}`);
  }

  async downloadReport(id: string, format = "json"): Promise<DownloadResponse> {
    return this.request<DownloadResponse>("GET", `/reports/${id}/download?format=${format}`);
  }

  async sendWeeklyPreview(): Promise<{ message: string }> {
    return this.request<{ message: string }>("POST", "/reports/weekly-preview");
  }

  async generateAuditPackage(framework = "soc2"): Promise<Report> {
    return this.request<Report>("POST", "/reports/audit-package", { framework });
  }

  async generateSpecializedReport(reportType: string): Promise<Report> {
    return this.request<Report>("POST", "/reports/specialized", { report_type: reportType });
  }

  // ── Org ─────────────────────────────────────────────────────────────────

  async getMembers(): Promise<Member[]> {
    return this.request<Member[]>("GET", "/org/members");
  }

  async removeMember(userId: string): Promise<void> {
    return this.request("DELETE", `/org/members/${userId}`);
  }

  async getInvites(): Promise<Invitation[]> {
    return this.request<Invitation[]>("GET", "/org/invites");
  }

  async createInvite(email: string, role: "member" | "admin"): Promise<Invitation> {
    return this.request<Invitation>("POST", "/org/invites", { email, role });
  }

  async revokeInvite(id: string): Promise<void> {
    return this.request("DELETE", `/org/invites/${id}`);
  }

  async acceptInvite(token: string, password: string): Promise<void> {
    const data = await this.request<{ access_token: string; refresh_token: string }>(
      "POST", "/org/invites/accept",
      { token, password },
      false,
    );
    this.setTokens(data.access_token, data.refresh_token);
  }

  // ── Account (GDPR) ───────────────────────────────────────────────────────

  async deleteAccount(): Promise<void> {
    return this.request("DELETE", "/org/account");
  }

  async exportAccountData(): Promise<Record<string, unknown>> {
    return this.request<Record<string, unknown>>("GET", "/org/account/export");
  }

  // ── Settings ─────────────────────────────────────────────────────────────

  async getCompany(): Promise<Company> {
    return this.request<Company>("GET", "/org/company");
  }

  async getOnboardingStatus(): Promise<{
    has_integration: boolean; has_evidence: boolean; has_vendor: boolean;
    has_member: boolean; has_training: boolean; has_report: boolean; has_risk: boolean;
  }> {
    return this.request("GET", "/org/onboarding-status");
  }

  async updateCompany(name: string, gstNumber?: string, primaryFrameworks?: string[]): Promise<Company> {
    return this.request<Company>("PATCH", "/org/company", {
      name,
      gst_number: gstNumber ?? null,
      ...(primaryFrameworks !== undefined ? { primary_frameworks: primaryFrameworks } : {}),
    });
  }

  async completeOnboarding(frameworks: string[] = []): Promise<void> {
    return this.request("POST", "/org/onboarding/complete", { frameworks });
  }

  // ── Compliance ───────────────────────────────────────────────────────────

  async getComplianceScore(framework = "soc2"): Promise<ComplianceScore> {
    return this.request<ComplianceScore>("GET", `/compliance/score?framework=${framework}`);
  }

  async getScoreHistory(framework = "soc2", days = 30): Promise<ScoreHistoryPoint[]> {
    return this.request<ScoreHistoryPoint[]>("GET", `/compliance/score-history?framework=${framework}&days=${days}`);
  }

  async timeMachine(date: string, framework = "soc2"): Promise<TimeMachineResult> {
    return this.request<TimeMachineResult>("GET", `/compliance/time-machine?date=${date}&framework=${framework}`);
  }

  async getEvidenceActivity(days = 14): Promise<EvidenceActivityPoint[]> {
    return this.request<EvidenceActivityPoint[]>("GET", `/compliance/evidence-activity?days=${days}`);
  }

  async getManualControls(framework = "soc2"): Promise<ManualControl[]> {
    return this.request<ManualControl[]>("GET", `/compliance/manual-controls?framework=${framework}`);
  }

  async updateManualControl(
    controlId: string,
    framework: string,
    status: string,
    notes: string | null,
  ): Promise<ManualControl> {
    return this.request<ManualControl>(
      "PUT",
      `/compliance/manual-controls/${controlId}?framework=${framework}`,
      { status, notes },
    );
  }

  async getAISummary(framework = "soc2"): Promise<{ summary: string; overall_score: number; generated_at: string }> {
    return this.request("POST", `/compliance/ai-summary?framework=${framework}`);
  }

  async advisorChat(
    framework: string,
    message: string,
    history: { role: string; content: string }[],
  ): Promise<{ reply: string }> {
    return this.request("POST", "/compliance/advisor/chat", { framework, message, history });
  }

  async assignManualControl(controlId: string, framework: string, ownerUserId: string | null): Promise<ManualControl> {
    return this.request<ManualControl>("PATCH", `/compliance/manual-controls/${controlId}/assign?framework=${framework}`, { owner_user_id: ownerUserId });
  }

  async driftEvents(limit = 20): Promise<DriftEvent[]> {
    return this.request<DriftEvent[]>("GET", `/compliance/drift-events?limit=${limit}`);
  }

  // ── Audit Sessions ────────────────────────────────────────────────────────

  async createAuditSession(label?: string, expiresDays?: number): Promise<AuditSession> {
    return this.request<AuditSession>("POST", "/audit-sessions", { label: label || null, expires_days: expiresDays ?? 90 });
  }

  async getAuditSessions(): Promise<AuditSession[]> {
    return this.request<AuditSession[]>("GET", "/audit-sessions");
  }

  async revokeAuditSession(id: string): Promise<void> {
    return this.request("DELETE", `/audit-sessions/${id}`);
  }

  async getPublicAuditView(token: string): Promise<PublicAuditView> {
    return this.request<PublicAuditView>("GET", `/audit-sessions/view/${token}`, undefined, false);
  }

  // ── Audit Log ────────────────────────────────────────────────────────────

  async getAuditLog(params?: {
    page?: number;
    page_size?: number;
    action?: string;
    user_email?: string;
    date_from?: string;
    date_to?: string;
  }): Promise<Page<AuditLog>> {
    const q = new URLSearchParams();
    if (params?.page) q.set("page", String(params.page));
    if (params?.page_size) q.set("page_size", String(params.page_size));
    if (params?.action) q.set("action", params.action);
    if (params?.user_email) q.set("user_email", params.user_email);
    if (params?.date_from) q.set("date_from", params.date_from);
    if (params?.date_to) q.set("date_to", params.date_to);
    const qs = q.toString();
    return this.request<Page<AuditLog>>("GET", `/audit-log${qs ? `?${qs}` : ""}`);
  }

  // ── Billing ──────────────────────────────────────────────────────────────

  async getSubscription(): Promise<BillingInfo> {
    return this.request<BillingInfo>("GET", "/billing/subscription");
  }

  async createCheckout(): Promise<{ checkout_url: string }> {
    return this.request<{ checkout_url: string }>("POST", "/billing/checkout");
  }

  // SSO
  async checkSSODomain(domain: string): Promise<{ sso_enabled: boolean; company_id?: string }> {
    return this.request("GET", `/auth/sso/check?domain=${encodeURIComponent(domain)}`);
  }

  async getSSOConfig(): Promise<{ id: string; enabled: boolean; domain: string; issuer: string; client_id: string; scopes: string }> {
    return this.request("GET", "/sso/config");
  }

  async upsertSSOConfig(body: { domain: string; issuer: string; client_id: string; client_secret: string; scopes?: string }): Promise<unknown> {
    return this.request("POST", "/sso/config", body);
  }

  async toggleSSO(enabled: boolean): Promise<unknown> {
    return this.request("PATCH", "/sso/config", { enabled });
  }

  async deleteSSOConfig(): Promise<void> {
    return this.request("DELETE", "/sso/config");
  }

  async getBillingPortal(): Promise<{ portal_url: string }> {
    return this.request<{ portal_url: string }>("POST", "/billing/portal");
  }

  // ── Risks ─────────────────────────────────────────────────────────────────

  async getRisks(): Promise<Risk[]> {
    return this.request<Risk[]>("GET", "/risks");
  }

  async createRisk(body: Partial<Risk>): Promise<Risk> {
    return this.request<Risk>("POST", "/risks", body);
  }

  async updateRisk(id: string, body: Partial<Risk>): Promise<Risk> {
    return this.request<Risk>("PATCH", `/risks/${id}`, body);
  }

  async deleteRisk(id: string): Promise<void> {
    return this.request("DELETE", `/risks/${id}`);
  }

  async runRiskDetection(): Promise<{ created: number }> {
    return this.request<{ created: number }>("POST", "/risks/detect");
  }

  // ── Policies ──────────────────────────────────────────────────────────────

  async getPolicies(): Promise<Policy[]> {
    return this.request<Policy[]>("GET", "/policies");
  }

  async savePolicy(slug: string, content: string): Promise<Policy> {
    return this.request<Policy>("PUT", `/policies/${slug}`, { content });
  }

  async setPolicyExpiry(slug: string, expires_at: string | null): Promise<Policy> {
    return this.request<Policy>("PATCH", `/policies/${slug}/expiry`, { expires_at });
  }

  // ── Risk exceptions ──────────────────────────────────────────────────────
  async getExceptions(framework: string): Promise<any[]> {
    return this.request("GET", `/compliance/exceptions?framework=${framework}`);
  }
  async createException(body: { framework: string; control_category: string; control_name: string; justification: string; owner_name?: string; owner_email?: string; expires_at?: string }): Promise<{ id: string }> {
    return this.request("POST", "/compliance/exceptions", body);
  }
  async deleteException(id: string): Promise<void> {
    return this.request("DELETE", `/compliance/exceptions/${id}`);
  }

  // ── Control exclusions ────────────────────────────────────────────────────
  async getExclusions(framework: string): Promise<any[]> {
    return this.request("GET", `/compliance/exclusions?framework=${framework}`);
  }
  async createExclusion(body: { framework: string; control_category: string; control_name: string; justification: string; exclusion_type?: string }): Promise<{ id: string }> {
    return this.request("POST", "/compliance/exclusions", body);
  }
  async deleteExclusion(id: string): Promise<void> {
    return this.request("DELETE", `/compliance/exclusions/${id}`);
  }

  // ── Onboarding ────────────────────────────────────────────────────────────
  async getOnboarding(): Promise<any[]> {
    return this.request("GET", "/onboarding");
  }
  async createOnboarding(body: { employee_email: string; employee_name?: string; hired_at?: string; department?: string; role_title?: string }): Promise<any> {
    return this.request("POST", "/onboarding", body);
  }
  async updateOnboardingTaskStatus(taskId: string, field: string, status: string): Promise<any> {
    return this.request("PATCH", `/onboarding/${taskId}/status`, { field, status });
  }
  async deleteOnboarding(taskId: string): Promise<void> {
    return this.request("DELETE", `/onboarding/${taskId}`);
  }

  // ── Subprocessors ─────────────────────────────────────────────────────────
  async getSubprocessors(): Promise<any[]> {
    return this.request("GET", "/subprocessors");
  }
  async createSubprocessor(body: any): Promise<any> {
    return this.request("POST", "/subprocessors", body);
  }
  async updateSubprocessor(id: string, body: any): Promise<any> {
    return this.request("PATCH", `/subprocessors/${id}`, body);
  }
  async deleteSubprocessor(id: string): Promise<void> {
    return this.request("DELETE", `/subprocessors/${id}`);
  }

  // ── Vendor questionnaires ─────────────────────────────────────────────────
  async getVendorQuestionnaires(): Promise<any[]> {
    return this.request("GET", "/vendor-questionnaires");
  }
  async getVendorQuestionnairesForVendor(vendorId: string): Promise<any[]> {
    return this.request("GET", `/vendor-questionnaires/by-vendor/${vendorId}`);
  }
  async sendVendorQuestionnaire(body: { vendor_id?: string; vendor_name: string; sent_to_email: string; due_days?: number }): Promise<any> {
    return this.request("POST", "/vendor-questionnaires", body);
  }

  async acknowledgePolicy(slug: string): Promise<{ detail: string; signed_at: string }> {
    return this.request("POST", `/policies/${slug}/sign`);
  }

  async revokeAcknowledgement(slug: string): Promise<{ detail: string }> {
    return this.request("DELETE", `/policies/${slug}/sign`);
  }

  async getPolicyAcknowledgments(slug: string): Promise<{
    signed: Array<{ user_id: string; email: string; name: string; signed_at: string }>;
    unsigned: Array<{ user_id: string; email: string; name: string }>;
  }> {
    return this.request("GET", `/policies/${slug}/signatures`);
  }

  // ── Agentic compliance ───────────────────────────────────────────────────
  async setControlDueDate(controlId: string, framework: string, due_date: string | null): Promise<ManualControl> {
    return this.request<ManualControl>("PATCH", `/compliance/manual-controls/${controlId}/due-date?framework=${framework}`, { due_date });
  }

  async getControlRemediation(controlId: string, framework: string): Promise<RemediationSuggestion> {
    return this.request<RemediationSuggestion>("POST", `/compliance/manual-controls/${controlId}/remediate?framework=${framework}`);
  }

  async getActionPlan(framework: string): Promise<ActionPlan> {
    return this.request<ActionPlan>("POST", `/compliance/action-plan?framework=${framework}`);
  }

  // ── Questionnaire ─────────────────────────────────────────────────────────

  async getQuestionnaireTypes(): Promise<QuestionnaireType[]> {
    return this.request<QuestionnaireType[]>("GET", "/questionnaire/types");
  }

  async generateQuestionnaire(questionnaireType: string): Promise<QuestionnaireResult> {
    return this.request<QuestionnaireResult>("POST", "/questionnaire/generate", { questionnaire_type: questionnaireType });
  }

  async aiAutofillQuestionnaire(questions: string[]): Promise<AutofillResult> {
    return this.request<AutofillResult>("POST", "/questionnaire/ai-autofill", { questions });
  }

  // ── Readiness ─────────────────────────────────────────────────────────────

  async getReadiness(framework = "soc2"): Promise<ReadinessData> {
    return this.request<ReadinessData>("GET", `/compliance/readiness?framework=${framework}`);
  }

  // ── Training ──────────────────────────────────────────────────────────────

  async getTraining(): Promise<TrainingRecord[]> {
    return this.request<TrainingRecord[]>("GET", "/training");
  }

  async createTraining(body: Partial<TrainingRecord>): Promise<TrainingRecord> {
    return this.request<TrainingRecord>("POST", "/training", body);
  }

  async updateTraining(id: string, body: Partial<TrainingRecord>): Promise<TrainingRecord> {
    return this.request<TrainingRecord>("PATCH", `/training/${id}`, body);
  }

  async deleteTraining(id: string): Promise<void> {
    return this.request("DELETE", `/training/${id}`);
  }

  async runTrainingDetection(): Promise<{ created: number }> {
    return this.request<{ created: number }>("POST", "/training/detect");
  }

  async getTrainingQuiz(token: string): Promise<TrainingQuiz> {
    return this.requestPublic<TrainingQuiz>("GET", `/training/take/${token}`);
  }

  async submitTrainingQuiz(token: string, answers: Record<string, number>): Promise<TrainingQuizResult> {
    return this.requestPublic<TrainingQuizResult>("POST", `/training/take/${token}/submit`, { answers });
  }

  async getTrainingCertificate(token: string): Promise<TrainingCertificate> {
    return this.requestPublic<TrainingCertificate>("GET", `/training/certificate/${token}`);
  }

  // ── Nango OAuth ────────────────────────────────────────────────────────────
  async nangoComplete(integrationType: string, connectionId: string): Promise<void> {
    await this.request("POST", "/integrations/nango/complete", {
      integration_type: integrationType,
      connection_id: connectionId,
    });
  }

  // ── Pen Tests ─────────────────────────────────────────────────────────────

  async getPenTests(): Promise<PenTest[]> {
    return this.request<PenTest[]>("GET", "/pen-tests");
  }

  async createPenTest(body: Partial<PenTest>): Promise<PenTest> {
    return this.request<PenTest>("POST", "/pen-tests", body);
  }

  async updatePenTest(id: string, body: Partial<PenTest>): Promise<PenTest> {
    return this.request<PenTest>("PATCH", `/pen-tests/${id}`, body);
  }

  async deletePenTest(id: string): Promise<void> {
    return this.request("DELETE", `/pen-tests/${id}`);
  }

  // ── Vendors ───────────────────────────────────────────────────────────────

  async getVendors(): Promise<Vendor[]> {
    return this.request<Vendor[]>("GET", "/vendors");
  }

  async createVendor(body: Partial<Vendor>): Promise<Vendor> {
    return this.request<Vendor>("POST", "/vendors", body);
  }

  async updateVendor(id: string, body: Partial<Vendor>): Promise<Vendor> {
    return this.request<Vendor>("PATCH", `/vendors/${id}`, body);
  }

  async deleteVendor(id: string): Promise<void> {
    return this.request("DELETE", `/vendors/${id}`);
  }

  async autoPopulateVendors(): Promise<{ created: number; skipped: number }> {
    return this.request("POST", "/vendors/auto-populate");
  }

  // ── Access Reviews ────────────────────────────────────────────────────────

  async getAccessReviews(): Promise<AccessReview[]> {
    return this.request<AccessReview[]>("GET", "/access-reviews");
  }

  async createAccessReview(body: Partial<AccessReview>): Promise<AccessReview> {
    return this.request<AccessReview>("POST", "/access-reviews", body);
  }

  async updateAccessReview(id: string, body: Partial<AccessReview>): Promise<AccessReview> {
    return this.request<AccessReview>("PATCH", `/access-reviews/${id}`, body);
  }

  async deleteAccessReview(id: string): Promise<void> {
    return this.request("DELETE", `/access-reviews/${id}`);
  }

  async generateAccessReview(): Promise<AccessReview> {
    return this.request<AccessReview>("POST", "/access-reviews/generate");
  }

  // ── Trust Center ──────────────────────────────────────────────────────────

  async getTrustPageSettings(): Promise<TrustPageSettings> {
    return this.request<TrustPageSettings>("GET", "/trust/settings");
  }

  async updateTrustPageSettings(body: Partial<TrustPageSettings>): Promise<TrustPageSettings> {
    return this.request<TrustPageSettings>("PUT", "/trust/settings", body);
  }

  async getPublicTrustPage(slug: string): Promise<PublicTrustPageView> {
    return this.request<PublicTrustPageView>("GET", `/trust/public/${slug}`, undefined, false);
  }

  // ── Documents ─────────────────────────────────────────────────────────────

  async getDocuments(resourceType: string, resourceId?: string): Promise<Document[]> {
    const q = new URLSearchParams({ resource_type: resourceType });
    if (resourceId) q.set("resource_id", resourceId);
    return this.request<Document[]>("GET", `/documents?${q}`);
  }

  async uploadDocument(file: File, resourceType: string, resourceId?: string): Promise<Document> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");
    const form = new FormData();
    form.append("file", file);
    form.append("resource_type", resourceType);
    if (resourceId) form.append("resource_id", resourceId);
    const res = await fetch(`${API_URL}/v1/documents/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(json.detail ?? "Upload failed");
    return json as Document;
  }

  async deleteDocument(id: string): Promise<void> {
    return this.request("DELETE", `/documents/${id}`);
  }

  async getDocumentUrl(id: string): Promise<{ url: string }> {
    return this.request<{ url: string }>("GET", `/documents/${id}/url`);
  }

  // ── Notifications ─────────────────────────────────────────────────────────

  async getNotificationSettings(): Promise<NotificationSettings> {
    return this.request<NotificationSettings>("GET", "/notifications/prefs");
  }

  async updateNotificationSettings(body: NotificationSettings): Promise<NotificationSettings> {
    return this.request<NotificationSettings>("PUT", "/notifications/prefs", body);
  }

  async getNotifications(): Promise<AppNotification[]> {
    return this.request<AppNotification[]>("GET", "/notifications/inbox");
  }

  async markNotificationRead(id: string): Promise<void> {
    return this.request("POST", `/notifications/inbox/${id}/read`);
  }

  async markAllNotificationsRead(): Promise<void> {
    return this.request("POST", "/notifications/inbox/read-all");
  }

  // ── Incidents ─────────────────────────────────────────────────────────────

  async getIncidents(): Promise<Incident[]> {
    return this.request<Incident[]>("GET", "/incidents");
  }

  async createIncident(body: Partial<Incident>): Promise<Incident> {
    return this.request<Incident>("POST", "/incidents", body);
  }

  async updateIncident(id: string, body: Partial<Incident>): Promise<Incident> {
    return this.request<Incident>("PATCH", `/incidents/${id}`, body);
  }

  async deleteIncident(id: string): Promise<void> {
    return this.request("DELETE", `/incidents/${id}`);
  }

  async runIncidentDetection(): Promise<{ created: number }> {
    return this.request<{ created: number }>("POST", "/incidents/detect");
  }

  // ── Assets ────────────────────────────────────────────────────────────────

  async getAssets(): Promise<Asset[]> {
    return this.request<Asset[]>("GET", "/assets");
  }

  async createAsset(body: Partial<Asset>): Promise<Asset> {
    return this.request<Asset>("POST", "/assets", body);
  }

  async updateAsset(id: string, body: Partial<Asset>): Promise<Asset> {
    return this.request<Asset>("PATCH", `/assets/${id}`, body);
  }

  async deleteAsset(id: string): Promise<void> {
    return this.request("DELETE", `/assets/${id}`);
  }

  async syncAssets(): Promise<{ created: number; skipped: number }> {
    return this.request("POST", "/assets/sync");
  }

  // ── Vulnerabilities ───────────────────────────────────────────────────────

  async getVulnerabilities(): Promise<Vulnerability[]> {
    return this.request<Vulnerability[]>("GET", "/vulnerabilities");
  }

  async createVulnerability(body: Partial<Vulnerability>): Promise<Vulnerability> {
    return this.request<Vulnerability>("POST", "/vulnerabilities", body);
  }

  async updateVulnerability(id: string, body: Partial<Vulnerability>): Promise<Vulnerability> {
    return this.request<Vulnerability>("PATCH", `/vulnerabilities/${id}`, body);
  }

  async deleteVulnerability(id: string): Promise<void> {
    return this.request("DELETE", `/vulnerabilities/${id}`);
  }

  async autoDetectVulnerabilities(): Promise<{ created: number; skipped: number }> {
    return this.request("POST", "/vulnerabilities/auto-detect");
  }

  // ── Business Continuity ───────────────────────────────────────────────────

  async getBcpRecords(): Promise<BcpRecord[]> {
    return this.request<BcpRecord[]>("GET", "/business-continuity");
  }

  async createBcpRecord(body: Partial<BcpRecord>): Promise<BcpRecord> {
    return this.request<BcpRecord>("POST", "/business-continuity", body);
  }

  async updateBcpRecord(id: string, body: Partial<BcpRecord>): Promise<BcpRecord> {
    return this.request<BcpRecord>("PATCH", `/business-continuity/${id}`, body);
  }

  async deleteBcpRecord(id: string): Promise<void> {
    return this.request("DELETE", `/business-continuity/${id}`);
  }

  // ── Background Checks ─────────────────────────────────────────────────────

  async getBackgroundChecks(): Promise<BackgroundCheck[]> {
    return this.request<BackgroundCheck[]>("GET", "/background-checks");
  }

  async createBackgroundCheck(body: Partial<BackgroundCheck>): Promise<BackgroundCheck> {
    return this.request<BackgroundCheck>("POST", "/background-checks", body);
  }

  async updateBackgroundCheck(id: string, body: Partial<BackgroundCheck>): Promise<BackgroundCheck> {
    return this.request<BackgroundCheck>("PATCH", `/background-checks/${id}`, body);
  }

  async deleteBackgroundCheck(id: string): Promise<void> {
    return this.request("DELETE", `/background-checks/${id}`);
  }

  async runBackgroundCheckDetection(): Promise<{ created: number }> {
    return this.request<{ created: number }>("POST", "/background-checks/detect");
  }

  // ── Offboarding ───────────────────────────────────────────────────────────

  async getOffboardings(): Promise<Offboarding[]> {
    return this.request<Offboarding[]>("GET", "/offboarding");
  }

  async createOffboarding(body: Partial<Offboarding>): Promise<Offboarding> {
    return this.request<Offboarding>("POST", "/offboarding", body);
  }

  async updateOffboarding(id: string, body: Partial<Offboarding>): Promise<Offboarding> {
    return this.request<Offboarding>("PATCH", `/offboarding/${id}`, body);
  }

  async deleteOffboarding(id: string): Promise<void> {
    return this.request("DELETE", `/offboarding/${id}`);
  }

  // ── Evidence Upload ───────────────────────────────────────────────────────

  async uploadEvidence(file: File, control: string, evidenceType: string): Promise<Evidence> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");
    const form = new FormData();
    form.append("file", file);
    form.append("control", control);
    form.append("evidence_type", evidenceType);
    const res = await fetch(`${API_URL}/v1/evidence/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(json.detail ?? "Upload failed");
    return json as Evidence;
  }

  async deleteEvidenceBulk(ids: string[]): Promise<void> {
    return this.request("DELETE", "/evidence/bulk", { ids });
  }

  // ── Partner ────────────────────────────────────────────────────────────────

  async getPartnerClients(): Promise<PartnerClient[]> {
    return this.request<PartnerClient[]>("GET", "/partner/clients");
  }

  async createPartnerClientCheckout(clientName: string): Promise<{ checkout_url: string; payment_id: string }> {
    return this.request("POST", "/partner/clients/checkout", { client_name: clientName });
  }

  async provisionPartnerClientDirect(clientName: string): Promise<PartnerClient> {
    return this.request<PartnerClient>("POST", "/partner/clients/provision", { client_name: clientName });
  }

  async switchToClient(clientCompanyId: string): Promise<PartnerSwitchResponse> {
    return this.request<PartnerSwitchResponse>("GET", `/partner/clients/${clientCompanyId}/switch`);
  }

  async getClientTrustCenter(clientCompanyId: string): Promise<PartnerTrustCenterInfo> {
    return this.request<PartnerTrustCenterInfo>("GET", `/partner/clients/${clientCompanyId}/trust-center`);
  }

  async getPartnerPayments(): Promise<Array<{
    id: string; client_name: string; status: string;
    amount_cents: number; created_at: string | null;
    paid_at: string | null; client_company_id: string | null;
  }>> {
    return this.request("GET", "/partner/payments");
  }

  /** Restore the partner's own token after exiting client context. */
  restorePartnerToken(): boolean {
    if (typeof window === "undefined") return false;
    const partnerToken = localStorage.getItem("partner_access_token");
    if (!partnerToken) return false;
    localStorage.setItem("access_token", partnerToken);
    localStorage.removeItem("partner_access_token");
    localStorage.removeItem("active_client_name");
    return true;
  }

  /** Store partner token and activate client context. */
  activateClientContext(switchResponse: PartnerSwitchResponse): void {
    if (typeof window === "undefined") return;
    const partnerToken = localStorage.getItem("access_token") ?? "";
    localStorage.setItem("partner_access_token", partnerToken);
    localStorage.setItem("active_client_name", switchResponse.client_name);
    localStorage.setItem("access_token", switchResponse.access_token);
  }

  isInClientContext(): boolean {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem("partner_access_token");
  }

  getActiveClientName(): string | null {
    if (typeof window === "undefined") return null;
    return localStorage.getItem("active_client_name");
  }

  // ── Audit Engagements ──────────────────────────────────────────────────────
  async getAuditEngagements(): Promise<AuditEngagement[]> {
    return this.request<AuditEngagement[]>("GET", "/audit-engagements");
  }

  async createAuditEngagement(data: {
    auditor_email: string;
    auditor_name?: string;
    auditor_firm?: string;
    framework: string;
    obs_start: string;
    obs_end: string;
    send_email?: boolean;
  }): Promise<AuditEngagement> {
    return this.request<AuditEngagement>("POST", "/audit-engagements", data);
  }

  async revokeAuditEngagement(id: string): Promise<void> {
    return this.request("DELETE", `/audit-engagements/${id}`);
  }

  async getAuditEngagementView(token: string): Promise<AuditEngagementView> {
    return this.requestPublic<AuditEngagementView>("GET", `/audit-engagements/view/${token}`);
  }

  async getEngagementComments(engagementId: string): Promise<AuditComment[]> {
    return this.request<AuditComment[]>("GET", `/audit-engagements/${engagementId}/comments`);
  }

  async addEngagementComment(engagementId: string, body: string): Promise<AuditComment> {
    return this.request<AuditComment>("POST", `/audit-engagements/${engagementId}/comments`, { body });
  }

  async getEngagementCommentsPublic(token: string): Promise<AuditComment[]> {
    return this.requestPublic<AuditComment[]>("GET", `/audit-engagements/by-token/${token}/comments`);
  }

  async addEngagementCommentPublic(token: string, body: string): Promise<AuditComment> {
    return this.requestPublic<AuditComment>("POST", `/audit-engagements/by-token/${token}/comments`, { body });
  }

  // ── Partner Directory ──────────────────────────────────────────────────────
  async getPartnerDirectory(partnerType?: "auditor" | "pen_test"): Promise<PartnerDirectoryEntry[]> {
    const params = partnerType ? `?partner_type=${partnerType}` : "";
    return this.requestPublic<PartnerDirectoryEntry[]>("GET", `/partner-directory${params}`);
  }

  // ── SoA ───────────────────────────────────────────────────────────────────
  async getSoa(): Promise<SoaItem[]> { return this.request("GET", "/soa"); }
  async initializeSoa(): Promise<SoaItem[]> { return this.request("POST", "/soa/initialize"); }
  async autoProgressSoa(): Promise<{ updated: number; integrations_scanned: number }> { return this.request("POST", "/soa/auto-progress"); }
  async updateSoaItem(id: string, data: Partial<SoaItem>): Promise<SoaItem> { return this.request("PATCH", `/soa/${id}`, data); }

  // ── RoPA ──────────────────────────────────────────────────────────────────
  async getRopaRecords(): Promise<RopaRecord[]> { return this.request("GET", "/ropa"); }
  async createRopaRecord(data: Partial<RopaRecord>): Promise<RopaRecord> { return this.request("POST", "/ropa", data); }
  async updateRopaRecord(id: string, data: Partial<RopaRecord>): Promise<RopaRecord> { return this.request("PATCH", `/ropa/${id}`, data); }
  async deleteRopaRecord(id: string): Promise<void> { return this.request("DELETE", `/ropa/${id}`); }
  async generateRopaFromFlows(): Promise<{ created: number; skipped: number }> { return this.request("POST", "/ropa/generate"); }

  // ── Data Breaches ─────────────────────────────────────────────────────────
  async getDataBreaches(): Promise<DataBreach[]> { return this.request("GET", "/data-breaches"); }
  async createDataBreach(data: Partial<DataBreach>): Promise<DataBreach> { return this.request("POST", "/data-breaches", data); }
  async updateDataBreach(id: string, data: Partial<DataBreach>): Promise<DataBreach> { return this.request("PATCH", `/data-breaches/${id}`, data); }
  async deleteDataBreach(id: string): Promise<void> { return this.request("DELETE", `/data-breaches/${id}`); }

  // ── Subject Requests ──────────────────────────────────────────────────────
  async getSubjectRequests(): Promise<SubjectRequest[]> { return this.request("GET", "/subject-requests"); }
  async createSubjectRequest(data: Partial<SubjectRequest>): Promise<SubjectRequest> { return this.request("POST", "/subject-requests", data); }
  async updateSubjectRequest(id: string, data: Partial<SubjectRequest>): Promise<SubjectRequest> { return this.request("PATCH", `/subject-requests/${id}`, data); }
  async deleteSubjectRequest(id: string): Promise<void> { return this.request("DELETE", `/subject-requests/${id}`); }

  // ── Management Reviews ────────────────────────────────────────────────────
  async getManagementReviews(): Promise<ManagementReview[]> { return this.request("GET", "/management-reviews"); }
  async createManagementReview(data: Partial<ManagementReview>): Promise<ManagementReview> { return this.request("POST", "/management-reviews", data); }
  async scheduleNextManagementReview(): Promise<ManagementReview> { return this.request<ManagementReview>("POST", "/management-reviews/schedule-next"); }
  async updateManagementReview(id: string, data: Partial<ManagementReview>): Promise<ManagementReview> { return this.request("PATCH", `/management-reviews/${id}`, data); }
  async deleteManagementReview(id: string): Promise<void> { return this.request("DELETE", `/management-reviews/${id}`); }

  // ── API Keys ──────────────────────────────────────────────────────────────
  async getApiKeys(): Promise<ApiKey[]> { return this.request("GET", "/api-keys"); }
  async createApiKey(name: string): Promise<{ id: string; name: string; key_prefix: string; raw_key: string; created_at: string }> { return this.request("POST", "/api-keys", { name }); }
  async revokeApiKey(id: string): Promise<void> { return this.request("DELETE", `/api-keys/${id}`); }

  // ── Super-Admin ───────────────────────────────────────────────────────────
  async superAdminListCompanies(): Promise<SuperAdminCompany[]> { return this.request("GET", "/super-admin/companies"); }
  async superAdminPatchCompany(id: string, data: { plan?: string; is_partner_account?: boolean; reset_subscription?: boolean }): Promise<SuperAdminCompany> { return this.request("PATCH", `/super-admin/companies/${id}`, data); }
  async superAdminDeleteCompany(id: string): Promise<void> { return this.request("DELETE", `/super-admin/companies/${id}`); }
  async superAdminListUsers(companyId: string): Promise<SuperAdminUser[]> { return this.request("GET", `/super-admin/companies/${companyId}/users`); }
  async superAdminPatchUser(companyId: string, userId: string, data: { role?: string; email_verified?: boolean }): Promise<SuperAdminUser> { return this.request("PATCH", `/super-admin/companies/${companyId}/users/${userId}`, data); }
  async superAdminDeleteUser(companyId: string, userId: string): Promise<void> { return this.request("DELETE", `/super-admin/companies/${companyId}/users/${userId}`); }
  async superAdminSeedDemo(companyId: string): Promise<{ integrations_added: number; integrations_skipped: number; evidence_upserted: number; added: string[] }> { return this.request("POST", `/super-admin/companies/${companyId}/seed-demo`); }
  async superAdminListPartnerDirectory(): Promise<PartnerDirectoryEntry[]> { return this.request("GET", "/super-admin/partner-directory"); }
  async superAdminCreatePartnerEntry(data: Omit<PartnerDirectoryEntry, "id"> & { is_active?: boolean }): Promise<PartnerDirectoryEntry> { return this.request("POST", "/super-admin/partner-directory", data); }
  async superAdminPatchPartnerEntry(id: string, data: Partial<Omit<PartnerDirectoryEntry, "id"> & { is_active: boolean }>): Promise<PartnerDirectoryEntry> { return this.request("PATCH", `/super-admin/partner-directory/${id}`, data); }
  async superAdminDeletePartnerEntry(id: string): Promise<void> { return this.request("DELETE", `/super-admin/partner-directory/${id}`); }
  async superAdminListToolLeads(): Promise<{ id: string; email: string; tool: string; created_at: string }[]> { return this.request("GET", "/super-admin/tool-leads"); }

  // ── Pen Test Agency Portal ────────────────────────────────────────────────
  async getPentestAgencyProfile(): Promise<PentestAgencyProfile> { return this.request("GET", "/pentest-agency/profile"); }
  async updatePentestAgencyProfile(data: Partial<Omit<PentestAgencyProfile, "id" | "company_id" | "is_verified" | "created_at" | "updated_at">>): Promise<PentestAgencyProfile> { return this.request("PATCH", "/pentest-agency/profile", data); }
  async getAgencyAssignments(params?: { status?: string }): Promise<AgencyAssignment[]> {
    const q = new URLSearchParams();
    if (params?.status) q.set("status", params.status);
    const qs = q.toString();
    return this.request("GET", `/pentest-agency/assignments${qs ? `?${qs}` : ""}`);
  }
  async getAgencyAssignment(id: string): Promise<AgencyAssignment> { return this.request("GET", `/pentest-agency/assignments/${id}`); }
  async updateAgencyAssignment(id: string, data: { status?: string; executive_summary?: string; report_url?: string; started_at?: string; completed_at?: string }): Promise<AgencyAssignment> { return this.request("PATCH", `/pentest-agency/assignments/${id}`, data); }
  async addAgencyFinding(testId: string, data: { title: string; severity?: string; description?: string | null; recommendation?: string | null; cvss_score?: number | null; cve_id?: string | null; ticket_url?: string | null }): Promise<AgencyFinding> { return this.request("POST", `/pentest-agency/assignments/${testId}/findings`, data); }
  async updateAgencyFinding(testId: string, findingId: string, data: Partial<AgencyFinding>): Promise<AgencyFinding> { return this.request("PATCH", `/pentest-agency/assignments/${testId}/findings/${findingId}`, data); }
  async deleteAgencyFinding(testId: string, findingId: string): Promise<void> { return this.request("DELETE", `/pentest-agency/assignments/${testId}/findings/${findingId}`); }
  async getAgencyTasks(): Promise<AgencyTask[]> { return this.request("GET", "/pentest-agency/tasks"); }
  async getPentestAgencyDirectory(): Promise<PentestAgencyProfile[]> { return this.request("GET", "/pentest-agency/directory", undefined, false); }

  // ── Evidence Export ───────────────────────────────────────────────────────
  async exportEvidenceCsv(params?: { control?: string; integration?: string }): Promise<void> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");
    const q = new URLSearchParams();
    if (params?.control) q.set("control", params.control);
    if (params?.integration) q.set("integration", params.integration);
    const qs = q.toString();
    const res = await fetch(`${API_URL}/v1/evidence/export${qs ? `?${qs}` : ""}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Export failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "evidence.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── AI Agent Events ───────────────────────────────────────────────────────

  async getAiAgentEvents(params?: { risk_level?: string; agent_type?: string; flagged_only?: boolean }): Promise<import("./types").AiAgentEvent[]> {
    const qs = params ? "?" + new URLSearchParams(Object.entries(params).filter(([, v]) => v !== undefined).map(([k, v]) => [k, String(v)])).toString() : "";
    return this.request("GET", `/ai-agent-events${qs}`);
  }

  async getAiAgentSessions(): Promise<import("./types").AiAgentSession[]> {
    return this.request("GET", "/ai-agent-events/sessions");
  }

  async createAiAgentEvent(body: Partial<import("./types").AiAgentEvent>): Promise<import("./types").AiAgentEvent> {
    return this.request("POST", "/ai-agent-events", body);
  }

  async updateAiAgentEvent(id: string, body: { is_flagged?: boolean; notes?: string; reviewed_by?: string }): Promise<import("./types").AiAgentEvent> {
    return this.request("PATCH", `/ai-agent-events/${id}`, body);
  }

  async deleteAiAgentEvent(id: string): Promise<void> {
    return this.request("DELETE", `/ai-agent-events/${id}`);
  }

  // ── Data Flows ────────────────────────────────────────────────────────────

  async getDataFlows(): Promise<import("./types").DataFlow[]> {
    return this.request("GET", "/data-flows");
  }

  async createDataFlow(body: Partial<import("./types").DataFlow>): Promise<import("./types").DataFlow> {
    return this.request("POST", "/data-flows", body);
  }

  async updateDataFlow(id: string, body: Partial<import("./types").DataFlow>): Promise<import("./types").DataFlow> {
    return this.request("PATCH", `/data-flows/${id}`, body);
  }

  async deleteDataFlow(id: string): Promise<void> {
    return this.request("DELETE", `/data-flows/${id}`);
  }

  async scanDataFlows(): Promise<import("./types").DataFlow[]> {
    return this.request("POST", "/data-flows/scan");
  }

  // ── Devices ───────────────────────────────────────────────────────────────

  async getDevices(): Promise<Device[]> {
    return this.request("GET", "/devices");
  }

  async createDevice(body: Partial<Device>): Promise<Device> {
    return this.request("POST", "/devices", body);
  }

  async updateDevice(id: string, body: Partial<Device>): Promise<Device> {
    return this.request("PATCH", `/devices/${id}`, body);
  }

  async deleteDevice(id: string): Promise<void> {
    return this.request("DELETE", `/devices/${id}`);
  }

  async attestDevice(body: {
    device_name: string;
    device_type: string;
    os_type: string;
    os_version?: string;
    serial_number?: string;
    disk_encrypted: boolean;
    lockscreen_enabled: boolean;
    antivirus_installed: boolean;
  }): Promise<Device> {
    return this.request("POST", "/devices/attest", body);
  }

  async getMyDevice(): Promise<Device | null> {
    return this.request("GET", "/devices/my");
  }

  // ── Trust Analytics ───────────────────────────────────────────────────────

  async getTrustAnalytics(): Promise<TrustAnalytics> {
    return this.request("GET", "/trust/analytics");
  }

  async verifyTrustDomain(): Promise<{ verified: boolean; message: string }> {
    return this.request("POST", "/trust/verify-domain");
  }

  // ── Questionnaire Sessions ────────────────────────────────────────────────

  async createQuestionnaireSession(body: {
    title: string;
    questionnaire_type?: string;
    answers: QuestionnaireSessionAnswer[];
    assigned_to_id?: string;
  }): Promise<QuestionnaireSession> {
    return this.request("POST", "/questionnaire/sessions", body);
  }

  async getQuestionnaireSessions(): Promise<QuestionnaireSession[]> {
    return this.request("GET", "/questionnaire/sessions");
  }

  async getQuestionnaireSession(id: string): Promise<QuestionnaireSession> {
    return this.request("GET", `/questionnaire/sessions/${id}`);
  }

  async updateQuestionnaireSession(
    id: string,
    body: { title?: string; status?: string; assigned_to_id?: string; answers?: QuestionnaireSessionAnswer[] }
  ): Promise<QuestionnaireSession> {
    return this.request("PATCH", `/questionnaire/sessions/${id}`, body);
  }

  async deleteQuestionnaireSession(id: string): Promise<void> {
    return this.request("DELETE", `/questionnaire/sessions/${id}`);
  }

  async getSessionComments(sessionId: string): Promise<QuestionnaireComment[]> {
    return this.request("GET", `/questionnaire/sessions/${sessionId}/comments`);
  }

  async addSessionComment(sessionId: string, questionIndex: number, text: string): Promise<QuestionnaireComment> {
    return this.request("POST", `/questionnaire/sessions/${sessionId}/comments`, {
      question_index: questionIndex,
      comment_text: text,
    });
  }

  // ── Questionnaire File Upload ─────────────────────────────────────────────

  async uploadQuestionnaire(file: File): Promise<void> {
    const token = this.getToken();
    if (!token) throw new Error("Not authenticated");
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(`${API_URL}/v1/questionnaire/upload`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    if (!res.ok) {
      const json = await res.json().catch(() => ({}));
      throw new Error((json as { detail?: string }).detail ?? "Upload failed");
    }
    // Download the answered file
    const blob = await res.blob();
    const disposition = res.headers.get("content-disposition") ?? "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] ?? "answered-questionnaire.csv";
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  }

  // ── Employee Portal ───────────────────────────────────────────────────────

  async getPortalTasks(): Promise<PortalTasksResponse> {
    return this.request("GET", "/portal/tasks");
  }

  async getPortalPolicy(slug: string): Promise<PolicyContentResponse> {
    return this.request("GET", `/portal/policies/${slug}`);
  }

  async signPolicy(slug: string): Promise<PolicyTaskItem> {
    return this.request("POST", `/portal/policies/${slug}/sign`);
  }

  // ── Slack Bot ─────────────────────────────────────────────────────────────

  async getSlackConfig(): Promise<SlackConfig | null> {
    return this.request("GET", "/slack/config");
  }

  async saveSlackConfig(data: { webhook_url: string; channel_name?: string; reminder_enabled: boolean }): Promise<SlackConfig> {
    return this.request("PUT", "/slack/config", data);
  }

  async testSlackWebhook(): Promise<{ ok: boolean; message: string }> {
    return this.request("POST", "/slack/test");
  }

  async sendSlackReminders(): Promise<{ ok: boolean; message: string }> {
    return this.request("POST", "/slack/send-reminders");
  }

  // ── Global Chat ──────────────────────────────────────────────────────────

  async listConversations(): Promise<ChatConversation[]> {
    return this.request("GET", "/chat/conversations");
  }

  async createConversation(): Promise<ChatConversation> {
    return this.request("POST", "/chat/conversations");
  }

  async getConversation(id: string): Promise<ChatConversationWithMessages> {
    return this.request("GET", `/chat/conversations/${id}`);
  }

  async renameConversation(id: string, title: string): Promise<ChatConversation> {
    return this.request("PATCH", `/chat/conversations/${id}`, { title });
  }

  async deleteConversation(id: string): Promise<void> {
    return this.request("DELETE", `/chat/conversations/${id}`);
  }

  async sendChatMessage(convId: string, content: string): Promise<{
    user_message: { id: string; role: string; content: string; created_at: string };
    assistant_message: { id: string; role: string; content: string; created_at: string };
    conversation_title: string;
  }> {
    return this.request("POST", `/chat/conversations/${convId}/messages`, { content });
  }

  // ── Policy generation ────────────────────────────────────────────────────

  async generatePolicy(slug: string): Promise<{ content: string }> {
    return this.request("POST", `/policies/${slug}/generate`);
  }

  // ── Access reviews v2 (campaign-based with per-user items) ───────────────

  async getAccessReviewsV2(): Promise<any[]> { return this.request("GET", "/access-reviews-v2"); }
  async createAccessReviewV2(body: { name: string; framework?: string; review_period?: string; due_date?: string }): Promise<any> { return this.request("POST", "/access-reviews-v2", body); }
  async getAccessReviewV2(id: string): Promise<any> { return this.request("GET", `/access-reviews-v2/${id}`); }
  async addAccessReviewItemV2(reviewId: string, body: { user_email: string; user_name?: string; system_name: string; role_or_permission?: string }): Promise<any> { return this.request("POST", `/access-reviews-v2/${reviewId}/items`, body); }
  async updateAccessReviewItemV2(reviewId: string, itemId: string, body: { decision: string; notes?: string }): Promise<any> { return this.request("PATCH", `/access-reviews-v2/${reviewId}/items/${itemId}`, body); }
  async deleteAccessReviewItemV2(reviewId: string, itemId: string): Promise<void> { return this.request("DELETE", `/access-reviews-v2/${reviewId}/items/${itemId}`); }
  async completeAccessReviewV2(reviewId: string): Promise<any> { return this.request("POST", `/access-reviews-v2/${reviewId}/complete`); }
  async deleteAccessReviewV2(id: string): Promise<void> { return this.request("DELETE", `/access-reviews-v2/${id}`); }

  // ── Devices v2 (MDM-aware endpoint tracking) ────────────────────────────

  async getDevicesV2(): Promise<any[]> { return this.request("GET", "/devices-v2"); }
  async getDeviceStatsV2(): Promise<any> { return this.request("GET", "/devices-v2/stats"); }
  async createDeviceV2(body: any): Promise<any> { return this.request("POST", "/devices-v2", body); }
  async updateDeviceV2(id: string, body: any): Promise<any> { return this.request("PATCH", `/devices-v2/${id}`, body); }
  async deleteDeviceV2(id: string): Promise<void> { return this.request("DELETE", `/devices-v2/${id}`); }

  // ── Pen tests v2 (with per-finding tracking) ────────────────────────────

  async getPenTestsV2(): Promise<any[]> { return this.request("GET", "/pen-tests-v2"); }
  async createPenTestV2(body: any): Promise<any> { return this.request("POST", "/pen-tests-v2", body); }
  async getPenTestV2(id: string): Promise<any> { return this.request("GET", `/pen-tests-v2/${id}`); }
  async updatePenTestV2(id: string, body: any): Promise<any> { return this.request("PATCH", `/pen-tests-v2/${id}`, body); }
  async deletePenTestV2(id: string): Promise<void> { return this.request("DELETE", `/pen-tests-v2/${id}`); }
  async addPenTestFindingV2(testId: string, body: any): Promise<any> { return this.request("POST", `/pen-tests-v2/${testId}/findings`, body); }
  async updatePenTestFindingV2(testId: string, findingId: string, body: any): Promise<any> { return this.request("PATCH", `/pen-tests-v2/${testId}/findings/${findingId}`, body); }
  async deletePenTestFindingV2(testId: string, findingId: string): Promise<void> { return this.request("DELETE", `/pen-tests-v2/${testId}/findings/${findingId}`); }

  // ── Custom frameworks ──────────────────────────────────────────────────────
  async getCustomFrameworks(): Promise<any[]> { return this.request("GET", "/custom-frameworks"); }
  async createCustomFramework(body: { name: string; description?: string; version?: string }): Promise<any> { return this.request("POST", "/custom-frameworks", body); }
  async getCustomFramework(id: string): Promise<any> { return this.request("GET", `/custom-frameworks/${id}`); }
  async updateCustomFramework(id: string, body: any): Promise<any> { return this.request("PATCH", `/custom-frameworks/${id}`, body); }
  async deleteCustomFramework(id: string): Promise<void> { return this.request("DELETE", `/custom-frameworks/${id}`); }
  async addCustomControl(frameworkId: string, body: any): Promise<any> { return this.request("POST", `/custom-frameworks/${frameworkId}/controls`, body); }
  async updateCustomControl(frameworkId: string, controlId: string, body: any): Promise<any> { return this.request("PATCH", `/custom-frameworks/${frameworkId}/controls/${controlId}`, body); }
  async deleteCustomControl(frameworkId: string, controlId: string): Promise<void> { return this.request("DELETE", `/custom-frameworks/${frameworkId}/controls/${controlId}`); }
  async getCustomFrameworkScore(id: string): Promise<any> { return this.request("GET", `/custom-frameworks/${id}/score`); }

  // ── Change management ──────────────────────────────────────────────────────
  async getChangeRequests(params?: { status?: string; change_type?: string; risk_level?: string }): Promise<any[]> {
    const q = params ? "?" + new URLSearchParams(Object.fromEntries(Object.entries(params).filter(([, v]) => v))).toString() : "";
    return this.request("GET", `/change-requests${q}`);
  }
  async getChangeRequestStats(): Promise<any> { return this.request("GET", "/change-requests/stats"); }
  async createChangeRequest(body: any): Promise<any> { return this.request("POST", "/change-requests", body); }
  async updateChangeRequest(id: string, body: any): Promise<any> { return this.request("PATCH", `/change-requests/${id}`, body); }
  async submitChangeRequest(id: string): Promise<any> { return this.request("POST", `/change-requests/${id}/submit`); }
  async approveChangeRequest(id: string, body: { approver_name: string; approver_email?: string }): Promise<any> { return this.request("POST", `/change-requests/${id}/approve`, body); }
  async rejectChangeRequest(id: string, body: { rejection_reason: string }): Promise<any> { return this.request("POST", `/change-requests/${id}/reject`, body); }
  async startChangeRequest(id: string): Promise<any> { return this.request("POST", `/change-requests/${id}/start`); }
  async deployChangeRequest(id: string): Promise<any> { return this.request("POST", `/change-requests/${id}/deploy`); }
  async failChangeRequest(id: string): Promise<any> { return this.request("POST", `/change-requests/${id}/fail`); }
  async closeChangeRequest(id: string): Promise<any> { return this.request("POST", `/change-requests/${id}/close`); }
  async deleteChangeRequest(id: string): Promise<void> { return this.request("DELETE", `/change-requests/${id}`); }
}

export const api = new ApiClient();
