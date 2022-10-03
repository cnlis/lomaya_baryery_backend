from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic.schema import UUID

from src.api.request_models.user_task import ChangeStatusRequest
from src.api.response_models.user_task import UserTaskResponse
from src.core.db.models import UserTask
from src.core.services.user_task_service import UserTaskService, get_user_task_service

router = APIRouter()


STR_ENTITY_NOT_EXIST = "Задачи с указанным id не существует!"


@router.get(
    "/user_tasks/{user_task_id}",
    response_model=UserTaskResponse,
    response_model_exclude_none=True,
    summary="Получить информацию об отчёте участника.",
    response_description="Полная информация об отчёте участника.",
)
async def get_user_report(
    user_task_id: UUID,
    user_task_service: UserTaskService = Depends(get_user_task_service),
) -> UserTask:
    """Вернуть отчет участника.

    - **user_task_id**: номер задачи, назначенной участнику на день смены (генерируется рандомно при старте смены)
    - **task_id**: номер задачи
    - **day_number**: номер дня смены
    - **status**: статус задачи
    - **photo_url**: url фото выполненной задачи
    """
    user_task = await user_task_service.get_or_none(user_task_id)
    if user_task is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=STR_ENTITY_NOT_EXIST)
    return user_task


@router.patch(
    "/user_tasks/{user_task_id}",
    response_model=UserTaskResponse,
    response_model_exclude_none=True,
    summary="Изменить статус участника.",
    response_description="Полная информация об отчёте участника.",
)
async def change_user_report_status(
    user_task_id: UUID,
    request: ChangeStatusRequest,
    user_task_service: UserTaskService = Depends(get_user_task_service),
) -> UserTask:
    """Изменить статус отчета участника.

    - **user_task_id**: номер задачи, назначенной участнику на день смены (генерируется рандомно при старте смены)
    - **task_id**: номер задачи
    - **day_number**: номер дня смены
    - **status**: статус задачи
    - **photo_url**: url фото выполненной задачи
    """
    user_task = await user_task_service.get_or_none(user_task_id)
    if user_task is None:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=STR_ENTITY_NOT_EXIST)
    user_task = await user_task_service.change_status(user_task, request.status)
    return user_task
