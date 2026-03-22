"""
Add more integrations + evidence to admin@tracelayer.it.com for richer demo.

Uses Supabase REST API (PostgREST) since direct Postgres port may be blocked.

Adds: snyk, wiz, knowbe4, zendesk, intercom, sendgrid, hubspot, splunk,
      new_relic, qualys, greenhouse, checkr, asana, bitbucket

Usage (from backend/ directory):
    python scripts/seed_demo_more_integrations.py
"""

import json
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Load .env manually
env_path = Path(__file__).parent.parent / ".env"
for line in env_path.read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        import os
        os.environ.setdefault(k.strip(), v.strip())

import os
import requests
from cryptography.fernet import Fernet

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
FERNET_KEY    = os.environ["FERNET_KEY"]
DEMO_EMAIL    = "admin@tracelayer.it.com"

NOW = datetime.now(timezone.utc)
DAY = timedelta(days=1)

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type":  "application/json",
    "Prefer":        "resolution=merge-duplicates,return=minimal",
}


def _enc(data: dict) -> str:
    f = Fernet(FERNET_KEY.encode())
    return f.encrypt(json.dumps(data).encode()).decode()


def _rest(method: str, table: str, data=None, params=None):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    resp = requests.request(method, url, headers=HEADERS, json=data, params=params)
    if not resp.ok:
        print(f"  ✗ {method} {table}: {resp.status_code} {resp.text[:200]}")
    return resp


def _ev(cid, integration, control, evidence_type, source_id, data, age_days=1):
    return {
        "id": str(uuid.uuid4()),
        "company_id": cid,
        "integration": integration,
        "control": control,
        "evidence_type": evidence_type,
        "source_id": source_id,
        "timestamp": (NOW - timedelta(days=age_days)).isoformat(),
        "data": data,
    }


NEW_INTEGRATIONS = [
    ("snyk",       {"api_token": "snyk-DEMO", "org_id": "acme-corp"}),
    ("wiz",        {"client_id": "wiz-DEMO", "client_secret": "DEMO", "tenant": "acme"}),
    ("knowbe4",    {"api_token": "kb4-DEMO", "region": "us"}),
    ("zendesk",    {"subdomain": "acme", "email": "admin@acme.com", "api_token": "zd-DEMO"}),
    ("intercom",   {"access_token": "ic-DEMO"}),
    ("sendgrid",   {"api_key": "SG.DEMO"}),
    ("hubspot",    {"access_token": "hs-DEMO"}),
    ("splunk",     {"host": "splunk.acme.internal", "token": "sp-DEMO", "port": "8089"}),
    ("new_relic",  {"api_key": "NRAK-DEMO", "account_id": "1234567"}),
    ("qualys",     {"username": "api-user", "password": "DEMO", "platform_url": "https://qualysapi.qualys.com"}),
    ("greenhouse", {"api_key": "gh-DEMO", "subdomain": "acme"}),
    ("checkr",     {"api_key": "ck-DEMO"}),
    ("asana",      {"access_token": "as-DEMO", "workspace_gid": "acme-ws"}),
    ("bitbucket",  {"username": "api-user", "app_password": "DEMO", "workspace": "acme-corp"}),
]


def build_evidence(cid):
    records = []

    # ── Snyk ──────────────────────────────────────────────────────────────────
    snyk_vulns = [
        ("snyk-1", "lodash",        "4.17.19", "Prototype Pollution",          "SNYK-JS-LODASH-567746",         "high",     "backend",       "fixed"),
        ("snyk-2", "axios",         "0.21.1",  "Server-Side Request Forgery",  "SNYK-JS-AXIOS-1579164",         "high",     "frontend",      "fixed"),
        ("snyk-3", "jsonwebtoken",  "8.5.1",   "Algorithm confusion attack",   "SNYK-JS-JSONWEBTOKEN-3180026",  "critical", "backend",       "open"),
        ("snyk-4", "semver",        "5.7.1",   "Regular Expression DoS",       "SNYK-JS-SEMVER-3247429",        "medium",   "data-pipeline", "open"),
        ("snyk-5", "word-wrap",     "1.2.3",   "Prototype Pollution",          "SNYK-JS-WORDWRAP-3149813",      "medium",   "mobile",        "open"),
        ("snyk-6", "minimatch",     "3.0.4",   "Regular Expression DoS",       "SNYK-JS-MINIMATCH-3166153",     "high",     "infra",         "fixed"),
        ("snyk-7", "tough-cookie",  "2.5.0",   "Prototype Pollution",          "SNYK-JS-TOUGHCOOKIE-5672873",   "medium",   "backend",       "open"),
        ("snyk-8", "pyyaml",        "5.3.1",   "Arbitrary Code Execution",     "SNYK-PYTHON-PYYAML-559098",     "high",     "data-pipeline", "open"),
    ]
    for sid, pkg, version, title, cve, severity, project, status in snyk_vulns:
        records.append(_ev(cid, "snyk", "vulnerability_management", "snyk_vulnerabilities", sid, {
            "id": sid, "title": title, "packageName": pkg, "version": version,
            "CVSSv3": cve, "severity": severity, "project": project, "status": status,
            "introducedThrough": f"{pkg}@{version}",
            "fixedIn": f"{pkg}@latest" if status == "fixed" else None,
            "disclosureTime": (NOW - timedelta(days=30)).isoformat(),
        }, age_days=1))
    records.append(_ev(cid, "snyk", "vulnerability_management", "snyk_summary", "snyk-summary-001", {
        "total_issues": len(snyk_vulns),
        "critical": 1, "high": 3, "medium": 3,
        "open": sum(1 for s in snyk_vulns if s[7] == "open"),
        "fixed": sum(1 for s in snyk_vulns if s[7] == "fixed"),
        "projects_scanned": 6,
    }, age_days=0))

    # ── Wiz ───────────────────────────────────────────────────────────────────
    wiz_issues = [
        ("wiz-1", "S3 bucket allows public access",          "CRITICAL", "acme-staging",  "RESOLVED"),
        ("wiz-2", "EC2 instance with public IP and no WAF",  "HIGH",     "prod-api-01",   "OPEN"),
        ("wiz-3", "RDS instance not encrypted at rest",      "HIGH",     "prod-db",       "RESOLVED"),
        ("wiz-4", "IAM role with wildcard permissions",      "HIGH",     "ci-runner-role","IN_PROGRESS"),
        ("wiz-5", "Container running as root",               "MEDIUM",   "data-pipeline", "OPEN"),
        ("wiz-6", "Secret exposed in environment variable",  "CRITICAL", "prod-api-02",   "RESOLVED"),
        ("wiz-7", "CloudTrail not enabled in all regions",   "MEDIUM",   "global",        "RESOLVED"),
        ("wiz-8", "Network ACL allows all inbound traffic",  "HIGH",     "prod-vpc",      "IN_PROGRESS"),
    ]
    for wid, title, severity, resource, status in wiz_issues:
        records.append(_ev(cid, "wiz", "vulnerability_management", "wiz_issues", wid, {
            "id": wid, "title": title, "severity": severity, "cloudPlatform": "AWS",
            "resourceName": resource, "status": status, "category": "Misconfiguration",
            "firstDetected": (NOW - timedelta(days=14)).isoformat(),
            "lastSeen": NOW.isoformat(),
        }, age_days=1))
    records.append(_ev(cid, "wiz", "vulnerability_management", "wiz_security_score", "wiz-score-001", {
        "securityScore": 78, "criticalIssues": 2, "highIssues": 4, "mediumIssues": 2,
        "resolvedThisMonth": 3, "resourcesScanned": 47, "cloudAccounts": ["aws-123456789012"],
    }, age_days=0))

    # ── KnowBe4 ───────────────────────────────────────────────────────────────
    training_users = [
        ("alice@acme.com",  "kb4-u1",  True,  100, "2026-02-15", 0),
        ("bob@acme.com",    "kb4-u2",  True,   95, "2026-02-20", 0),
        ("carol@acme.com",  "kb4-u3",  True,  100, "2026-02-10", 0),
        ("dave@acme.com",   "kb4-u4",  False,  60, None,         1),
        ("eve@acme.com",    "kb4-u5",  True,  100, "2026-03-01", 0),
        ("frank@acme.com",  "kb4-u6",  False,  40, None,         3),
        ("grace@acme.com",  "kb4-u7",  True,   90, "2026-02-28", 1),
        ("henry@acme.com",  "kb4-u8",  False,   0, None,         0),
        ("ivan@acme.com",   "kb4-u9",  True,  100, "2026-02-05", 0),
        ("julia@acme.com",  "kb4-u10", True,  100, "2026-03-10", 0),
    ]
    for email, uid, completed, score, completed_date, phish_failures in training_users:
        records.append(_ev(cid, "knowbe4", "security_awareness", "knowbe4_users", uid, {
            "email": email, "userId": uid, "trainingCompleted": completed,
            "currentTrainingScore": score, "lastTrainingCompletedDate": completed_date,
            "phishingTestFailures": phish_failures,
            "riskScore": "high" if phish_failures >= 2 else ("medium" if phish_failures == 1 else "low"),
        }))
    records.append(_ev(cid, "knowbe4", "security_awareness", "knowbe4_campaign", "kb4-camp-001", {
        "campaignName": "2026 Annual Security Awareness Training",
        "status": "In Progress", "completionRate": 80,
        "usersEnrolled": 10, "usersCompleted": 8, "averageScore": 88,
        "phishingTestsScheduled": 4, "dueDate": "2026-03-31",
    }, age_days=5))

    # ── Qualys ────────────────────────────────────────────────────────────────
    qualys_vulns = [
        ("qid-1", "TLS/SSL 3.0 Protocol Detected",               "CRITICAL", "legacy-portal.acme.com",  "CVE-2014-3566",  "OPEN"),
        ("qid-2", "OpenSSH < 9.3 Multiple Vulnerabilities",      "HIGH",     "bastion-01.acme.com",     "CVE-2023-38408", "IN_PROGRESS"),
        ("qid-3", "Apache 2.4.56 Remote Code Execution",         "HIGH",     "internal-wiki.acme.com",  "CVE-2023-25690", "FIXED"),
        ("qid-4", "MySQL 5.7.x Privilege Escalation",            "HIGH",     "dev-db-01.acme.com",      "CVE-2023-21912", "FIXED"),
        ("qid-5", "WordPress Core < 6.3 XSS",                    "MEDIUM",   "marketing.acme.com",      "CVE-2023-2745",  "OPEN"),
        ("qid-6", "Outdated SSL Certificate (expired within 30d)","MEDIUM",   "staging.acme.com",        None,             "OPEN"),
    ]
    for qid, title, severity, host, cve, status in qualys_vulns:
        records.append(_ev(cid, "qualys", "vulnerability_management", "qualys_vulnerabilities", qid, {
            "id": qid, "title": title, "severity": severity, "host": host,
            "cveId": cve, "status": status,
            "firstFound": (NOW - timedelta(days=20)).isoformat(),
            "lastFound": NOW.isoformat(),
        }, age_days=1))
    records.append(_ev(cid, "qualys", "vulnerability_management", "qualys_scan_summary", "qualys-scan-latest", {
        "scanName": "Production External Scan", "scanDate": NOW.isoformat(),
        "hostsScanned": 24, "vulnerabilitiesFound": len(qualys_vulns),
        "critical": 1, "high": 3, "medium": 2, "patchCompliance": "73%",
    }, age_days=0))

    # ── Splunk ────────────────────────────────────────────────────────────────
    splunk_alerts = [
        ("splunk-1", "Multiple Failed Login Attempts",            "HIGH",     "auth-service",    "Triggered"),
        ("splunk-2", "Privileged Account Activity Outside Hours", "HIGH",     "aws-cloudtrail",  "Triggered"),
        ("splunk-3", "Large Data Export Detected",                "MEDIUM",   "s3-access-logs",  "Resolved"),
        ("splunk-4", "New Admin Account Created",                 "MEDIUM",   "okta",            "Resolved"),
        ("splunk-5", "Outbound Traffic Anomaly",                  "HIGH",     "vpc-flow-logs",   "Investigating"),
        ("splunk-6", "Container Escape Attempt",                  "CRITICAL", "k8s-audit-log",   "Resolved"),
        ("splunk-7", "API Rate Limit Exceeded (suspected DDoS)",  "MEDIUM",   "api-gateway",     "Resolved"),
    ]
    for sid, title, severity, source, status in splunk_alerts:
        records.append(_ev(cid, "splunk", "logging_monitoring", "splunk_alerts", sid, {
            "alertId": sid, "alertName": title, "severity": severity,
            "sourceType": source, "status": status,
            "triggeredAt": (NOW - timedelta(hours=abs(hash(sid)) % 72)).isoformat(),
        }, age_days=1))
    records.append(_ev(cid, "splunk", "logging_monitoring", "splunk_index_summary", "splunk-idx-001", {
        "indexName": "main", "dailyIngestGB": 12.4, "retentionDays": 365,
        "searchableEventCount": 847000000,
        "sourcetypes": ["aws:cloudtrail", "okta:systemlog", "nginx:access", "k8s:audit", "vpc:flowlogs"],
    }, age_days=0))

    # ── New Relic ─────────────────────────────────────────────────────────────
    nr_services = [
        ("nr-1", "backend-api",   "Node.js",  99.97, 142, 0.08, "healthy"),
        ("nr-2", "data-pipeline", "Python",   99.45, 312, 0.45, "warning"),
        ("nr-3", "auth-service",  "Node.js",  99.99,  89, 0.02, "healthy"),
        ("nr-4", "frontend",      "Next.js",  99.98,  68, 0.05, "healthy"),
        ("nr-5", "mobile-api",    "Node.js",  99.91, 198, 0.18, "healthy"),
    ]
    for nid, name, lang, uptime, p99_ms, error_rate, status in nr_services:
        records.append(_ev(cid, "new_relic", "logging_monitoring", "newrelic_services", nid, {
            "appId": nid, "name": name, "language": lang,
            "uptimePercent": uptime, "responseTimeP99Ms": p99_ms,
            "errorRate": error_rate, "healthStatus": status,
            "throughputRpm": abs(hash(name)) % 5000 + 500,
        }, age_days=0))

    # ── Zendesk ───────────────────────────────────────────────────────────────
    zd_tickets = [
        ("zd-1", "Unable to export compliance report",     "normal", "open",    "alice@customer.com"),
        ("zd-2", "2FA setup not working",                  "urgent", "solved",  "bob@enterprise.io"),
        ("zd-3", "Data export for DSAR request",           "high",   "pending", "carol@bigcorp.com"),
        ("zd-4", "Integration with Azure AD failing",      "high",   "open",    "dave@startup.co"),
        ("zd-5", "Billing question — annual upgrade",      "normal", "solved",  "eve@scaleup.com"),
        ("zd-6", "SOC 2 evidence package download broken", "urgent", "open",    "frank@enterprise.io"),
        ("zd-7", "API rate limit questions",               "low",    "solved",  "grace@smallco.com"),
    ]
    for tid, subject, priority, status, requester in zd_tickets:
        records.append(_ev(cid, "zendesk", "logging_monitoring", "zendesk_tickets", tid, {
            "id": tid, "subject": subject, "priority": priority,
            "status": status, "requesterEmail": requester,
            "createdAt": (NOW - timedelta(days=abs(hash(tid)) % 20)).isoformat(),
        }, age_days=1))

    # ── Intercom ──────────────────────────────────────────────────────────────
    ic_users = [
        ("ic-1", "alice@customer.com", "Alice Chen",   "Enterprise", "Active",  True),
        ("ic-2", "bob@startup.io",     "Bob Martinez", "Growth",     "Active",  True),
        ("ic-3", "carol@corp.com",     "Carol Lewis",  "Enterprise", "Active",  False),
        ("ic-4", "dave@mid.com",       "Dave Taylor",  "Growth",     "Churned", False),
        ("ic-5", "eve@bigco.com",      "Eve Johnson",  "Enterprise", "Active",  True),
    ]
    for iid, email, name, plan, status, nps_promoter in ic_users:
        records.append(_ev(cid, "intercom", "customer_data", "intercom_contacts", iid, {
            "contactId": iid, "email": email, "name": name,
            "plan": plan, "status": status, "npsPromoter": nps_promoter,
            "lastSeenAt": (NOW - timedelta(days=abs(hash(iid)) % 10)).isoformat(),
        }, age_days=2))

    # ── HubSpot ───────────────────────────────────────────────────────────────
    hs_deals = [
        ("hs-1", "Acme Corp — Enterprise Annual",     75000, "closedwon"),
        ("hs-2", "Globex Corp — Growth Plan",         18000, "closedwon"),
        ("hs-3", "Initech — Enterprise Evaluation",   60000, "presentationscheduled"),
        ("hs-4", "Umbrella Corp — Security Add-on",   24000, "decisionmakerboughtin"),
        ("hs-5", "Hooli — Enterprise Annual",         90000, "contractsent"),
        ("hs-6", "Pied Piper — Growth Annual",         9600, "closedwon"),
    ]
    for hid, name, amount, stage in hs_deals:
        records.append(_ev(cid, "hubspot", "customer_data", "hubspot_deals", hid, {
            "dealId": hid, "dealName": name, "amount": amount,
            "dealStage": stage, "pipeline": "Sales",
        }, age_days=2))

    # ── SendGrid ──────────────────────────────────────────────────────────────
    records.append(_ev(cid, "sendgrid", "logging_monitoring", "sendgrid_stats", "sg-stats-today", {
        "date": NOW.date().isoformat(), "requests": 1842, "delivered": 1799,
        "opens": 634, "clicks": 128, "bounces": 12, "spamReports": 2,
        "deliveryRate": 97.7, "openRate": 35.2,
    }, age_days=0))

    # ── Greenhouse ────────────────────────────────────────────────────────────
    gh_jobs = [
        ("ghr-1", "Senior Backend Engineer",  "Engineering", "open",   8),
        ("ghr-2", "Security Engineer",        "Security",    "open",   5),
        ("ghr-3", "Head of Customer Success", "Sales",       "open",  12),
        ("ghr-4", "Product Manager",          "Product",     "draft",  0),
        ("ghr-5", "DevOps Engineer",          "Engineering", "closed", 3),
    ]
    for gid, title, dept, status, apps in gh_jobs:
        records.append(_ev(cid, "greenhouse", "hr", "greenhouse_jobs", gid, {
            "jobId": gid, "title": title, "department": dept,
            "status": status, "applications": apps, "hiringManager": "julia@acme.com",
        }, age_days=2))

    # ── Checkr ────────────────────────────────────────────────────────────────
    ck_checks = [
        ("ck-1", "alice@acme.com",  "Alice Smith",  "clear",   "2025-11-01"),
        ("ck-2", "bob@acme.com",    "Bob Jones",    "clear",   "2025-11-15"),
        ("ck-3", "carol@acme.com",  "Carol White",  "clear",   "2025-10-20"),
        ("ck-4", "frank@acme.com",  "Frank Miller", "clear",   "2026-01-10"),
        ("ck-5", "grace@acme.com",  "Grace Wilson", "pending", None),
        ("ck-6", "ivan@acme.com",   "Ivan Clark",   "clear",   "2025-09-05"),
    ]
    for cid_check, email, name, status, completed_at in ck_checks:
        records.append(_ev(cid, "checkr", "hr", "checkr_reports", cid_check, {
            "reportId": cid_check, "candidateEmail": email, "candidateName": name,
            "status": status, "completedAt": completed_at, "packageType": "employee_pro",
        }, age_days=3))

    # ── Asana ─────────────────────────────────────────────────────────────────
    asana_projects = [
        ("as-1", "ISO 27001 Certification Roadmap", "Engineering", "in_progress", "carol@acme.com"),
        ("as-2", "Q1 2026 Security Sprint",          "Engineering", "completed",   "alice@acme.com"),
        ("as-3", "GDPR Data Mapping Project",        "Legal",       "in_progress", "julia@acme.com"),
        ("as-4", "Vendor Risk Review 2026",          "Security",    "in_progress", "carol@acme.com"),
        ("as-5", "Pentest Remediation Tracker",      "Engineering", "in_progress", "alice@acme.com"),
    ]
    for aid, name, team, status, owner in asana_projects:
        records.append(_ev(cid, "asana", "change_management", "asana_projects", aid, {
            "projectId": aid, "name": name, "team": team, "status": status, "owner": owner,
            "taskCount": abs(hash(aid)) % 40 + 5,
        }, age_days=1))

    # ── Bitbucket ─────────────────────────────────────────────────────────────
    bb_repos = [
        ("bb-1", "ops-scripts",     True,  "main",   True),
        ("bb-2", "legacy-portal",   True,  "master", False),
        ("bb-3", "terraform-infra", True,  "main",   True),
        ("bb-4", "api-gateway",     True,  "main",   True),
        ("bb-5", "shared-utils",    False, "main",   False),
    ]
    for bid, name, private, branch, protected in bb_repos:
        records.append(_ev(cid, "bitbucket", "change_management", "bitbucket_repos", bid, {
            "repoId": bid, "name": name, "fullName": f"acme-corp/{name}",
            "private": private, "mainBranch": branch, "branchProtected": protected,
            "visibility": "private" if private else "public",
        }, age_days=1))

    for login, uid in [("alice","bb-m1"),("carol","bb-m2"),("ivan","bb-m3"),("grace","bb-m4"),("frank","bb-m5")]:
        records.append(_ev(cid, "bitbucket", "access_control", "bitbucket_members", uid, {
            "accountId": uid, "displayName": login.capitalize(),
            "nickname": login, "isAdmin": login in ["alice","carol","ivan"],
        }))

    return records


def main():
    # Look up company_id via Supabase REST
    resp = _rest("GET", "users", params={"email": f"eq.{DEMO_EMAIL}", "select": "company_id"})
    rows = resp.json()
    if not rows:
        print(f"✗ User {DEMO_EMAIL} not found.")
        sys.exit(1)

    company_id = rows[0]["company_id"]
    print(f"✓ Found demo account: {DEMO_EMAIL} (company_id={company_id})")

    # Check existing integrations
    resp = _rest("GET", "integrations", params={
        "company_id": f"eq.{company_id}",
        "select": "integration_type",
    })
    existing_types = {r["integration_type"] for r in resp.json()}

    # Add new integrations
    collected = NOW.isoformat()
    added, skipped = [], []
    to_insert = []
    for itype, creds in NEW_INTEGRATIONS:
        if itype in existing_types:
            skipped.append(itype)
        else:
            to_insert.append({
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "integration_type": itype,
                "credentials_enc": _enc(creds),
                "status": "active",
                "last_collected_at": collected,
            })
            added.append(itype)

    if to_insert:
        _rest("POST", "integrations", data=to_insert)

    print(f"✓ Integrations: {len(added)} added ({', '.join(added) or 'none'}), {len(skipped)} already existed")

    # Upsert evidence
    evidence = build_evidence(company_id)

    # Supabase REST upsert in batches of 50
    BATCH = 50
    total = 0
    for i in range(0, len(evidence), BATCH):
        batch = evidence[i:i+BATCH]
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/evidence",
            headers={**HEADERS, "Prefer": "resolution=merge-duplicates,return=minimal"},
            json=batch,
        )
        if resp.ok:
            total += len(batch)
        else:
            print(f"  ✗ Evidence batch {i//BATCH+1}: {resp.status_code} {resp.text[:200]}")

    print(f"✓ Evidence: {total} records upserted")
    print()
    print("  New integrations:")
    print("    Snyk · Wiz · KnowBe4 · Qualys · Splunk · New Relic")
    print("    Zendesk · Intercom · SendGrid · HubSpot")
    print("    Greenhouse · Checkr · Asana · Bitbucket")
    print()
    print("  Evidence coverage added:")
    print("    Vulnerability: snyk (8 issues) · wiz (8 issues) · qualys (6 scans)")
    print("    Security awareness: knowbe4 (10 users + campaign)")
    print("    SIEM: splunk (7 alerts) · new_relic (5 services)")
    print("    Support/CRM: zendesk (7 tickets) · intercom (5 contacts) · hubspot (6 deals)")
    print("    HR/Recruiting: greenhouse (5 jobs) · checkr (6 reports)")
    print("    Projects: asana (5 projects) · bitbucket (5 repos + 5 members)")


if __name__ == "__main__":
    main()
