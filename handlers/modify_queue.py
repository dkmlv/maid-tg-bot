import logging

from aiogram import types

from loader import dp, users, queues
from utils.get_db_data import (
    get_queue_array,
    get_queue_list,
    get_team_id,
    get_setup_person,
)
from utils.sticker_file_ids import NOPE_STICKER


@dp.callback_query_handler(text_startswith="modify_")
async def modify_a_queue(call: types.CallbackQuery):
    """
    Provides some options to modify the queue (delete, reorder, reassign turn)
    """
    keyboard = types.InlineKeyboardMarkup()

    buttons = [
        types.InlineKeyboardButton(text="delete", callback_data="delete_queue"),
        types.InlineKeyboardButton(text="reorder", callback_data="reorder_queue"),
        types.InlineKeyboardButton(text="reassign", callback_data="reassign_turn"),
    ]

