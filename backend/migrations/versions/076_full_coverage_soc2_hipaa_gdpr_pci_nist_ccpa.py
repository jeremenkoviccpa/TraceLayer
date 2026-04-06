"""Full coverage: SOC 2, HIPAA, GDPR, PCI DSS, NIST CSF, CCPA.

Replaces the stub controls (SOC 2: 3, HIPAA: 3, GDPR/PCI/NIST/CCPA: 0)
with production-ready granular controls:
  SOC 2    → 12 controls (all TSC CC categories + A/C criteria)
  HIPAA    →  9 controls (Admin + Technical Safeguards)
  GDPR     → 10 controls (full Chapter coverage)
  PCI DSS  → 12 controls (all 12 Requirements)
  NIST CSF →  6 controls (all 6 CSF 2.0 Functions)
  CCPA     →  6 controls (CCPA + CPRA obligations)

Revision ID: 076_full_coverage_soc2_hipaa_gdpr_pci_nist_ccpa
Revises: 075_iso27001_full_controls
Create Date: 2026-04-06
"""

from alembic import op

revision = "076_full_coverage_soc2_hipaa_gdpr_pci_nist_ccpa"
down_revision = "075_iso27001_full_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Delete all existing stub controls for these frameworks
    op.execute("""
        DELETE FROM controls
        WHERE framework IN ('soc2', 'hipaa', 'gdpr', 'pci_dss', 'nist_csf', 'ccpa');
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # SOC 2 — Trust Service Criteria (TSC 2017, updated 2022)
    # UUID prefix: 00000000-0000-0000-0004-*
    # ══════════════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000001',
            'Control Environment and Governance',
            'soc2', 'control_environment',
            'CC1 requires the entity to demonstrate commitment to integrity and ethical values, establish board oversight of internal control, define appropriate structures and reporting lines, demonstrate commitment to competence, and hold individuals accountable. Policies must be documented and communicated. CC2 covers internal communication of control objectives and external communication with relevant parties. Evidence includes IAM policies defining least-privilege, identity platform policy configurations, and source code management policies.',
            'CC1, CC2'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000002',
            'Risk Assessment',
            'soc2', 'risk_assessment',
            'CC3 requires the entity to specify objectives with sufficient clarity to identify and assess risks, identify risks to achieving those objectives, assess fraud risk, and identify significant changes that could impact the system of internal control. CC9.1 requires identifying, selecting, and developing risk mitigation activities. Risk registers must document likelihood, impact, owner, and treatment. Evidence includes vulnerability scan results, cloud security posture findings, dependency scan reports, and formal risk register records.',
            'CC3, CC9.1'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000003',
            'Logical and Physical Access Controls',
            'soc2', 'access_control',
            'CC6.1–CC6.3 require restricting logical access to system components, managing access credentials including multi-factor authentication, controlling access based on least privilege and need-to-know, and reviewing user access periodically. Identity and access management must cover all system components. Evidence includes IAM user and policy records, identity platform user directories (Okta, Azure AD, Google Workspace), GitHub membership and admin role records, MFA enrolment status, and periodic access review records.',
            'CC6.1-CC6.3'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000004',
            'Privileged Access and Authentication',
            'soc2', 'privileged_access',
            'CC6.2–CC6.3 require controlling and monitoring privileged access accounts. Service accounts must be inventoried and access restricted. Multi-factor authentication is required for all privileged access. Vault and PAM solutions demonstrate controlled access to sensitive credentials and infrastructure. Evidence includes IAM privileged role records, Vault policy and auth method configurations, GitHub admin membership, MFA policy and enrolment records, and privileged access review logs.',
            'CC6.2-CC6.3'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000005',
            'System Monitoring and Alerting',
            'soc2', 'logging_monitoring',
            'CC7.1–CC7.2 require the entity to use detection and monitoring procedures to identify changes to configurations, new vulnerabilities, and anomalous activity. CC4.1–CC4.2 require ongoing and periodic evaluations of internal control components. SIEM platforms, cloud audit logs, and infrastructure monitoring tools are primary evidence sources. Evidence includes CloudTrail log records, Datadog and Splunk monitoring configurations and alert records, and anomaly detection configurations.',
            'CC4, CC7.1-CC7.2'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000006',
            'Incident Response and Management',
            'soc2', 'incident_response',
            'CC7.3–CC7.5 require the entity to evaluate security events to determine whether they constitute incidents, respond to identified incidents according to a documented incident response plan, and communicate information about incidents to affected parties. Post-incident reviews must identify root causes and drive remediation. Evidence includes on-call escalation policy records, incident ticket records, incident response playbooks, post-incident review documentation, and SLA compliance records.',
            'CC7.3-CC7.5'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000007',
            'Change Management',
            'soc2', 'change_management',
            'CC8.1 requires the entity to authorise, design, develop or acquire, configure, document, test, approve, and implement changes to infrastructure, data, software, and procedures. Changes must follow a formal approval workflow. Emergency changes require post-implementation review. Evidence includes source code repository records with branch protection and pull request review requirements, project management records showing change authorisation, and deployment pipeline records.',
            'CC8.1'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000008',
            'Endpoint Protection and Malware Defence',
            'soc2', 'endpoint_security',
            'CC6.6–CC6.7 require controls to prevent or detect and act on the introduction of unauthorised software on systems. Endpoints must be managed with MDM, disk encryption enforced, antivirus/EDR deployed, and patch levels monitored. Evidence includes MDM platform records (Jamf, Kandji, Kolide), EDR deployment records (CrowdStrike, SentinelOne), device compliance posture reports, and endpoint patching status records.',
            'CC6.6-CC6.7'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000009',
            'Vulnerability Management',
            'soc2', 'vulnerability_management',
            'CC7.1 requires identifying, monitoring, and evaluating configurations and vulnerabilities. Vulnerability scans must be performed regularly, findings prioritised by severity, and remediation tracked to closure within defined SLAs. CC5.3 requires deploying control activities through policies and procedures including patch management. Evidence includes vulnerability scan results, dependency scanner reports (Snyk), cloud posture findings (Wiz), EDR detection records, and bug bounty programme results.',
            'CC5.3, CC7.1'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000010',
            'Vendor and Third-Party Risk Management',
            'soc2', 'vendor_risk',
            'CC9.2 requires the entity to assess and manage risks associated with vendors and business partners. Vendor risk assessments must be performed before engagement and reviewed periodically. Security requirements must be included in vendor contracts. Evidence includes vendor risk assessment records, third-party security questionnaire responses, subprocessor agreements, and dependency vulnerability scan results demonstrating ongoing monitoring of third-party components.',
            'CC9.2'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000011',
            'Availability and Business Continuity',
            'soc2', 'availability',
            'A1.1–A1.3 require the entity to maintain, monitor, and evaluate current processing capacity, manage environmental threats, implement backup and recovery procedures, and test recovery plans. SLO/SLA commitments must be monitored continuously. Evidence includes service monitoring records, uptime SLO configurations, on-call schedule and escalation records demonstrating 24/7 coverage, disaster recovery test results, and backup validation records.',
            'A1.1-A1.3'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0004-000000000012',
            'Confidentiality Controls',
            'soc2', 'confidentiality',
            'C1.1–C1.2 require identifying and maintaining confidentiality commitments, disposing of confidential information, and restricting access to confidential information to authorised parties. Encryption at rest and in transit, DLP controls, and access restrictions are primary mechanisms. Evidence includes IAM policy records enforcing least-privilege, CloudTrail records demonstrating controlled data access, cloud security posture findings related to data exposure, and encryption configuration records.',
            'C1.1-C1.2'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # HIPAA Security Rule — 45 CFR Part 164
    # UUID prefix: 00000000-0000-0000-0005-*
    # ══════════════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000001',
            'Security Management Process',
            'hipaa', 'security_management',
            '§164.308(a)(1) requires covered entities and business associates to implement policies and procedures to prevent, detect, contain, and correct security violations. This includes a risk analysis to identify threats and vulnerabilities to ePHI, a risk management programme to reduce risks to a reasonable level, a sanction policy for workforce members who fail to comply, and information system activity review. Evidence includes vulnerability scan results, cloud security posture findings, risk register records, and audit log review records.',
            '§164.308(a)(1)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000002',
            'Workforce Security and Clearance',
            'hipaa', 'workforce_security',
            '§164.308(a)(3) requires implementing policies to ensure all workforce members have appropriate access to ePHI and prevent those who do not have access from obtaining it. This includes workforce clearance procedures, authorisation and supervision, and termination procedures to remove access immediately upon departure. Evidence includes identity platform user records demonstrating access is tied to employment status, offboarding workflow records, and access provisioning and deprovisioning logs.',
            '§164.308(a)(3)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000003',
            'Information Access Management',
            'hipaa', 'information_access_management',
            '§164.308(a)(4) requires implementing policies for authorising access to ePHI consistent with the minimum necessary standard. Access authorisation, establishment, modification, and termination procedures must be documented. Role-based access controls must restrict ePHI access to those with a need-to-know. Evidence includes IAM user and policy records, identity platform access group and role records, and periodic access review documentation.',
            '§164.308(a)(4)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000004',
            'Security Awareness and Training',
            'hipaa', 'security_awareness',
            '§164.308(a)(5) requires a security awareness and training programme for all workforce members including management. Training must cover malicious software protection, log-in monitoring, and password management. Training must be provided upon hire and periodically thereafter. Evidence includes user directory records showing all workforce are enrolled in identity platforms (demonstrating they are tracked), training completion records, and security awareness programme documentation.',
            '§164.308(a)(5)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000005',
            'Security Incident Procedures',
            'hipaa', 'incident_procedures',
            '§164.308(a)(6) requires implementing policies and procedures to address security incidents. This includes identifying and responding to suspected or known security incidents, mitigating harmful effects, and documenting security incidents and their outcomes. A documented and tested incident response plan is required. Evidence includes on-call escalation policy records, incident ticket records demonstrating classification and response, incident response playbooks, and post-incident review documentation.',
            '§164.308(a)(6)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000006',
            'Contingency Plan and Business Continuity',
            'hipaa', 'contingency_plan',
            '§164.308(a)(7) requires establishing and implementing policies for responding to emergencies that damage systems containing ePHI. This includes a data backup plan, disaster recovery plan, emergency mode operation plan, testing and revision procedures, and applications and data criticality analysis. RTO and RPO must be defined and tested. Evidence includes backup configuration records, monitoring and uptime SLO records, disaster recovery test results, and business continuity plan documentation.',
            '§164.308(a)(7)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000007',
            'Access Control — Technical Safeguards',
            'hipaa', 'access_control',
            '§164.312(a)(1) requires implementing technical policies and procedures that allow only authorised persons or software programs to access ePHI. Required specifications include unique user identification, emergency access procedures, and automatic logoff. Addressable specifications include encryption and decryption of ePHI. MFA and role-based access are primary controls. Evidence includes IAM user records, identity platform user and policy records, MFA enrolment records, and session timeout configuration.',
            '§164.312(a)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000008',
            'Audit Controls',
            'hipaa', 'audit_controls',
            '§164.312(b) requires implementing hardware, software, and procedural mechanisms that record and examine activity in information systems that contain or use ePHI. Audit logs must capture access to ePHI, modifications, and failed access attempts. Logs must be retained and regularly reviewed. Evidence includes CloudTrail log records with ePHI-related API calls, Datadog and Splunk log records, log retention policy documentation, and audit log review records.',
            '§164.312(b)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0005-000000000009',
            'Transmission Security',
            'hipaa', 'transmission_security',
            '§164.312(e)(1) requires implementing technical security measures to guard against unauthorised access to ePHI transmitted over electronic communications networks. Encryption of ePHI in transit is an addressable implementation specification that is effectively required given modern threat levels. TLS must be enforced for all data in transit. Evidence includes Vault TLS configuration records, IAM policy records enforcing encrypted API calls, CloudTrail records demonstrating HTTPS-only access, and network security configuration.',
            '§164.312(e)'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # GDPR — Regulation (EU) 2016/679
    # UUID prefix: 00000000-0000-0000-0006-*
    # ══════════════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000001',
            'Lawful Basis and Consent Management',
            'gdpr', 'lawful_basis',
            'Art. 6 requires that personal data is processed only where a lawful basis applies: consent, contract, legal obligation, vital interests, public task, or legitimate interests. Where consent is the basis (Art. 7), it must be freely given, specific, informed, and unambiguous, with an equally easy withdrawal mechanism. Consent records must be maintained. Evidence includes identity platform user consent records, IAM policy configurations restricting data access, DLP policy records, and consent management platform records.',
            'Art. 6-7'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000002',
            'Data Subject Rights',
            'gdpr', 'data_subject_rights',
            'Art. 12–22 grant data subjects rights including: access (Art. 15), rectification (Art. 16), erasure/right to be forgotten (Art. 17), restriction of processing (Art. 18), data portability (Art. 20), and objection (Art. 21). Controllers must respond within one month (extendable to three). Procedures for receiving, verifying identity, and fulfilling requests must be documented. Evidence includes subject request records and response timelines, identity platform user records used for identity verification, and DSR process documentation.',
            'Art. 12-22'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000003',
            'Data Protection by Design and by Default',
            'gdpr', 'privacy_by_design',
            'Art. 25 requires implementing appropriate technical and organisational measures to ensure data protection principles are integrated into processing activities by design and by default. Data minimisation, purpose limitation, and storage limitation must be embedded in system design. Privacy-enhancing technologies and access controls limiting data exposure are primary mechanisms. Evidence includes IAM policy records demonstrating least-privilege, cloud security posture records, and privacy impact assessment documentation.',
            'Art. 25'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000004',
            'Data Protection Officer',
            'gdpr', 'data_protection_officer',
            'Art. 37–39 require appointing a DPO when processing is carried out by a public authority, involves large-scale systematic monitoring of individuals, or involves large-scale processing of special categories of data. The DPO must be registered with the supervisory authority, have expert knowledge of data protection law, and report directly to the highest management level. Evidence includes DPO appointment records, supervisory authority registration confirmation, and identity platform records documenting the DPO role.',
            'Art. 37-39'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000005',
            'Records of Processing Activities (RoPA)',
            'gdpr', 'records_of_processing',
            'Art. 30 requires controllers and processors to maintain records of processing activities. Records must include the purposes of processing, categories of data subjects and personal data, recipients, transfers to third countries, and retention periods. Records must be made available to the supervisory authority on request. Evidence includes RoPA records maintained in the compliance platform, IAM policy records documenting data access controls, and CloudTrail records demonstrating data processing activity.',
            'Art. 30'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000006',
            'Data Processor Agreements',
            'gdpr', 'processor_agreements',
            'Art. 28 requires that processing by a processor is governed by a binding contract (Data Processing Agreement) setting out the subject-matter, duration, nature, and purpose of processing, the type of personal data, and the controller''s obligations and rights. Processors may only act on documented instructions. Sub-processor agreements must impose equivalent obligations. Evidence includes DPA records with all vendors processing personal data, sub-processor lists, and vendor security assessment records.',
            'Art. 28'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000007',
            'Personal Data Breach Notification',
            'gdpr', 'breach_notification',
            'Art. 33 requires notifying the supervisory authority of a personal data breach within 72 hours of becoming aware, where feasible, unless the breach is unlikely to result in risk to individuals. Art. 34 requires communicating high-risk breaches to affected data subjects without undue delay. Breach records must document the nature, categories and approximate number of affected individuals, and remediation measures. Evidence includes breach incident records with notification timestamps, on-call alert records, and supervisory authority communication records.',
            'Art. 33-34'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000008',
            'Data Protection Impact Assessment',
            'gdpr', 'data_protection_impact',
            'Art. 35 requires conducting a DPIA before processing likely to result in high risk to individuals — including systematic profiling, large-scale processing of special categories, or systematic monitoring of public areas. DPIAs must assess necessity, proportionality, and risks, and identify mitigation measures. Prior consultation with the supervisory authority (Art. 36) is required where residual risk remains high. Evidence includes DPIA records, vulnerability and cloud posture findings informing risk assessments, and supervisory authority consultation records.',
            'Art. 35-36'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000009',
            'International Data Transfers',
            'gdpr', 'cross_border_transfers',
            'Art. 44–49 restrict transfers of personal data to third countries or international organisations to those providing adequate protection. Mechanisms include: adequacy decisions (Art. 45), appropriate safeguards such as Standard Contractual Clauses (Art. 46), Binding Corporate Rules (Art. 47), and derogations for specific situations (Art. 49). Transfer impact assessments are required for SCCs post-Schrems II. Evidence includes SCC records, transfer impact assessments, network policy records, and IAM policy records restricting data residency.',
            'Art. 44-49'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0006-000000000010',
            'Security of Processing',
            'gdpr', 'security_of_processing',
            'Art. 32 requires implementing appropriate technical and organisational measures to ensure a level of security appropriate to the risk, including: pseudonymisation and encryption, ongoing confidentiality, integrity, availability, and resilience, ability to restore data after incidents, and regular testing of security measures. Evidence includes IAM policy records, cloud security posture findings, vulnerability scan results, EDR deployment records, encryption configuration, and incident response capability records.',
            'Art. 32'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # PCI DSS v4.0 — Payment Card Industry Data Security Standard
    # UUID prefix: 00000000-0000-0000-0007-*
    # ══════════════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000001',
            'Network Security Controls',
            'pci_dss', 'network_security_controls',
            'Requirement 1 requires installing and maintaining network security controls to protect the cardholder data environment (CDE). Firewall rules must restrict inbound and outbound traffic to only that necessary. Network diagrams must document connections to and from the CDE. Wireless networks must be secured. Evidence includes firewall rule configuration records, network security group records, Cloudflare WAF configuration, zero-trust network access records (Tailscale, Zscaler), and network segmentation test results.',
            'Req. 1'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000002',
            'Secure Configurations for System Components',
            'pci_dss', 'secure_configuration',
            'Requirement 2 requires applying secure configurations to all system components. Default passwords must be changed, unnecessary services disabled, and security parameters set appropriately. Configuration standards must be developed for all component types. Evidence includes cloud security posture management findings (Wiz), IAM policy records enforcing secure defaults, CrowdStrike policy records, and hardening benchmark compliance records.',
            'Req. 2'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000003',
            'Protection of Stored Account Data',
            'pci_dss', 'data_protection',
            'Requirement 3 requires protecting stored account data. Sensitive authentication data must not be stored after authorisation. Primary account numbers (PANs) must be rendered unreadable (encryption, truncation, tokenisation, or hashing) wherever stored. Data retention and disposal policies must exist. Evidence includes IAM policy records enforcing encryption, Vault secrets management records, cloud storage encryption configuration, and data retention policy documentation.',
            'Req. 3'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000004',
            'Encryption of Cardholder Data in Transit',
            'pci_dss', 'encryption_in_transit',
            'Requirement 4 requires protecting primary account numbers during transmission over open, public networks using strong cryptography. TLS 1.2+ must be enforced for all cardholder data transmission. Certificate management must ensure validity and proper configuration. Evidence includes Vault TLS configuration and certificate records, IAM policy records mandating HTTPS-only API access, CloudTrail records confirming encrypted transmission, and certificate inventory records.',
            'Req. 4'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000005',
            'Malware Protection and Secure System Development',
            'pci_dss', 'vulnerability_management',
            'Requirement 5 requires protecting all systems against malware using anti-malware software or programmes. Requirement 6 requires developing and maintaining secure systems and software. All system components must be protected from known vulnerabilities by installing security patches within defined timeframes (1 month for critical). DAST and penetration testing are required. Evidence includes EDR deployment and scan records, Snyk dependency scan results, vulnerability scan records, and patch management records.',
            'Req. 5-6'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000006',
            'Access Control and Identity Management',
            'pci_dss', 'access_control',
            'Requirement 7 requires restricting access to system components and cardholder data by business need-to-know. Requirement 8 requires identifying users and authenticating access to system components. Each user must have a unique ID. MFA is required for all non-console administrative access to the CDE and all remote access. Shared and group accounts are prohibited except where technically required. Evidence includes IAM user and policy records, identity platform user records, MFA enrolment records, and GitHub membership records.',
            'Req. 7-8'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000007',
            'Physical Access Controls',
            'pci_dss', 'physical_access',
            'Requirement 9 requires restricting physical access to cardholder data. Physical entry controls must distinguish onsite personnel from visitors, restrict access to systems in the CDE to those with legitimate business need, and secure media containing cardholder data. Evidence includes IAM policy records restricting cloud console access to authorised personnel, CloudTrail records of console access, and physical security policy documentation.',
            'Req. 9'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000008',
            'Logging and Audit Trail Management',
            'pci_dss', 'logging_monitoring',
            'Requirement 10 requires logging and monitoring all access to system components and cardholder data. Audit logs must capture all individual access, actions by those with root/admin privileges, access to audit trails, invalid access attempts, use of identification mechanisms, initialisation and deletion of audit logs, and creation/deletion of system-level objects. Logs must be retained for at least 12 months with three months immediately available. Evidence includes CloudTrail, Datadog, and Splunk log records and retention configuration.',
            'Req. 10'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000009',
            'Regular Security Testing',
            'pci_dss', 'security_testing',
            'Requirement 11 requires testing the security of systems and networks regularly. Wireless access points must be scanned quarterly. Internal and external vulnerability scans must be performed quarterly and after significant changes. Penetration testing must be performed annually and after significant infrastructure or application changes. File-integrity monitoring must detect unauthorised changes. Evidence includes vulnerability scan reports, penetration test records and finding remediation, and wireless scan records.',
            'Req. 11'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000010',
            'Information Security Policy and Programme',
            'pci_dss', 'security_policy',
            'Requirement 12 requires supporting information security with organisational policies and programmes. A comprehensive information security policy must be established, published, maintained, and disseminated. Annual risk assessments must be performed. A security awareness programme must educate all personnel. Evidence includes IAM and identity platform policy records, security awareness training completion records, annual risk assessment documentation, and responsibility assignment records.',
            'Req. 12.1-12.7'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000011',
            'Third-Party and Service Provider Management',
            'pci_dss', 'service_provider_management',
            'Requirement 12.8–12.9 require maintaining and implementing policies for managing service providers with whom cardholder data is shared. A list of all service providers must be maintained. Written agreements must include acknowledgement of responsibility for security. Due diligence must be performed before engagement and monitoring maintained throughout. Incidents at service providers must be managed. Evidence includes vendor and subprocessor records, DPA records, and third-party security assessment results.',
            'Req. 12.8-12.9'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0007-000000000012',
            'Multi-Factor Authentication',
            'pci_dss', 'mfa_and_authentication',
            'Requirement 8.4–8.6 mandate MFA for all non-console administrative access into the CDE and for all remote network access (including for personnel and administrators) originating from outside the entity''s network. MFA must not be susceptible to replay attacks. Authentication factors must be from at least two different categories. Evidence includes MFA policy configuration records, MFA enrolment records across all identity platforms (Okta, Azure AD, Google Workspace), and privileged access review records.',
            'Req. 8.4-8.6'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # NIST Cybersecurity Framework 2.0
    # UUID prefix: 00000000-0000-0000-0008-*
    # ══════════════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0008-000000000001',
            'Govern — Cybersecurity Risk Governance',
            'nist_csf', 'govern',
            'The Govern function (GV) establishes the organisational context for cybersecurity risk decisions. It covers organisational context (GV.OC), risk management strategy (GV.RM), roles and responsibilities (GV.RR), policies (GV.PO), oversight (GV.OV), and cybersecurity supply chain risk management (GV.SC). Management must establish and communicate the risk appetite, assign cybersecurity responsibilities, and ensure accountability. Evidence includes IAM policy records, identity platform policy configurations, and governance documentation.',
            'GV'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0008-000000000002',
            'Identify — Asset and Risk Management',
            'nist_csf', 'identify',
            'The Identify function (ID) develops an organisational understanding of cybersecurity risk to systems, assets, data, and capabilities. It covers asset management (ID.AM), risk assessment (ID.RA), and improvement (ID.IM). Organisations must maintain an inventory of hardware, software, data, and external dependencies. Risk assessments must identify threats, vulnerabilities, likelihoods, and impacts. Evidence includes asset inventory records, vulnerability scan results, cloud posture findings, dependency scanner results, and risk register records.',
            'ID'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0008-000000000003',
            'Protect — Access, Training, and Data Security',
            'nist_csf', 'protect',
            'The Protect function (PR) implements safeguards to manage cybersecurity risk. It covers identity management and access control (PR.AA), awareness and training (PR.AT), data security (PR.DS), platform security (PR.PS), and technology infrastructure resilience (PR.IR). MFA, least-privilege access, encryption, endpoint security, and patch management are primary protective controls. Evidence includes IAM and identity platform records, MFA enrolment, EDR and MDM records, Vault encryption records, and patch compliance records.',
            'PR'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0008-000000000004',
            'Detect — Continuous Monitoring and Anomaly Detection',
            'nist_csf', 'detect',
            'The Detect function (DE) enables timely discovery of cybersecurity events. It covers continuous monitoring (DE.CM) and adverse event analysis (DE.AE). Monitoring must cover network traffic, user activity, physical environment, external service provider activity, and the vulnerability management process. Anomalous activity must be detected and analysed to understand attack targets and methods. Evidence includes CloudTrail audit logs, SIEM records (Datadog, Splunk), EDR detection records (CrowdStrike, SentinelOne), and cloud posture monitoring findings.',
            'DE'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0008-000000000005',
            'Respond — Incident Management and Communication',
            'nist_csf', 'respond',
            'The Respond function (RS) enables action following a cybersecurity incident. It covers incident management (RS.MA), incident analysis (RS.AN), incident response reporting and communication (RS.CO), and incident mitigation (RS.MI). Incident response plans must be coordinated with internal and external stakeholders. Containment and eradication actions must be documented. Post-incident analysis must inform improvements. Evidence includes incident ticket records, on-call escalation records, incident response playbooks, and post-incident review reports.',
            'RS'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0008-000000000006',
            'Recover — Restoration and Improvement',
            'nist_csf', 'recover',
            'The Recover function (RC) supports timely restoration of capabilities following a cybersecurity incident. It covers incident recovery plan execution (RC.RP), incident recovery communication (RC.CO), and improvements informed by post-incident lessons-learned (RC.IM). Recovery plans must define RTO/RPO targets. Business continuity and disaster recovery plans must be tested regularly. Evidence includes service monitoring and uptime SLO records demonstrating recovery capability, backup and DR test records, and on-call runbook documentation.',
            'RC'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    # ══════════════════════════════════════════════════════════════════════════
    # CCPA / CPRA — California Consumer Privacy Act (as amended)
    # UUID prefix: 00000000-0000-0000-0009-*
    # ══════════════════════════════════════════════════════════════════════════

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0009-000000000001',
            'Consumer Rights Fulfilment',
            'ccpa', 'consumer_rights',
            '§1798.100–125 grant California consumers the right to know what personal information is collected, sold, or disclosed; the right to delete personal information; the right to correct inaccurate personal information (CPRA); the right to opt-out of sale/sharing; the right to limit use of sensitive personal information; and the right to non-discrimination. Businesses must respond to verifiable consumer requests within 45 days. Evidence includes subject request records with response timestamps, identity platform records for identity verification, and consumer rights fulfilment process documentation.',
            '§1798.100-125'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0009-000000000002',
            'Privacy Notice and Disclosure',
            'ccpa', 'privacy_notice',
            '§1798.100(b) requires businesses to inform consumers at or before the point of collection of the categories of personal information collected and the purposes for which it is used. The privacy policy must disclose categories of personal information collected in the prior 12 months, purposes, sources, third parties with whom it is shared, and consumer rights. The privacy policy must be updated annually. Evidence includes privacy policy documentation, data flow records documenting categories collected, and at-collection notice records.',
            '§1798.100(b), §1798.130'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0009-000000000003',
            'Data Inventory and Mapping',
            'ccpa', 'data_inventory',
            '§1798.115 requires businesses to disclose the categories of personal information collected, sold, or disclosed for a business purpose. Maintaining an accurate data inventory is a prerequisite for honouring consumer rights and responding to regulatory inquiries. Data flows must document sources, categories of personal information, purposes, and recipients. Evidence includes data flow records, RoPA records, CloudTrail records documenting data access patterns, and IAM policy records demonstrating data access controls.',
            '§1798.115'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0009-000000000004',
            'Opt-Out of Sale and Sharing',
            'ccpa', 'opt_out_mechanisms',
            '§1798.120 grants consumers the right to opt-out of the sale or sharing of their personal information. Businesses must provide a clear and conspicuous "Do Not Sell or Share My Personal Information" link. Opt-out requests must be honoured within 15 business days. Global Privacy Control (GPC) signals must be honoured (CPRA). Evidence includes opt-out mechanism records, consent management platform configurations, IAM policy records restricting data sharing, and opt-out request processing records.',
            '§1798.120, §1798.135'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0009-000000000005',
            'Service Provider and Contractor Contracts',
            'ccpa', 'service_provider_contracts',
            '§1798.140 defines service providers and contractors as entities that process personal information pursuant to a written contract that prohibits retaining, using, or disclosing it for purposes other than performing services. Contracts must include specific CCPA-required provisions. Businesses must conduct reasonable due diligence on service providers. Evidence includes service provider and contractor agreement records containing CCPA-compliant provisions, vendor assessment records, and subprocessor lists.',
            '§1798.140'
        ) ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES (
            '00000000-0000-0000-0009-000000000006',
            'Sensitive Personal Information Controls',
            'ccpa', 'sensitive_personal_information',
            '§1798.121 (CPRA) grants consumers the right to limit the use and disclosure of sensitive personal information (SPI) — including SSNs, financial account data, precise geolocation, racial/ethnic origin, religious beliefs, biometric data, and health information — to uses necessary to perform requested services. Businesses must implement data minimisation for SPI and provide a "Limit the Use of My Sensitive Personal Information" link if SPI is used beyond permitted purposes. Evidence includes IAM policy records restricting SPI access, data classification records, and cloud posture findings.',
            '§1798.121'
        ) ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM controls
        WHERE framework IN ('soc2', 'hipaa', 'gdpr', 'pci_dss', 'nist_csf', 'ccpa');
    """)
