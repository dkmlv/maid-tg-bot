import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.deep_linking import get_start_link

from loader import dp, teams, users, queues
from states.all_states import QueueSetup
from utils.get_db_data import get_queue_array, get_team_id, get_queue_list 


@dp.callback_query_handler(text_endswith="_ready", state="*")
async def ask_whose_turn(call: types.CallbackQuery, state: FSMContext):
    """
    Asks the user whose turn it is on the list to do the chore.
    """
    await QueueSetup.marking.set()

    team_id = await get_team_id(call.from_user.id)

    queue_type = call.data.split("_")[0]
    await state.update_data(queue_type=queue_type)

    queue_array = await get_queue_array(team_id, queue_type)
    await state.update_data(queue_array=queue_array)

    keyboard = types.InlineKeyboardMarkup()

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                text=name,
                callback_data=f"turn_{index-1}",
            )
        )

    await call.message.edit_text(
        f"<b>Select the person whose turn it is to do the chore.</b>\n{queue_list}",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="turn_", state=QueueSetup.marking)
async def mark_roommate(call: types.CallbackQuery, state: FSMContext):
    """
    Changes the 'current_turn' status of the selected user to True.
    Asks if there are any other roommates to select
    (e.g. for chores that are done in pairs)
    """
    state_data = await state.get_data()

    queue_type = state_data["queue_type"]
    queue_array = state_data["queue_array"]

    position = int(call.data.split("_")[1])

    queue_array[position]["current_turn"] = True
    await state.update_data(queue_array=queue_array)

    team_id = await get_team_id(call.from_user.id)

    q_data = {f"queues.{queue_type}": queue_array}
    await queues.update_one({"id": team_id}, {"$set": q_data}, upsert=True)

    keyboard = types.InlineKeyboardMarkup()

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        current_turn = member["current_turn"]

        if current_turn:
            queue_list += f"<b><i>{index}. {name}</i></b>\n"
        else:
            queue_list += f"{index}. {name}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                text=name,
                callback_data=f"turn_{index-1}",
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(text="Done", callback_data="assigning_done")
    )

    await call.message.edit_text(
        "Awesome, if this chore is usually done by more than one person at a "
        "time, please select another person whose turn it is to do this chore."
        f"\n{queue_list}\nOnce you are done, press <i><b>Done</b></i>.",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text="assigning_done", state=QueueSetup.marking)
async def reset(call: types.CallbackQuery, state: FSMContext):
    """
    Test.
    """
    await state.finish()
    await call.answer()

