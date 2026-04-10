from app.core.config import get_settings


class RagService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def is_enabled(self) -> bool:
        return self.settings.rag_enabled

    async def diagnose(self, query: str) -> dict:
        if not self.settings.rag_enabled:
            return {
                'enabled': False,
                'answer': 'RAG service is disabled. Set RAG_ENABLED=true to enable it.',
            }

        # Placeholder for LangChain/LlamaIndex + Chroma integration.
        return {
            'enabled': True,
            'answer': f'Received query: {query}',
        }
