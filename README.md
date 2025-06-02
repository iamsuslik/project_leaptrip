# 🧸 Планирование путешествий с использованием LLM (Travel Planner with LLM) ✈️

Проект представляет собой мобильное приложение для планирования путешествий с использованием языковых моделей (LLM) для генерации рекомендаций.

## 📝 Описание проекта

Сервис предоставляет следующие возможности:
-  Регистрация и авторизация пользователей
-  Поиск авиабилетов по заданным параметрам
-  Поиск отелей по заданным критериям
-  Telegram-бот с LLM (GigaChat) для рекомендаций по путешествиям

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

## 🛠 Технологический стек

**Frontend**:  
Kotlin (Android)

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
#### `POST /login` - Вход пользователя (по email или username).

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
#### `POST /flights/search` - Поиск авиабилетов через API Travelpayouts.
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
#### `POST /hotels/search`- Поиск отелей через API Hotellook.
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

##### Response (HotelResponse):
```
[
  {
    "name": "string",
    "stars": 0,
    "price": 0,           
    "price_per_night": 0, 
    "location": {  
      "lat": 0,
      "lon": 0
    },
    "booking_url": "string" 
  }
]
```
## 🧳 Travel Planner Telegram Bot (GigaChat Integration)

## 📌 Описание
Telegram-бот для подбора идеального города путешествия с использованием GigaChat API. Бот задает пользователю серию вопросов и на основе ответов генерирует персонализированные рекомендации.

## ✨ Особенности
- Интерактивный диалог с пользователем
- Интеграция с GigaChat API для генерации рекомендаций
- Клавиатура с вариантами ответов
- Возможность прервать диалог в любой момент

## 🛠 Технологии
- `python-telegram-bot` v20+ - работа с Telegram API
- `gigachat` - взаимодействие с GigaChat API
- `requests` - HTTP-запросы

### Этапы диалога
 1. Тип отдыха
 2. Бюджет
 3. Климат
 4. Длительность
 5. Компания (DURATION → COMPANION)
 6. Генерация рекомендаций (COMPANION → завершение)
 
### 📝 Пример диалога
### Вопросы бота:
#### Какой тип отдыха вас интересует?
- Активный / Культурный / Религиозный / Пляжный / Гастрономический / Экотуризм
#### Какой у вас бюджет на поездку?
- До 50 тыс. руб. / 50–100 тыс. руб. / 100–200 тыс. руб. / Не важно
#### Какой климат предпочитаете?
- Теплый / Умеренный / Холодный / Любой
#### На сколько планируете поездку?
- 3–5 дней / 1–2 недели / Месяц+ / Еще не решил
#### С кем вы путешествуете?
- Один/с партнером / С семьей / С друзьями / Групповой тур

### Пример ответа GigaChat:
```
1. Бали (Индонезия):
   - 🌎 Почему подходит: Идеально сочетает пляжный отдых и активные развлечения
   - 💰 Бюджет: ~120 тыс. руб. на 2 недели
   - 📍 Совет: Обязательно посетите храм Танах Лот на закате!

2. Барселона (Испания):
   - 🌎 Почему подходит: Богатая культура и гастрономическая сцена
   - 💰 Бюджет: ~150 тыс. руб. на 10 дней
   - 📍 Совет: Попробуйте паэлью в ресторане 7 Portes!

3. Токио (Япония):
   - 🌎 Почему подходит: Уникальное сочетание традиций и современных технологий
   - 💰 Бюджет: ~200 тыс. руб. на 2 недели
   - 📍 Совет: Посетите район Акихабара для технологичных развлечений
```

## 📱 Приложение
<img src="images/Рисунок1.png" alt="бот" width="200"> <img src="images/Рисунок2.png" alt="бот" width="200"> <img src="images/Рисунок3.png" alt="бот" width="200"> <img src="images/Рисунок5.png" alt="бот" width="200"> <img src="images/Рисунок6.png" alt="бот" width="200"> <img src="images/Рисунок7.png" alt="бот" width="200"> <img src="images/Рисунок8.png" alt="бот" width="200"> <img src="images/Рисунок9.png" alt="бот" width="200"> <img src="images/Рисунок10.png" alt="бот" width="200"> <img src="images/Рисунок11.png" alt="бот" width="200"> 

## 👥 Команда
**Frontend** 🎨
- Лоскутова Анастасия
- Кириенко Анастасия

**Backend** 👩‍💻
- Ельцова Дарья
- Василянская Алена
- Баженова Дарья

