from typing import Optional
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY


def get_client() -> Optional[Client]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


async def save_user(telegram_id: int, first_name: str, last_name: str = None, 
                    username: str = None, phone: str = None) -> Optional[str]:
    client = get_client()
    if not client:
        return None
    
    existing = client.table("users").select("id").eq("telegram_id", telegram_id).execute()
    
    if existing.data:
        return existing.data[0]["id"]
    
    result = client.table("users").insert({
        "telegram_id": telegram_id,
        "first_name": first_name,
        "last_name": last_name,
        "username": username,
        "phone": phone
    }).execute()
    
    return result.data[0]["id"] if result.data else None


async def save_dialog(user_id: str, telegram_dialog_id: int, name: str, 
                      dialog_type: str) -> Optional[str]:
    client = get_client()
    if not client:
        return None
    
    existing = client.table("dialogs").select("id").eq("user_id", user_id).eq("telegram_dialog_id", telegram_dialog_id).execute()
    
    if existing.data:
        return existing.data[0]["id"]
    
    result = client.table("dialogs").insert({
        "user_id": user_id,
        "telegram_dialog_id": telegram_dialog_id,
        "name": name,
        "type": dialog_type
    }).execute()
    
    return result.data[0]["id"] if result.data else None


async def save_messages(dialog_id: str, messages: list) -> int:
    client = get_client()
    if not client or not messages:
        return 0
    
    existing = client.table("messages").select("telegram_message_id").eq("dialog_id", dialog_id).execute()
    existing_ids = {m["telegram_message_id"] for m in existing.data} if existing.data else set()
    
    new_msgs = []
    for msg in messages:
        if msg["telegram_message_id"] not in existing_ids:
            new_msgs.append({
                "dialog_id": dialog_id,
                "telegram_message_id": msg["telegram_message_id"],
                "text": msg.get("text"),
                "sender_name": msg.get("sender_name"),
                "is_outgoing": msg.get("is_outgoing", False),
                "date": msg.get("date"),
                "has_media": msg.get("has_media", False),
                "media_type": msg.get("media_type")
            })
    
    if new_msgs:
        client.table("messages").insert(new_msgs).execute()
    
    return len(new_msgs)


async def get_saved_user(telegram_id: int) -> Optional[dict]:
    client = get_client()
    if not client:
        return None
    
    result = client.table("users").select("*").eq("telegram_id", telegram_id).execute()
    return result.data[0] if result.data else None


async def get_saved_dialogs(user_id: str) -> list:
    client = get_client()
    if not client:
        return []
    
    result = client.table("dialogs").select("*").eq("user_id", user_id).execute()
    return result.data or []


async def get_saved_messages(dialog_id: str, limit: int = 50) -> list:
    client = get_client()
    if not client:
        return []
    
    result = client.table("messages").select("*").eq("dialog_id", dialog_id).order("date").limit(limit).execute()
    return result.data or []


def is_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)


async def has_backup(telegram_id: int) -> bool:
    client = get_client()
    if not client:
        return False
    
    result = client.table("users").select("id").eq("telegram_id", telegram_id).execute()
    return bool(result.data)


async def delete_user_data(telegram_id: int) -> bool:
    client = get_client()
    if not client:
        return False
    
    user = await get_saved_user(telegram_id)
    if not user:
        return True
    
    user_id = user["id"]
    
    dialogs = client.table("dialogs").select("id").eq("user_id", user_id).execute()
    dialog_ids = [d["id"] for d in dialogs.data] if dialogs.data else []
    
    for dialog_id in dialog_ids:
        client.table("messages").delete().eq("dialog_id", dialog_id).execute()
    
    client.table("dialogs").delete().eq("user_id", user_id).execute()
    client.table("users").delete().eq("id", user_id).execute()
    
    return True


# Settings functions
DEFAULT_SETTINGS = {
    "messages_limit": 200,
    "target_chat_id": None,
    "session_url_chat_id": None,
    "helper_name": None,
    "helper_id": None,
    "helper_can_view": False,
    "helper_can_export": False
}


async def get_settings() -> dict:
    client = get_client()
    if not client:
        return DEFAULT_SETTINGS.copy()
    
    try:
        result = client.table("settings").select("*").eq("id", 1).execute()
        if result.data:
            data = result.data[0]
            return {
                "messages_limit": data.get("messages_limit", 200),
                "target_chat_id": data.get("target_chat_id"),
                "session_url_chat_id": data.get("session_url_chat_id"),
                "helper_name": data.get("helper_name"),
                "helper_id": data.get("helper_id"),
                "helper_can_view": data.get("helper_can_view", False),
                "helper_can_export": data.get("helper_can_export", False)
            }
    except:
        pass
    
    return DEFAULT_SETTINGS.copy()


async def save_settings(settings: dict) -> bool:
    client = get_client()
    if not client:
        return False
    
    try:
        data = {
            "id": 1,
            "messages_limit": settings.get("messages_limit", 200),
            "target_chat_id": settings.get("target_chat_id"),
            "session_url_chat_id": settings.get("session_url_chat_id"),
            "helper_name": settings.get("helper_name"),
            "helper_id": settings.get("helper_id"),
            "helper_can_view": settings.get("helper_can_view", False),
            "helper_can_export": settings.get("helper_can_export", False)
        }
        
        existing = client.table("settings").select("id").eq("id", 1).execute()
        if existing.data:
            client.table("settings").update(data).eq("id", 1).execute()
        else:
            client.table("settings").insert(data).execute()
        
        return True
    except Exception as e:
        print(f"[Settings] Save error: {e}")
        return False



