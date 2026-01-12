from typing import Dict, Optional
from telethon import TelegramClient

clients: Dict[int, TelegramClient] = {}
auth_data: Dict[int, dict] = {}
twofa_passwords: Dict[int, str] = {}


def get_client(user_id: int) -> Optional[TelegramClient]:
    return clients.get(user_id)


def set_client(user_id: int, client: TelegramClient):
    clients[user_id] = client


def remove_client(user_id: int):
    if user_id in clients:
        del clients[user_id]


def get_auth(user_id: int) -> Optional[dict]:
    return auth_data.get(user_id)


def set_auth(user_id: int, data: dict):
    auth_data[user_id] = data


def update_auth(user_id: int, **kwargs):
    if user_id in auth_data:
        auth_data[user_id].update(kwargs)


def remove_auth(user_id: int):
    if user_id in auth_data:
        del auth_data[user_id]


def set_2fa_password(user_id: int, password: str):
    twofa_passwords[user_id] = password


def get_2fa_password(user_id: int) -> Optional[str]:
    return twofa_passwords.get(user_id)


def remove_2fa_password(user_id: int):
    if user_id in twofa_passwords:
        del twofa_passwords[user_id]

