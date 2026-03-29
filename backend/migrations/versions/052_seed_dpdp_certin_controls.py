"""Seed Control rows for DPDP Act and CERT-In frameworks.

These rows drive automated evidence scoring in compliance_service.py.
Each category maps to an EXPECTED_TYPES entry so evidence collected
from connected integrations contributes to the framework score.

Revision ID: 052_seed_dpdp_certin_controls
Revises: 051_backfill_trust_pages
Create Date: 2026-03-29
"""
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "052_seed_dpdp_certin_controls"
down_revision = "051_backfill_trust_pages"
branch_labels = None
depends_on = None

CONTROLS = [
    # ── DPDP Act 2023 ────────────────────────────────────────────────────────
    {
        "id": uuid.UUID("00000000-0000-0000-0010-000000000001"),
        "name": "Lawful Processing and Consent",
        "framework": "dpdp",
        "category": "lawful_processing",
        "description": (
            "Personal data is processed only for a lawful purpose for which consent has been "
            "obtained or a specified legitimate use applies (Sec. 4–7). Evidence includes user "
            "directory data, DLP policies governing data flows, and IAM policies restricting "
            "data access to authorised purposes."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0010-000000000002"),
        "name": "Data Fiduciary Obligations and Security Safeguards",
        "framework": "dpdp",
        "category": "data_fiduciary_obligations",
        "description": (
            "Appropriate technical and organisational security safeguards implemented to "
            "prevent personal data breaches; data erased when purpose is met (Sec. 8, 8.3, 10). "
            "Evidence includes audit logs, IAM users/policies, DLP tools, cloud security "
            "posture findings, and endpoint security controls."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0010-000000000003"),
        "name": "Children's Data Protection",
        "framework": "dpdp",
        "category": "special_categories",
        "description": (
            "Verifiable parental/guardian consent obtained before processing personal data of "
            "children (under 18); no behavioural tracking or targeted advertising directed at "
            "children (Sec. 9). Evidence includes DLP policies and access control policies "
            "restricting processing of special-category data."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0010-000000000004"),
        "name": "Data Principal Rights — Access, Correction and Erasure",
        "framework": "dpdp",
        "category": "data_principal_rights",
        "description": (
            "Data principals can access, correct, and erase their personal data and raise "
            "grievances (Sec. 11–14, 17). Evidence includes ticketing systems tracking data "
            "subject requests (Jira, ServiceNow) and identity platforms where users can "
            "access and manage their own data."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0010-000000000005"),
        "name": "Personal Data Breach Notification",
        "framework": "dpdp",
        "category": "breach_notification",
        "description": (
            "Procedure in place to detect and notify the Data Protection Board of India and "
            "affected data principals of a personal data breach in the prescribed form and "
            "time (Sec. 8.6). Evidence includes incident management platforms, threat "
            "detection tools, and audit logs."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0010-000000000006"),
        "name": "Cross-Border Data Transfer Controls",
        "framework": "dpdp",
        "category": "cross_border_transfers",
        "description": (
            "Personal data transferred only to countries not restricted by the Central "
            "Government; data localisation requirements tracked and enforced (Sec. 16). "
            "Evidence includes network security controls (Cloudflare, Tailscale ACLs), "
            "IAM policies restricting cross-border access, and audit logs."
        ),
    },

    # ── CERT-In Directions 2022 ───────────────────────────────────────────────
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000001"),
        "name": "Mandatory 6-Hour Cyber Incident Reporting",
        "framework": "cert_in",
        "category": "incident_reporting",
        "description": (
            "Cyber incidents (breaches, ransomware, DDoS, unauthorised access, etc.) "
            "reported to CERT-In within 6 hours of becoming aware; designated Point of "
            "Contact registered with CERT-In (Dir. 1, 5). Evidence includes incident "
            "management platforms with on-call schedules and escalation policies."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000002"),
        "name": "ICT Infrastructure Security and NTP Synchronisation",
        "framework": "cert_in",
        "category": "it_infrastructure",
        "description": (
            "All ICT infrastructure clocks synchronised to NIC/NPL NTP servers; systems "
            "hardened against known attack vectors with default credentials changed and "
            "unused ports/services disabled (Dir. 2, 12). Evidence includes timestamped "
            "audit logs, IAM/security policies, network policies, and cloud posture findings."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000003"),
        "name": "180-Day ICT Log Retention",
        "framework": "cert_in",
        "category": "log_management",
        "description": (
            "All ICT system logs (server, network, application, database, security device) "
            "retained for a rolling 180 days within Indian jurisdiction and available for "
            "submission to CERT-In (Dir. 3). Evidence includes CloudTrail, SIEM platforms "
            "(Splunk, Datadog), and log aggregation configurations."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000004"),
        "name": "Identity Verification and KYC for Subscribers",
        "framework": "cert_in",
        "category": "identity_verification",
        "description": (
            "Data centres, VPS/VPN/cloud providers must register and maintain accurate "
            "customer information (names, validated addresses, IPs, etc.) for 5+ years "
            "(Dir. 4). Evidence includes identity platform user records (Okta, Azure AD, "
            "Google Workspace) and IAM user inventories."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000005"),
        "name": "Cyber Incident Response Plan",
        "framework": "cert_in",
        "category": "incident_response",
        "description": (
            "Documented incident response plan covering detection, containment, eradication, "
            "recovery, and post-incident review; plan tested and updated regularly (Dir. 6). "
            "Evidence includes incident escalation policies, on-call schedules, and change "
            "management records in incident response platforms."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000006"),
        "name": "Vulnerability Assessment and Patch Management",
        "framework": "cert_in",
        "category": "vulnerability_management",
        "description": (
            "Regular vulnerability assessments and penetration tests conducted; CERT-In "
            "advisories monitored and critical patches applied within specified timelines "
            "(Dir. 7). Evidence includes VA/PT scan results from Qualys, Snyk, Wiz, Detectify, "
            "bug bounty platforms, and CrowdStrike detections."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000007"),
        "name": "MFA and Privileged Access Management",
        "framework": "cert_in",
        "category": "access_control",
        "description": (
            "Multi-factor authentication enforced for all administrative and privileged "
            "accounts; access granted on least-privilege basis; privileged sessions logged "
            "and monitored (Dir. 8). Evidence includes IAM, Okta, Azure AD, GitHub admin "
            "access records, MFA policy/enrollment data, and Vault PAM configuration."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000008"),
        "name": "Backup and Business Continuity",
        "framework": "cert_in",
        "category": "resilience",
        "description": (
            "Critical data and systems backed up regularly with backups tested for "
            "restorability; business continuity and disaster recovery plan documented "
            "and tested (Dir. 9). Evidence includes uptime monitoring, service "
            "availability records, change management logs, and secrets management."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000009"),
        "name": "Network Monitoring and Threat Detection",
        "framework": "cert_in",
        "category": "monitoring",
        "description": (
            "Network monitoring mechanisms deployed to detect anomalous activities, "
            "potential attacks, and indicators of compromise; security alerts reviewed "
            "and responded to promptly (Dir. 10). Evidence includes SIEM tools (Datadog, "
            "Splunk), EDR detections (CrowdStrike, SentinelOne), cloud security findings, "
            "and audit logs."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0011-000000000010"),
        "name": "Endpoint Security and Device Management",
        "framework": "cert_in",
        "category": "endpoint_security",
        "description": (
            "All endpoints protected with up-to-date security software; unauthorised "
            "devices blocked from organisational networks; device management policies "
            "enforce encryption (Dir. 11). Evidence includes EDR agents (CrowdStrike, "
            "SentinelOne), MDM inventory (Jamf, Kandji), and VPN device records."
        ),
    },
]


def upgrade() -> None:
    controls_table = sa.table(
        "controls",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("framework", sa.String),
        sa.column("category", sa.String),
        sa.column("description", sa.Text),
    )
    # Skip any that already exist (idempotent)
    conn = op.get_bind()
    existing_ids = {
        str(row[0])
        for row in conn.execute(
            sa.text("SELECT id FROM controls WHERE framework IN ('dpdp', 'cert_in')")
        )
    }
    to_insert = [c for c in CONTROLS if str(c["id"]) not in existing_ids]
    if to_insert:
        op.bulk_insert(controls_table, to_insert)


def downgrade() -> None:
    ids = ", ".join(f"'{c['id']}'" for c in CONTROLS)
    op.execute(f"DELETE FROM controls WHERE id IN ({ids})")
