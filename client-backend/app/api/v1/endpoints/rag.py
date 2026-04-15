from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_username
from app.db.session import get_db
from app.models.entities import AiConversation
from app.services.rag_service import RagService

router = APIRouter(prefix='/rag', tags=['rag'])
rag_service = RagService()


class RagQuery(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    sessionId: str = 'default'


@router.post('/diagnose')
async def rag_diagnose(
    payload: RagQuery,
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    history_rows = (
        await db.scalars(
            select(AiConversation)
            .where(AiConversation.username == username, AiConversation.session_id == payload.sessionId)
            .order_by(AiConversation.created_at.asc())
        )
    ).all()
    history = [{'role': row.role, 'content': row.content} for row in history_rows]
    response = await rag_service.diagnose(payload.question, history)
    return {
        'code': 200,
        'data': response,
    }


@router.get('/history')
async def rag_history(
    sessionId: str = 'default',
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    rows = (
        await db.scalars(
            select(AiConversation)
            .where(AiConversation.username == username, AiConversation.session_id == sessionId)
            .order_by(AiConversation.created_at.asc())
        )
    ).all()
    return {
        'code': 200,
        'data': [
            {
                'id': row.id,
                'role': row.role,
                'content': row.content,
                'createdAt': row.created_at.strftime('%Y-%m-%d %H:%M'),
            }
            for row in rows
        ],
    }


@router.get('/export')
async def export_history(
    sessionId: str = 'default',
    username: str = Depends(get_current_username),
    db: AsyncSession = Depends(get_db),
) -> dict:
    rows = (
        await db.scalars(
            select(AiConversation)
            .where(AiConversation.username == username, AiConversation.session_id == sessionId)
            .order_by(AiConversation.created_at.asc())
        )
    ).all()
    lines = ['角色,内容,时间']
    for row in rows:
        lines.append(f'{row.role},{row.content},{row.created_at.strftime("%Y-%m-%d %H:%M")}')
    return {'code': 200, 'data': {'filename': 'ai-dialog.csv', 'content': '\n'.join(lines)}}
