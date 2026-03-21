import type { AccessReview, AppNotification, Asset, AutofillResult, AuditLog, AuditSession, BackgroundCheck, BcpRecord, BillingInfo, Company, ComplianceScore, DataBreach, Document, DownloadResponse, Evidence, EvidenceActivityPoint, Incident, Integration, Invitation, ManagementReview, ManualControl, Member, NotificationSettings, Offboarding, Page, PartnerClient, PartnerSwitchResponse, PartnerTrustCenterInfo, PenTest, Policy, PublicAuditView, PublicTrustPageView, QuestionnaireResult, QuestionnaireType, ReadinessData, Report, Risk, RopaRecord, ScoreHistoryPoint, SoaItem, SubjectRequest, TrainingRecord, TrustPageSettings, User, Vendor, Vulnerability } from "./types";

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

  // ── Auth ────────────────────────────────────────────────────────────────

  async register(email: string, password: string, companyName: string, accountType: "company" | "partner" = "company"): Promise<void> {
    const data = await this.request<{ access_token: string; refresh_token: string }>(
      "POST", "/auth/register",
      { email, password, company_name: companyName, account_type: accountType },
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

  async updateCompany(name: string): Promise<Company> {
    return this.request<Company>("PATCH", "/org/company", { name });
  }

  async completeOnboarding(): Promise<void> {
    return this.request("POST", "/org/onboarding/complete");
  }

  // ── Compliance ───────────────────────────────────────────────────────────

  async getComplianceScore(framework = "soc2"): Promise<ComplianceScore> {
    return this.request<ComplianceScore>("GET", `/compliance/score?framework=${framework}`);
  }

  async getScoreHistory(framework = "soc2", days = 30): Promise<ScoreHistoryPoint[]> {
    return this.request<ScoreHistoryPoint[]>("GET", `/compliance/score-history?framework=${framework}&days=${days}`);
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

  async assignManualControl(controlId: string, framework: string, ownerUserId: string | null): Promise<ManualControl> {
    return this.request<ManualControl>("PATCH", `/compliance/manual-controls/${controlId}/assign?framework=${framework}`, { owner_user_id: ownerUserId });
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

  // ── SoA ───────────────────────────────────────────────────────────────────
  async getSoa(): Promise<SoaItem[]> { return this.request("GET", "/soa"); }
  async initializeSoa(): Promise<SoaItem[]> { return this.request("POST", "/soa/initialize"); }
  async updateSoaItem(id: string, data: Partial<SoaItem>): Promise<SoaItem> { return this.request("PATCH", `/soa/${id}`, data); }

  // ── RoPA ──────────────────────────────────────────────────────────────────
  async getRopaRecords(): Promise<RopaRecord[]> { return this.request("GET", "/ropa"); }
  async createRopaRecord(data: Partial<RopaRecord>): Promise<RopaRecord> { return this.request("POST", "/ropa", data); }
  async updateRopaRecord(id: string, data: Partial<RopaRecord>): Promise<RopaRecord> { return this.request("PATCH", `/ropa/${id}`, data); }
  async deleteRopaRecord(id: string): Promise<void> { return this.request("DELETE", `/ropa/${id}`); }

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
  async updateManagementReview(id: string, data: Partial<ManagementReview>): Promise<ManagementReview> { return this.request("PATCH", `/management-reviews/${id}`, data); }
  async deleteManagementReview(id: string): Promise<void> { return this.request("DELETE", `/management-reviews/${id}`); }
}

export const api = new ApiClient();
