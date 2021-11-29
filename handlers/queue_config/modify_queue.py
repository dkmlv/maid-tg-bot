"""
Modifying a queue.
This option is also available only to the admin (aka setup person)
"""

import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp
from states.all_states import QueueSetup
from utils.get_db_data import get_queue_array, get_queue_list, get_team_id


@dp.callback_query_handler(text_startswith="modify_")
async def modify_a_queue(call: types.CallbackQuery, state: FSMContext):
    """Reset the current_turn and presents the queue for modification."""
    logging.info("Modifying queue.")

    await QueueSetup.setting_up.set()

    team_id = await get_team_id(call.from_user.id)
    queue_name = call.data.split("_")[-1]

    await state.update_data(queue_name=queue_name)

    queue_array = await get_queue_array(team_id, queue_name)

    # resetting current_turn
    for index, member in enumerate(queue_array):
        if member["current_turn"]:
            queue_array[index]["current_turn"] = False

    await state.update_data(queue_array=queue_array)

    queue_list = await get_queue_list(queue_array)

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(text="Reorder", callback_data="reorder"),
        types.InlineKeyboardButton(text="Done", callback_data="order_ready"),
    ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        f"<b>Here is your {queue_name} queue:</b>\n{queue_list}\nIf you "
        f"would like the {queue_name} queue to have a different order, "
        "choose the <b>Reorder</b> option below.\nOnce you are happy with "
        "the queue order, select <b>Done</b>.",
        reply_markup=keyboard,
    )

    await call.answer()
