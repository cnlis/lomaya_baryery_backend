from typing import Optional

from fastapi import Depends
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.request_models.user import UserSortRequest
from src.api.response_models.user import UserWithStatusResponse
from src.core.db.db import get_session
from src.core.db.models import User
from src.core.db.repository import AbstractRepository


class UserRepository(AbstractRepository):
    """Репозиторий для работы с моделью User."""

    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        super().__init__(session, User)

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        user = await self._session.execute(select(User).where(User.telegram_id == telegram_id))
        return user.scalars().first()

    async def check_user_existence(self, telegram_id: int, phone_number: str) -> bool:
        user_exists = await self._session.execute(
            select(select(User).where(or_(User.phone_number == phone_number, User.telegram_id == telegram_id)).exists())
        )
        return user_exists.scalar()

    async def get_users_with_status(
        self,
        status: Optional[User.Status] = None,
        sort: Optional[UserSortRequest] = None,
    ) -> list[UserWithStatusResponse]:
        users = (
            select(User)
            .where(
                or_(status is None, User.status == status),
            )
            .order_by(sort or User.created_at.desc())
        )
        users = await self._session.execute(users)
        return users.all()
