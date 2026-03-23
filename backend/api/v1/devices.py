import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.deps import get_current_admin, get_current_user
from models.device import Device
from models.user import User

router = APIRouter(prefix="/devices", tags=["devices"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class DeviceCreate(BaseModel):
    device_name: str
    device_type: str = "laptop"
    os_type: str = "macos"
    os_version: Optional[str] = None
    serial_number: Optional[str] = None
    user_id: Optional[str] = None
    notes: Optional[str] = None


class DeviceUpdate(BaseModel):
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    serial_number: Optional[str] = None
    user_id: Optional[str] = None
    notes: Optional[str] = None
    disk_encrypted: Optional[bool] = None
    lockscreen_enabled: Optional[bool] = None
    antivirus_installed: Optional[bool] = None


class AttestRequest(BaseModel):
    device_name: str
    device_type: str = "laptop"
    os_type: str = "macos"
    os_version: Optional[str] = None
    serial_number: Optional[str] = None
    disk_encrypted: bool
    lockscreen_enabled: bool
    antivirus_installed: bool


class DeviceOut(BaseModel):
    id: str
    company_id: str
    user_id: Optional[str]
    device_name: str
    device_type: str
    os_type: str
    os_version: Optional[str]
    serial_number: Optional[str]
    attested_by_email: Optional[str]
    disk_encrypted: bool
    lockscreen_enabled: bool
    antivirus_installed: bool
    last_attested_at: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str
    # Computed
    compliance_score: int
    is_compliant: bool

    model_config = {"from_attributes": True}


def _to_out(d: Device) -> DeviceOut:
    checks = [d.disk_encrypted, d.lockscreen_enabled, d.antivirus_installed]
    score = int(sum(checks) / len(checks) * 100)
    return DeviceOut(
        id=str(d.id),
        company_id=str(d.company_id),
        user_id=str(d.user_id) if d.user_id else None,
        device_name=d.device_name,
        device_type=d.device_type,
        os_type=d.os_type,
        os_version=d.os_version,
        serial_number=d.serial_number,
        attested_by_email=d.attested_by_email,
        disk_encrypted=d.disk_encrypted,
        lockscreen_enabled=d.lockscreen_enabled,
        antivirus_installed=d.antivirus_installed,
        last_attested_at=d.last_attested_at.isoformat() if d.last_attested_at else None,
        notes=d.notes,
        created_at=d.created_at.isoformat(),
        updated_at=d.updated_at.isoformat(),
        compliance_score=score,
        is_compliant=score == 100,
    )


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.get("", response_model=list[DeviceOut])
async def list_devices(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device)
        .where(Device.company_id == current_user.company_id)
        .order_by(Device.created_at.desc())
    )
    return [_to_out(d) for d in result.scalars().all()]


@router.post("", response_model=DeviceOut, status_code=201)
async def create_device(
    body: DeviceCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    user_uuid = uuid.UUID(body.user_id) if body.user_id else None
    device = Device(
        company_id=current_user.company_id,
        user_id=user_uuid,
        device_name=body.device_name,
        device_type=body.device_type,
        os_type=body.os_type,
        os_version=body.os_version,
        serial_number=body.serial_number,
        notes=body.notes,
    )
    db.add(device)
    await db.commit()
    await db.refresh(device)
    return _to_out(device)


@router.patch("/{device_id}", response_model=DeviceOut)
async def update_device(
    device_id: str,
    body: DeviceUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(Device.id == uuid.UUID(device_id), Device.company_id == current_user.company_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    if body.device_name is not None:
        device.device_name = body.device_name
    if body.device_type is not None:
        device.device_type = body.device_type
    if body.os_type is not None:
        device.os_type = body.os_type
    if body.os_version is not None:
        device.os_version = body.os_version
    if body.serial_number is not None:
        device.serial_number = body.serial_number
    if body.notes is not None:
        device.notes = body.notes
    if body.user_id is not None:
        device.user_id = uuid.UUID(body.user_id) if body.user_id else None
    if body.disk_encrypted is not None:
        device.disk_encrypted = body.disk_encrypted
    if body.lockscreen_enabled is not None:
        device.lockscreen_enabled = body.lockscreen_enabled
    if body.antivirus_installed is not None:
        device.antivirus_installed = body.antivirus_installed

    await db.commit()
    await db.refresh(device)
    return _to_out(device)


@router.delete("/{device_id}", status_code=204)
async def delete_device(
    device_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(Device.id == uuid.UUID(device_id), Device.company_id == current_user.company_id)
    )
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(device)
    await db.commit()


# ── Self-attest (any authenticated user) ─────────────────────────────────────

@router.post("/attest", response_model=DeviceOut)
async def attest_device(
    body: AttestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Employee self-attests their device's security controls.
    Creates a new device record or updates existing one for this user.
    """
    # Look for existing device for this user
    existing = await db.execute(
        select(Device).where(
            Device.company_id == current_user.company_id,
            Device.user_id == current_user.id,
        )
    )
    device = existing.scalars().first()

    now = datetime.now(timezone.utc)

    if device:
        device.device_name = body.device_name
        device.device_type = body.device_type
        device.os_type = body.os_type
        device.os_version = body.os_version
        device.serial_number = body.serial_number
        device.disk_encrypted = body.disk_encrypted
        device.lockscreen_enabled = body.lockscreen_enabled
        device.antivirus_installed = body.antivirus_installed
        device.attested_by_email = current_user.email
        device.last_attested_at = now
    else:
        device = Device(
            company_id=current_user.company_id,
            user_id=current_user.id,
            device_name=body.device_name,
            device_type=body.device_type,
            os_type=body.os_type,
            os_version=body.os_version,
            serial_number=body.serial_number,
            disk_encrypted=body.disk_encrypted,
            lockscreen_enabled=body.lockscreen_enabled,
            antivirus_installed=body.antivirus_installed,
            attested_by_email=current_user.email,
            last_attested_at=now,
        )
        db.add(device)

    await db.commit()
    await db.refresh(device)
    return _to_out(device)


@router.get("/my", response_model=Optional[DeviceOut])
async def get_my_device(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Device).where(
            Device.company_id == current_user.company_id,
            Device.user_id == current_user.id,
        )
    )
    device = result.scalars().first()
    return _to_out(device) if device else None
