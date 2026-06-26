import asyncio
import traceback
from sqlalchemy import select
from app.database.session import AsyncSessionFactory
from app.models.domain import Region
from app.schemas.admin import RegionAdminInput
from app.services.admin import AdminService

async def test():
    print("Starting debug test...")
    async with AsyncSessionFactory() as session:
        service = AdminService(session)
        payload = RegionAdminInput(name="TestRegionDebug", subtitle="Hello", description="Test", display_order=1)
        try:
            res = await service.create_entity(Region, payload)
            print("Successfully created:", res)
            await session.commit()
        except Exception as e:
            print("Error occurred:")
            traceback.print_exc()
            await session.rollback()

if __name__ == "__main__":
    asyncio.run(test())
