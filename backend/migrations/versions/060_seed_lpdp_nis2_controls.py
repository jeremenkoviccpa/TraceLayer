"""Seed controls for Serbian LPDP and NIS2 Directive.

Revision ID: 060_seed_lpdp_nis2_controls
Revises: 059_add_tool_leads
Create Date: 2026-04-05
"""
import uuid

import sqlalchemy as sa
from alembic import op

revision = "060_seed_lpdp_nis2_controls"
down_revision = "059_add_tool_leads"
branch_labels = None
depends_on = None

# LPDP controls — UUID prefix 00000000-0000-0000-0012-*
LPDP_CONTROLS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0012-000000000001"),
        "name": "Lawful Processing Basis",
        "framework": "lpdp",
        "category": "lawful_processing",
        "external_id": "Art.5-11",
        "description": (
            "Personal data may be processed only on one of six legal grounds: consent, contract, "
            "legal obligation, vital interests, public interest, or legitimate interests (Art. 5-11). "
            "Consent must be freely given, specific, informed, and unambiguous. Evidence includes "
            "user directory data, DLP policies, consent management records, and IAM policies."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0012-000000000002"),
        "name": "Data Subject Rights",
        "framework": "lpdp",
        "category": "data_subject_rights",
        "external_id": "Art.26-39",
        "description": (
            "Data subjects hold rights to access (Art. 26), rectification (Art. 29), erasure (Art. 30), "
            "restriction (Art. 31), portability (Art. 36), and objection (Art. 37-39). Controllers must "
            "respond within 30 days. Evidence includes subject request logs, documented procedures, and "
            "response records."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0012-000000000003"),
        "name": "Controller Obligations and Records of Processing",
        "framework": "lpdp",
        "category": "controller_obligations",
        "external_id": "Art.40-43",
        "description": (
            "Controllers must maintain Records of Processing Activities (ROPA), implement data protection "
            "by design and by default (Art. 43), and sign written data processing agreements with all "
            "processors (Art. 44-45). Evidence includes ROPA records, DPA contracts, and policy documentation."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0012-000000000004"),
        "name": "Data Protection Impact Assessment",
        "framework": "lpdp",
        "category": "controller_obligations",
        "external_id": "Art.54-56",
        "description": (
            "A DPIA is mandatory before high-risk processing, systematic profiling, or large-scale "
            "processing of special categories (Art. 54-56). Must consult Poverenik when residual risk "
            "remains high. Evidence includes DPIA documents and risk registers."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0012-000000000005"),
        "name": "Technical and Organizational Security Measures",
        "framework": "lpdp",
        "category": "data_security",
        "external_id": "Art.49",
        "description": (
            "Controllers and processors must implement appropriate technical and organizational measures "
            "considering risk level: pseudonymisation, encryption, ensuring ongoing confidentiality, "
            "integrity, availability, and resilience of systems (Art. 49). Evidence includes IAM policies, "
            "audit logs, encryption configs, and vulnerability scan results."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0012-000000000006"),
        "name": "Personal Data Breach Notification to Poverenik",
        "framework": "lpdp",
        "category": "breach_notification",
        "external_id": "Art.53",
        "description": (
            "Personal data breaches must be notified to the Poverenik (Commissioner) within 72 hours of "
            "becoming aware unless the breach is unlikely to result in risk to individuals (Art. 53). "
            "High-risk breaches must also be communicated to affected individuals without undue delay. "
            "Evidence includes breach records, notification timestamps, and Poverenik reference numbers."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0012-000000000007"),
        "name": "Data Protection Officer",
        "framework": "lpdp",
        "category": "dpo_requirements",
        "external_id": "Art.57-61",
        "description": (
            "A DPO is mandatory for public authorities, controllers/processors performing large-scale "
            "systematic monitoring, or processing special categories at scale (Art. 57). DPO must be "
            "registered with Poverenik. Evidence includes DPO appointment records, contact details, and "
            "Poverenik registration."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0012-000000000008"),
        "name": "Cross-border Data Transfers",
        "framework": "lpdp",
        "category": "cross_border_transfers",
        "external_id": "Art.65-74",
        "description": (
            "Transfers outside Serbia are permitted to countries on the Poverenik adequacy list, or using "
            "appropriate safeguards: standard contractual clauses, binding corporate rules, or approved "
            "codes of conduct (Art. 65-74). Evidence includes data flow records, transfer impact assessments, "
            "and SCCs."
        ),
    },
]

# NIS2 controls — UUID prefix 00000000-0000-0000-0013-*
NIS2_CONTROLS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000001"),
        "name": "Risk Management Policy",
        "framework": "nis2",
        "category": "risk_management",
        "external_id": "Art.21.2a",
        "description": (
            "Essential and important entities must adopt policies on risk analysis and information system "
            "security, approved by the management body (Art. 20, 21.2a). Evidence includes risk registers, "
            "security policies, management sign-off records, and vulnerability assessment results."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000002"),
        "name": "Incident Handling",
        "framework": "nis2",
        "category": "incident_handling",
        "external_id": "Art.21.2b",
        "description": (
            "Entities must implement incident handling procedures covering detection, analysis, containment, "
            "and recovery (Art. 21.2b). Must maintain on-call capabilities and incident response playbooks. "
            "Evidence includes incident records, response procedures, and on-call schedules."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000003"),
        "name": "Business Continuity and Disaster Recovery",
        "framework": "nis2",
        "category": "business_continuity",
        "external_id": "Art.21.2c",
        "description": (
            "Entities must implement backup management, disaster recovery, and crisis management (Art. 21.2c). "
            "Includes BCP testing and defined RTO/RPO objectives. Evidence includes BCP records, backup "
            "configuration audit, and DR test results."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000004"),
        "name": "Supply Chain Security",
        "framework": "nis2",
        "category": "supply_chain_security",
        "external_id": "Art.21.2d",
        "description": (
            "Entities must address security in supply chains including relationships with direct suppliers "
            "and service providers (Art. 21.2d). Requires vendor risk assessments and security requirements "
            "in supplier contracts. Evidence includes vendor assessments, supplier security questionnaires, "
            "and contract clauses."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000005"),
        "name": "Network and System Security",
        "framework": "nis2",
        "category": "network_security",
        "external_id": "Art.21.2e",
        "description": (
            "Entities must secure network and information systems including vulnerability handling, patch "
            "management, and security in acquisition, development, and maintenance of systems (Art. 21.2e). "
            "Evidence includes vulnerability scans, patch records, firewall configs, and security testing results."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000006"),
        "name": "Access Control and Multi-Factor Authentication",
        "framework": "nis2",
        "category": "access_control",
        "external_id": "Art.21.2i",
        "description": (
            "Entities must implement access control policies, privileged access management, and multi-factor "
            "authentication or continuous authentication solutions (Art. 21.2i). Evidence includes IAM user "
            "records, MFA configuration, access review reports, and privileged account audits."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000007"),
        "name": "Cryptography and Encryption",
        "framework": "nis2",
        "category": "cryptography",
        "external_id": "Art.21.2h",
        "description": (
            "Entities must maintain policies and procedures on the use of cryptography and, where appropriate, "
            "encryption of data at rest and in transit (Art. 21.2h). Evidence includes encryption configuration, "
            "certificate inventory, and cryptographic policy documentation."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000008"),
        "name": "Cyber Hygiene and Security Training",
        "framework": "nis2",
        "category": "cyber_hygiene",
        "external_id": "Art.21.2g",
        "description": (
            "Entities must maintain basic cyber hygiene practices and cybersecurity training programmes for "
            "staff (Art. 21.2g). Management body members must undertake training. Evidence includes training "
            "completion records, security awareness programmes, and background check results."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000009"),
        "name": "Security Monitoring and Audit Logging",
        "framework": "nis2",
        "category": "logging_monitoring",
        "external_id": "Art.21.2e-mon",
        "description": (
            "Entities must implement security event monitoring, audit logging, and intrusion detection "
            "capabilities as part of securing network and information systems (Art. 21.2e). Evidence includes "
            "SIEM/audit logs, CloudTrail records, log retention policies, and monitoring alert configs."
        ),
    },
    {
        "id": uuid.UUID("00000000-0000-0000-0013-000000000010"),
        "name": "Significant Incident Reporting to CSIRT",
        "framework": "nis2",
        "category": "incident_reporting",
        "external_id": "Art.23",
        "description": (
            "Significant incidents must be reported in three stages: early warning within 24 hours, incident "
            "notification within 72 hours, and final report within 1 month (Art. 23). Reports go to national "
            "CSIRT or competent authority. Evidence includes incident records with NIS2 reporting timestamps "
            "and CSIRT reference numbers."
        ),
    },
]


def upgrade() -> None:
    controls_table = sa.table(
        "controls",
        sa.column("id", sa.String),
        sa.column("name", sa.String),
        sa.column("framework", sa.String),
        sa.column("category", sa.String),
        sa.column("description", sa.Text),
        sa.column("external_id", sa.String),
    )
    conn = op.get_bind()
    existing_ids = {
        str(row[0])
        for row in conn.execute(
            sa.text("SELECT id FROM controls WHERE framework IN ('lpdp', 'nis2')")
        )
    }
    to_insert = [
        {
            "id": str(ctrl["id"]),
            "name": ctrl["name"],
            "framework": ctrl["framework"],
            "category": ctrl["category"],
            "description": ctrl["description"],
            "external_id": ctrl["external_id"],
        }
        for ctrl in LPDP_CONTROLS + NIS2_CONTROLS
        if str(ctrl["id"]) not in existing_ids
    ]
    if to_insert:
        op.bulk_insert(controls_table, to_insert)


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM controls WHERE framework IN ('lpdp', 'nis2')")
    )
