"""Seed ISO/IEC 42001:2023 AI Management System controls and framework version.

Revision ID: 074_iso42001
Revises: 073_change_requests
Create Date: 2026-04-06
"""

from alembic import op

revision = "074_iso42001"
down_revision = "073_change_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Controls (UUID prefix 00000000-0000-0000-0017-*) ──────────────────────
    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000001',
            'AI Governance and Leadership',
            'iso42001',
            'ai_governance',
            'Top management must establish, maintain, and continually improve an AI Management System (AIMS). Clause 4 requires understanding internal/external context and interested parties. Clause 5 requires a formal AI policy, defined organizational roles, and management accountability for AI objectives. Evidence includes AI governance policies, board-level AI charters, role assignments, and management review records.',
            'Cl.4-5'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000002',
            'AI Risk Assessment and Treatment',
            'iso42001',
            'ai_risk_management',
            'Organizations must perform systematic AI risk assessments covering risks to individuals, groups, and society from AI system behaviour (Clause 6.1). A risk treatment plan must address identified risks through technical controls, human oversight, or system modification. Evidence includes AI risk registers, impact assessments, risk treatment plans, and residual risk acceptance records.',
            'Cl.6.1'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000003',
            'AI Objectives and Planning',
            'iso42001',
            'ai_governance',
            'Measurable AI objectives must be established, aligned to the AI policy, and communicated across the organization (Clause 6.2). Plans must specify what will be done, resources required, responsible parties, timelines, and how results will be evaluated. Evidence includes AI roadmaps, OKR/KPI records, planning documents, and objective review minutes.',
            'Cl.6.2'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000004',
            'Support — Resources, Competence, and Awareness',
            'iso42001',
            'ai_competence',
            'Organizations must ensure personnel working on AI systems are competent via education, training, or experience (Clause 7.2). An awareness programme covering the AI policy, AI risks, and individual responsibilities is required (Clause 7.3). Documented information must be controlled (Clause 7.5). Evidence includes training completion records, competency matrices, awareness campaigns, and document management logs.',
            'Cl.7'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000005',
            'AI System Impact Assessment',
            'iso42001',
            'ai_impact_assessment',
            'Before deploying an AI system, organizations must conduct an AI system impact assessment (AISIA) evaluating potential impacts on individuals, groups, and society (Clause 8.3). The assessment must cover intended use, reasonably foreseeable misuse, and interactions with humans. Evidence includes AISIA documents, pre-deployment review sign-offs, and stakeholder consultation records.',
            'Cl.8.3'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000006',
            'AI Data Management and Training Data Governance',
            'iso42001',
            'data_governance',
            'Organizations must implement controls over data used across the AI system lifecycle — collection, processing, labelling, and storage (Clause 8.4). Data quality, provenance, bias, and representativeness must be assessed. Special categories of sensitive data require additional controls. Evidence includes data governance policies, data quality reports, bias audits, data lineage records, and labelling guidelines.',
            'Cl.8.4'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000007',
            'AI System Development, Testing, and Validation',
            'iso42001',
            'ai_development',
            'AI systems must be developed and tested following documented procedures covering design specifications, training, validation, and performance benchmarking (Clause 8.5). Accuracy, robustness, and security testing must be performed before production deployment. Evidence includes model cards, test results, validation reports, performance benchmarks, and security testing artefacts.',
            'Cl.8.5'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000008',
            'Human Oversight and Accountability',
            'iso42001',
            'human_oversight',
            'Appropriate human oversight mechanisms must be designed into AI systems to allow intervention, correction, and shutdown (Clause 8.6). Systems must not override human decisions without explicit design intent. Accountability must be traceable to individuals. Evidence includes oversight policies, human-in-the-loop workflow records, intervention logs, and accountability matrices.',
            'Cl.8.6'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000009',
            'Performance Evaluation and Monitoring',
            'iso42001',
            'ai_monitoring',
            'Organizations must monitor, measure, analyse, and evaluate AI system performance in production (Clause 9.1). Internal audits of the AIMS must be conducted at planned intervals (Clause 9.2). Management reviews must assess AIMS suitability, adequacy, and effectiveness (Clause 9.3). Evidence includes model performance dashboards, drift detection logs, internal audit reports, and management review minutes.',
            'Cl.9'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000010',
            'Continual Improvement and Corrective Action',
            'iso42001',
            'continual_improvement',
            'Nonconformities must be identified, investigated, corrected, and subject to root-cause analysis with corrective actions (Clause 10.1). The AIMS must be continually improved to enhance performance and address emerging AI risks (Clause 10.2). Evidence includes nonconformity records, corrective action plans, lessons-learned logs, and improvement tracking registers.',
            'Cl.10'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000011',
            'Transparency and Explainability',
            'iso42001',
            'transparency',
            'Annex A Control 6.1 requires appropriate transparency of AI systems to stakeholders — disclosing when AI is in use, providing meaningful explanations of AI-driven decisions, and maintaining explainability appropriate to the application context and regulatory requirements. Evidence includes transparency notices, explainability documentation (SHAP/LIME analyses), model cards, and decision explanation logs.',
            'A.6.1'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000012',
            'Bias Detection and Fairness',
            'iso42001',
            'fairness',
            'Annex A Control 6.2 requires identifying, assessing, and mitigating harmful bias in AI system outputs across protected characteristics and demographic groups. Fairness metrics must be defined and continuously monitored. Evidence includes bias audit reports, fairness metric dashboards, demographic parity analyses, mitigation records, and re-testing results after bias remediation.',
            'A.6.2'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000013',
            'Privacy and Data Protection in AI Systems',
            'iso42001',
            'ai_privacy',
            'Annex A Control 8.2 requires integrating data protection principles into AI system design and operation — data minimisation, purpose limitation, and privacy-enhancing technologies (differential privacy, federated learning, synthetic data). Data protection impact assessments for AI processing must be conducted. Evidence includes AI DPIA records, privacy-by-design documentation, and data minimisation audit results.',
            'A.8.2'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000014',
            'AI Incident Management and Reporting',
            'iso42001',
            'ai_incident_management',
            'Annex A Control 9.1 requires procedures for detecting, recording, investigating, and responding to AI-specific incidents including unexpected outputs, performance degradation, safety failures, and security breaches affecting AI systems. Post-incident analysis and model recall/rollback capabilities are required. Evidence includes AI incident records, post-incident analyses, rollback logs, and incident response playbooks.',
            'A.9.1'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    op.execute("""
        INSERT INTO controls (id, name, framework, category, description, external_id)
        VALUES
        (
            '00000000-0000-0000-0017-000000000015',
            'AI Supplier and Third-Party Management',
            'iso42001',
            'ai_supply_chain',
            'Annex A Control 10.1 requires assessing and managing risks introduced by third-party AI components, models, datasets, and services. Supplier AI governance capabilities must be evaluated. Contractual requirements for AI transparency, auditability, and incident notification must be established. Evidence includes AI supplier assessments, due diligence records, supplier AI contracts, and third-party model audit reports.',
            'A.10.1'
        )
        ON CONFLICT (id) DO NOTHING;
    """)

    # ── Framework versions ────────────────────────────────────────────────────
    op.execute("""
        INSERT INTO framework_versions (id, framework_key, version, display_name, published_at, is_current)
        SELECT gen_random_uuid(), 'iso42001', '2023', 'ISO/IEC 42001:2023', '2023-12-18', true
        WHERE NOT EXISTS (
            SELECT 1 FROM framework_versions WHERE framework_key = 'iso42001'
        );
    """)

    # ── Framework source manifests ─────────────────────────────────────────────
    op.execute("""
        INSERT INTO framework_source_manifests (id, framework_key, source_url, current_version)
        SELECT gen_random_uuid(), 'iso42001', 'https://www.iso.org/standard/81230.html', '2023'
        WHERE NOT EXISTS (
            SELECT 1 FROM framework_source_manifests WHERE framework_key = 'iso42001'
        );
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM controls
        WHERE framework = 'iso42001';
    """)

    op.execute("""
        DELETE FROM framework_versions
        WHERE framework_key = 'iso42001';
    """)

    op.execute("""
        DELETE FROM framework_source_manifests
        WHERE framework_key = 'iso42001';
    """)
