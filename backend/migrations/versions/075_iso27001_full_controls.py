"""Expand ISO 27001:2022 from 4 thin aggregated controls to 14 granular controls
covering all major Annex A themes with proper external_id references.

Revision ID: 075_iso27001_full_controls
Revises: 074_iso42001
Create Date: 2026-04-06
"""

from alembic import op

revision = "075_iso27001_full_controls"
down_revision = "074_iso42001"
branch_labels = None
depends_on = None

# UUIDs 0001-000000000001 through 0001-000000000004 already exist —
# update them in-place. UUIDs 0001-000000000005 through 0001-000000000014 are new.

def upgrade() -> None:
    # ── Update existing 4 controls ────────────────────────────────────────────

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000001',
            'Access Control and Identity Management',
            'iso27001',
            'access_control',
            'A.5.15–18 and A.8.2–3 require a formal access control policy, user access provisioning and de-provisioning, management of privileged access rights, and restriction of access to information and systems. Identity management must ensure each user has a unique ID. Evidence includes IAM user and policy records, identity platform (Okta, Azure AD) user directories and group memberships, and GitHub membership and admin role reports.',
            'A.5.15-18, A.8.2-3'
        )
        ON CONFLICT (id) DO UPDATE SET
            name        = EXCLUDED.name,
            category    = EXCLUDED.category,
            description = EXCLUDED.description,
            external_id = EXCLUDED.external_id;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000002',
            'Technical Vulnerability Management',
            'iso27001',
            'vulnerability_management',
            'A.8.8 requires timely identification, evaluation, and remediation of technical vulnerabilities in information systems. Organisations must maintain an inventory of assets, subscribe to vulnerability intelligence, test and deploy patches within defined SLAs, and track remediation to closure. A.8.19 covers security controls for software installation on operational systems. Evidence includes vulnerability scan results, Snyk/Wiz/CrowdStrike findings, asset records, and patch management logs.',
            'A.8.8, A.8.19'
        )
        ON CONFLICT (id) DO UPDATE SET
            name        = EXCLUDED.name,
            category    = EXCLUDED.category,
            description = EXCLUDED.description,
            external_id = EXCLUDED.external_id;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000003',
            'Network and Communications Security',
            'iso27001',
            'network_security',
            'A.8.20–22 require securing networks against threats, defining security requirements for external network services, and segregating networks hosting systems with different sensitivity levels. A.5.14 covers information transfer policies and procedures including secure messaging. Evidence includes network policy configurations, cloud security group rules, zero-trust network access records (Tailscale, Zscaler), firewall configurations, and web application firewall (Cloudflare) settings.',
            'A.5.14, A.8.20-22'
        )
        ON CONFLICT (id) DO UPDATE SET
            name        = EXCLUDED.name,
            category    = EXCLUDED.category,
            description = EXCLUDED.description,
            external_id = EXCLUDED.external_id;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000004',
            'Change Management',
            'iso27001',
            'change_management',
            'A.8.32 requires formal change management procedures for information processing facilities and systems. Changes must be planned, tested, approved, and documented. Emergency changes require post-implementation review. A.8.33 covers test information management. Evidence includes source code repository records demonstrating branch protection and PR review requirements, project and ticket management records showing change tracking and approval workflows.',
            'A.8.32-33'
        )
        ON CONFLICT (id) DO UPDATE SET
            name        = EXCLUDED.name,
            category    = EXCLUDED.category,
            description = EXCLUDED.description,
            external_id = EXCLUDED.external_id;
    """)

    # ── Insert 10 new controls ─────────────────────────────────────────────────

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000005',
            'Logging and Security Monitoring',
            'iso27001',
            'logging_and_monitoring',
            'A.8.15 requires event logs recording user activities, exceptions, faults, and security events to be produced, protected, and retained. A.8.16 requires monitoring of networks, systems, and applications for anomalous behaviour and potential security incidents. A.8.17 requires synchronisation of clocks across systems. Evidence includes CloudTrail log records, SIEM (Splunk, Datadog, Elastic) configuration and alert records, log retention policy documentation, and monitoring dashboard configurations.',
            'A.8.15-17'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000006',
            'Endpoint Security and Malware Protection',
            'iso27001',
            'endpoint_security',
            'A.8.1 requires that endpoint devices (laptops, mobiles, workstations) used to access organisational information are managed and secured. A.8.7 requires controls against malware including anti-malware software, user awareness, and controls on use of removable media. MDM enrolment, disk encryption, screen lock, and OS patch compliance are primary controls. Evidence includes MDM platform records (Jamf, Kandji, Kolide, CrowdStrike), device compliance posture reports, and endpoint detection and response (EDR) deployment records.',
            'A.8.1, A.8.7'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000007',
            'Cryptography and Key Management',
            'iso27001',
            'cryptography',
            'A.8.24 requires a policy on the use of cryptography, covering encryption of data at rest and in transit, key management procedures, key lifecycle (generation, distribution, storage, retirement, destruction), and certificate management. Evidence includes secrets management platform records (HashiCorp Vault), IAM policy statements enforcing encryption, TLS certificate inventory, CloudTrail records of KMS key operations, and cryptographic policy documentation.',
            'A.8.24'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000008',
            'Supplier and Cloud Service Security',
            'iso27001',
            'supplier_security',
            'A.5.19–23 require identifying and managing information security risks associated with suppliers and third-party service providers. Security requirements must be established in agreements. A.5.23 specifically covers information security for use of cloud services including due diligence, contractual controls, and ongoing monitoring. Evidence includes vendor risk assessment records, supplier security questionnaire responses, cloud service security configurations, dependency vulnerability scans (Snyk), and cloud posture management findings (Wiz).',
            'A.5.19-23'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000009',
            'Information Security Incident Management',
            'iso27001',
            'incident_management',
            'A.5.24–27 require planning and preparing for managing information security incidents consistently and effectively. Organisations must assess events to classify them as incidents, respond to incidents according to documented procedures, and conduct post-incident analysis to prevent recurrence. A.5.28 covers collection of evidence. Evidence includes on-call schedule and escalation policy records (PagerDuty, Opsgenie), incident ticket records (ServiceNow, Jira), incident response playbook documentation, and post-incident review reports.',
            'A.5.24-28'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000010',
            'Business Continuity and Availability',
            'iso27001',
            'business_continuity',
            'A.5.29–30 require planning information security continuity within business continuity management processes. ICT continuity plans must address recovery time objectives (RTO) and recovery point objectives (RPO). Resilience requirements for critical systems must be defined. Evidence includes on-call service configuration records demonstrating monitoring coverage, uptime SLO records, backup configuration and test results, DR plan documentation, and change management records showing tested recovery procedures.',
            'A.5.29-30'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000011',
            'Secure Development Lifecycle',
            'iso27001',
            'secure_development',
            'A.8.25–31 require integrating security into the software development lifecycle from requirements through design, coding, testing, and deployment. Secure coding principles must be documented and applied. Security testing (SAST, DAST, dependency scanning) must be performed before release. A.8.26 covers application security requirements. A.8.29 covers security testing in development and acceptance. Evidence includes repository branch protection and code review records, dependency vulnerability scan results (Snyk), DAST/pen test findings, and security testing artefacts.',
            'A.8.25-31'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000012',
            'Human Resource Security',
            'iso27001',
            'hr_security',
            'A.6.1–6.8 cover the full employee lifecycle: pre-employment screening (A.6.1), terms and conditions defining security responsibilities (A.6.2), security awareness education and training (A.6.3), disciplinary process for policy violations (A.6.4), responsibilities after termination (A.6.5), confidentiality agreements (A.6.6), remote working security (A.6.7), and reporting of security events by staff (A.6.8). Evidence includes user directory records demonstrating all active staff are enrolled in identity platforms, training completion records, and offboarding workflow documentation.',
            'A.6.1-6.8'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000013',
            'Asset Management and Information Classification',
            'iso27001',
            'asset_management',
            'A.5.9–14 require maintaining an inventory of information and supporting assets (A.5.9), defining acceptable use rules (A.5.10), ensuring return of assets (A.5.11), classifying information by sensitivity (A.5.12), labelling information according to classification (A.5.13), and managing information transfer (A.5.14). Evidence includes asset inventory records, cloud resource inventories from AWS/Azure/GCP, software asset records from repository management, and information classification policies.',
            'A.5.9-14'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0001-000000000014',
            'Organisational Security Policies and Governance',
            'iso27001',
            'organizational_controls',
            'A.5.1–8 establish the foundation of the ISMS: an information security policy approved by management (A.5.1), defined roles and responsibilities (A.5.2), segregation of duties (A.5.3), management responsibilities (A.5.4), contacts with authorities (A.5.5), threat intelligence (A.5.7), and information security in project management (A.5.8). Evidence includes IAM policy records demonstrating least-privilege controls, identity platform policy configurations, and source code management policies enforcing mandatory review.',
            'A.5.1-8'
        )
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    # Remove the 10 new controls; restore original 4 to their prior state
    op.execute("""
        DELETE FROM controls
        WHERE framework = 'iso27001'
          AND id IN (
            '00000000-0000-0000-0001-000000000005',
            '00000000-0000-0000-0001-000000000006',
            '00000000-0000-0000-0001-000000000007',
            '00000000-0000-0000-0001-000000000008',
            '00000000-0000-0000-0001-000000000009',
            '00000000-0000-0000-0001-000000000010',
            '00000000-0000-0000-0001-000000000011',
            '00000000-0000-0000-0001-000000000012',
            '00000000-0000-0000-0001-000000000013',
            '00000000-0000-0000-0001-000000000014'
          );
    """)

    op.execute("""
        UPDATE controls SET
            name        = 'Access Control (A.9)',
            category    = 'access_control',
            description = 'Business requirements for access control, user access management, system and application access control.',
            external_id = NULL
        WHERE id = '00000000-0000-0000-0001-000000000001';
    """)

    op.execute("""
        UPDATE controls SET
            name        = 'Operations Security (A.12)',
            category    = 'operations_security',
            description = 'Operational procedures, protection from malware, backup, logging, monitoring and control of operational software.',
            external_id = NULL
        WHERE id = '00000000-0000-0000-0001-000000000002';
    """)

    op.execute("""
        UPDATE controls SET
            name        = 'Communications Security (A.13)',
            category    = 'communications_security',
            description = 'Network security management and information transfer policies and procedures.',
            external_id = NULL
        WHERE id = '00000000-0000-0000-0001-000000000003';
    """)

    op.execute("""
        UPDATE controls SET
            name        = 'System Acquisition & Change Control (A.14)',
            category    = 'change_management',
            description = 'Security requirements for information systems, secure development and support processes.',
            external_id = NULL
        WHERE id = '00000000-0000-0000-0001-000000000004';
    """)
