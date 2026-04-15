from fastapi import APIRouter

from app.schemas.common import MessageResponse

router = APIRouter(prefix='/system', tags=['system'])


@router.get('/status', response_model=MessageResponse)
async def system_status() -> MessageResponse:
    return MessageResponse(message='System framework initialized successfully.')
