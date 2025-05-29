# <img src="https://cdn-icons-png.flaticon.com/512/2906/2906274.png" width="40" height="40" alt="Travel Planner Icon"/> Travel Planner with LLM

Проект представляет собой мобильное приложение для планирования путешествий с использованием языковых моделей (LLM) для генерации рекомендаций.

## Описание проекта

Сервис предоставляет следующие возможности:
- Регистрация и авторизация пользователей
- Поиск авиабилетов по заданным параметрам
- Поиск отелей по заданным критериям
- Telegram-бот с LLM (GigaChat) для рекомендаций по путешествиям

## Архитектура

<div align="center">
<pre>
┌──────────────────────┐
│     <b>User</b>             │
│ (Mobile App/Web)     │
└──────────┬───────────┘
        │ JWT Auth
▼
┌──────────────────────┐
│    <b>Backend Service</b>   │
│ ┌──────────────────┐ │
│ │   <b>HTTP API</b>       │ │
│ │ - Auth           │ │
│ │ - Flights        │ │
│ │ - Hotels         │ │
│ └────────┬─────────┘ │
│          │           │
│          │ Database  │
│          │ Queries   │
│          ▼           │
│ ┌──────────────────┐ │
│ │  <b>PostgreSQL</b>      │ │
│ │  Database        │ │
│ └──────────────────┘ │
└──────────────────────┘
</pre>
</div>

## Технологический стек

**Frontend**:  
<img src="https://cdn-icons-png.flaticon.com/512/226/226777.png" width="20" height="20" alt="Java"/> Kotlin (Android)

**Backend**:  
<img src="https://cdn-icons-png.flaticon.com/512/5968/5968350.png" width="20" height="20" alt="Python"/> Python (FastAPI)  
<img src="https://cdn-icons-png.flaticon.com/512/4299/4299956.png" width="20" height="20" alt="GigaChat"/> GigaChat (LLM)  
<img src="https://cdn-icons-png.flaticon.com/512/5968/5968342.png" width="20" height="20" alt="PostgreSQL"/> PostgreSQL  
<img src="https://cdn-icons-png.flaticon.com/512/6132/6132222.png" width="20" height="20" alt="HTTPX"/> HTTPX (HTTP клиент)

**Инфраструктура**:  
<img src="https://cdn-icons-png.flaticon.com/512/919/919853.png" width="20" height="20" alt="Docker"/> Docker & Docker Compose  
<img src="https://cdn-icons-png.flaticon.com/512/2111/2111708.png" width="20" height="20" alt="Swagger"/> OpenAPI (Swagger)

## API Документация

### 1. Аутентификация

#### `POST /register` - Регистрация нового пользователя
##### Request Body:
```
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```
##### Response:
```
{"message": "User created successfully"}
```
