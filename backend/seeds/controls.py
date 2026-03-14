"""
Seed the controls table with SOC 2 control definitions.

Run with:
    cd backend && python -m seeds.controls
"""
import asyncio
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from models.control import Control

SOC2_CONTROLS = [
    {
        "name": "Logical Access Control",
        "framework": "soc2",
        "category": "access_control",
        "description": (
            "The entity restricts logical access to its systems, data, and resources "
            "to authorized individuals. Evidence includes IAM user lists, admin user "
            "lists, and workspace user configurations."
        ),
    },
    {
        "name": "Logging and Monitoring",
        "framework": "soc2",
        "category": "logging_monitoring",
        "description": (
            "The entity monitors system components and the operation of those controls "
            "on an ongoing basis to detect security events. Evidence includes CloudTrail "
            "logs and audit trails."
        ),
    },
    {
        "name": "Change Management",
        "framework": "soc2",
        "category": "change_management",
        "description": (
            "The entity authorizes, designs, develops or acquires, implements, operates, "
            "approves, maintains, and enhances software controls. Evidence includes "
            "repository configurations and commit activity."
        ),
    },
]


async def seed(db: AsyncSession) -> None:
    for control_data in SOC2_CONTROLS:
        existing = await db.execute(
            select(Control).where(
                Control.category == control_data["category"],
                Control.framework == control_data["framework"],
            )
        )
        if existing.scalar_one_or_none():
            print(f"  skip (exists): {control_data['category']}")
            continue

        control = Control(id=uuid.uuid4(), **control_data)
        db.add(control)
        print(f"  seeded: {control_data['category']}")

    await db.commit()


async def main() -> None:
    print("Seeding controls...")
    async with AsyncSessionLocal() as db:
        await seed(db)
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
