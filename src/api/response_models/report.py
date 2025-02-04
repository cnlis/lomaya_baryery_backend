from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel
from pydantic.schema import UUID

from src.api.response_models.task import TaskInfoResponse
from src.api.response_models.user import UserInfoResponse
from src.core.db.models import Report, Shift


class UserAndTaskInfoResponse(UserInfoResponse, TaskInfoResponse):
    """Модель для ответа с обобщенной информацией о задании и юзере."""

    id: UUID


class ReportResponse(BaseModel):
    """Pydantic-схема, для описания объекта, полученного из БД."""

    shift_id: UUID
    task_id: UUID
    member_id: UUID
    task_date: date
    status: Report.Status
    report_url: Optional[str]
    uploaded_at: datetime
    number_attempt: int

    class Config:
        orm_mode = True


class ReportSummaryResponse(BaseModel):
    shift_id: UUID
    shift_status: Shift.Status
    shift_started_at: date
    report_id: UUID
    report_status: Report.Status
    report_created_at: date
    user_name: str
    user_surname: str
    task_id: UUID
    task_description: str
    task_url: str
    photo_url: Optional[str]

    class Config:
        orm_mode = True
