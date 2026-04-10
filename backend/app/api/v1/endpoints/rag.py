from fastapi import APIRouter
from pydantic import BaseModel

from app.services.rag_service import RagService

router = APIRouter(prefix='/rag', tags=['rag'])
rag_service = RagService()


class RagQuery(BaseModel):
    question: str


@router.post('/diagnose')
async def rag_diagnose(payload: RagQuery) -> dict:
    return await rag_service.diagnose(payload.question)
