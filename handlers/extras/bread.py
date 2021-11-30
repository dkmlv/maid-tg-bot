"""
This files has some functions that will be called if the queue under
question is 'Bread'.
"""

from aiogram import types

from loader import dp
from utils.sticker_file_ids import CHARISMATIC_STICKER


@dp.callback_query_handler(text="ask_if_theres_bread")
async def ask_if_theres_bread(call: types.CallbackQuery):
    """Ask if there's already enough bread.

    This is needed as if there's already enough bread, then there's no
    need to buy it at that time and hence no need to transfer the turn
    to the next person in the queue.
    """

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(text="Yes", callback_data="enough_bread"),
        types.InlineKeyboardButton(text="No", callback_data="transfer_Bread"),
    ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        "Actually, do you have enough bread at home?\nIf you have enough, you "
        "don't have to buy today and I can remind you next time.",
        reply_markup=keyboard,
    )
    await call.answer()


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
