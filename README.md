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

##### Ошибки:
-  400: Username already registered
-  400: Email already registered
##### POST /login - Вход пользователя (по email или username).

##### Request Body:  (UserLoginSchema):
```
{
  "username_or_email": "string",
  "password": "string"
}
```
##### Response:
```
{
  "access_token": "string"
}
```
##### Ошибки:
-  401: User not found or inactive
-  401: Incorrect password

### 2. Поиск авиабилетов
#### POST /flights/search
##### Описание: Поиск авиабилетов через API Travelpayouts.
##### Request Body (FlightRequest):
```
{
  "fromCity": "string",
  "toCity": "string",
  "departureDate": "string (YYYY-MM-DD)",
  "returnDate": "string (YYYY-MM-DD)",
  "one_way": "boolean",
  "direct": "boolean",
  "limit": "integer"
}
```
##### Response: (FlightResponse):
```
[
{
  "airline": "string",
  "flight_number": "string",
  "departure_at": "string (YYYY-MM-DD HH:MM)",
  "return_at": "string (YYYY-MM-DD HH:MM)",
  "price": "integer",
  "transfers": "string",
  "duration": "string",
  "booking_url": "string"
}
]
```
##### Ошибки:
-  400: Invalid city name or IATA code
-  400: Departure date must be in the future
-  400: Return date must be after departure
-  404: No flights found
-  500: Internal server error
### 3. Поиск отелей
#### POST /hotels/search
##### Описание: Поиск отелей через API Hotellook.
##### Request Body (HotelRequest):
```
{
  "city": "string",
  "check_in": "string",
  "check_out": "string",
  "adults": 2,
  "stars": [3, 4, 5], 
  "price_min": 0,           
  "price_max": 0,
  "limit": 10
}
```
##### Проверки:
- Корректность дат (check_out > check_in).
- Фильтрация по звездам, цене и другим параметрам.

##### Response (List[HotelResponse]):
```
[
  {
    "name": "string",
    "stars": 0,
    "price": 0,             // Общая цена за период
    "price_per_night": 0,   // Цена за ночь
    "location": {           // Координаты
      "lat": 0,
      "lon": 0
    },
    "booking_url": "string" // Ссылка на бронирование
  }
]
```
##### Ошибки:
400: Неверные даты или параметры.
404: Отели не найдены.
500: Ошибка сервера.
