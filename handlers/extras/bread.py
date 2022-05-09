"""
This files has one function that will be called if the queue under question is
'Bread'.
"""

from aiogram import types

from loader import dp
from utils.sticker_file_ids import CHARISMATIC_STICKER


@dp.callback_query_handler(text="enough_bread")
async def cheer_user_up(call: types.CallbackQuery):
    """Let user know that they don't have to buy bread today."""
    await call.message.delete_reply_markup()

    await call.message.answer_sticker(CHARISMATIC_STICKER)
    await call.message.answer(
        "That's great news! You don't have to buy bread today, you can relax. "
        "I'll remind you to buy it next time."
    )
    await call.answer()
