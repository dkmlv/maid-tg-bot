import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, queues
from states.all_states import QueueSetup
from utils.get_db_data import (
    get_queue_array,
    get_team_id,
    get_queue_list,
)

@dp.callback_query_handler(text_startswith="reorder_")
async def ask_to_pick(call: types.CallbackQuery, state: FSMContext):
    """
    First part of reordering the queue.
    Asks the user to pick an item to move on the list.
    """
    await QueueSetup.reordering.set()

    team_id = await get_team_id(call.from_user.id)

    queue_type = call.data.split("_")[-1]
    await state.update_data(q_type=queue_type)

    queue_array = await get_queue_array(team_id, queue_type)
    await state.update_data(queue=queue_array)

    keyboard = types.InlineKeyboardMarkup()

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                text=name,
                callback_data=f"from_{index-1}",
            )
        )

    await call.message.edit_text(
        f"<b>Pick the name that you want to move on the list.</b>\n{queue_list}",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="from_", state=QueueSetup.reordering)
async def ask_to_position(call: types.CallbackQuery, state: FSMContext):
    """
    Second part of reordering the queue.
    Asks the user where they want to move the previously selected item.
    """
    from_position = int(call.data.split("_")[-1])
    await state.update_data(from_position=from_position)

    queue_data = await state.get_data()
    queue_array = queue_data["queue"]

    keyboard = types.InlineKeyboardMarkup()

    queue_list = await get_queue_list(queue_array)

    for index, member in enumerate(queue_array, start=1):
        keyboard.add(
            types.InlineKeyboardButton(
                text=str(index),
                callback_data=f"to_{index-1}",
            )
        )

    await call.message.edit_text(
        "<b>Pick the place that you want to move it to on the "
        f"list.</b>\n{queue_list}",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="to_", state=QueueSetup.reordering)
async def reorder_queue(call: types.CallbackQuery, state: FSMContext):
    """
    Third & final part of reordering the queue.
    Actually reorders the queue (big surprise)
    """
    queue_data = await state.get_data()

    from_position = queue_data["from_position"]
    to_position = int(call.data.split("_")[-1])

    queue_array = queue_data["queue"]
    queue_type = queue_data["q_type"]

    item_to_move = queue_array.pop(from_position)
    queue_array.insert(to_position, item_to_move)

    team_id = await get_team_id(call.from_user.id)

    q_data = {f"queues.{queue_type}": queue_array}
    await queues.update_one({"id": team_id}, {"$set": q_data}, upsert=True)

    queue_list = await get_queue_list(queue_array)

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            text="Reorder", callback_data=f"reorder_{queue_type}"
        ),
        types.InlineKeyboardButton(text="Done", callback_data=f"{queue_type}_ready"),
    ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        f"<b>Here is your {queue_type} queue:</b>\n{queue_list}\nIf you would like "
        f"the {queue_type} queue to have a different order, choose the <i><b>Reorder"
        "</b></i> option below.\nOnce you are happy with the queue order, select "
        "<i><b>Done</b></i>.",
        reply_markup=keyboard,
    )

    await call.answer()

    await state.finish()

