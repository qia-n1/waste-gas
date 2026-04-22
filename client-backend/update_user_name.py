import asyncio
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.entities import UserProfile

async def update_user_name():
    async with SessionLocal() as session:
        # Find the user with username 'zsq'
        user = await session.scalar(
            select(UserProfile).where(UserProfile.username == 'zsq')
        )
        
        if user:
            # Update the name
            user.name = '气盾卫士--多源化工废气智能治理系统'
            await session.commit()
            print(f"User {user.username}'s name updated to: {user.name}")
        else:
            print("User 'zsq' not found")

asyncio.run(update_user_name())