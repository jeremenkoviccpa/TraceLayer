import logging
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import get_db
from core.deps import get_current_user
from models.document import Document
from models.user import User
from services import audit_service, storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

DOCUMENTS_BUCKET = "documents"


class DocumentResponse(BaseModel):
    id: uuid.UUID
    resource_type: str
    resource_id: Optional[str]
    filename: str
    file_size: int
    mime_type: str
    uploader_email: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile,
    resource_type: str = Form(...),
    resource_id: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a file as a document attachment and store it in Supabase Storage."""
    file_bytes = await file.read()
    file_name = file.filename or "upload"
    file_size = len(file_bytes)
    content_type = file.content_type or "application/octet-stream"

    unique_id = uuid.uuid4()
    storage_path = (
        f"{current_user.company_id}/{resource_type}/"
        f"{resource_id or 'general'}/{unique_id}/{file_name}"
    )
    storage_url = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/"
        f"{DOCUMENTS_BUCKET}/{storage_path}"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            storage_url,
            content=file_bytes,
            headers={
                "Authorization": f"Bearer {settings.supabase_service_key}",
                "Content-Type": content_type,
                "x-upsert": "true",
            },
        )

    if resp.status_code not in (200, 201):
        logger.error("Supabase Storage upload failed: %s %s", resp.status_code, resp.text)
        raise HTTPException(status_code=502, detail="File upload to storage failed")

    public_url = (
        f"{settings.supabase_url.rstrip('/')}/storage/v1/object/public/"
        f"{DOCUMENTS_BUCKET}/{storage_path}"
    )

    doc = Document(
        company_id=current_user.company_id,
        uploader_user_id=current_user.id,
        resource_type=resource_type,
        resource_id=resource_id,
        filename=file_name,
        file_url=public_url,
        storage_path=storage_path,
        file_size=file_size,
        mime_type=content_type,
    )
    db.add(doc)
    await audit_service.log_action(
        db=db,
        company_id=current_user.company_id,
        action="document.uploaded",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata={"filename": file_name, "file_size": file_size},
    )
    await db.commit()
    await db.refresh(doc)

    return DocumentResponse(
        id=doc.id,
        resource_type=doc.resource_type,
        resource_id=doc.resource_id,
        filename=doc.filename,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        uploader_email=current_user.email,
        created_at=doc.created_at,
    )


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents for the current company, optionally filtered by resource."""
    filters = [Document.company_id == current_user.company_id]
    if resource_type:
        filters.append(Document.resource_type == resource_type)
    if resource_id:
        filters.append(Document.resource_id == resource_id)

    result = await db.execute(
        select(Document)
        .where(and_(*filters))
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()

    # Fetch uploader emails in one query if needed
    uploader_ids = {d.uploader_user_id for d in docs if d.uploader_user_id}
    uploader_map: dict = {}
    if uploader_ids:
        user_result = await db.execute(
            select(User).where(User.id.in_(uploader_ids))
        )
        for u in user_result.scalars().all():
            uploader_map[u.id] = u.email

    return [
        DocumentResponse(
            id=d.id,
            resource_type=d.resource_type,
            resource_id=d.resource_id,
            filename=d.filename,
            file_size=d.file_size,
            mime_type=d.mime_type,
            uploader_email=uploader_map.get(d.uploader_user_id) if d.uploader_user_id else None,
            created_at=d.created_at,
        )
        for d in docs
    ]


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document record and its storage object."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.company_id == current_user.company_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        storage_service.delete_object(DOCUMENTS_BUCKET, doc.storage_path)
    except Exception as exc:
        logger.warning("Failed to delete storage object %s: %s", doc.storage_path, exc)

    await audit_service.log_action(
        db=db,
        company_id=current_user.company_id,
        action="document.deleted",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_type=doc.resource_type,
        resource_id=doc.resource_id,
        metadata={"filename": doc.filename},
    )
    await db.delete(doc)
    await db.commit()


@router.get("/{document_id}/url")
async def get_document_signed_url(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return a signed 1-hour download URL for a document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.company_id == current_user.company_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        signed_url = storage_service.create_signed_url(
            DOCUMENTS_BUCKET, doc.storage_path, expires_in=3600
        )
    except Exception as exc:
        logger.error("Failed to create signed URL for document %s: %s", document_id, exc)
        raise HTTPException(status_code=502, detail="Could not generate signed URL")

    return {"url": signed_url, "expires_in": 3600}
