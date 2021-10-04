import base64
import hmac
import hashlib
from typing import Optional
import json

from fastapi import FastAPI, Form, Cookie, Body
from fastapi.responses import Response


app = FastAPI() # Экземпляр приложения фастапи

SECRET_KEY = "5986c6a698a3024cbc8c7174fc0f17cb4f7375e5c861a8732d12559c89ae91bc" # Ключ сгенерированный в терминале openssl rand -hex 32
PASSWORD_SALT = "5d1d9771cb056cc2721183c35aff96278eaf9522e1ad2fe6df44df06d1fc1278"


def sign_data(data: str) -> str:
    """Возвращает подписанные данные data"""
    return hmac.new(
        SECRET_KEY.encode(),
        msg=data.encode(),
        digestmod=hashlib.sha256
    ).hexdigest().upper()


def get_username_from_signed_string(username_signed: str) -> Optional[str]:
    username_base64, sign = username_signed.split(".")
    username = base64.b64decode(username_base64.encode()).decode()
    valid_sign = sign_data(username)
    if hmac.compare_digest(valid_sign, sign):
        return username

def verify_password(username: str, password: str) -> bool:
    password_hash = hashlib.sha256( (password + PASSWORD_SALT).encode() ).hexdigest().lower()
    stored_password_hash = users[username]["password"].lower()
    return password_hash == stored_password_hash


users = { # Создаем некое подобие примера базы данных с пользователями
    'olga@mail.ru': {
        "name": "Ольга Сергеевна",
        "password": "218059507f3c6220f3cd0b3eff7cd2bbb9c664a4d258e42aaede1116233faf42",
        "balance": 1000
    },
    "mikhail@user.ru": {
        "name": "Миша",
        "password": "07761f5e7ca680957165ca4f42902772b48b56ed24de3da2f37ea7800fc35e4f",
        "balance": 555_555
    }
}


@app.get("/") # Декоратор для запуска функции
def index_page(username: Optional[str] = Cookie(default=None)): # Простая функция для обработки ответа. Индексная (главная) страница сайта
    with open('templates/login.html', 'r') as f:
        login_page = f.read()
    if not username:
        return Response(login_page, media_type="text/html")
    valid_username = get_username_from_signed_string(username)
    if not valid_username:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username")
        return response
    try:
        user = users[valid_username]
    except KeyError:
        response = Response(login_page, media_type="text/html")
        response.delete_cookie(key="username")
        return response
    return Response(
        f"Привет, {users[valid_username]['name']}! <br />"
        f"Баланс: {users[valid_username]['balance']}"
        , media_type="text/html")


# Создаем функцию для страницы с логином и паролем
@app.post("/login") 
def process_login_page(data: dict = Body(...)):
    username = data["username"]
    password = data["password"]
    user = users.get(username)
    if not user or not verify_password(username, password):
        return Response(
            json.dumps({
                "success": False,
                "message": "Я вас не знаю"
            }),
            media_type="application/json")

    response = Response(
        json.dumps({
            "success": True,
            "message": f"Привет, {user['name']}!<br/>Баланс: {user['balance']}"
        }), media_type="application/json")
    
    username_signed = base64.b64encode(username.encode()).decode() + "." + \
        sign_data(username)
    response.set_cookie(key="username", value=username_signed) # Устанавливаем куки по ключу username
    return response