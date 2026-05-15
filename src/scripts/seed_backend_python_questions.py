import asyncio
import math
import re
from typing import Any

from sqlalchemy import select

from src.database import AsyncSessionLocal
from src.models.interview_question import InterviewQuestion


WORDS_PER_MINUTE = 120


def estimate_answer_time_limit_sec(expected_answer: str) -> int:
    words = re.findall(r"[\wА-Яа-яЁё-]+", expected_answer, flags=re.UNICODE)
    minutes = max(1, math.ceil(len(words) / WORDS_PER_MINUTE))
    return minutes * 60


def make_rubric(level: str, difficulty: int) -> dict[str, Any]:
    return {
        "score_source": "key_points_weights",
        "level": level,
        "difficulty": difficulty,
        "coverage_thresholds": {
            "strong": 80,
            "acceptable": 60,
            "weak": 40,
        },
        "notes": "Оценивать по покрытым key_points. Не засчитывать ответ, если он не относится к вопросу.",
    }


def question(
    code: str,
    competency: str,
    level: str,
    difficulty: int,
    question_text: str,
    expected_answer: str,
    key_points: list[dict[str, Any]],
    red_flags: list[str],
    follow_ups: list[str],
    answer_time_limit_sec: int | None = None,
) -> dict[str, Any]:
    weight_total = sum(int(point["weight"]) for point in key_points)
    if weight_total != 100:
        raise ValueError(f"{code}: key_points weights must total 100, got {weight_total}")

    return {
        "code": code,
        "profession": "backend",
        "language": "python",
        "competency": competency,
        "level": level,
        "difficulty": difficulty,
        "question_text": question_text,
        "expected_answer": expected_answer,
        "key_points": key_points,
        "red_flags": red_flags,
        "follow_ups": follow_ups,
        "evaluation_rubric": make_rubric(level, difficulty),
        "answer_time_limit_sec": estimate_answer_time_limit_sec(expected_answer),
        "is_active": True,
        "source": "curated_backend_python_mvp",
    }


QUESTIONS: list[dict[str, Any]] = [
    question(
        "backend_python_python_core_junior_01",
        "python_core",
        "junior",
        1,
        "Чем отличаются list, tuple, set и dict в Python, и когда какой тип выбирать?",
        "Нужно объяснить назначение базовых коллекций: list для упорядоченной изменяемой последовательности, tuple для неизменяемой структуры, set для уникальных значений и быстрых проверок вхождения, dict для отображения ключ-значение. Важно упомянуть изменяемость, порядок, уникальность и типичные операции.",
        [
            {"title": "Изменяемость list/dict/set и неизменяемость tuple", "weight": 25},
            {"title": "Порядок и уникальность элементов", "weight": 25},
            {"title": "Выбор структуры под задачу", "weight": 30},
            {"title": "Понимание базовой сложности операций", "weight": 20},
        ],
        [
            "Путает dict и set",
            "Говорит, что tuple всегда быстрее и поэтому нужен везде",
            "Не может привести практический пример выбора коллекции",
        ],
        [
            "Почему set обычно удобен для проверки наличия значения?",
            "Когда tuple лучше list в API-контракте?",
        ],
    ),
    question(
        "backend_python_python_core_middle_01",
        "python_core",
        "middle",
        3,
        "Что такое декоратор в Python и какие риски есть при написании своих декораторов?",
        "Ожидается объяснение, что декоратор оборачивает функцию или класс, добавляя поведение без изменения вызывающего кода. Нужно упомянуть замыкания, передачу аргументов, functools.wraps для сохранения metadata, обработку async-функций и отсутствие скрытых побочных эффектов.",
        [
            {"title": "Понимание функции-обертки и замыкания", "weight": 25},
            {"title": "Передача *args/**kwargs и возврат результата", "weight": 20},
            {"title": "functools.wraps и сохранение metadata", "weight": 20},
            {"title": "Риски с async, исключениями и побочными эффектами", "weight": 35},
        ],
        [
            "Не возвращает результат исходной функции",
            "Игнорирует functools.wraps",
            "Одинаково оборачивает sync и async функции",
        ],
        [
            "Как написать декоратор, который принимает параметры?",
            "Как отличить async-функцию внутри декоратора?",
        ],
    ),
    question(
        "backend_python_python_core_senior_01",
        "python_core",
        "senior",
        5,
        "Как вы бы искали и исправляли проблему с ростом памяти в Python backend-сервисе?",
        "Сильный ответ должен описать воспроизведение, метрики RSS/heap, профилирование tracemalloc/objgraph/memray, поиск удерживаемых ссылок, кэшей без лимитов, глобальных коллекций, циклов с __del__, больших payload в логах или очередях. Важно разделять leak, fragmentation и ожидаемый рост нагрузки, а фикс подтверждать тестом или нагрузочным прогоном.",
        [
            {"title": "Сбор симптомов и воспроизводимый сценарий", "weight": 20},
            {"title": "Использование профилировщиков памяти", "weight": 25},
            {"title": "Поиск удерживаемых ссылок и безлимитных кэшей", "weight": 25},
            {"title": "Проверка фикса метриками и нагрузкой", "weight": 20},
            {"title": "Различает leak, fragmentation и нормальный рост", "weight": 10},
        ],
        [
            "Предлагает просто перезапускать сервис по cron",
            "Сразу винит garbage collector без измерений",
            "Не отличает утечку от роста из-за нагрузки",
        ],
        [
            "Какие метрики вы бы добавили в production?",
            "Как бы вы ограничили in-memory cache?",
        ],
        180,
    ),
    question(
        "backend_python_fastapi_junior_01",
        "fastapi",
        "junior",
        2,
        "Как FastAPI валидирует входные данные запроса и что возвращается клиенту при ошибке валидации?",
        "Нужно объяснить роль Pydantic-схем, type hints, path/query/body параметров и автоматической валидации. При ошибке FastAPI возвращает 422 с деталями полей. Хороший ответ упоминает response_model, OpenAPI-документацию и явную обработку бизнес-ошибок через HTTPException.",
        [
            {"title": "Pydantic и type hints как основа валидации", "weight": 35},
            {"title": "Различает path/query/body параметры", "weight": 20},
            {"title": "Понимает 422 validation error", "weight": 20},
            {"title": "Упоминает response_model и документацию", "weight": 15},
            {"title": "Не смешивает валидацию и бизнес-ошибки", "weight": 10},
        ],
        [
            "Говорит, что FastAPI не валидирует данные",
            "Возвращает 500 на пользовательские ошибки ввода",
            "Путает Pydantic-модель с SQLAlchemy-моделью",
        ],
        [
            "Где лучше описывать request schema?",
            "Чем 400 отличается от 422 в таком API?",
        ],
    ),
    question(
        "backend_python_fastapi_middle_01",
        "fastapi",
        "middle",
        3,
        "Как организовать dependency injection в FastAPI для работы с базой данных и авторизацией?",
        "Ожидается объяснение Depends, зависимостей для сессии БД, yield-зависимостей для cleanup, переиспользования зависимостей авторизации и тестовой подмены dependency_overrides. Важно не создавать глобальную session на все запросы и явно закрывать ресурсы.",
        [
            {"title": "Depends и композиция зависимостей", "weight": 25},
            {"title": "Безопасный lifecycle DB session через yield", "weight": 30},
            {"title": "Авторизация как отдельная dependency", "weight": 20},
            {"title": "Тестовая подмена dependency_overrides", "weight": 15},
            {"title": "Отсутствие глобальной request session", "weight": 10},
        ],
        [
            "Предлагает одну глобальную DB session",
            "Размещает авторизацию прямо в каждом handler",
            "Не закрывает соединения или транзакции",
        ],
        [
            "Как протестировать endpoint с подменой пользователя?",
            "Где бы вы открывали и коммитили транзакцию?",
        ],
    ),
    question(
        "backend_python_fastapi_senior_01",
        "fastapi",
        "senior",
        4,
        "Что важно учесть при проектировании большого FastAPI-приложения, чтобы оно не превратилось в набор толстых route handlers?",
        "Сильный ответ разделяет API-слой, схемы, сервисы, репозитории или data-access, зависимости, конфигурацию и фоновые задачи. Нужно упомянуть границы модулей, тестируемость бизнес-логики вне FastAPI, явные DTO, обработку ошибок и observability.",
        [
            {"title": "Тонкие handlers и вынос бизнес-логики в сервисы", "weight": 25},
            {"title": "Модульные границы и понятная структура пакетов", "weight": 25},
            {"title": "DTO/схемы отдельно от ORM-моделей", "weight": 15},
            {"title": "Тестируемость без запуска ASGI", "weight": 20},
            {"title": "Единая обработка ошибок и observability", "weight": 15},
        ],
        [
            "Складывает всю бизнес-логику в endpoints",
            "Предлагает один огромный router для всего приложения",
            "Смешивает ORM entity и внешний API contract",
        ],
        [
            "Где должна жить транзакционная бизнес-операция?",
            "Как бы вы разделили bounded contexts в API?",
        ],
        180,
    ),
    question(
        "backend_python_databases_junior_01",
        "databases",
        "junior",
        2,
        "Что такое индекс в PostgreSQL и почему индекс не всегда ускоряет запрос?",
        "Нужно объяснить, что индекс помогает быстрее находить строки, но требует места и обновления при записи. Индекс полезен не для каждого запроса: маленькие таблицы, низкая селективность, неподходящее условие или функции над колонкой могут привести к sequential scan.",
        [
            {"title": "Индекс как структура для ускорения поиска", "weight": 30},
            {"title": "Стоимость индекса при insert/update/delete", "weight": 20},
            {"title": "Селективность и размер таблицы", "weight": 25},
            {"title": "Понимание случаев, когда индекс не используется", "weight": 25},
        ],
        [
            "Считает, что индекс всегда ускоряет любые запросы",
            "Не знает о цене индекса на запись",
            "Предлагает индексировать все колонки",
        ],
        [
            "Как проверить, использует ли запрос индекс?",
            "Что такое составной индекс?",
        ],
    ),
    question(
        "backend_python_databases_middle_01",
        "databases",
        "middle",
        3,
        "Как избежать N+1 query problem в backend-приложении с ORM?",
        "Ожидается описание проблемы: один запрос за списком и отдельные запросы за связанными объектами. Решения: eager loading, selectinload/joinedload, явные JOIN, batch loading, правильная сериализация и тесты/логирование количества запросов.",
        [
            {"title": "Корректно описывает N+1", "weight": 25},
            {"title": "Знает eager loading и batch loading", "weight": 30},
            {"title": "Понимает trade-off joinedload/selectinload", "weight": 20},
            {"title": "Контролирует сериализацию и количество запросов", "weight": 15},
            {"title": "Подтверждает исправление метриками или тестом", "weight": 10},
        ],
        [
            "Предлагает просто увеличить pool соединений",
            "Не видит связи между сериализацией и lazy loading",
            "Всегда выбирает JOIN без учета кардинальности",
        ],
        [
            "Когда selectinload лучше joinedload?",
            "Как поймать N+1 в тестах?",
        ],
    ),
    question(
        "backend_python_databases_senior_01",
        "databases",
        "senior",
        5,
        "Как вы проектируете транзакции и уровни изоляции для операции списания денег или резервирования ресурса?",
        "Сильный ответ должен покрывать атомарность операции, границы транзакции, блокировки строк, SELECT FOR UPDATE или optimistic locking, idempotency key, retry на serialization/deadlock ошибки, outbox для внешних событий и выбор уровня изоляции под инварианты.",
        [
            {"title": "Четкие границы транзакции и атомарность", "weight": 20},
            {"title": "Блокировки или optimistic locking", "weight": 25},
            {"title": "Idempotency и retry strategy", "weight": 20},
            {"title": "Выбор isolation level под инварианты", "weight": 20},
            {"title": "Безопасная публикация внешних событий", "weight": 15},
        ],
        [
            "Делает внешние HTTP-вызовы внутри долгой транзакции без причины",
            "Не учитывает повтор запроса клиентом",
            "Полагается только на проверку в приложении без ограничений БД",
        ],
        [
            "Когда нужен SELECT FOR UPDATE?",
            "Зачем нужен outbox pattern?",
        ],
        180,
    ),
    question(
        "backend_python_async_junior_01",
        "async",
        "junior",
        2,
        "Что означает async/await в Python и какую проблему оно решает в web backend?",
        "Нужно объяснить, что async/await позволяет не блокировать event loop на I/O-операциях: сеть, БД, файлы через async API. Это не делает CPU-bound код быстрее само по себе. Важно понимать coroutine, await и необходимость async-compatible библиотек.",
        [
            {"title": "Понимает coroutine и await", "weight": 25},
            {"title": "Связывает async с I/O-bound задачами", "weight": 30},
            {"title": "Отличает I/O-bound от CPU-bound", "weight": 25},
            {"title": "Упоминает async-compatible библиотеки", "weight": 20},
        ],
        [
            "Говорит, что async ускоряет любой код",
            "Путает async с многопоточностью один к одному",
            "Использует blocking requests внутри async handler",
        ],
        [
            "Что будет, если вызвать time.sleep внутри async endpoint?",
            "Почему нужен async database driver?",
        ],
    ),
    question(
        "backend_python_async_middle_01",
        "async",
        "middle",
        4,
        "Как безопасно запустить несколько независимых async-операций и обработать их ошибки?",
        "Ожидается понимание asyncio.gather, TaskGroup в новых версиях Python, timeout/cancellation, ограничения параллелизма через Semaphore, обработки частичных ошибок и cleanup. Важно не создавать бесконтрольные background tasks без наблюдения.",
        [
            {"title": "gather или TaskGroup для конкурентного запуска", "weight": 25},
            {"title": "Timeout и cancellation handling", "weight": 25},
            {"title": "Ограничение параллелизма", "weight": 20},
            {"title": "Стратегия обработки частичных ошибок", "weight": 20},
            {"title": "Наблюдаемость background tasks", "weight": 10},
        ],
        [
            "Создает task и забывает про нее",
            "Не обрабатывает cancellation",
            "Запускает тысячи операций без лимита",
        ],
        [
            "Чем gather отличается от TaskGroup?",
            "Как бы вы ограничили 1000 запросов к внешнему API?",
        ],
    ),
    question(
        "backend_python_async_senior_01",
        "async",
        "senior",
        5,
        "Как диагностировать деградацию latency в async FastAPI-сервисе под нагрузкой?",
        "Сильный ответ включает метрики latency percentiles, event loop lag, pool saturation, slow queries, blocking calls, профилирование, tracing, backpressure, connection pool limits и проверку зависимостей. Важно идти от измерений к гипотезам, а не переписывать все на async.",
        [
            {"title": "Метрики p95/p99 и event loop lag", "weight": 25},
            {"title": "Проверка pool saturation и slow queries", "weight": 20},
            {"title": "Поиск blocking calls в event loop", "weight": 20},
            {"title": "Tracing/profiling под нагрузкой", "weight": 20},
            {"title": "Backpressure и лимиты ресурсов", "weight": 15},
        ],
        [
            "Предлагает увеличить воркеры без анализа",
            "Игнорирует event loop lag",
            "Не проверяет БД и внешние зависимости",
        ],
        [
            "Как измерить event loop lag?",
            "Когда лучше добавить worker processes?",
        ],
        180,
    ),
    question(
        "backend_python_architecture_junior_01",
        "architecture",
        "junior",
        2,
        "Зачем разделять router, service и repository/data-access слой в backend-приложении?",
        "Нужно объяснить разделение ответственности: router отвечает за HTTP, service за бизнес-операцию, repository или data-access за работу с хранилищем. Это упрощает тесты, повторное использование и изменение деталей инфраструктуры.",
        [
            {"title": "Разделение HTTP, бизнес-логики и data access", "weight": 40},
            {"title": "Тестируемость сервисного слоя", "weight": 25},
            {"title": "Снижение дублирования и связанности", "weight": 20},
            {"title": "Понимание, что слои не нужны ради слоев", "weight": 15},
        ],
        [
            "Считает router подходящим местом для всей логики",
            "Не может объяснить пользу тестируемости",
            "Добавляет абстракции без причины",
        ],
        [
            "Какая логика должна остаться в router?",
            "Когда repository может быть лишним?",
        ],
    ),
    question(
        "backend_python_architecture_middle_01",
        "architecture",
        "middle",
        4,
        "Как спроектировать API endpoint для создания заказа так, чтобы он был устойчив к повторной отправке запроса?",
        "Ожидается idempotency key, хранение статуса обработки, уникальные ограничения в БД, корректные HTTP-ответы при повторе, транзакционная запись результата и осторожность с внешними вызовами. Важно не создавать дубль заказа при retry клиента.",
        [
            {"title": "Idempotency key и область его действия", "weight": 30},
            {"title": "Уникальные ограничения и транзакционность", "weight": 25},
            {"title": "Поведение при повторном запросе", "weight": 20},
            {"title": "Обработка внешних эффектов", "weight": 15},
            {"title": "Понятный контракт ошибок и статусов", "weight": 10},
        ],
        [
            "Полагается только на frontend, чтобы не нажимали два раза",
            "Не хранит результат первой операции",
            "Не учитывает retry после timeout",
        ],
        [
            "Где хранить idempotency key?",
            "Что вернуть клиенту при повторе успешного запроса?",
        ],
    ),
    question(
        "backend_python_architecture_senior_01",
        "architecture",
        "senior",
        5,
        "Когда вы бы выделяли отдельный сервис из монолита, а когда оставили бы модуль внутри монолита?",
        "Сильный ответ должен учитывать организационные границы, независимый lifecycle, масштабирование, разные требования к данным, стоимость распределенной системы, observability, контракты, транзакции и командную готовность поддерживать сервис.",
        [
            {"title": "Оценивает бизнес/командные границы", "weight": 20},
            {"title": "Понимает стоимость distributed systems", "weight": 25},
            {"title": "Учитывает данные, транзакции и consistency", "weight": 20},
            {"title": "Учитывает deployment и independent scaling", "weight": 15},
            {"title": "Говорит про observability и контракт API", "weight": 20},
        ],
        [
            "Предлагает микросервисы по умолчанию",
            "Игнорирует транзакции и consistency",
            "Не учитывает поддержку и мониторинг",
        ],
        [
            "Какие признаки говорят, что модуль пора отделять?",
            "Как сохранить контракт между сервисами?",
        ],
        180,
    ),
    question(
        "backend_python_testing_junior_01",
        "testing",
        "junior",
        2,
        "Какие тесты вы бы написали для простого endpoint, который создает запись в базе?",
        "Нужно назвать unit-тесты валидации/сервиса и integration-тест endpoint плюс БД. Важно проверить успешный сценарий, ошибки валидации, бизнес-ошибки и состояние БД. Хороший ответ упоминает test database и изоляцию тестов.",
        [
            {"title": "Покрывает happy path", "weight": 25},
            {"title": "Проверяет validation и error cases", "weight": 25},
            {"title": "Проверяет состояние БД", "weight": 20},
            {"title": "Разделяет unit и integration tests", "weight": 20},
            {"title": "Использует изолированную test database", "weight": 10},
        ],
        [
            "Тестирует только HTTP 200",
            "Использует production database",
            "Не проверяет результат в БД",
        ],
        [
            "Как изолировать данные между тестами?",
            "Что лучше замокать, а что оставить реальным?",
        ],
    ),
    question(
        "backend_python_testing_middle_01",
        "testing",
        "middle",
        3,
        "Как тестировать код, который зависит от внешнего HTTP API?",
        "Ожидается разделение контракта клиента и бизнес-логики, mock/fake HTTP client в unit-тестах, integration/contract tests для реального API или sandbox, timeouts/retries/error responses и отсутствие реальных сетевых вызовов в быстрых тестах.",
        [
            {"title": "Выделяет клиента внешнего API", "weight": 20},
            {"title": "Использует mock/fake для быстрых тестов", "weight": 25},
            {"title": "Проверяет error responses, timeout и retry", "weight": 25},
            {"title": "Отдельно держит integration/contract tests", "weight": 20},
            {"title": "Не ходит в сеть из unit-тестов", "weight": 10},
        ],
        [
            "Unit-тесты зависят от реального внешнего API",
            "Не проверяет timeouts",
            "Мокает весь сервис целиком и ничего не проверяет",
        ],
        [
            "Как проверить retry logic?",
            "Где хранить fixtures ответов внешнего API?",
        ],
    ),
    question(
        "backend_python_testing_senior_01",
        "testing",
        "senior",
        4,
        "Как выстроить тестовую стратегию для критичного backend-сервиса с PostgreSQL, Redis и очередями?",
        "Сильный ответ покрывает пирамиду тестов, unit-тесты бизнес-логики, integration tests с реальными PostgreSQL/Redis в контейнерах, contract tests, миграции, race conditions, observability проверок и баланс скорости с надежностью CI.",
        [
            {"title": "Баланс unit/integration/contract/e2e", "weight": 25},
            {"title": "Реальные инфраструктурные зависимости в integration tests", "weight": 25},
            {"title": "Проверка миграций и транзакционных сценариев", "weight": 15},
            {"title": "Тесты на конкуренцию и retry", "weight": 20},
            {"title": "CI скорость, стабильность и диагностика", "weight": 15},
        ],
        [
            "Все проверяет только e2e тестами",
            "Не тестирует миграции",
            "Использует нестабильные sleep в concurrency tests",
        ],
        [
            "Какие тесты должны блокировать merge?",
            "Как тестировать worker, который читает очередь?",
        ],
        180,
    ),
    question(
        "backend_python_security_junior_01",
        "security",
        "junior",
        2,
        "Какие базовые меры безопасности нужны для endpoint, который принимает данные от пользователя?",
        "Нужно назвать валидацию входа, авторизацию, ограничение размера payload, безопасную обработку ошибок, отсутствие секретов в логах, rate limiting для чувствительных операций и параметризованные SQL-запросы через ORM/driver.",
        [
            {"title": "Валидация и ограничения input", "weight": 25},
            {"title": "Авторизация и проверка прав", "weight": 25},
            {"title": "Безопасные ошибки и логи без секретов", "weight": 20},
            {"title": "Защита от SQL injection", "weight": 20},
            {"title": "Rate limiting для чувствительных операций", "weight": 10},
        ],
        [
            "Доверяет данным с frontend",
            "Логирует токены или пароли",
            "Собирает SQL строкой из input",
        ],
        [
            "Где проверять права пользователя?",
            "Почему нельзя возвращать traceback клиенту?",
        ],
    ),
    question(
        "backend_python_security_middle_01",
        "security",
        "middle",
        4,
        "Как безопасно хранить и проверять пароли пользователей?",
        "Ожидается: пароли не хранятся в открытом виде, используется password hashing с солью и адаптивным алгоритмом вроде bcrypt/argon2, сравнение через verify-функцию, политика reset tokens, rate limiting и отсутствие паролей в логах.",
        [
            {"title": "Хранит только password hash", "weight": 25},
            {"title": "Использует bcrypt/argon2 и соль", "weight": 30},
            {"title": "Корректная verify-проверка", "weight": 15},
            {"title": "Reset tokens и срок жизни", "weight": 15},
            {"title": "Rate limiting и безопасные логи", "weight": 15},
        ],
        [
            "Предлагает шифровать пароли обратимым ключом",
            "Использует обычный sha256 без соли",
            "Логирует пароль при ошибке входа",
        ],
        [
            "Почему hash лучше обратимого шифрования для паролей?",
            "Как безопасно реализовать forgot password?",
        ],
    ),
    question(
        "backend_python_security_senior_01",
        "security",
        "senior",
        5,
        "Как спроектировать авторизацию в API, где есть роли, владение ресурсами и сервисные интеграции?",
        "Сильный ответ должен разделять authentication и authorization, описывать RBAC/ABAC или policy layer, проверку ownership рядом с бизнес-операцией, сервисные credentials с ограниченными scope, аудит, deny-by-default и тесты на негативные сценарии.",
        [
            {"title": "Разделяет authentication и authorization", "weight": 20},
            {"title": "Policy layer с RBAC/ABAC", "weight": 25},
            {"title": "Проверка ownership и tenant boundary", "weight": 25},
            {"title": "Scoped service credentials и аудит", "weight": 15},
            {"title": "Deny-by-default и negative tests", "weight": 15},
        ],
        [
            "Проверяет роль только на frontend",
            "Не проверяет владение конкретным ресурсом",
            "Дает сервисным токенам полный доступ без scope",
        ],
        [
            "Где хранить authorization policies?",
            "Как тестировать запрет доступа к чужому ресурсу?",
        ],
        180,
    ),
    question(
        "backend_python_devops_junior_01",
        "devops",
        "junior",
        2,
        "Что должно быть в Dockerfile для Python backend-приложения, чтобы образ был воспроизводимым и запускался предсказуемо?",
        "Нужно упомянуть базовый образ с версией Python, рабочую директорию, установку системных зависимостей, копирование requirements, установку зависимостей, копирование кода, expose и команду запуска. Хороший ответ говорит про .dockerignore и env через окружение.",
        [
            {"title": "Фиксированный базовый образ и рабочая директория", "weight": 20},
            {"title": "Установка зависимостей отдельным слоем", "weight": 25},
            {"title": "Копирование кода и команда запуска", "weight": 20},
            {"title": "Env/config не зашиты в образ", "weight": 20},
            {"title": ".dockerignore и размер образа", "weight": 15},
        ],
        [
            "Хардкодит секреты в Dockerfile",
            "Ставит зависимости после копирования всего кода без причины",
            "Не понимает разницу build-time и runtime config",
        ],
        [
            "Зачем сначала копировать requirements.txt?",
            "Где должны храниться секреты для контейнера?",
        ],
    ),
    question(
        "backend_python_devops_middle_01",
        "devops",
        "middle",
        3,
        "Какие health checks и метрики вы бы добавили для FastAPI-сервиса в Docker?",
        "Ожидается readiness/liveness различение, проверка процесса, доступности БД для readiness, latency/error rate, saturation ресурсов, connection pool, structured logs и трассировка. Health check не должен быть тяжелым и не должен ломать сервис при кратком сбое внешней зависимости.",
        [
            {"title": "Различает liveness и readiness", "weight": 25},
            {"title": "Проверяет БД только там, где это нужно", "weight": 20},
            {"title": "Метрики latency/error rate/saturation", "weight": 25},
            {"title": "Логи и tracing для диагностики", "weight": 15},
            {"title": "Health check легкий и стабильный", "weight": 15},
        ],
        [
            "Делает тяжелый health check с множеством внешних вызовов",
            "Не различает liveness и readiness",
            "Считает HTTP 200 единственной нужной метрикой",
        ],
        [
            "Что должен проверять readiness endpoint?",
            "Какие метрики помогут понять, что БД стала bottleneck?",
        ],
    ),
    question(
        "backend_python_devops_senior_01",
        "devops",
        "senior",
        4,
        "Как организовать безопасный zero-downtime deploy backend-сервиса с миграциями БД?",
        "Сильный ответ описывает backward-compatible migrations, expand/contract подход, разделение schema migration и app rollout, health/readiness, rolling deploy, feature flags, rollback plan и наблюдение за метриками. Важно не ломать старую версию приложения новой схемой.",
        [
            {"title": "Backward-compatible migrations", "weight": 30},
            {"title": "Expand/contract rollout", "weight": 25},
            {"title": "Разделение миграций и деплоя приложения", "weight": 15},
            {"title": "Readiness, rolling deploy и rollback", "weight": 20},
            {"title": "Мониторинг после релиза", "weight": 10},
        ],
        [
            "Удаляет колонку до выката новой версии кода",
            "Не имеет rollback plan",
            "Запускает долгую блокирующую миграцию в peak time без оценки",
        ],
        [
            "Что такое expand/contract migration?",
            "Как выкатывать изменение обязательного поля?",
        ],
        180,
    ),
]


async def seed_questions() -> tuple[int, int]:
    created = 0
    updated = 0

    async with AsyncSessionLocal() as session:
        for payload in QUESTIONS:
            result = await session.execute(
                select(InterviewQuestion).where(InterviewQuestion.code == payload["code"])
            )
            existing = result.scalar_one_or_none()

            if existing is None:
                session.add(InterviewQuestion(**payload))
                created += 1
                continue

            for key, value in payload.items():
                setattr(existing, key, value)
            updated += 1

        await session.commit()

    return created, updated


async def main() -> None:
    created, updated = await seed_questions()
    print(f"Seeded backend/python interview questions: created={created}, updated={updated}")


if __name__ == "__main__":
    asyncio.run(main())
