from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import AiConversation


class RagService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def is_enabled(self) -> bool:
        return self.settings.rag_enabled

    async def diagnose(self, query: str, history: list[dict] | None = None) -> dict:
        history = history or []
        answer = self._build_answer(query)
        similar_cases = [
            '2026-03-18 A 区风机停转导致 VOCs 瞬时升高',
            '2026-02-26 活性炭饱和导致处理效率下降',
            '2026-01-12 排口阀门卡滞引发局部高浓度',
        ]
        sop = [
            '确认告警设备与周边排口的实时数值是否同步波动',
            '检查风机、电流、压差和吸附装置运行状态',
            '现场拍照并提交处置记录，完成闭环确认',
        ]
        if history:
            answer = f'结合当前多轮上下文，{answer}'

        return {
            'enabled': True,
            'answer': answer,
            'similarCases': similar_cases,
            'sop': sop,
            'historyCount': len(history),
        }

    def _build_answer(self, query: str) -> str:
        normalized = query.strip()
        if '误报' in normalized:
            return '建议先对比相邻传感器和近 10 分钟趋势，若单点突刺且现场复核正常，可按误报流程处理。'
        if '处置' in normalized or '怎么做' in normalized:
            return '建议先控制异常源头，再检查风机与吸附装置，最后复测并提交照片和处置说明。'
        return '根据当前告警表现，优先排查风机工况、吸附材料状态及排口阀门是否异常。'
