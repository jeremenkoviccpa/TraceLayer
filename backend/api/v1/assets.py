import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.asset import Asset
from models.evidence import Evidence
from models.user import User
from schemas.asset import AssetCreate, AssetResponse, AssetUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assets", tags=["assets"])


def _to_response(asset: Asset, owner_map: dict) -> AssetResponse:
    owner_id = asset.owner_user_id
    return AssetResponse(
        id=str(asset.id),
        company_id=str(asset.company_id),
        name=asset.name,
        asset_type=asset.asset_type,
        owner_user_id=str(owner_id) if owner_id else None,
        owner_name=owner_map.get(owner_id) if owner_id else None,
        environment=asset.environment,
        classification=asset.classification,
        status=asset.status,
        vendor=asset.vendor,
        version=asset.version,
        ip_address=asset.ip_address,
        location=asset.location,
        description=asset.description,
        last_reviewed_at=asset.last_reviewed_at,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.get("", response_model=list[AssetResponse])
async def list_assets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Asset).where(Asset.company_id == current_user.company_id).order_by(Asset.created_at.desc())
    )
    assets = result.scalars().all()

    owner_ids = {a.owner_user_id for a in assets if a.owner_user_id is not None}
    owner_map: dict = {}
    if owner_ids:
        users_result = await db.execute(
            select(User.id, User.full_name, User.email).where(User.id.in_(owner_ids))
        )
        for row in users_result.all():
            owner_map[row.id] = row.full_name or row.email

    return [_to_response(a, owner_map) for a in assets]


@router.post("", response_model=AssetResponse, status_code=201)
async def create_asset(
    body: AssetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    owner_user_id: Optional[uuid.UUID] = None
    if body.owner_user_id:
        res = await db.execute(
            select(User).where(User.id == uuid.UUID(body.owner_user_id), User.company_id == current_user.company_id)
        )
        owner = res.scalar_one_or_none()
        if not owner:
            raise HTTPException(status_code=400, detail="owner_user_id does not belong to your company")
        owner_user_id = owner.id

    asset = Asset(
        company_id=current_user.company_id,
        name=body.name,
        asset_type=body.asset_type,
        owner_user_id=owner_user_id,
        environment=body.environment,
        classification=body.classification,
        status=body.status,
        vendor=body.vendor,
        version=body.version,
        ip_address=body.ip_address,
        location=body.location,
        description=body.description,
        last_reviewed_at=body.last_reviewed_at,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)

    owner_map: dict = {}
    if owner_user_id:
        res = await db.execute(select(User.id, User.full_name, User.email).where(User.id == owner_user_id))
        row = res.one_or_none()
        if row:
            owner_map[row.id] = row.full_name or row.email

    return _to_response(asset, owner_map)


@router.patch("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: uuid.UUID,
    body: AssetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.company_id == current_user.company_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    update_data = body.model_dump(exclude_unset=True)

    if "owner_user_id" in update_data:
        raw_id = update_data.pop("owner_user_id")
        if raw_id is None:
            asset.owner_user_id = None
        else:
            res = await db.execute(
                select(User).where(User.id == uuid.UUID(raw_id), User.company_id == current_user.company_id)
            )
            owner = res.scalar_one_or_none()
            if not owner:
                raise HTTPException(status_code=400, detail="owner_user_id does not belong to your company")
            asset.owner_user_id = owner.id

    for field, value in update_data.items():
        setattr(asset, field, value)

    await db.commit()
    await db.refresh(asset)

    owner_map: dict = {}
    if asset.owner_user_id:
        res = await db.execute(select(User.id, User.full_name, User.email).where(User.id == asset.owner_user_id))
        row = res.one_or_none()
        if row:
            owner_map[row.id] = row.full_name or row.email

    return _to_response(asset, owner_map)


@router.post("/sync", status_code=200)
async def sync_assets_from_integrations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Pull asset data from collected integration evidence and create Asset records."""
    ASSET_EVIDENCE_TYPES = {"repositories", "ec2_instances", "s3_buckets", "rds_instances"}

    evidence_result = await db.execute(
        select(Evidence).where(
            Evidence.company_id == current_user.company_id,
            Evidence.evidence_type.in_(ASSET_EVIDENCE_TYPES),
        )
    )
    all_evidence = evidence_result.scalars().all()

    existing_result = await db.execute(
        select(Asset.name, Asset.asset_type).where(Asset.company_id == current_user.company_id)
    )
    existing_keys = {(row[0], row[1]) for row in existing_result.all()}

    created = 0
    skipped = 0

    for ev in all_evidence:
        data = ev.data or {}
        asset_name: Optional[str] = None
        asset_type: str = "other"
        vendor: Optional[str] = None
        environment: str = "production"
        classification: str = "internal"
        status: str = "active"
        description: Optional[str] = None
        location: Optional[str] = None

        if ev.evidence_type == "repositories":
            asset_name = data.get("name")
            full_name = data.get("full_name", asset_name)
            private = data.get("private", True)
            archived = data.get("archived", False)
            asset_type = "software"
            vendor = "GitHub"
            classification = "internal" if private else "public"
            status = "retired" if archived else "active"
            description = f"GitHub repository: {full_name}"
            location = "GitHub"

        elif ev.evidence_type == "ec2_instances":
            asset_name = data.get("InstanceId") or data.get("instance_id")
            asset_type = "cloud"
            vendor = "AWS"
            environment = data.get("environment", "production")
            description = f"EC2 instance: {data.get('InstanceType', '')} in {data.get('region', ev.integration)}"
            location = data.get("region", "aws")

        elif ev.evidence_type == "s3_buckets":
            asset_name = data.get("Name") or data.get("name")
            asset_type = "cloud"
            vendor = "AWS"
            description = f"S3 bucket: {asset_name}"
            location = data.get("region", "aws")

        if not asset_name:
            continue

        key = (asset_name, asset_type)
        if key in existing_keys:
            skipped += 1
            continue

        asset = Asset(
            company_id=current_user.company_id,
            name=asset_name,
            asset_type=asset_type,
            vendor=vendor,
            environment=environment,
            classification=classification,
            status=status,
            description=description,
            location=location,
        )
        db.add(asset)
        existing_keys.add(key)
        created += 1

    await db.commit()
    return {"created": created, "skipped": skipped}


@router.delete("/{asset_id}", status_code=204)
async def delete_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Asset).where(Asset.id == asset_id, Asset.company_id == current_user.company_id)
    )
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    await db.delete(asset)
    await db.commit()
