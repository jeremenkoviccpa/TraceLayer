from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from core.config import settings

# Railway (and most providers) give a postgres:// or postgresql:// URL.
# SQLAlchemy async requires postgresql+asyncpg://.
_db_url = settings.database_url
for _prefix in ("postgres://", "postgresql://"):
    if _db_url.startswith(_prefix):
        _db_url = "postgresql+asyncpg://" + _db_url[len(_prefix):]
        break

engine = create_async_engine(_db_url, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
