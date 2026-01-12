from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def numpad(code: str = "") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📝 Код: {code or '—'}", callback_data="display")],
        [
            InlineKeyboardButton(text="7", callback_data="num_7"),
            InlineKeyboardButton(text="8", callback_data="num_8"),
            InlineKeyboardButton(text="9", callback_data="num_9"),
        ],
        [
            InlineKeyboardButton(text="4", callback_data="num_4"),
            InlineKeyboardButton(text="5", callback_data="num_5"),
            InlineKeyboardButton(text="6", callback_data="num_6"),
        ],
        [
            InlineKeyboardButton(text="1", callback_data="num_1"),
            InlineKeyboardButton(text="2", callback_data="num_2"),
            InlineKeyboardButton(text="3", callback_data="num_3"),
        ],
        [
            InlineKeyboardButton(text="0", callback_data="num_0"),
            InlineKeyboardButton(text="⬅️", callback_data="backspace"),
            InlineKeyboardButton(text="✅", callback_data="submit"),
        ],
    ])
