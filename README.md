# ИИ-ассистент аналитического портала (Tableau)

Реализация по [PRD.md](PRD.md): чат-виджет, который отвечает на вопросы о показателях компании кратким аналитическим выводом и автоматически открывает нужный дэшборд на портале.

## Состав проекта

```
PRD/
├── backend/              # Бэкенд ассистента (FastAPI)
│   ├── app/
│   │   ├── main.py       # Приложение, CORS, раздача виджета и демо-портала
│   │   ├── config.py     # Настройки (env ASSISTANT_*)
│   │   ├── schemas.py    # Pydantic-модели API
│   │   ├── routers/      # /api/chat, /api/dashboards, /api/metrics
│   │   └── services/
│   │       ├── orchestrator.py  # Оркестрация диалога (FR-1…FR-5)
│   │       ├── router.py        # Словарный NLU-роутинг (fallback без LLM)
│   │       ├── llm.py           # Слой LLM (OpenAI-совместимый API)
│   │       ├── analytics.py     # Аналитический слой: YTD, АППГ, план
│   │       ├── catalog.py       # Каталог дэшбордов и ключевых слов
│   │       ├── data.py          # Демо-данные (этап 3 → витрина DWH)
│   │       └── audit.py         # Аудит-лог запросов (logs/audit.jsonl)
│   └── tests/            # pytest: API и сценарии чата
├── widget/               # Чат-виджет — отдельный JS-модуль (этап 4)
│   ├── assistant.js      # Панель 390×600, чипы, «печатает…», автопереход
│   └── assistant.css
├── portal-view/          # Демо-страница портала для проверки встраивания
├── requirements.txt
├── pytest.ini
└── run.bat               # Запуск сервера на Windows
```

## Ключевые принципы (из PRD §8.2)

- **LLM не считает.** Все числа (YTD, динамика к АППГ, выполнение плана) вычисляет аналитический слой `analytics.py`. LLM только классифицирует намерение и формулирует текст из готовых цифр — галлюцинации в показателях исключены.
- **Модельно-агностично.** Слой LLM — за абстракцией OpenAI-совместимого API (`services/llm.py`); замена модели не трогает остальной код.
- **Деградация без LLM.** Если LLM не настроена или недоступна, работает словарный роутинг с учётом словоформ + шаблонные формулировки (NFR «Надёжность»).
- **Виджет — отдельный модуль.** Подключается на любую страницу портала двумя строками; с рабочей областью общается событием `ai-assistant:open-dashboard` (в целевой версии — навигация по URL-вью через Tableau Embedding API v3).

## Запуск

Требуется Python 3.12+.

```bash
pip install -r requirements.txt
```

Затем одним из способов:

```bash
run.bat
```

или

```bash
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Демо-портал с виджетом: http://127.0.0.1:8000/ (или `/portal`).
Документация API: http://127.0.0.1:8000/docs.

## Проверка

```bash
python -m pytest backend/tests -q
```

9 тестов: каталог, KPI, распознавание интентов (выручка, EBITDA, регионы), fallback с чипами, контекст сессии («а по регионам?»).

## Подключение LLM (опционально)

Через переменные окружения или файл `.env` в корне:

```env
ASSISTANT_LLM_API_BASE=https://<корпоративный-шлюз>/v1
ASSISTANT_LLM_API_KEY=...
ASSISTANT_LLM_MODEL=gpt-4o-mini
ASSISTANT_LLM_TIMEOUT_SEC=4
```

Без этих переменных ассистент полностью работает в словарном режиме (отмечается `llm_used: false` в ответах).

## API

| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/chat` | Диалог: `{session_id?, message}` → вывод + дэшборд/чипы |
| GET | `/api/dashboards` | Каталог дэшбордов портала |
| GET | `/api/metrics` | Список метрик аналитического слоя |
| GET | `/api/metrics/{id}/summary` | KPI-сводка по метрике (YTD, АППГ, план) |
| GET | `/health` | Проверка живости |

## Встраивание виджета в страницу портала

```html
<link rel="stylesheet" href="/widget/assistant.css">
<script src="/widget/assistant.js" data-api="/api" defer></script>
```

Реакция портала на команду открытия дэшборда (FR-3):

```js
window.addEventListener("ai-assistant:open-dashboard", (e) => {
  // e.detail: { id, viewUrl, title }
  // В целевой версии: переключить <tableau-viz> на e.detail.viewUrl
});
```

## Статус дорожной карты

- Этап 0 (прототип UX) — готов, см. PRD §13.
- **Этап 2 (бэкенд + LLM)** — реализован в этом репозитории: оркестрация диалога, словарный роутинг, слой LLM с fallback, аудит-лог.
- Этап 3 (аналитический слой на реальных данных): заменить `services/data.py` адаптером витрины DWH / Tableau REST API — интерфейс `kpi_summary()`/`regions_insight()` сохраняется.
- Этап 4 (виджет как модуль): `widget/` готов к встраиванию; остаётся подключить реальные URL-вью Tableau в `catalog.py` и обработчик `ai-assistant:open-dashboard` на стороне портала.
