# SECURITY AUDIT & INFRASTRUCTURE TRUST ASSESSMENT REPORT

---

```
DOCUMENT CLASSIFICATION:   CONFIDENTIAL — RESTRICTED DISTRIBUTION
PREPARED FOR:              [Partner Organization Name]
PREPARED BY:               Meridian Security Advisors LLC
                           Infrastructure & Cloud Security Practice
ENGAGEMENT CODE:           MSA-2025-TL-0094
REPORT VERSION:            1.0 — FINAL
REPORT DATE:               April 28, 2025
ASSESSMENT PERIOD:         February 3, 2025 – April 18, 2025
```

---

> **Disclaimer:** This report has been prepared solely for the use of the named recipient and may not be reproduced, distributed, or disclosed to any third party without the prior written consent of Meridian Security Advisors LLC and TraceLayer Inc. The findings, opinions, and recommendations expressed in this document represent the professional judgment of Meridian Security Advisors LLC based on information made available during the assessment period. This report does not constitute a guarantee of security or an absence of undisclosed vulnerabilities.

---

## TABLE OF CONTENTS

1. [Engagement Overview](#1-engagement-overview)
2. [Executive Summary](#2-executive-summary)
3. [Methodology & Scope](#3-methodology--scope)
4. [Infrastructure & Data Residency](#4-infrastructure--data-residency)
5. [Access Control Review](#5-access-control-review)
6. [Application Security Assessment](#6-application-security-assessment)
7. [Compliance Posture & Controls Coverage](#7-compliance-posture--controls-coverage)
8. [Incident Response & Business Continuity](#8-incident-response--business-continuity)
9. [Third-Party & Supply Chain Risk](#9-third-party--supply-chain-risk)
10. [Data Privacy & Regulatory Alignment](#10-data-privacy--regulatory-alignment)
11. [Findings Summary & Risk Register](#11-findings-summary--risk-register)
12. [Summary & Conclusion](#12-summary--conclusion)
13. [Assessor Attestation](#13-assessor-attestation)
14. [Appendices](#14-appendices)

---

## 1. ENGAGEMENT OVERVIEW

### 1.1 Engaging Parties

| Field | Details |
|---|---|
| **Client Organization** | TraceLayer Inc. |
| **Platform Name** | TraceLayer Compliance Automation Platform |
| **Platform URL** | tracelayer.it.com |
| **Requesting Party** | [Partner Organization Name] |
| **Requesting Party Role** | Prospective White-Label Distribution Partner |
| **Assessing Firm** | Meridian Security Advisors LLC |
| **Lead Assessor** | Daniel R. Hargrove, CISSP, CISM, ISO 27001 Lead Auditor |
| **Supporting Analysts** | Sarah L. Kim, CEH, OSCP; Thomas B. Wren, CCSP, AWS-SAA |
| **Engagement Type** | Infrastructure Trust & Security Posture Assessment |
| **Assessment Basis** | SOC 2 Trust Service Criteria (AICPA TSC 2017), ISO/IEC 27001:2022, NIST SP 800-53 Rev. 5, CIS AWS Foundations Benchmark v2.0 |

### 1.2 Purpose of Engagement

This assessment was commissioned by [Partner Organization Name] (hereinafter "the Partner") as part of its vendor due diligence process prior to executing a white-label reseller agreement with TraceLayer Inc. (hereinafter "TraceLayer"). The Partner required independent validation of TraceLayer's security posture, data handling practices, infrastructure controls, and overall suitability for deployment within a regulated compliance consulting environment serving enterprise clients.

Meridian Security Advisors LLC was retained as an independent third-party assessor with no prior commercial relationship with TraceLayer. This report represents the unbiased findings of that assessment.

### 1.3 Scope of Assessment

The following systems, processes, and domains were included in this assessment:

- Production cloud infrastructure hosted on Amazon Web Services (AWS)
- Application layer security (API services, frontend application, background processing)
- Identity and access management controls
- Data-at-rest and data-in-transit encryption implementations
- Multi-tenancy architecture and tenant data isolation
- Third-party integration architecture (OAuth/API credential handling)
- Vulnerability management and secure development lifecycle processes
- Incident response and business continuity planning
- Compliance monitoring capabilities (the platform's own continuous compliance posture)
- Data privacy controls and regulatory alignment (GDPR, HIPAA, CCPA)

The following were explicitly **out of scope** for this engagement:
- Physical facility assessments (TraceLayer operates in a fully cloud-native model)
- Financial or legal audits
- Social engineering or phishing simulation exercises
- Customer-side implementations or integrations deployed by end users

---

## 2. EXECUTIVE SUMMARY

### 2.1 Overall Security Rating

```
╔══════════════════════════════════════════════════════════════════╗
║                    OVERALL SECURITY RATING                      ║
║                                                                  ║
║                           A  /  HIGH                            ║
║                                                                  ║
║   Infrastructure Maturity:       ████████████░░   STRONG        ║
║   Application Security:          ██████████░░░░   GOOD          ║
║   Access Control:                ████████████░░   STRONG        ║
║   Compliance Alignment:          █████████████░   STRONG        ║
║   Incident Readiness:            ████████████░░   STRONG        ║
║   Data Privacy:                  ████████████░░   STRONG        ║
╚══════════════════════════════════════════════════════════════════╝
```

**Assessment Date:** April 28, 2025
**Assessment Basis:** 74-day active assessment period (February 3 – April 18, 2025)
**Critical Findings:** 0
**High Findings:** 0
**Medium Findings:** 2 (both with documented remediation timelines)
**Low / Informational Findings:** 5

### 2.2 Summary Statement

Meridian Security Advisors LLC has completed a comprehensive security and infrastructure trust assessment of the TraceLayer Compliance Automation Platform. The assessment encompassed cloud infrastructure architecture review, application security testing, access control evaluation, compliance posture analysis, and business continuity planning review.

TraceLayer demonstrates a **mature, defense-in-depth security posture** appropriate for an enterprise-grade SaaS platform operating in the compliance technology sector. The platform's infrastructure is entirely hosted within AWS US-East-1 (N. Virginia), with all data encrypted at rest using AES-256 and in transit using TLS 1.2 or higher. No production data is replicated, cached, or transmitted outside of United States jurisdiction under standard operating conditions.

The platform's zero-knowledge integration architecture — whereby third-party OAuth tokens and API credentials are stored in encrypted form and used exclusively for read-only data collection — represents a notably security-conscious design decision that materially reduces the risk profile of the platform for both TraceLayer and its customers.

TraceLayer operates its own continuous compliance monitoring against SOC 2 Type II and ISO 27001:2022 control sets, meaning the platform continuously validates its own security posture using the same automated evidence collection capabilities it sells to customers. This "eat your own cooking" approach provides a higher degree of assurance than periodic manual review alone.

The two medium-severity findings identified during this engagement relate to API rate-limit logging granularity and an opportunistic hardening recommendation for container image base layers. Both findings have documented remediation plans with timelines acceptable to Meridian's assessors.

**Based on the totality of evidence reviewed, Meridian Security Advisors LLC finds that TraceLayer's platform meets enterprise security standards and is suitable for white-label deployment within a compliance consulting firm's service portfolio, including delivery to clients pursuing SOC 2, ISO 27001, GDPR, HIPAA, and NIS2 certification.**

---

## 3. METHODOLOGY & SCOPE

### 3.1 Assessment Methodology

Meridian Security Advisors LLC conducted this assessment using a risk-based methodology aligned to the following frameworks:

| Framework | Application in This Engagement |
|---|---|
| **NIST SP 800-53 Rev. 5** | Primary control catalog for technical and operational security controls |
| **AICPA TSC 2017 (SOC 2)** | Trust Service Criteria for availability, confidentiality, processing integrity, security, and privacy |
| **ISO/IEC 27001:2022** | Annex A controls mapped to observed TraceLayer practices |
| **CIS AWS Foundations Benchmark v2.0** | Cloud infrastructure configuration review baseline |
| **OWASP Application Security Verification Standard (ASVS) v4.0** | Application-layer security testing standard |

### 3.2 Evidence Collection Activities

The following activities were conducted during the assessment period:

**Documentation Review**
- Review of infrastructure architecture diagrams and network topology documentation
- Examination of information security policies, standards, and procedures (15 policy documents reviewed)
- Analysis of access control matrices and user provisioning records
- Review of vulnerability scan reports (Q4 2024 and Q1 2025)
- Examination of penetration testing report from independent firm (conducted November 2024)
- Review of incident response plan documentation and tabletop exercise records
- Analysis of backup and recovery procedures and test results
- Review of third-party vendor risk assessments

**Technical Testing**
- Authenticated and unauthenticated API security testing (OWASP ASVS Level 2)
- Cloud infrastructure configuration review (AWS Config, IAM, Security Hub, GuardDuty)
- Static analysis of representative application code modules (with TraceLayer's consent)
- Container image scanning review (validation of CI/CD pipeline outputs)
- Network perimeter review (security group configurations, public exposure analysis)
- Authentication mechanism testing (JWT implementation, session management, MFA enforcement)
- Multi-tenant isolation testing (cross-tenant data access attempt simulation)

**Interviews**
- CTO / Lead Architect: infrastructure architecture, security design decisions
- Engineering Lead: SDLC practices, code review, deployment pipeline
- Operations Lead: monitoring, alerting, incident response, backup procedures

### 3.3 Limitations & Assumptions

- This assessment is point-in-time and reflects the state of TraceLayer's systems and controls as observed between February 3 and April 18, 2025.
- Technical testing was limited to non-destructive techniques and did not include active exploitation of identified vulnerabilities.
- Assessors relied on documentation and verbal representations provided by TraceLayer personnel, which were validated through technical testing where feasible but not independently verified through source code audit of all modules.
- This report does not constitute a SOC 2 audit or ISO 27001 certification; those require formal processes governed by accredited bodies.

---

## 4. INFRASTRUCTURE & DATA RESIDENCY

### 4.1 Cloud Infrastructure Architecture

TraceLayer operates an entirely cloud-native infrastructure hosted exclusively on Amazon Web Services. There are no on-premises components, co-located servers, or hybrid infrastructure arrangements in scope.

**Primary Region:** `us-east-1` (N. Virginia, United States)
**Disaster Recovery / Backup Region:** `us-west-2` (Oregon, United States)
**Infrastructure-as-Code:** All infrastructure is provisioned and managed via infrastructure-as-code tooling, enabling reproducible, auditable environment configurations.
**Environment Separation:** Production, staging, and development environments are logically and network-isolated within separate AWS accounts using AWS Organizations.

| Infrastructure Component | Technology | Location |
|---|---|---|
| Application Servers | AWS EC2 / ECS (containerized) | us-east-1 |
| API Services | AWS ECS Fargate | us-east-1 |
| Primary Database | Amazon RDS (PostgreSQL) | us-east-1 |
| Object Storage | Amazon S3 | us-east-1 |
| Background Job Processing | AWS ECS (task-based) | us-east-1 |
| CDN / Edge | AWS CloudFront | Global CDN (US-origin) |
| DNS | AWS Route 53 | Global |
| Backup Storage | Amazon S3 (replicated) | us-west-2 |
| Secrets Management | AWS Secrets Manager | us-east-1 |
| Monitoring & Logging | Amazon CloudWatch + AWS CloudTrail | us-east-1 |

### 4.2 Data Residency Confirmation

A core requirement identified by the Partner was verification that all customer data — including compliance evidence, control mappings, audit logs, and integration credentials — remains within United States geographic boundaries.

**Finding:** Meridian assessors reviewed AWS service configurations, S3 bucket policies, RDS instance settings, and CloudFront distribution origin configurations. No data replication, cross-border transfer, or third-party data processor arrangement was identified that would result in customer data leaving the United States under normal operating conditions.

| Data Category | Storage Location | Replication | Cross-Border Transfer |
|---|---|---|---|
| Compliance evidence records | AWS S3 us-east-1 | DR copy to us-west-2 | None |
| Database records (tenants, controls) | AWS RDS us-east-1 | AWS automated replicas within region | None |
| Audit package PDFs | AWS S3 us-east-1 | None in production | None |
| Integration credentials (encrypted) | AWS RDS / Secrets Manager us-east-1 | None | None |
| Application logs | AWS CloudWatch us-east-1 | None | None |
| User session data | AWS RDS / in-memory cache us-east-1 | None | None |

> **Assessor Note:** CloudFront, as a global CDN, may serve static frontend assets (HTML, CSS, JavaScript) from edge locations outside the United States. This is standard for all CDN-delivered web applications and does not constitute data residency exposure, as no customer data is present in edge caches — only static application code. This architecture is consistent with industry norms.

### 4.3 Encryption at Rest

All production data stores were confirmed to use encryption at rest:

| Data Store | Encryption Standard | Key Management |
|---|---|---|
| Amazon RDS (PostgreSQL) | AES-256 (AWS KMS-managed) | AWS KMS Customer Managed Key |
| Amazon S3 (primary) | AES-256 (SSE-S3 / SSE-KMS) | AWS KMS Customer Managed Key |
| Amazon S3 (backup) | AES-256 (SSE-S3 / SSE-KMS) | AWS KMS Customer Managed Key |
| EBS volumes (EC2/ECS) | AES-256 (AWS KMS-managed) | AWS KMS |
| Secrets Manager | AES-256 | AWS KMS |
| Third-party credentials (app-layer) | Fernet symmetric encryption (AES-128-CBC + HMAC-SHA256) | Application-managed key derivation |

**Finding:** Encryption at rest is comprehensively implemented across all storage tiers. The additional application-layer encryption of third-party integration credentials (OAuth tokens, API keys) using Fernet encryption before database storage represents a defense-in-depth approach: credentials are encrypted both at the AWS infrastructure layer (AES-256 KMS) and at the application layer, such that compromise of the database alone would not yield usable credentials.

### 4.4 Encryption in Transit

| Connection Type | Protocol | Minimum Version | Certificate Management |
|---|---|---|---|
| End-user to application | HTTPS/TLS | TLS 1.2 (TLS 1.3 preferred) | AWS Certificate Manager (auto-renew) |
| API client to API service | HTTPS/TLS | TLS 1.2 | AWS Certificate Manager |
| Application to RDS database | TLS | TLS 1.2 | AWS-managed RDS certificate |
| Application to S3 | HTTPS/TLS | TLS 1.2 | AWS-managed |
| Application to third-party APIs | HTTPS/TLS | Provider-dependent (≥ TLS 1.2) | System trust store |
| Internal service-to-service | HTTPS/TLS (within VPC) | TLS 1.2 | AWS Certificate Manager |

**Finding:** No plaintext communication channels were identified in production traffic patterns. HTTP requests are redirected to HTTPS at the load balancer layer. TLS 1.0 and 1.1 are disabled on all public-facing endpoints. Assessors confirmed cipher suite configurations exclude known-weak ciphers (RC4, 3DES, NULL ciphers).

### 4.5 Network Security Architecture

The production VPC employs a multi-layer network security model:

- **Public Subnet:** Application Load Balancer only. No application servers reside in the public subnet.
- **Private Application Subnet:** ECS tasks / EC2 instances. Outbound internet access via NAT Gateway only.
- **Private Data Subnet:** RDS instances and Secrets Manager VPC endpoint. No direct internet connectivity.
- **Security Groups:** Least-privilege rules. Database security groups permit inbound connections only from application-tier security groups. No `0.0.0.0/0` inbound rules on non-public-facing resources.
- **AWS WAF:** Deployed on Application Load Balancer. OWASP Core Rule Set enabled. Rate limiting rules configured.
- **AWS Shield Standard:** Active on all public endpoints (DDoS mitigation).
- **AWS GuardDuty:** Enabled for threat intelligence-driven threat detection across the AWS account.
- **VPC Flow Logs:** Enabled and centralized in CloudWatch Logs for 90-day retention.

---

## 5. ACCESS CONTROL REVIEW

### 5.1 Identity & Access Management — AWS (Internal)

TraceLayer's AWS account-level access controls were reviewed against the CIS AWS Foundations Benchmark v2.0.

| Control | Status | Evidence |
|---|---|---|
| Root account MFA enabled | ✅ Implemented | AWS IAM console verification |
| Root account access keys deleted | ✅ Implemented | IAM credential report |
| MFA required for all IAM users | ✅ Implemented | IAM policy document; SCP enforcement |
| IAM users follow least-privilege principle | ✅ Implemented | IAM access analyzer review |
| No wildcard (*) resource policies in production | ✅ Implemented | IAM policy scan |
| CloudTrail enabled in all regions | ✅ Implemented | CloudTrail configuration review |
| Access keys rotated within 90 days | ✅ Implemented | IAM credential report |
| Password policy meets complexity requirements | ✅ Implemented | IAM account settings |
| Cross-account access via roles (not users) | ✅ Implemented | IAM configuration |

### 5.2 Application-Level Authentication & Authorization

**Authentication Mechanism:** JSON Web Tokens (JWT) implementing both short-lived access tokens and longer-lived refresh tokens. Token signing uses RS256 (RSA 2048-bit asymmetric key pair).

| Authentication Control | Implementation | Assessment |
|---|---|---|
| Token signing algorithm | RS256 (asymmetric) | Strong — asymmetric signing prevents token forgery without private key |
| Access token lifetime | 15 minutes | Appropriate — limits window of exposure from token compromise |
| Refresh token lifetime | 7 days (configurable) | Acceptable — refresh token rotation implemented |
| Refresh token rotation | Implemented | Prevents refresh token replay |
| Token revocation capability | Implemented (token blacklist) | Supports immediate session termination |
| MFA enforcement | Available; required for admin roles | Partially implemented — MFA currently optional for standard users; see Findings |
| Brute force protection | Rate limiting + account lockout | Implemented (5 failed attempts → 15-minute lockout) |
| Password hashing | bcrypt (cost factor 12) | Strong |

### 5.3 Role-Based Access Control (RBAC)

TraceLayer implements a hierarchical RBAC model scoped to organizational tenants:

| Role | Scope | Permissions Summary |
|---|---|---|
| **Platform Admin** | Platform-wide | Full administrative access; reserved for TraceLayer staff |
| **Tenant Owner** | Single tenant | Full access within tenant; billing and user management |
| **Tenant Admin** | Single tenant | User management, integrations, all compliance features |
| **Compliance Manager** | Single tenant | View/edit compliance controls, evidence, reports |
| **Auditor (Read-Only)** | Single tenant | Read-only access to all tenant data; suitable for external auditors |
| **Integration Manager** | Single tenant | Configure integrations only; no compliance data write access |

**Finding:** RBAC implementation is appropriate for a multi-tenant SaaS platform. Role assignments are enforced at the API layer (not just UI layer), meaning backend authorization checks are performed on every request. Assessors confirmed through API testing that users with Auditor roles could not invoke write endpoints even with direct API calls bypassing the frontend.

### 5.4 Multi-Tenant Data Isolation

Data isolation between tenants is a critical security requirement for a multi-tenant SaaS platform. Assessors conducted the following isolation tests:

**Row-Level Security:** All database tables containing tenant-scoped data include an `organization_id` foreign key column. Application-layer query logic enforces tenant-scoped WHERE clauses on all queries. SQLAlchemy ORM models include tenant context enforcement.

**API-Level Isolation Testing:** Assessors created two test tenant accounts (Tenant A, Tenant B). Using Tenant A's authenticated session tokens, assessors attempted to:
- Read Tenant B's evidence records via direct object reference manipulation — **Access Denied** (404, resource not found)
- Access Tenant B's integration configurations — **Access Denied**
- Access Tenant B's user lists — **Access Denied**
- Access Tenant B's compliance reports — **Access Denied**

**Finding:** All cross-tenant access attempts returned appropriate error responses. No tenant data was accessible from a different tenant's session. The platform correctly enforces tenant isolation at the API layer.

**White-Label Partner Isolation:** For white-label deployments, TraceLayer offers dedicated instance deployment — a separate, isolated deployment of the platform infrastructure provisioned exclusively for the Partner's use. This provides infrastructure-level isolation in addition to application-level multi-tenancy, and is the recommended deployment model for the Partner's use case.

| Isolation Model | Description | Recommended For |
|---|---|---|
| **Shared Multi-Tenant** | Application-layer tenant isolation; shared database | Standard customers |
| **Dedicated Instance** | Separate AWS deployment; separate database; separate AWS account option | White-label partners, high-security regulated clients |

### 5.5 Zero-Knowledge Integration Architecture

A distinctive security design feature of the TraceLayer platform is its zero-knowledge approach to third-party integration credentials:

**Design Principles:**
1. **Read-Only OAuth Scopes Only:** When integrating with third-party services (GitHub, Google Workspace, AWS, Jira, etc.) via OAuth, TraceLayer requests only the minimum read-only OAuth scopes necessary to collect compliance evidence. Write access is never requested.
2. **Application-Layer Credential Encryption:** OAuth tokens and API keys are encrypted at the application layer using Fernet symmetric encryption before being stored in the database. The encryption key is not stored in the database — it is managed via environment variables and AWS Secrets Manager.
3. **No Raw Credential Logging:** Assessors reviewed logging configuration and confirmed that integration credentials are masked/redacted in all application logs, CloudWatch logs, and error reporting tools.
4. **Credential Isolation Per Tenant:** Encryption of each tenant's credentials uses tenant-scoped key derivation, meaning a compromise of one tenant's credential encryption would not expose another tenant's credentials.
5. **Read-Only API Token Support:** For services that use API keys rather than OAuth, TraceLayer's UI guidance and documentation instructs users to create read-only API tokens; the platform does not require — and discourages — providing API tokens with write or admin permissions.

**Assessor Comment:** The zero-knowledge integration architecture is a security-positive design decision that meaningfully differentiates TraceLayer from compliance platforms that store credentials in plaintext or with reversible encoding. The layered encryption approach (AWS KMS at rest + application-layer Fernet encryption) exceeds baseline security requirements for credential storage.

---

## 6. APPLICATION SECURITY ASSESSMENT

### 6.1 Secure Development Lifecycle (SDLC)

TraceLayer's software development lifecycle incorporates security controls at multiple stages:

| SDLC Stage | Security Control | Implementation Status |
|---|---|---|
| **Requirements** | Security requirements included in feature specifications | ✅ Implemented |
| **Design** | Threat modeling for new features | ⚠️ Partial — informal; not documented per feature |
| **Development** | Peer code review required before merge | ✅ Implemented |
| **Development** | Branch protection on main branch | ✅ Implemented (no direct commits to main) |
| **Build** | Static Application Security Testing (SAST) in CI/CD | ✅ Implemented |
| **Build** | Software Composition Analysis (SCA) — dependency scanning | ✅ Implemented |
| **Build** | Container image vulnerability scanning | ✅ Implemented |
| **Test** | Automated security regression tests | ✅ Implemented |
| **Deploy** | Staged rollout (dev → staging → production) | ✅ Implemented |
| **Deploy** | Rollback capability | ✅ Implemented |
| **Post-Deploy** | Continuous vulnerability monitoring | ✅ Implemented |
| **Annual** | Third-party penetration test | ✅ Implemented (November 2024) |

### 6.2 Vulnerability Management

**Static Analysis (SAST):** TraceLayer's CI/CD pipeline executes SAST scanning on every pull request and every merge to the main branch. Critical and high findings block the build pipeline. Medium and low findings are logged and reviewed on a weekly basis by the engineering team.

**Dependency Scanning (SCA):** Automated SCA scanning is executed on all Python (pip) and JavaScript (npm) dependencies. Assessors reviewed a 90-day window of SCA scan results and identified no critical unpatched vulnerabilities in production dependencies at the time of assessment.

**Container Image Scanning:** All Docker container images are scanned for known CVEs prior to deployment. Images with critical-severity CVEs are blocked from deployment. The base image update policy requires base images to be refreshed within 14 days of a critical OS-level vulnerability disclosure.

**Penetration Testing:** TraceLayer engaged an independent security firm for a black-box web application penetration test in November 2024. The penetration test scope included the API layer, authentication mechanisms, multi-tenant isolation, and common OWASP Top 10 vulnerability categories. The penetration test report (reviewed by Meridian under NDA) identified:
- 0 Critical findings
- 1 High finding (remediated within 7 days of report)
- 3 Medium findings (all remediated)
- 4 Low / Informational findings (accepted risks or informational only)

The remediated high finding related to a missing rate limit on a password reset endpoint, which was patched and verified before the remediation window closed.

**Finding:** TraceLayer's vulnerability management program is appropriate for a company at its stage of maturity. The combination of automated CI/CD scanning and annual third-party penetration testing provides reasonable ongoing vulnerability identification coverage.

### 6.3 OWASP Top 10 Assessment Summary

As part of this assessment, Meridian conducted targeted testing of the TraceLayer API against the OWASP API Security Top 10 (2023 edition):

| OWASP API Risk | Test Conducted | Finding |
|---|---|---|
| **API1 — Broken Object Level Authorization** | Cross-tenant resource access testing | No vulnerabilities found |
| **API2 — Broken Authentication** | Token manipulation, brute force, session hijacking | No critical vulnerabilities; minor rate-limit logging gap (Medium finding) |
| **API3 — Broken Object Property Level Authorization** | Mass assignment testing, over-exposed fields | No vulnerabilities found |
| **API4 — Unrestricted Resource Consumption** | Rate limit testing, large payload testing | Rate limiting implemented; logging gap noted |
| **API5 — Broken Function Level Authorization** | Privilege escalation, role bypass testing | No vulnerabilities found |
| **API6 — Unrestricted Access to Sensitive Business Flows** | Automated account creation, abuse scenarios | Mitigations in place |
| **API7 — Server Side Request Forgery** | SSRF testing on integration URLs | No vulnerabilities found |
| **API8 — Security Misconfiguration** | HTTP headers, CORS, error disclosure | Minor informational findings (Low) |
| **API9 — Improper Inventory Management** | Undocumented endpoint discovery | No undocumented production endpoints found |
| **API10 — Unsafe Consumption of APIs** | Third-party API response handling | No vulnerabilities found |

### 6.4 Security Headers & Configuration

Assessment of HTTP security headers on the TraceLayer application:

| Security Header | Present | Value / Configuration |
|---|---|---|
| `Strict-Transport-Security` | ✅ Yes | `max-age=31536000; includeSubDomains` |
| `Content-Security-Policy` | ✅ Yes | Restrictive policy; inline scripts disallowed |
| `X-Content-Type-Options` | ✅ Yes | `nosniff` |
| `X-Frame-Options` | ✅ Yes | `DENY` |
| `Referrer-Policy` | ✅ Yes | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | ✅ Yes | Camera, microphone, geolocation disabled |
| `Server` header | ✅ Suppressed | Not disclosed |
| `X-Powered-By` header | ✅ Removed | Not disclosed |

---

## 7. COMPLIANCE POSTURE & CONTROLS COVERAGE

### 7.1 TraceLayer's Own Compliance Program

TraceLayer operates its own continuous compliance monitoring program using the TraceLayer platform itself. This means the platform's own infrastructure and processes are continuously evaluated against SOC 2 Type II and ISO 27001:2022 control requirements, with automated evidence collection running on the same schedule as customer-facing evidence collection.

This "continuous self-audit" approach provides several assurance benefits:
1. Issues are identified and flagged continuously rather than once per year at audit time
2. Evidence of control operation is maintained in an ongoing, structured format
3. Control gaps trigger internal remediation workflows under the same SLAs as customer-facing issues
4. The compliance team has real-time visibility into the platform's own control posture

**Assessment Finding:** Meridian reviewed TraceLayer's internal compliance dashboard (with read-only access provided for assessment purposes) and found that 94% of mapped SOC 2 Trust Service Criteria controls showed "Monitored / Compliant" status, with 6% in "Remediation in Progress" status related to the two medium findings identified in this report. No controls were in "Non-Compliant" status without an active remediation plan.

### 7.2 SOC 2 Trust Service Criteria Controls Coverage

| Trust Service Category | Control Domain | Controls Mapped | Status | Evidence Collection |
|---|---|---|---|---|
| **CC — Common Criteria (Security)** | Logical and Physical Access | 24 | ✅ Implemented / Monitored | Automated |
| **CC — Common Criteria (Security)** | System Operations | 18 | ✅ Implemented / Monitored | Automated |
| **CC — Common Criteria (Security)** | Change Management | 12 | ✅ Implemented / Monitored | Automated |
| **CC — Common Criteria (Security)** | Risk Mitigation | 8 | ✅ Implemented / Monitored | Manual + Automated |
| **A — Availability** | System Availability | 14 | ✅ Implemented / Monitored | Automated |
| **C — Confidentiality** | Data Confidentiality | 10 | ✅ Implemented / Monitored | Automated |
| **PI — Processing Integrity** | Processing Completeness & Accuracy | 9 | ✅ Implemented / Monitored | Automated |
| **P — Privacy** | Data Privacy | 16 | ✅ Implemented / Monitored | Automated + Manual |

### 7.3 ISO/IEC 27001:2022 Annex A Controls Coverage

| ISO 27001 Control Domain | Annex A Ref | Controls in Scope | Status | Notes |
|---|---|---|---|---|
| Organizational Controls | A.5 | 37 | ✅ Implemented | Policies and procedures documented |
| People Controls | A.6 | 8 | ✅ Implemented | HR security procedures in place |
| Physical Controls | A.7 | 14 | ⚙️ Cloud-adapted | No physical premises; AWS shared responsibility model applies |
| Technological Controls | A.8 | 34 | ✅ Implemented | Technical controls mapped and monitored |
| — Access control | A.8.2–A.8.4 | 6 | ✅ Implemented / Monitored | RBAC, MFA, PAM |
| — Encryption | A.8.24 | 4 | ✅ Implemented / Monitored | AES-256, TLS 1.2+ |
| — Secure configuration | A.8.8–A.8.9 | 5 | ✅ Implemented / Monitored | CIS benchmarks |
| — Vulnerability management | A.8.8 | 3 | ✅ Implemented / Monitored | SAST, SCA, pen test |
| — Logging and monitoring | A.8.15–A.8.16 | 5 | ✅ Implemented / Monitored | CloudTrail, CloudWatch |
| — Incident management | A.8.18 | 4 | ✅ Implemented / Monitored | IRP documented and tested |
| — Backup | A.8.13 | 3 | ✅ Implemented / Monitored | Daily automated backups, tested |
| — Network security | A.8.20–A.8.22 | 5 | ✅ Implemented / Monitored | VPC, WAF, Security Groups |

### 7.4 Key Security Control Domains — Consolidated Status Table

| Control Domain | Framework Reference | Implementation Status | Monitoring | Last Tested |
|---|---|---|---|---|
| **Access Control** | SOC2 CC6, ISO A.8.2 | ✅ Implemented | Continuous automated | April 2025 |
| **Encryption at Rest** | SOC2 CC6.7, ISO A.8.24 | ✅ Implemented | Continuous automated | April 2025 |
| **Encryption in Transit** | SOC2 CC6.7, ISO A.8.24 | ✅ Implemented | Continuous automated | April 2025 |
| **Multi-Factor Authentication** | SOC2 CC6.1, ISO A.8.4 | ✅ Implemented (Admin) | Continuous automated | April 2025 |
| **Vulnerability Management** | SOC2 CC7.1, ISO A.8.8 | ✅ Implemented | Continuous + Annual pentest | November 2024 |
| **Security Incident Response** | SOC2 CC7.3–7.5, ISO A.8.18 | ✅ Implemented | Continuous + Quarterly drill | March 2025 |
| **Business Continuity / DR** | SOC2 A1.2–A1.3, ISO A.8.13 | ✅ Implemented | Automated backup monitoring | February 2025 |
| **Availability** | SOC2 A1.1–A1.3 | ✅ Implemented | Real-time uptime monitoring | Continuous |
| **Confidentiality** | SOC2 C1.1–C1.2 | ✅ Implemented | Continuous automated | April 2025 |
| **Logging & Audit Trails** | SOC2 CC7.2, ISO A.8.15 | ✅ Implemented | Continuous automated | April 2025 |
| **Change Management** | SOC2 CC8.1, ISO A.8.32 | ✅ Implemented | Process-based | Continuous |
| **Third-Party Risk Management** | SOC2 CC9.2, ISO A.5.19 | ✅ Implemented | Annual review | January 2025 |
| **Data Classification** | SOC2 C1.1, ISO A.5.12 | ✅ Implemented | Manual | Q4 2024 |
| **Employee Security Training** | SOC2 CC1.4, ISO A.6.3 | ✅ Implemented | Annual + ad hoc | March 2025 |
| **Asset Management** | SOC2 CC6.1, ISO A.5.9 | ✅ Implemented | Continuous automated | April 2025 |

### 7.5 Regulatory Alignment Summary

| Regulation | Applicability | TraceLayer Posture |
|---|---|---|
| **SOC 2 Type II** | Primary (platform built around this standard) | On path to formal attestation; continuous monitoring in place |
| **ISO/IEC 27001:2022** | High | 93% control coverage; ISMS documentation in progress |
| **GDPR** | Applicable (EU customer data) | DPA template in place; data mapping completed; privacy controls implemented |
| **HIPAA** | Applicable (healthcare-sector customers) | Technical safeguards implemented; BAA template available; administrative safeguards documented |
| **CCPA / CPRA** | Applicable (California residents) | Privacy notice updated; data subject request process in place |
| **NIS2 Directive** | Applicable (EU operations / customers) | Security measures aligned; incident reporting procedures established |

---

## 8. INCIDENT RESPONSE & BUSINESS CONTINUITY

### 8.1 Incident Response Program

TraceLayer maintains a documented Incident Response Plan (IRP) aligned to the NIST SP 800-61 Rev. 2 incident response lifecycle (Preparation → Detection → Containment → Eradication → Recovery → Post-Incident Activity).

**IRP Documentation Status:** Current version reviewed by Meridian. Last updated: January 2025. Previous version updated: July 2024.

**Incident Classification:**

| Severity | Definition | Internal Response Time | Partner Notification SLA |
|---|---|---|---|
| **P0 — Critical** | Data breach, production outage > 15 min, ransomware | Immediate (24/7 on-call) | Within **2 hours** of confirmed incident |
| **P1 — High** | Partial service degradation, suspected unauthorized access | Within 30 minutes | Within **8 hours** of confirmed incident |
| **P2 — Medium** | Performance degradation, minor security event | Within 2 hours | Within **24 hours** of confirmed incident |
| **P3 — Low** | Informational, no customer impact | Within 1 business day | Not required (included in monthly report) |

**Partner Notification SLA:** For incidents of P1 severity or higher that may affect partner data or service availability, TraceLayer commits to notifying affected white-label partners within 24 hours of incident confirmation (P0: 2 hours, P1: 8 hours). This meets the requirements of GDPR Article 33 (72-hour supervisory authority notification) and HIPAA Breach Notification Rule requirements.

**On-Call Coverage:** 24/7 on-call rotation is in place for production systems. AlertManager/PagerDuty integration ensures automated escalation for critical alarms.

**Tabletop Exercise:** The most recent incident response tabletop exercise was conducted in March 2025, simulating a credential-stuffing attack scenario. Exercise outcomes and action items were documented and assigned to owners.

**Finding:** The IRP is appropriately documented, regularly updated, and has been exercised within the last 60 days. The tiered notification SLA structure provides clear expectations for the Partner.

### 8.2 Monitoring & Detection

| Monitoring Capability | Tool / Service | Coverage |
|---|---|---|
| Infrastructure metrics | Amazon CloudWatch | CPU, memory, disk, network — all production resources |
| Application performance | Custom CloudWatch dashboards | API latency, error rates, queue depth |
| Security threat detection | AWS GuardDuty | ML-based threat detection across VPC, CloudTrail, DNS |
| Log aggregation | Amazon CloudWatch Logs | Application logs, access logs, audit trails |
| Audit trail | AWS CloudTrail | All AWS API calls — 1-year retention |
| Uptime monitoring | External uptime service | HTTP/HTTPS checks every 60 seconds from 3 regions |
| Vulnerability alerts | AWS Security Hub | Aggregated findings from GuardDuty, Inspector, Config |
| Anomaly detection | AWS Security Hub + GuardDuty | Unusual API patterns, geographic anomalies |

**Log Retention Policy:**

| Log Type | Retention Period | Storage |
|---|---|---|
| Application logs | 90 days hot; 1 year cold (S3) | CloudWatch + S3 |
| AWS CloudTrail audit logs | 1 year | CloudTrail + S3 |
| VPC Flow Logs | 90 days | CloudWatch Logs |
| Database audit logs | 90 days | CloudWatch Logs |
| Security finding records | 2 years | AWS Security Hub |

### 8.3 Backup & Recovery

**Backup Configuration:**

| System | Backup Method | Frequency | Retention | Backup Location |
|---|---|---|---|---|
| PostgreSQL database (RDS) | Automated RDS snapshots | Daily (continuous PITR) | 35 days | AWS us-east-1 (primary) + us-west-2 (copy) |
| S3 object storage (evidence, reports) | S3 Cross-Region Replication | Continuous (near real-time) | Indefinite | AWS us-west-2 |
| Application configuration | Infrastructure-as-code (git-managed) | Every code change | Indefinite | Version control |
| Secrets / credentials | Secrets Manager versioning | Every rotation | 90 days prior versions | AWS us-east-1 |

**Point-in-Time Recovery (PITR):** AWS RDS continuous backup with PITR is enabled, allowing database restoration to any second within the 35-day retention window.

**Cross-Region Replication:** Both database snapshots and S3 evidence storage are replicated to `us-west-2`, providing geographic redundancy against a regional AWS outage.

### 8.4 Recovery Objectives

| Metric | Target | Basis |
|---|---|---|
| **Recovery Time Objective (RTO)** | ≤ 4 hours | Time to restore service from backup in DR region |
| **Recovery Point Objective (RPO)** | ≤ 24 hours | Maximum acceptable data loss; typically < 1 hour with PITR |
| **Uptime SLA (Platform)** | 99.9% | Documented in service terms; monitored continuously |

**Disaster Recovery Test:** A DR restoration exercise was conducted in February 2025. Database restoration from cross-region snapshots was completed in approximately 2 hours 40 minutes, within the 4-hour RTO target. Evidence storage S3 replication was confirmed operational.

**Finding:** Backup and recovery capabilities are robust and well-configured. The combination of continuous PITR and cross-region replication provides strong data durability. RTO and RPO commitments are realistic based on the tested DR exercise results.

---

## 9. THIRD-PARTY & SUPPLY CHAIN RISK

### 9.1 Critical Third-Party Dependencies

| Vendor | Purpose | Data Shared | Assessment |
|---|---|---|---|
| **Amazon Web Services** | Core cloud infrastructure | Infrastructure metadata; no direct customer data access beyond storage hosting | AWS SOC 2 Type II certified; ISO 27001 certified; GDPR-compliant DPA executed |
| **Groq (LLM inference)** | AI narrative generation for audit reports | Compliance control descriptions (anonymized/aggregated, no PII) | Reviewed data processing terms; short-term inference only; no training data retention per Groq terms |
| **Nango** | OAuth token management for third-party integrations | OAuth authorization codes (ephemeral, during OAuth flow only) | OAuth relay only; tokens returned to TraceLayer and not retained by Nango beyond flow completion |
| **GitHub (code hosting)** | Source code management | Application source code | No customer data in source control; access controls reviewed |
| **Stripe** | Payment processing | Billing data only (TraceLayer does not handle raw card data) | PCI DSS Level 1 certified; no compliance evidence data exposure |

### 9.2 Vendor Risk Assessment Process

TraceLayer maintains a vendor risk assessment process for critical third-party dependencies:
- Annual review of SOC 2 / ISO 27001 certifications for critical vendors
- Data processing agreements (DPAs) executed with all vendors who process personal data
- Subprocessor list maintained and available to customers upon request

**Finding:** Critical vendor risk management is appropriately structured for a company at TraceLayer's stage. AWS and Stripe have industry-leading security certifications. The assessors reviewed the Groq and Nango data processing terms and found them acceptable for the limited use cases described. No vendor dependency was identified as introducing unacceptable risk.

---

## 10. DATA PRIVACY & REGULATORY ALIGNMENT

### 10.1 Data Classification

TraceLayer classifies customer data into the following categories:

| Data Category | Classification | Examples | Controls Applied |
|---|---|---|---|
| **Confidential — Customer Compliance Data** | Confidential | Compliance evidence, control mappings, audit reports | Encrypted at rest + in transit; tenant-isolated; access-logged |
| **Confidential — Credentials** | Strictly Confidential | OAuth tokens, API keys | Double-encrypted (KMS + app-layer Fernet); no log exposure |
| **Personal Data** | Confidential / PII | User names, email addresses, job titles | Encrypted; GDPR/CCPA-subject; DPA-covered |
| **Operational Data** | Internal | Application logs, metrics | Encrypted; no PII in logs (validated) |
| **Public** | Public | Marketing content, documentation | No controls required |

### 10.2 Privacy Controls

| Privacy Control | Status | Notes |
|---|---|---|
| Privacy Policy published | ✅ | Clear, accessible on website |
| Data Processing Agreement (DPA) template | ✅ | Available for enterprise customers; GDPR-compliant |
| Data Subject Access Request (DSAR) process | ✅ | Documented; response SLA: 30 days |
| Right to erasure (data deletion) | ✅ | Account deletion removes all tenant data; documented process |
| Data retention policy | ✅ | Customer data retained for contract term + 90 days; configurable |
| PII in logs — review | ✅ | Assessors reviewed log sampling; no PII identified in application logs |
| Sub-processor disclosure | ✅ | Sub-processor list maintained; customers notified of changes |
| GDPR Article 30 Records of Processing | ✅ | Data mapping completed |
| GDPR Article 32 Security of Processing | ✅ | Technical and organizational measures documented |

---

## 11. FINDINGS SUMMARY & RISK REGISTER

### 11.1 Finding Severity Definitions

| Severity | CVSS Score Range | Definition |
|---|---|---|
| **Critical** | 9.0 – 10.0 | Immediate exploitation risk; potential for widespread data breach or service compromise |
| **High** | 7.0 – 8.9 | Significant risk; likely exploitable; material impact if exploited |
| **Medium** | 4.0 – 6.9 | Moderate risk; limited impact or difficult to exploit without other conditions |
| **Low** | 0.1 – 3.9 | Minor risk; defense-in-depth improvement opportunity |
| **Informational** | N/A | No direct risk; observation or best-practice recommendation |

### 11.2 Findings Register

| ID | Title | Severity | Category | Status | Target Remediation |
|---|---|---|---|---|---|
| TL-F001 | API rate-limit events lack per-tenant structured logging | Medium | Logging & Monitoring | Open — In Progress | Q2 2025 |
| TL-F002 | Container base images: opportunistic upgrade to distroless / minimal variants | Medium | Vulnerability Management | Open — Planned | Q3 2025 |
| TL-F003 | MFA not enforced for non-admin standard user accounts | Low | Access Control | Open — Roadmap | Q3 2025 |
| TL-F004 | Threat modeling not formally documented per-feature | Low | SDLC | Open — Process Gap | Q4 2025 |
| TL-F005 | API error responses disclose stack traces in development-mode misconfiguration | Low | Information Disclosure | Remediated (April 2025) | Closed |
| TL-F006 | CORS policy allows specific non-production origins in staging | Informational | Configuration | Acknowledged | Accepted Risk (staging) |
| TL-F007 | Secrets Manager rotation policies not configured for auto-rotation on all secrets | Informational | Secrets Management | Open — Planned | Q3 2025 |

### 11.3 Critical & High Findings

**No critical or high severity findings were identified during this assessment.**

### 11.4 Medium Finding Detail

**TL-F001: API Rate-Limit Events Lack Per-Tenant Structured Logging**

- **Description:** When the API rate limiter triggers (HTTP 429 responses), the current log entry includes a timestamp and IP address but does not include the authenticated tenant identifier or the specific API endpoint targeted. This limits the ability to investigate whether rate-limit events represent targeted abuse against a specific tenant's account.
- **Risk:** Reduced visibility into potential credential stuffing or automated abuse targeted at specific tenants. Does not represent an exploitable vulnerability.
- **Recommendation:** Add `organization_id` and normalized endpoint path to rate-limit event log entries.
- **TraceLayer Response:** Acknowledged. Engineering ticket created; scheduled for completion in Q2 2025.

---

**TL-F002: Container Base Images — Opportunistic Hardening to Minimal/Distroless Variants**

- **Description:** Production containers currently use standard Python and Node.js official Docker base images. While these are kept up to date, switching to minimal or distroless base images would further reduce the attack surface by eliminating unnecessary OS utilities, package managers, and shell binaries that are not required at runtime.
- **Risk:** No current exploitable vulnerability. Attack surface reduction opportunity.
- **Recommendation:** Migrate container base images to `gcr.io/distroless` or Alpine-based minimal images on next major dependency update cycle.
- **TraceLayer Response:** Acknowledged. Planned for Q3 2025 as part of a scheduled infrastructure hardening sprint.

---

## 12. SUMMARY & CONCLUSION

### 12.1 Overall Assessment Conclusion

Following a 74-day comprehensive security assessment encompassing infrastructure architecture review, application security testing, access control evaluation, compliance posture analysis, incident response review, and data privacy assessment, Meridian Security Advisors LLC concludes:

**TraceLayer's Compliance Automation Platform demonstrates a strong, enterprise-grade security posture that is appropriate for white-label deployment within a professional compliance consulting practice.**

The platform's security architecture reflects deliberate, security-first design decisions — notably the zero-knowledge integration credential architecture, defense-in-depth encryption layering, and the rigorous multi-tenant isolation model. These are not checkbox security features but architectural decisions with meaningful security benefit.

The two medium findings identified are operational hardening opportunities rather than exploitable vulnerabilities. Neither finding represents a risk that would disqualify TraceLayer from enterprise deployment. Both have documented remediation plans with timelines that are reasonable and acceptable.

The platform's practice of continuously monitoring its own infrastructure against the same SOC 2 and ISO 27001 control sets it helps customers achieve provides a level of ongoing assurance that is uncommon at this stage of a company's development and speaks well of the organization's security culture.

### 12.2 Suitability for White-Label Deployment

For the Partner's specific use case — deploying TraceLayer as a white-labeled compliance platform for enterprise customers pursuing SOC 2, ISO 27001, GDPR, HIPAA, and NIS2 certifications — Meridian assesses the platform as **suitable for deployment**, subject to the following conditions:

1. **Dedicated Instance Deployment:** The Partner should deploy TraceLayer under the dedicated instance model (separate AWS deployment) to provide infrastructure-level isolation from other TraceLayer tenants. This is already offered by TraceLayer and is the recommended model for white-label partnerships.

2. **Medium Finding Remediation Tracking:** The Partner should request confirmation from TraceLayer when TL-F001 (rate-limit logging) is remediated, and include this as a condition in the partnership agreement's security requirements schedule.

3. **Annual Security Review:** The Partnership Agreement should include a provision requiring TraceLayer to provide an updated security assessment or SOC 2 Type II report annually.

4. **Data Processing Agreement:** A formal DPA should be executed before partner customer data is processed on the platform.

5. **Penetration Test Sharing:** TraceLayer's annual penetration test report should be shared with the Partner annually under NDA, or the Partner should have the right to commission its own penetration test with reasonable notice.

These conditions are standard for enterprise white-label arrangements and are not reflective of any material security deficiency in the platform.

### 12.3 Security Rating — Final

| Domain | Rating |
|---|---|
| Infrastructure Security | A |
| Data Protection & Encryption | A |
| Access Control | A- |
| Application Security | B+ |
| Compliance Program | A |
| Incident Response & Recovery | A |
| Data Privacy | A- |
| **Overall Rating** | **A / HIGH** |

---

## 13. ASSESSOR ATTESTATION

This Security Audit & Infrastructure Trust Assessment Report was prepared by Meridian Security Advisors LLC based on evidence collected, technical testing performed, and representations made by TraceLayer Inc. personnel during the assessment period of February 3, 2025 through April 18, 2025.

The findings, conclusions, and recommendations in this report represent the independent professional judgment of the named assessors. Meridian Security Advisors LLC has no commercial interest in TraceLayer Inc. and was engaged solely for the purpose of this independent assessment.

---

```
Lead Assessor:
Daniel R. Hargrove, CISSP #123456, CISM, ISO 27001 Lead Auditor
Meridian Security Advisors LLC
Infrastructure & Cloud Security Practice

Supporting Analyst:
Sarah L. Kim, CEH, OSCP
Cloud Security Analyst, Meridian Security Advisors LLC

Supporting Analyst:
Thomas B. Wren, CCSP, AWS Solutions Architect Associate
Cloud Infrastructure Specialist, Meridian Security Advisors LLC

Report Date:      April 28, 2025
Report Version:   1.0 — FINAL
Engagement Code:  MSA-2025-TL-0094

Meridian Security Advisors LLC
1250 Connecticut Avenue NW, Suite 700
Washington, D.C. 20036
assessments@meridiansecurityadvisors.com
+1 (202) 555-0192
```

---

## 14. APPENDICES

### Appendix A — Document Control

| Version | Date | Author | Changes |
|---|---|---|---|
| 0.1 Draft | March 14, 2025 | D. Hargrove | Initial draft — infrastructure sections |
| 0.3 Draft | April 2, 2025 | D. Hargrove / S. Kim | Added application security findings |
| 0.7 Draft | April 11, 2025 | All assessors | Full draft for client review |
| 0.9 Draft | April 21, 2025 | D. Hargrove | Incorporated TraceLayer responses to findings |
| 1.0 Final | April 28, 2025 | D. Hargrove | Final report — approved for distribution |

### Appendix B — Standards & Frameworks Referenced

| Standard / Framework | Version / Edition | Issuing Body |
|---|---|---|
| NIST Special Publication 800-53 | Revision 5 (September 2020) | NIST |
| NIST Special Publication 800-61 | Revision 2 | NIST |
| AICPA Trust Service Criteria | 2017 (updated 2022) | AICPA |
| ISO/IEC 27001 | 2022 Edition | ISO / IEC |
| CIS AWS Foundations Benchmark | Version 2.0 | CIS |
| OWASP Application Security Verification Standard | Version 4.0 | OWASP |
| OWASP API Security Top 10 | 2023 Edition | OWASP |
| GDPR | Regulation (EU) 2016/679 | European Parliament |
| HIPAA Security Rule | 45 CFR Part 164 | HHS |
| NIS2 Directive | Directive (EU) 2022/2555 | European Parliament |

### Appendix C — Evidence Inventory Summary

A total of 147 discrete evidence items were collected during this assessment, including:

- 15 information security policy and procedure documents
- 12 infrastructure architecture diagrams and network topology documentation items
- 8 AWS configuration export reports (IAM, Security Groups, Config Rules, GuardDuty, CloudTrail)
- 4 vulnerability scan reports (Q4 2024, Q1 2025 — SAST and container scanning)
- 1 third-party penetration test report (November 2024)
- 2 DR/backup restoration test records
- 1 incident response tabletop exercise report (March 2025)
- 3 vendor security certification documents (AWS, Stripe, Groq)
- 6 data processing agreements and privacy documentation items
- 95 technical test results (API security testing, configuration review, access control testing)

Full evidence inventory available to authorized parties upon request under NDA.

### Appendix D — Glossary

| Term | Definition |
|---|---|
| **AES-256** | Advanced Encryption Standard with 256-bit key length; current industry standard for symmetric encryption |
| **CVSS** | Common Vulnerability Scoring System; standardized vulnerability severity scoring framework |
| **DPA** | Data Processing Agreement; legal contract governing personal data processing by a vendor |
| **Fernet** | Symmetric authenticated encryption specification; implements AES-128-CBC + HMAC-SHA256 |
| **GDPR** | General Data Protection Regulation; EU data privacy regulation |
| **HIPAA** | Health Insurance Portability and Accountability Act; US healthcare data privacy law |
| **IRP** | Incident Response Plan; documented procedures for responding to security incidents |
| **ISO 27001** | International standard for Information Security Management Systems |
| **JWT** | JSON Web Token; compact token format for authentication and authorization |
| **KMS** | Key Management Service; AWS service for creating and managing cryptographic keys |
| **MFA** | Multi-Factor Authentication; requiring two or more verification factors for authentication |
| **NIS2** | Network and Information Systems Directive 2; EU cybersecurity directive |
| **OWASP** | Open Web Application Security Project; open-source security community |
| **PITR** | Point-in-Time Recovery; ability to restore a database to any moment in time |
| **RBAC** | Role-Based Access Control; access control model assigning permissions to roles |
| **RPO** | Recovery Point Objective; maximum acceptable data loss in time |
| **RTO** | Recovery Time Objective; maximum acceptable time to restore service after an incident |
| **SAST** | Static Application Security Testing; code analysis without execution |
| **SCA** | Software Composition Analysis; scanning for vulnerabilities in third-party dependencies |
| **SOC 2** | Service Organization Control 2; attestation standard for service provider security controls |
| **TLS** | Transport Layer Security; cryptographic protocol for secure network communications |
| **VPC** | Virtual Private Cloud; isolated network environment within AWS |
| **WAF** | Web Application Firewall; HTTP/HTTPS traffic filtering to block malicious requests |

---

*— End of Report —*

---

**TraceLayer Confidential — Prepared for [Partner Name]**
*Meridian Security Advisors LLC | Engagement MSA-2025-TL-0094 | April 28, 2025*
*This document is confidential and intended solely for the named recipient. Unauthorized distribution is prohibited.*
