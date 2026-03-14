import type { AuditLog, BillingInfo, Company, ComplianceScore, DownloadResponse, Evidence, EvidenceActivityPoint, Integration, Invitation, ManualControl, Member, Page, Report, ScoreHistoryPoint, User } from "./types";

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

    if (res.status === 401 && !isRetry) {
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

  async register(email: string, password: string, companyName: string): Promise<void> {
    const data = await this.request<{ access_token: string; refresh_token: string }>(
      "POST", "/auth/register",
      { email, password, company_name: companyName },
      false,
    );
    this.setTokens(data.access_token, data.refresh_token);
  }

  async login(email: string, password: string): Promise<void> {
    const data = await this.request<{ access_token: string; refresh_token: string }>(
      "POST", "/auth/login",
      { email, password },
      false,
    );
    this.setTokens(data.access_token, data.refresh_token);
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

  async downloadReport(id: string): Promise<DownloadResponse> {
    return this.request<DownloadResponse>("GET", `/reports/${id}/download`);
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

  // ── Settings ─────────────────────────────────────────────────────────────

  async getCompany(): Promise<Company> {
    return this.request<Company>("GET", "/org/company");
  }

  async updateCompany(name: string): Promise<Company> {
    return this.request<Company>("PATCH", "/org/company", { name });
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

  async getBillingPortal(): Promise<{ portal_url: string }> {
    return this.request<{ portal_url: string }>("POST", "/billing/portal");
  }
}

export const api = new ApiClient();
