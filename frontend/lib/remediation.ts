// Remediation guides for compliance controls
// Keyed by missing evidence type or control category

export interface RemediationGuide {
  title: string;
  urgency: "critical" | "high" | "medium";
  steps: string[];
  hint?: string;
}

// Maps evidence type strings (from missing_types) → actionable fix steps
export const EVIDENCE_REMEDIATION: Record<string, RemediationGuide> = {
  // AWS
  iam_users: {
    title: "AWS IAM Users",
    urgency: "critical",
    steps: [
      "Open AWS IAM → Users and review all active accounts",
      "Enable MFA for every user with AWS Console access",
      "Remove or disable access keys older than 90 days",
      "Apply a strong account password policy (12+ chars, rotation enabled)",
      "Connect your AWS integration in TraceLayer to automate this evidence",
    ],
    hint: "IAM evidence covers SOC 2 CC6.1 and ISO 27001 A.9",
  },
  cloudtrail_events: {
    title: "AWS CloudTrail Logs",
    urgency: "critical",
    steps: [
      "Enable CloudTrail in all AWS regions (not just us-east-1)",
      "Enable log file validation to detect tampering",
      "Send CloudTrail logs to an S3 bucket with versioning and MFA-delete enabled",
      "Set up a CloudWatch alarm for root account usage",
    ],
    hint: "CloudTrail covers SOC 2 CC7 monitoring controls",
  },
  s3_buckets: {
    title: "AWS S3 Bucket Configuration",
    urgency: "high",
    steps: [
      "Enable S3 Block Public Access at the account level",
      "Enable default encryption (SSE-S3 or SSE-KMS) on all buckets",
      "Enable access logging on buckets containing sensitive data",
      "Review and remove any public bucket policies",
    ],
  },
  password_policy: {
    title: "AWS Account Password Policy",
    urgency: "high",
    steps: [
      "Go to IAM → Account settings → Password policy",
      "Require minimum 12 characters",
      "Enable uppercase, lowercase, numbers, and symbols",
      "Set password expiry to 90 days and prevent reuse of last 24 passwords",
    ],
  },

  // GitHub
  repositories: {
    title: "GitHub Repository Security",
    urgency: "high",
    steps: [
      "Enable branch protection on all main/production branches",
      "Require at least 1 approved review before merging",
      "Enable required status checks (CI must pass before merge)",
      "Disable force-pushes and branch deletion on protected branches",
      "Enable secret scanning and Dependabot alerts",
    ],
    hint: "Repository evidence covers SOC 2 CC8 change management",
  },
  audit_log: {
    title: "GitHub Audit Log",
    urgency: "high",
    steps: [
      "Enable GitHub audit log streaming (requires GitHub Enterprise)",
      "Review the audit log monthly for unexpected permission changes",
      "Set up a GitHub App or webhook to capture audit events",
    ],
  },

  // Slack
  audit_logs: {
    title: "Slack Audit Logs",
    urgency: "medium",
    steps: [
      "Upgrade to Slack Business+ or Enterprise Grid to access audit logs",
      "Enable the Audit Logs API and stream events to your SIEM",
      "Review the audit log monthly for suspicious logins or data exports",
    ],
  },

  // Google Workspace
  admin_activity: {
    title: "Google Workspace Admin Activity",
    urgency: "high",
    steps: [
      "Go to Admin Console → Reports → Audit → Admin",
      "Enable alert policies for suspicious admin actions",
      "Review admin activity logs monthly",
      "Restrict super-admin accounts to dedicated accounts with hardware MFA",
    ],
  },
  users: {
    title: "User Account Review",
    urgency: "critical",
    steps: [
      "Review all active user accounts and remove departed employees immediately",
      "Enable MFA enforcement for all users in your identity provider",
      "Implement quarterly access reviews with documented sign-off",
      "Set up automated de-provisioning tied to your HR system",
    ],
  },

  // Okta
  system_log: {
    title: "Okta System Log",
    urgency: "high",
    steps: [
      "Enable Okta System Log streaming to your SIEM or a storage bucket",
      "Set up Okta Workflows to alert on suspicious authentication events",
      "Review failed login attempts and impossible travel alerts weekly",
    ],
  },
  policies: {
    title: "Okta Authentication Policies",
    urgency: "critical",
    steps: [
      "Create a Global Session Policy requiring MFA for all applications",
      "Enforce phishing-resistant MFA (WebAuthn/FIDO2) for admin users",
      "Set session lifetime to 8 hours max for sensitive applications",
      "Enable Okta ThreatInsight to block suspicious IPs automatically",
    ],
  },

  // Jira
  projects: {
    title: "Jira Project Access",
    urgency: "medium",
    steps: [
      "Audit project-level permissions and remove users with unnecessary access",
      "Use Jira permission schemes instead of individual user grants",
      "Review and restrict 'Anyone' or 'Service Account' level project access",
    ],
  },

  // Azure AD
  azure_users: {
    title: "Azure Active Directory Users",
    urgency: "critical",
    steps: [
      "Enable Conditional Access policies requiring MFA for all users",
      "Enable Azure AD Identity Protection and review risky sign-ins",
      "Enable Privileged Identity Management (PIM) for admin role activation",
      "Review guest users and remove those with no recent activity",
    ],
  },
};

// Fallback guides by control category when evidence type isn't recognised
export const CATEGORY_REMEDIATION: Record<string, RemediationGuide> = {
  "Access Control": {
    title: "Access Control",
    urgency: "critical",
    steps: [
      "Enforce MFA across all cloud providers and SaaS tools",
      "Implement quarterly documented user access reviews",
      "Apply least-privilege: remove permissions that aren't actively needed",
      "Automate de-provisioning when employees leave",
      "Document all privileged (admin) accounts and justify their access",
    ],
  },
  "Logging & Monitoring": {
    title: "Logging & Monitoring",
    urgency: "critical",
    steps: [
      "Enable audit logging on every system that touches production data",
      "Centralise logs in a tamper-proof location (CloudTrail → S3, Datadog, etc.)",
      "Set up alerts for suspicious events: root login, permission escalation, data exports",
      "Define a log retention policy (minimum 12 months for SOC 2)",
      "Review logs at a defined cadence (weekly minimum for production systems)",
    ],
  },
  "Change Management": {
    title: "Change Management",
    urgency: "high",
    steps: [
      "Require peer code review for all changes to production branches",
      "Enable branch protection rules with required approvals",
      "Gate deployments on passing CI checks (tests, linting, security scans)",
      "Document your deployment process and keep a deployment log",
      "Separate production deployment access from development access",
    ],
  },
  "Data Protection": {
    title: "Data Protection",
    urgency: "critical",
    steps: [
      "Enable encryption at rest for all databases and object storage",
      "Enforce TLS 1.2+ for all data in transit",
      "Inventory where sensitive data lives (PII, credentials, financial data)",
      "Implement data retention and deletion policies",
      "Scan infrastructure for exposed secrets (GitHub secret scanning, etc.)",
    ],
  },
  "Availability": {
    title: "Availability & Backup",
    urgency: "high",
    steps: [
      "Automate daily backups with success/failure notifications",
      "Test recovery from backup at least annually and document the results",
      "Define RTO (Recovery Time Objective) and RPO (Recovery Point Objective)",
      "Set up uptime monitoring with alerting for your production services",
      "Document your business continuity plan and share it with the team",
    ],
  },
  "Incident Response": {
    title: "Incident Response",
    urgency: "high",
    steps: [
      "Write and publish an Incident Response Plan (IRP) in your wiki",
      "Define severity levels and escalation paths",
      "Run a tabletop exercise annually — document the date and participants",
      "Create runbooks for your most likely incidents (data breach, outage, etc.)",
      "Establish a post-mortem process to capture learnings after each incident",
    ],
  },
  "Vendor Management": {
    title: "Vendor Risk Management",
    urgency: "medium",
    steps: [
      "Inventory all vendors who access your data or infrastructure",
      "Collect a SOC 2 report or security questionnaire from each critical vendor annually",
      "Include security requirements in vendor contracts and MSAs",
      "Review vendor access annually and revoke when no longer needed",
    ],
  },
};

export function getRemediationForMissingType(missingType: string): RemediationGuide | null {
  return EVIDENCE_REMEDIATION[missingType] ?? null;
}

export function getRemediationForCategory(category: string): RemediationGuide | null {
  return CATEGORY_REMEDIATION[category] ?? null;
}
