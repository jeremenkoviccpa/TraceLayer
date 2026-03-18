import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.asset import Asset
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
