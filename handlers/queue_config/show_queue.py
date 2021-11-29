"""
Show the queue to the user in form of a list with the current turn
person highlighted.
This, unlike every other option in the /queues inline keyboard, is
available for all users, not just the admin.
"""

import logging

from aiogram import types

from loader import dp
from utils.get_db_data import get_queue_array, get_queue_list, get_team_id
from utils.sticker_file_ids import HERE_STICKER


@dp.callback_query_handler(text_startswith="show_")
async def show_a_queue(call: types.CallbackQuery):
    """Show the queue a user has selected to them."""
    logging.info("Showing a queue.")

    team_id = await get_team_id(call.from_user.id)
    queue_type = call.data.split("_")[-1]

    queue_array = await get_queue_array(team_id, queue_type)

    queue_list = await get_queue_list(queue_array)

    await call.message.answer(f"Here is your <b>{queue_type}</b> queue:\n{queue_list}")
    await call.message.answer_sticker(HERE_STICKER)

    await call.answer()
