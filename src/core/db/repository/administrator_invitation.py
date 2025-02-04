from datetime import datetime
from typing import Optional

from fastapi import Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db.db import get_session
from src.core.db.models import AdministratorInvitation
from src.core.db.repository import AbstractRepository
from src.core.exceptions import AdministratorInvitationInvalid


class AdministratorInvitationRepository(AbstractRepository):
    def __init__(self, session: AsyncSession = Depends(get_session)) -> None:
        super().__init__(session, AdministratorInvitation)

    async def get_mail_request_by_token(self, token: str) -> Optional[AdministratorInvitation]:
        statement = select(AdministratorInvitation).where(
            and_(AdministratorInvitation.token == token, AdministratorInvitation.expired_date > datetime.utcnow())
        )
        result = (await self._session.scalars(statement)).first()
        if result is None:
            raise AdministratorInvitationInvalid
        return result
