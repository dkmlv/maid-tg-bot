import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from typing import Tuple

from handlers.chore_frequency import ask_chore_frequency
from loader import dp, queues
from states.all_states import QueueSetup
from utils.get_db_data import get_queue_array, get_team_id, get_queue_list


@dp.callback_query_handler(text="order_ready", state=QueueSetup.setting_up)
async def ask_whose_turn(call: types.CallbackQuery, state: FSMContext):
    """
    Asks the user whose turn it is on the list to do the chore.
    """
    state_data = await state.get_data()

    queue_array = state_data["queue_array"]

    keyboard = types.InlineKeyboardMarkup()

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                text=name,
                callback_data=f"mark_{index-1}",
            )
        )

    await call.message.edit_text(
        f"<b>Select the person whose turn it is to do the chore.</b>\n{queue_list}",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="mark_", state=QueueSetup.setting_up)
async def mark_roommate(call: types.CallbackQuery, state: FSMContext):
    """
    Changes the 'current_turn' status of the selected user to True.
    Additionally asks chore frequency.
    """
    state_data = await state.get_data()

    queue_name = state_data["queue_name"]
    queue_array = state_data["queue_array"]

    position = int(call.data.split("_")[1])

    queue_array[position]["current_turn"] = True
    await state.update_data(queue_array=queue_array)

    team_id = await get_team_id(call.from_user.id)

    queue_data = {f"queues.{queue_name}": queue_array}
    await queues.update_one({"id": team_id}, {"$set": queue_data}, upsert=True)

    await ask_chore_frequency(call)


async def mark_next_person(queue_array: list) -> Tuple[list, int]:
    """
    Marks next person in the queue (transfers current_turn to the them).
    Returns the modified queue_array with the id of the person marked.
    """
    for index, member in enumerate(queue_array):
        if member["current_turn"]:
            queue_array[index]["current_turn"] = False

            # shouldnt fail when next person is at the beginning of the queue
            next_person_pos = (index + 1) % len(queue_array)
            queue_array[next_person_pos]["current_turn"] = True

            return (queue_array, queue_array[next_person_pos]["user_id"])

    logging.error("Failed to find next person in the queue")
    return ([], 0)
