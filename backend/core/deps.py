import uuid

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value

from core.database import get_db
from core.security import decode_access_token
from models.user import User

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # Support partner context switching: if token carries a different company_id
    # (issued by the switch endpoint), override user.company_id for this request
    # without marking the column dirty in SQLAlchemy.
    token_company_id = payload.get("company_id")
    if token_company_id and str(user.company_id) != token_company_id:
        try:
            set_committed_value(user, "company_id", uuid.UUID(token_company_id))
        except (ValueError, AttributeError):
            pass

    return user


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


async def get_current_partner(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Require the user's own company (not a switched context) to be a partner account."""
    from models.company import Company
    result = await db.execute(select(Company).where(Company.id == current_user.company_id))
    company = result.scalar_one_or_none()
    if not company or not company.is_partner_account:
        raise HTTPException(status_code=403, detail="Partner account required")
    return current_user
