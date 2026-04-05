"""Seed controls for Serbian LPDP and NIS2 Directive.

Revision ID: 060_seed_lpdp_nis2_controls
Revises: 059_add_tool_leads
Create Date: 2026-04-05
"""
from alembic import op

revision = "060_seed_lpdp_nis2_controls"
down_revision = "059_add_tool_leads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Serbian LPDP controls (00000000-0000-0000-0012-*) ─────────────────────

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0012-000000000001'::uuid,
               'Lawful Processing Basis', 'lpdp', 'lawful_processing',
               'Personal data may be processed only on one of six legal grounds: consent, contract, legal obligation, vital interests, public interest, or legitimate interests (Art. 5-11). Consent must be freely given, specific, informed, and unambiguous. Evidence includes user directory data, DLP policies, consent management records, and IAM policies.',
               'Art.5-11'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0012-000000000001'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0012-000000000002'::uuid,
               'Data Subject Rights', 'lpdp', 'data_subject_rights',
               'Data subjects hold rights to access (Art. 26), rectification (Art. 29), erasure (Art. 30), restriction (Art. 31), portability (Art. 36), and objection (Art. 37-39). Controllers must respond within 30 days. Evidence includes subject request logs, documented procedures, and response records.',
               'Art.26-39'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0012-000000000002'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0012-000000000003'::uuid,
               'Controller Obligations and Records of Processing', 'lpdp', 'controller_obligations',
               'Controllers must maintain Records of Processing Activities (ROPA), implement data protection by design and by default (Art. 43), and sign written data processing agreements with all processors (Art. 44-45). Evidence includes ROPA records, DPA contracts, and policy documentation.',
               'Art.40-43'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0012-000000000003'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0012-000000000004'::uuid,
               'Data Protection Impact Assessment', 'lpdp', 'controller_obligations',
               'A DPIA is mandatory before high-risk processing, systematic profiling, or large-scale processing of special categories (Art. 54-56). Must consult Poverenik when residual risk remains high. Evidence includes DPIA documents and risk registers.',
               'Art.54-56'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0012-000000000004'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0012-000000000005'::uuid,
               'Technical and Organizational Security Measures', 'lpdp', 'data_security',
               'Controllers and processors must implement appropriate technical and organizational measures considering risk level: pseudonymisation, encryption, ensuring ongoing confidentiality, integrity, availability, and resilience of systems (Art. 49). Evidence includes IAM policies, audit logs, encryption configs, and vulnerability scan results.',
               'Art.49'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0012-000000000005'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0012-000000000006'::uuid,
               'Personal Data Breach Notification to Poverenik', 'lpdp', 'breach_notification',
               'Personal data breaches must be notified to the Poverenik (Commissioner) within 72 hours of becoming aware unless the breach is unlikely to result in risk to individuals (Art. 53). High-risk breaches must also be communicated to affected individuals without undue delay. Evidence includes breach records, notification timestamps, and Poverenik reference numbers.',
               'Art.53'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0012-000000000006'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0012-000000000007'::uuid,
               'Data Protection Officer', 'lpdp', 'dpo_requirements',
               'A DPO is mandatory for public authorities, controllers/processors performing large-scale systematic monitoring, or processing special categories at scale (Art. 57). DPO must be registered with Poverenik. Evidence includes DPO appointment records, contact details, and Poverenik registration.',
               'Art.57-61'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0012-000000000007'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0012-000000000008'::uuid,
               'Cross-border Data Transfers', 'lpdp', 'cross_border_transfers',
               'Transfers outside Serbia are permitted to countries on the Poverenik adequacy list, or using appropriate safeguards: standard contractual clauses, binding corporate rules, or approved codes of conduct (Art. 65-74). Evidence includes data flow records, transfer impact assessments, and SCCs.',
               'Art.65-74'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0012-000000000008'::uuid)
    """)

    # ── NIS2 Directive controls (00000000-0000-0000-0013-*) ───────────────────

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000001'::uuid,
               'Risk Management Policy', 'nis2', 'risk_management',
               'Essential and important entities must adopt policies on risk analysis and information system security, approved by the management body (Art. 20, 21.2a). Evidence includes risk registers, security policies, management sign-off records, and vulnerability assessment results.',
               'Art.21.2a'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000001'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000002'::uuid,
               'Incident Handling', 'nis2', 'incident_handling',
               'Entities must implement incident handling procedures covering detection, analysis, containment, and recovery (Art. 21.2b). Must maintain on-call capabilities and incident response playbooks. Evidence includes incident records, response procedures, and on-call schedules.',
               'Art.21.2b'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000002'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000003'::uuid,
               'Business Continuity and Disaster Recovery', 'nis2', 'business_continuity',
               'Entities must implement backup management, disaster recovery, and crisis management (Art. 21.2c). Includes BCP testing and defined RTO/RPO objectives. Evidence includes BCP records, backup configuration audit, and DR test results.',
               'Art.21.2c'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000003'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000004'::uuid,
               'Supply Chain Security', 'nis2', 'supply_chain_security',
               'Entities must address security in supply chains including relationships with direct suppliers and service providers (Art. 21.2d). Requires vendor risk assessments and security requirements in supplier contracts. Evidence includes vendor assessments, supplier security questionnaires, and contract clauses.',
               'Art.21.2d'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000004'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000005'::uuid,
               'Network and System Security', 'nis2', 'network_security',
               'Entities must secure network and information systems including vulnerability handling, patch management, and security in acquisition, development, and maintenance of systems (Art. 21.2e). Evidence includes vulnerability scans, patch records, firewall configs, and security testing results.',
               'Art.21.2e'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000005'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000006'::uuid,
               'Access Control and Multi-Factor Authentication', 'nis2', 'access_control',
               'Entities must implement access control policies, privileged access management, and multi-factor authentication or continuous authentication solutions (Art. 21.2i). Evidence includes IAM user records, MFA configuration, access review reports, and privileged account audits.',
               'Art.21.2i'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000006'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000007'::uuid,
               'Cryptography and Encryption', 'nis2', 'cryptography',
               'Entities must maintain policies and procedures on the use of cryptography and, where appropriate, encryption of data at rest and in transit (Art. 21.2h). Evidence includes encryption configuration, certificate inventory, and cryptographic policy documentation.',
               'Art.21.2h'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000007'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000008'::uuid,
               'Cyber Hygiene and Security Training', 'nis2', 'cyber_hygiene',
               'Entities must maintain basic cyber hygiene practices and cybersecurity training programmes for staff (Art. 21.2g). Management body members must undertake training. Evidence includes training completion records, security awareness programmes, and background check results.',
               'Art.21.2g'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000008'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000009'::uuid,
               'Security Monitoring and Audit Logging', 'nis2', 'logging_monitoring',
               'Entities must implement security event monitoring, audit logging, and intrusion detection capabilities as part of securing network and information systems (Art. 21.2e). Evidence includes SIEM/audit logs, CloudTrail records, log retention policies, and monitoring alert configs.',
               'Art.21.2e-mon'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000009'::uuid)
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        SELECT '00000000-0000-0000-0013-000000000010'::uuid,
               'Significant Incident Reporting to CSIRT', 'nis2', 'incident_reporting',
               'Significant incidents must be reported in three stages: early warning within 24 hours, incident notification within 72 hours, and final report within 1 month (Art. 23). Reports go to national CSIRT or competent authority. Evidence includes incident records with NIS2 reporting timestamps and CSIRT reference numbers.',
               'Art.23'
        WHERE NOT EXISTS (SELECT 1 FROM controls WHERE id = '00000000-0000-0000-0013-000000000010'::uuid)
    """)


def downgrade() -> None:
    op.execute("DELETE FROM controls WHERE framework IN ('lpdp', 'nis2')")
