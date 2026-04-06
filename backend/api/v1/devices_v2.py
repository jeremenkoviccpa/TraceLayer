"""Endpoint/device security tracking (SOC 2 CC6.7)."""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_user
from models.device_v2 import DeviceV2
from models.user import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/devices-v2", tags=["devices-v2"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class DeviceCreate(BaseModel):
    employee_email: Optional[str] = None
    employee_name: Optional[str] = None
    hostname: Optional[str] = None
    serial_number: Optional[str] = None
    os_type: Optional[str] = None  # mac | windows | linux | other
    os_version: Optional[str] = None
    disk_encryption: bool = False
    screen_lock: bool = False
    mdm_enrolled: bool = False
    mdm_platform: Optional[str] = None
    notes: Optional[str] = None


class DeviceUpdate(BaseModel):
    employee_email: Optional[str] = None
    employee_name: Optional[str] = None
    hostname: Optional[str] = None
    serial_number: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    disk_encryption: Optional[bool] = None
    screen_lock: Optional[bool] = None
    mdm_enrolled: Optional[bool] = None
    mdm_platform: Optional[str] = None
    notes: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _compute_status(disk_encryption: bool, screen_lock: bool, mdm_enrolled: bool) -> str:
    if disk_encryption and screen_lock and mdm_enrolled:
        return "compliant"
    if not disk_encryption or not screen_lock or not mdm_enrolled:
        return "non_compliant"
    return "unknown"


def _device_dict(d: DeviceV2) -> dict:
    return {
        "id": str(d.id),
        "company_id": str(d.company_id),
        "employee_email": d.employee_email,
        "employee_name": d.employee_name,
        "hostname": d.hostname,
        "serial_number": d.serial_number,
        "os_type": d.os_type,
        "os_version": d.os_version,
        "disk_encryption": d.disk_encryption,
        "screen_lock": d.screen_lock,
        "mdm_enrolled": d.mdm_enrolled,
        "mdm_platform": d.mdm_platform,
        "last_seen_at": d.last_seen_at.isoformat() if d.last_seen_at else None,
        "status": d.status,
        "notes": d.notes,
        "created_at": d.created_at.isoformat(),
        "updated_at": d.updated_at.isoformat(),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("")
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeviceV2)
        .where(DeviceV2.company_id == current_user.company_id)
        .order_by(DeviceV2.created_at.desc())
    )
    return [_device_dict(d) for d in result.scalars().all()]


@router.get("/stats")
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeviceV2).where(DeviceV2.company_id == current_user.company_id)
    )
    devices = result.scalars().all()
    total = len(devices)
    compliant = sum(1 for d in devices if d.status == "compliant")
    non_compliant = sum(1 for d in devices if d.status == "non_compliant")
    unknown = sum(1 for d in devices if d.status == "unknown")
    compliance_pct = round(compliant / total * 100) if total else 0
    return {
        "total": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "unknown": unknown,
        "compliance_pct": compliance_pct,
    }


@router.post("", status_code=201)
async def create_device(
    body: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    now = datetime.now(timezone.utc)
    status = _compute_status(body.disk_encryption, body.screen_lock, body.mdm_enrolled)
    device = DeviceV2(
        id=uuid.uuid4(),
        company_id=current_user.company_id,
        employee_email=body.employee_email,
        employee_name=body.employee_name,
        hostname=body.hostname,
        serial_number=body.serial_number,
        os_type=body.os_type,
        os_version=body.os_version,
        disk_encryption=body.disk_encryption,
        screen_lock=body.screen_lock,
        mdm_enrolled=body.mdm_enrolled,
        mdm_platform=body.mdm_platform,
        status=status,
        notes=body.notes,
        created_at=now,
        updated_at=now,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return _device_dict(device)


@router.patch("/{device_id}")
async def update_device(
    device_id: uuid.UUID,
    body: DeviceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeviceV2).where(
            DeviceV2.id == device_id,
            DeviceV2.company_id == current_user.company_id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(device, field, value)

    device.status = _compute_status(device.disk_encryption, device.screen_lock, device.mdm_enrolled)
    device.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(device)
    return _device_dict(device)


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(DeviceV2).where(
            DeviceV2.id == device_id,
            DeviceV2.company_id == current_user.company_id,
        )
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()
