# agent-harness

[English version](README.md)

`agent-harness` хранит в Git роли Codex, навыки и профили моделей, чтобы использовать их в разных проектах. MVP работает на встроенной оркестрации Codex. Compound Engineering можно подключить отдельно с закреплённой версией. Herdr в MVP не входит.

| Компонент | Назначение |
| --- | --- |
| [`harness.yaml`](harness.yaml) и [`harness.lock.yaml`](harness.lock.yaml) | Описывают окружение и закрепляют ревизию Compound Engineering. Это форматы этого репозитория. |
| [`agents/`](agents/) | `architect` планирует на `gpt-6-astra`; `backend`, `frontend` и `reviewer` работают на `gpt-6.1-sol`. |
| [`skills/`](skills/) | `$architecture-review`, `$api-design`, `$task-decomposition`, `$backend-standard`, `$frontend-standard` и `$harness-workflow`. |
| [`profiles/codex/`](profiles/codex/) | Профили CLI `architect` и `developer`. Каждый ограничивает число параллельных сессий агентов четырьмя. |
| [`scripts/doctor.py`](scripts/doctor.py) и [`scripts/install.py`](scripts/install.py) | Проверяют исходную конфигурацию, устанавливают и сверяют файлы из манифеста. |

## Установка и запуск

Понадобятся `uv`, Python 3.11 или новее и свежая версия Codex CLI. Для запуска моделей войдите через `codex login` и проверьте доступ к моделям из манифеста. Как Codex находит файлы, описано в официальной документации по [навыкам](https://developers.openai.com/codex/skills), [сабагентам](https://developers.openai.com/codex/subagents) и [профилям](https://developers.openai.com/codex/config-advanced#profiles).

Из корня этого репозитория проверьте конфигурацию и установите её в нужный проект:

```bash
uv run --locked python scripts/doctor.py
uv run --locked python scripts/install.py --project /path/to/project --dry-run
uv run --locked python scripts/install.py --project /path/to/project
uv run --locked python scripts/doctor.py --project /path/to/project
codex -C /path/to/project
```

При установке в проект роли копируются в `.codex/agents/`, а навыки — в `.agents/skills/`. Чтобы использовать роли в интерактивном режиме, отметьте проект как доверенный в Codex. В новой сессии напишите: `Используй $harness-workflow для этой задачи: …`. Опишите ожидаемый результат и проверки. Коммит, отправка в Git и слияние остаются отдельными действиями.

Для установки сразу для всех проектов используйте `--user` вместо `--project`. Профили будут установлены в `CODEX_HOME` (по умолчанию `~/.codex`), навыки — в `~/.agents/skills/`. Запуск: `codex --profile architect` или `codex --profile developer`. Чтобы проверить пользовательскую установку в другом месте, передайте вместе с `--user` оба параметра: `--codex-home` и `--skills-dir`.

При повторной установке одинаковые файлы пропускаются. Если существующий файл отличается, установщик остановится до копирования. Сравните указанные файлы и выберите, какую версию сохранить, прежде чем повторять установку.

## Дополнительно: Compound Engineering

```bash
uv run --locked python scripts/install.py --user --with-plugins --dry-run
uv run --locked python scripts/install.py --user --with-plugins
uv run --locked python scripts/doctor.py --user --plugins
```

Этот шаг использует команды Codex для установки плагина на закреплённой ревизии Git. Он обновляет настройки плагинов Codex. Если маркетплейс уже настроен с другим источником или ревизией, установщик покажет конфликт. Диагностика сверяет ревизию в кэше и обнаруживает изменения в файлах, которые отслеживает Git. Если не удалось скачать плагин, восстановите доступ к сети и повторите команду. Основной сценарий работает и без плагина.

## Пробная задача

Из корня репозитория скопируйте стартовый проект во временный каталог. Для проверок фронтенда нужен Node.js.

```bash
demo="$(mktemp -d)"
cp -R examples/smoke/. "$demo/"
uv run --locked python scripts/install.py --project "$demo"
uv run --locked python scripts/doctor.py --project "$demo"
uv run --locked python scripts/run.py --project "$demo" --prompt-file "$demo/task.txt"
(cd "$demo" && python3 check_status.py && node --test check_status.test.mjs)
```

[`run.py`](scripts/run.py) запускает Codex с установленными ролями и моделью из профиля разработчика. Скрипт передаёт роли явно, поэтому демо работает без загрузки личных настроек и без добавления папки в список доверенных. Используется текущий вход в Codex.

[Задача](examples/smoke/task.txt) задействует все четыре роли. Бэкенд добавляет `message: "Service is healthy"` к существующему ответу, фронтенд выводит сообщение и сохраняет обработку ошибки запроса. Проверки специально падают на стартовом проекте, пока задача не выполнена. Чтобы увидеть результат в браузере, запустите `python3 server.py` в каталоге демо и откройте `http://127.0.0.1:8000`.

Тесты самого харнеса можно запустить без Codex: `uv run --locked python -m unittest discover -s tests -v`.

Правила работы с репозиторием описаны в [AGENTS.md](AGENTS.md). Инструкции для агентов пишем на английском, документацию для людей ведём на русском и английском.
