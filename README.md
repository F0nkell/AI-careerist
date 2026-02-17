<div align="center">

# 🚀 AI Careerist: The Ultimate Job Offer Machine
### Твой Личный ИИ-Рекрутер, Коуч и Ментор в одном кармане.

[![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![Telegram](https://img.shields.io/badge/Telegram-Web_App-26A5E4?style=for-the-badge&logo=telegram)](https://core.telegram.org/bots/webapps)

<p align="center">
  <a href="#-почему-это-революция">Фичи</a> •
  <a href="#-технологический-стек">Стек</a> •
  <a href="#-архитектура-ии">AI Core</a> •
  <a href="#-установка-и-запуск">Запуск</a>
</p>

</div>

---

## ⚡ Почему это революция?

Поиск работы — это война. **AI Careerist** — это твое супероружие.
Мы объединили передовые LLM, компьютерное зрение и голосовые технологии, чтобы создать симулятор собеседований, который **жестче, чем реальный HR**.

Это не просто чат-бот. Это полноценное **Telegram Web App (TWA)**, которое видит, слышит и знает всё о твоей профессии.

---

## 🔥 Убойный Функционал

### 1. 💀 Resume Killer (Анализатор Резюме)
Забудь про "мягкий фидбек". Наш ИИ разнесет твое резюме в пух и прах, как это делают рекрутеры Google и Yandex.
*   **Deep Analysis:** Находит "воду", клише и слабые места.
*   **Auto-Rewrite:** (Premium) Переписывает резюме так, чтобы оно проходило ATS-фильтры и продавало тебя за секунды.
*   **PDF Parsing:** Работает с реальными файлами.

### 2. 🎤 Hardcore Mock Interview (Голосовой Симулятор)
Тренируйся проходить собеседования голосом, как в Zoom.
*   **Real Voice:** Ты говоришь — он отвечает. Никакого текста.
*   **Строгий HR:** ИИ настроен на роль требовательного техлида. Он перебивает, душнит и ловит на ошибках.
*   **Vision (Зрение):** Скинь скриншот кода или архитектуры — ИИ увидит его и задаст вопрос по картинке!
*   **RAG (База Знаний):** Бот не выдумывает вопросы. Он лезет в базу данных (600+ реальных вопросов с GitHub) и гоняет тебя по тому, что реально спрашивают на рынке.

---

## 🛠 Технологический Стек

Мы не использовали no-code конструкторы. Это **серьезная инженерная разработка**.

| Компонент | Технологии | Описание |
| :--- | :--- | :--- |
| **Frontend** | **React + TypeScript + Vite** | Молниеносный UI, адаптированный под Telegram (TWA SDK). Стилизация через **Tailwind CSS**. Анимации **Framer Motion**. |
| **Backend** | **FastAPI (Python)** | Асинхронное ядро. Строгая типизация (Pydantic). Валидация данных `initData` от Telegram (HMAC-SHA256). |
| **Database** | **PostgreSQL + SQLAlchemy** | Хранение пользователей и огромной базы вопросов (RAG). Миграции через **Alembic**. |
| **Infrastructure** | **Docker Compose + Nginx** | Полная контейнеризация. Nginx как Reverse Proxy шлюз. Production-ready сборка. |

---

## 🧠 Архитектура ИИ (The Brain)

Мы собрали "Франкенштейна" из лучших бесплатных и дешевых решений на рынке:

1.  **Мозг (LLM):** `Google Gemini 1.5 Flash` / `Qwen-2-VL` (через OpenRouter/VseGPT). Обеспечивает мгновенную реакцию и мультимодальность.
2.  **Уши (STT):** `Google Speech Recognition` + `Groq Whisper`. Понимает даже шепот и технический сленг ("Тьюпл", "Деплой").
3.  **Голос (TTS):** `Microsoft Edge-TTS`. Нейросетевой голос (Дмитрий/Светлана), который звучит пугающе реалистично.
4.  **Память (RAG):** Векторный/Текстовый поиск по базе вопросов (Python, JS, Marketing, Medicine и др.), собранных из топовых репозиториев GitHub.

---

## 🚀 Установка и Запуск

Разверни своего "Убийцу Резюме" за 2 минуты.

### Предварительные требования
*   Docker & Docker Compose
*   API Key (VseGPT или OpenRouter)
*   Telegram Bot Token

### 1. Клонирование
```bash
git clone https://github.com/your-username/ai-careerist.git
cd ai-careerist
```
### 2. Настройка окружения
Создай файл .env в корне:
```
BOT_TOKEN="твой_токен_от_botfather"
OPENROUTER_API_KEY="твой_ключ_ai"
# Остальные настройки см. в config.py
POSTGRES_USER=app_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=twa_db
POSTGRES_HOST=db
```

### 3. Запуск (One-Click)
```bash
docker compose up --build -d
```
### 4. Наполнение Базы Знаний (RAG)
Чтобы бот стал умным, загрузи в него 1000+ вопросов:

```bash
docker compose exec app python parse_github.py  # Вопросы с GitHub
docker compose exec app python import_custom.py # Твои JSON паки
```

### 💎 Монетизация (Business Logic)
<br>Проект готов к заработку денег:
<br>Freemium модель: Бесплатный разбор ошибок, платное исправление.
<br>Subscription: Подписка на безлимитные мок-интервью.
<br>Tech: Подготовлен к интеграции Telegram Stars.
<div align="center">
[ Star this Repo ⭐ ] если хочешь пройти собес с первого раза!
Designed & Engineered by [Твое Имя] & AI Architect
</div>
