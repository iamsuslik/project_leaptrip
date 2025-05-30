from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from authx import AuthX, AuthXConfig
from pydantic import BaseModel, Field, validator
from databases import Database
from sqlalchemy import create_engine, MetaData, Table, Column, String, Boolean, Integer, UniqueConstraint
from passlib.context import CryptContext
import re
from typing import List, Optional
from datetime import datetime
from fastapi.templating import Jinja2Templates 
import httpx
from cachetools import TTLCache
from dateutil import parser, tz
import logging


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = "postgresql+asyncpg://postgres:...@localhost:5432/testv0"
database = Database(DATABASE_URL)
metadata = MetaData()


users = Table(
    "usersversion1",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String, unique=True),
    Column("email", String, unique=True),
    Column("password", String),
    Column("is_active", Boolean, default=True),
    UniqueConstraint('email', name='unique_email')
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await database.connect()
        print("✅ Подключение к БД успешно!")

        engine = create_engine(DATABASE_URL.replace("+asyncpg", ""))
        metadata.create_all(engine)
        print("✅ Таблица 'users' создана (или уже существует)")

        yield
    except Exception as e:
        print(f"❌ Ошибка при подключении к БД: {e}")
        raise
    finally:
        await database.disconnect()

app = FastAPI(lifespan=lifespan)


templates = Jinja2Templates(directory="templates")

cache = TTLCache(maxsize=100, ttl=3600)
    


config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]

security = AuthX(config=config)



class UserLoginSchema(BaseModel):
    username_or_email: str
    password: str

class UserCreateSchema(BaseModel):
    username: str
    email: str
    password: str

def is_valid_email(email: str) -> bool:
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

@app.get("/")
async def home():
    return {"message": "Welcome to the API!"}

@app.post("/register")
async def register(user: UserCreateSchema):
    print(f"🔹 Регистрация пользователя: {user.username}")  
    
    query = users.select().where(users.c.username == user.username)
    existing_user = await database.fetch_one(query)
    
    if existing_user:
        print("🔴 Пользователь уже существует!")
        raise HTTPException(status_code=400, detail="Username already registered")
    
    query = users.select().where(users.c.email == user.email)
    existing_email = await database.fetch_one(query)
    
    if existing_email:
        print("🔴 Email уже зарегистрирован!") 
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = pwd_context.hash(user.password)
    print(f"🔹 Хеш пароля: {hashed_password}") 
    
    query = users.insert().values(
        username=user.username,
        email=user.email,
        password=hashed_password,
        is_active=True
    )
    await database.execute(query)
    print("🟢 Пользователь добавлен в БД!")  # Лог 4
    
    return {"message": "User created successfully"}


@app.post("/login")
async def login(creds: UserLoginSchema, response: Response):
    # Determine if login is by email or username
    if is_valid_email(creds.username_or_email):
        query = users.select().where(users.c.email == creds.username_or_email)
    else:
        query = users.select().where(users.c.username == creds.username_or_email)
    
    user = await database.fetch_one(query)
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    if not pwd_context.verify(creds.password, user.password):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    token = security.create_access_token(uid=user.username)
    response.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)
    return {"access_token": token}




####################################################################################################
#  парсинг авиабилетов 

logging.basicConfig(level=logging.DEBUG) 
logger = logging.getLogger(__name__)


API_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"
API_TOKEN = "..."
TIMEOUT = 30

AIRLINE_NAMES = {
    "SU": "Аэрофлот", "TK": "Turkish Airlines", "S7": "S7 Airlines",
    "U6": "Уральские авиалинии", "DP": "Победа", "WZ": "Red Wings",
    "2S": "Southwind", 
}


CITY_NAMES_TO_IATA = {
    "москва": "MOW", "санкт-петербург": "LED", "казань": "KZN",
    "екатеринбург": "SVX", "новосибирск": "OVB", "сочи": "AER",
    "краснодар": "KRR", "уфа": "UFA", "самара": "KUF",
    "ростов-на-дону": "ROV", "волгоград": "VOG", "пермь": "PEE",
    "воронеж": "VOZ", "омск": "OMS", "красноярск": "KJA",
    "стамбул": "IST", "анталья": "AYT", "дубай": "DXB",
    "тегеран": "IKA", "ереван": "EVN", "баку": "GYD",
    "ташкент": "TAS", "алматы": "ALA", "нью-йорк": "NYC",
    "лондон": "LON", "париж": "PAR", "берлин": "BER",
    "рим": "ROM", "токио": "TYO", "пекин": "BJS",
}

class FlightRequest(BaseModel):
    origin: str = Field(..., alias="fromCity")
    destination: str = Field(..., alias="toCity") 
    depart_date: str =Field(..., alias="departureDate")
    return_date: Optional[str] = Field(None, alias="returnDate")
    one_way: bool = Field(False, alias="oneWay")
    direct: bool = Field(False, alias="direct")
    limit: int = Field(10, alias="limit")

    @validator("depart_date", "return_date")
    def validate_date_format(cls, v):
        if v:
            try:
                parser.parse(v).date()  # Проверяем, что дата парсится
            except ValueError:
                raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД")
        return v

class FlightResponse(BaseModel):
    airline: str
    flight_number: str
    departure_at: str
    return_at: Optional[str]
    price: int
    transfers: str
    duration: str
    booking_url: str

class FlightSearchResponse(BaseModel):
    flights: List[FlightResponse]
    
def city_name_to_iata(city_name: str) -> str:
    city_name_lower = city_name.strip().lower()
    if city_name_lower in CITY_NAMES_TO_IATA:
        return CITY_NAMES_TO_IATA[city_name_lower]
    
    if len(city_name) == 3 and city_name.isupper():
        return city_name
    
    raise HTTPException(status_code=400, detail=f"Город '{city_name}' не найден. Пожалуйста, укажите корректное название города или код IATA")

async def fetch_flights(params: dict) -> List[dict]:
    try:
        headers = {
            "X-Access-Token": API_TOKEN,
            "User-Agent": "Mozilla/5.0",  
        }
        
        params.update({
            "currency": "rub",
            "sorting": "price",
            "flexible_dates": "1", 
        })
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            r = await client.get(API_URL, params=params, headers=headers)
            r.raise_for_status()
            data = r.json()
            
            logger.debug(f"Raw API data: {data}") 
            
            if not data.get("success", True):
                logger.error(f"API Error: {data.get('error')}")
                return []
                
            return data.get("data", [])
            
    except httpx.RequestError as e:
        logger.error(f"Request failed: {e}")
        return []

def format_time(dt_str: str, timezone="Europe/Moscow") -> str:
    try:
        dt = parser.parse(dt_str)
        if not dt.tzinfo:
            dt = dt.replace(tzinfo=tz.UTC)
        local_dt = dt.astimezone(tz.gettz(timezone))
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        logger.warning(f"Error formatting time: {dt_str}")
        return dt_str

def parse_duration(duration_minutes: int) -> str:
    hours = duration_minutes // 60
    minutes = duration_minutes % 60
    return f"{hours}ч {minutes}м" if hours > 0 else f"{minutes}м"

@app.post("/flights/search", response_model=List[FlightResponse])
async def search_flights(request: FlightRequest, raw_request: Request):
    request_body = await raw_request.body()
    logger.info(f"Получен запрос: {request_body.decode()}")
    try:
        origin_iata = city_name_to_iata(request.origin)
        destination_iata = city_name_to_iata(request.destination)
        
        depart_date = parser.parse(request.depart_date).date()
        if depart_date < datetime.now().date():
            raise HTTPException(400, "Дата вылета должна быть в будущем")

        params = {
            "origin": origin_iata,
            "destination": destination_iata,
            "departure_at": request.depart_date,
            "one_way": str(request.one_way).lower(),
            "direct": str(request.direct).lower(),
            "limit": request.limit,
        }

        if request.return_date and not request.one_way:
            return_date = parser.parse(request.return_date).date()
            if return_date <= depart_date:
                raise HTTPException(400, "Дата возврата должна быть позже вылета")
            params["return_at"] = request.return_date

        flights = await fetch_flights(params)
        if not flights:
            raise HTTPException(404, "Рейсы не найдены")

        results = []
        for flight in flights[:request.limit]:
            try:
                price = int(flight.get("price", 0))
                if price <= 0:
                    continue

                airline = AIRLINE_NAMES.get(flight.get("airline", ""), flight.get("airline", "Unknown"))
                
                booking_url = (
                    f"https://www.aviasales.ru/redirect?flight_token={flight['flight_token']}"
                    if flight.get("flight_token")
                    else f"https://www.aviasales.ru/search?origin={origin_iata}&destination={destination_iata}"
                )

                departure_at = format_time(flight["departure_at"])
                return_at = format_time(flight["return_at"]) if flight.get("return_at") else None
                duration = parse_duration(flight.get('duration', 0)) 

                results.append(FlightResponse(
                    airline=airline,
                    flight_number=flight.get("flight_number", ""),
                    departure_at=departure_at,
                    return_at=return_at,
                    price=price,
                    transfers="Прямой" if flight.get("transfers", 0) == 0 else f"{flight['transfers']} пересадки",
                    duration=duration,
                    booking_url=booking_url,
                ))
            except Exception as e:
                logger.warning(f"Skipping flight due to error: {e}")

        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        raise HTTPException(500, "Internal server error")



 
####################################################################################################
# парсинг отелей

HOTELS_API_URL = "https://engine.hotellook.com/api/v2/cache.json"
API_TOKEN = "..."
TIMEOUT = 30

class HotelRequest(BaseModel):
    city: str  # Название города
    check_in: str  # формат: ГГГГ-ММ-ДД
    check_out: str  # формат: ГГГГ-ММ-ДД
    adults: int = 2
    stars: Optional[List[int]] = None  # например [3,4,5]
    price_min: Optional[int] = None  # минимальная цена за весь период
    price_max: Optional[int] = None  # максимальная цена за весь период
    limit: int = 10

class HotelResponse(BaseModel):
    name: str
    stars: int
    price: int  # общая цена
    price_per_night: int
    location: dict  # {lat, lon}
    booking_url: str

async def fetch_hotels(params: dict) -> List[dict]:
    """Получение отелей из API"""
    try:
        params.update({
            "token": API_TOKEN,
            "currency": "rub",
            "lang": "ru"
        })
        
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.get(HOTELS_API_URL, params=params)
            logger.debug(f"Ответ API: {response.status_code}, {response.text[:200]}...")
            
            if response.status_code != 200:
                logger.error(f"Ошибка запроса к API: {response.status_code}")
                return []
            
            data = response.json()
            
            if isinstance(data, dict) and 'hotels' in data:
                return data['hotels']
            elif isinstance(data, list):
                return data
            else:
                logger.error(f"Неожиданный формат ответа API: {type(data)}")
                return []
                
    except Exception as e:
        logger.error(f"Ошибка при получении отелей: {str(e)}", exc_info=True)
        return []

def process_hotel(hotel: dict, nights: int) -> Optional[dict]:
    try:
        price = hotel.get('priceAvg') or hotel.get('priceFrom')
        if price is None:
            logger.warning(f"Пропускаем отель {hotel.get('hotelName')} - нет цены")
            return None
            
        price = int(price)
        
        location_data = hotel.get('location', {}).get('geo', {})
        location = {
            'lat': location_data.get('lat', 0),
            'lon': location_data.get('lon', 0)
        }
        
        booking_url = f"https://search.hotellook.com/?hotelId={hotel.get('hotelId')}"
        
        return {
            'name': hotel.get('hotelName', 'Неизвестный отель'),
            'stars': hotel.get('stars', 0),
            'price': price,
            'price_per_night': round(price / nights) if nights > 0 else price,
            'location': location,
            'booking_url': booking_url
        }
    except Exception as e:
        logger.warning(f"Ошибка обработки отеля: {str(e)}")
        return None

@app.post("/hotels/search", response_model=List[HotelResponse])
async def search_hotels(request: HotelRequest):
    try:
        try:
            check_in = parser.parse(request.check_in).date()
            check_out = parser.parse(request.check_out).date()
            
            if check_in < datetime.now().date():
                raise HTTPException(400, "Дата заезда должна быть в будущем")
            if check_out <= check_in:
                raise HTTPException(400, "Дата выезда должна быть после даты заезда")
                
            nights = (check_out - check_in).days
        except Exception as e:
            raise HTTPException(400, f"Неверный формат даты: {str(e)}")

        params = {
            "location": request.city,
            "checkIn": request.check_in,
            "checkOut": request.check_out,
            "adults": request.adults,
            "limit": request.limit * 2
        }
        
        hotels = await fetch_hotels(params)
        if not hotels:
            raise HTTPException(404, "По вашему запросу отели не найдены")
        
        results = []
        for hotel in hotels:
            try:
                processed = process_hotel(hotel, nights)
                if not processed:
                    continue
                
                if request.stars and processed['stars'] not in request.stars:
                    continue
                if request.price_min and processed['price'] < request.price_min:
                    continue
                if request.price_max and processed['price'] > request.price_max:
                    continue
                
                results.append(processed)
                
                if len(results) >= request.limit:
                    break
                    
            except Exception as e:
                logger.warning(f"Пропускаем отель из-за ошибки: {str(e)}")
                continue
        
        if not results:
            raise HTTPException(404, "Нет отелей, соответствующих вашим критериям")
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка сервера: {str(e)}", exc_info=True)
        raise HTTPException(500, "Внутренняя ошибка сервера")
