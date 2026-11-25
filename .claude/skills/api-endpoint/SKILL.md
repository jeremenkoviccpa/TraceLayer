---
name: api-endpoint
description: Add or change a FastAPI route in TraceLayer's backend the way this repo does it, with auth, tenancy, schemas, a router and a test. Use whenever you touch backend/api/v1/.
---

# Adding an API endpoint

Reference implementation: `backend/api/v1/risks.py`, with `schemas/risk.py` and `models/risk.py`.

## The pattern

```python
router = APIRouter(prefix="/things", tags=["things"])

@router.get("/{thing_id}", response_model=ThingResponse)
async def get_thing(
    thing_id: uuid.UUID,
    current_user: User = Depends(get_current_user),      # or get_current_admin
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Thing).where(Thing.id == thing_id, Thing.company_id == current_user.company_id)
    )
    thing = result.scalar_one_or_none()
    if not thing:
        raise HTTPException(status_code=404, detail="Thing not found")
    return thing
```

## Checklist

1. **Auth:** use `Depends(get_current_user)`, or `get_current_admin` for writes that change org settings. Use `require_growth` from `core/plan_gate.py` for paid features.
2. **Tenancy:** every `select`, `update` and `delete` filters on `company_id == current_user.company_id`. Take `company_id` from the user, never from the request body. If something belongs to another company, return **404**, not 403, so you don't reveal that it exists.
3. **Foreign IDs in the body** (owner, vendor and so on): check that they belong to the same company before saving. `create_risk` shows how.
4. **Schemas:** request and response models go in `schemas/<domain>.py`. Never return ORM objects that have secret columns, such as credentials or token hashes.
5. **Errors:** use `HTTPException(status, detail="human sentence")`. The frontend shows `detail` as is.
6. **Rate limits:** for unauthenticated or abuse-prone routes, add `@rate_limit("N/minute")` from `core/limiter.py`. The route needs a `request: Request` parameter.
7. **Wiring:** import the router in `main.py` and `app.include_router(x.router, prefix="/v1")`. Add the client method to `frontend/lib/api.ts`.
8. **Schema change:** add an Alembic version in `migrations/versions/`. For JSONB defaults use `server_default=text("'[]'::jsonb")`, not a bare string.
9. **Test:** in `backend/tests/test_<domain>.py`, cover the happy path, 401 without a token, and 404 for another company's object. Fixtures are in `conftest.py`.
