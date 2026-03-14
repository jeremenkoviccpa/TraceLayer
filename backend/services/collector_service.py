import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from integrations.registry import get_adapter
from models.associations import evidence_controls
from models.control import Control
from models.evidence import Evidence
from models.integration import Integration
from utils.encryption import decrypt_credentials

logger = logging.getLogger(__name__)


async def run_collection(
    company_id: uuid.UUID,
    integration_type: str,
    db: AsyncSession,
) -> int:
    """
    Run a full evidence collection cycle for one integration.
    Returns the number of evidence records upserted.
    """
    result = await db.execute(
        select(Integration).where(
            Integration.company_id == company_id,
            Integration.integration_type == integration_type,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        raise ValueError(f"Integration '{integration_type}' not found for company {company_id}")

    try:
        credentials = decrypt_credentials(integration.credentials_enc)
        adapter = get_adapter(integration_type)
        await adapter.connect(credentials)

        raw_data = await adapter.collect_evidence()
        normalized = adapter.normalize(raw_data)

        # Load controls into a lookup: category -> control_id
        controls_result = await db.execute(select(Control))
        control_map: dict[str, uuid.UUID] = {
            c.category: c.id for c in controls_result.scalars().all()
        }

        now = datetime.now(timezone.utc)
        count = 0

        for record in normalized:
            ts = _parse_timestamp(record.get("timestamp"), fallback=now)

            # Upsert evidence, getting the ID back via RETURNING
            insert_stmt = pg_insert(Evidence).values(
                company_id=str(company_id),
                integration=record["integration"],
                control=record["control"],
                evidence_type=record["evidence_type"],
                source_id=record["source_id"],
                timestamp=ts,
                data=record["data"],
            )
            upsert_stmt = insert_stmt.on_conflict_do_update(
                index_elements=["company_id", "integration", "evidence_type", "source_id"],
                set_={
                    "data": insert_stmt.excluded.data,
                    "timestamp": insert_stmt.excluded.timestamp,
                    "updated_at": now,
                },
            ).returning(Evidence.id)

            ev_result = await db.execute(upsert_stmt)
            evidence_id = ev_result.scalar_one()

            # Link evidence to control via junction table
            control_id = control_map.get(record["control"])
            if control_id and evidence_id:
                ec_stmt = pg_insert(evidence_controls).values(
                    evidence_id=evidence_id,
                    control_id=control_id,
                ).on_conflict_do_nothing()
                await db.execute(ec_stmt)

            count += 1

        integration.last_collected_at = now
        integration.status = "active"
        integration.last_error = None
        await db.commit()

        logger.info(
            "Collection complete: company=%s integration=%s records=%d",
            company_id, integration_type, count,
        )
        return count

    except Exception as e:
        logger.error(
            "Collection failed: company=%s integration=%s error=%s",
            company_id, integration_type, e,
        )
        integration.status = "error"
        integration.last_error = str(e)
        await db.commit()
        raise


def _parse_timestamp(value: str | None, fallback: datetime) -> datetime:
    if not value:
        return fallback
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return fallback
