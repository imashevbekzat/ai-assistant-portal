"""Слой LLM за абстракцией OpenAI-совместимого API.

Модель не считает: только классифицирует намерение по каталогу дэшбордов
и формулирует текст из уже вычисленных цифр аналитического слоя.
При недоступности API все методы возвращают None — оркестратор
переходит на словарный роутинг и шаблонные формулировки.
"""

from __future__ import annotations

import json
import re

import httpx

from ..config import settings


class LLMService:
    def __init__(self) -> None:
        self.available = bool(settings.llm_api_base and settings.llm_api_key)

    async def _chat(self, messages: list[dict], temperature: float = 0.2) -> str | None:
        if not self.available:
            return None
        url = settings.llm_api_base.rstrip("/") + "/chat/completions"
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": 400,
        }
        headers = {"Authorization": f"Bearer {settings.llm_api_key}"}
        try:
            async with httpx.AsyncClient(timeout=settings.llm_timeout_sec) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
        except Exception:
            return None

    async def classify_intent(self, text: str, catalog: list[dict]) -> str | None:
        """Классификация намерения по каталогу. Возвращает id дэшборда или None."""
        if not self.available:
            return None
        system = (
            "Ты — классификатор запросов к корпоративному аналитическому порталу. "
            "По запросу пользователя выбери ровно один дэшборд из каталога или null, "
            "если запрос не относится ни к одному. Ответ — строго JSON вида "
            '{"dashboard_id": "sales" | null}, без пояснений.'
        )
        user = f"Каталог дэшбордов:\n{json.dumps(catalog, ensure_ascii=False)}\n\nЗапрос: {text}"
        raw = await self._chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
        )
        if not raw:
            return None
        m = re.search(r'"dashboard_id"\s*:\s*"([a-z_]+)"', raw)
        if m:
            return m.group(1)
        if '"dashboard_id": null' in raw.replace("'", '"'):
            return None
        return None

    async def formulate(self, intent_title: str, facts_text: str, user_text: str) -> str | None:
        """Формулировка делового вывода по готовым цифрам. LLM не получает
        никаких данных, кроме уже вычисленного текста фактов."""
        if not self.available:
            return None
        system = (
            "Ты — аналитический ассистент корпоративного портала. Дай краткий деловой вывод "
            "по присланным фактам: 1–3 предложения, сначала цифры, затем интерпретация. "
            "Запрещено менять или выдумывать числа — используй только присланные. "
            "Эмодзи не используй. Язык — русский."
        )
        user = (
            f"Тема: {intent_title}\n"
            f"Вопрос пользователя: {user_text}\n\n"
            f"Факты (уже вычислены аналитическим слоем):\n{facts_text}"
        )
        return await self._chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.3,
        )


llm_service = LLMService()
