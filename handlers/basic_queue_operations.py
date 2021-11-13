import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, users, queues
from states.all_states import QueueSetup
from utils.get_db_data import (
    get_queue_array,
    get_queue_list,
    get_team_id,
    get_setup_person,
)
from utils.sticker_file_ids import NOPE_STICKER


@dp.message_handler(commands="queues", state="*")
async def show_queues(message: types.Message):
    """
    Shows all the chore queues the user has along with some options on what can
    be done with them.
    """
    team_id = await get_team_id(message.from_user.id)

    queues_data = await queues.find_one(
        {"id": team_id},
        {"queues": 1, "_id": 0},
    )
    queues_data = queues_data["queues"]

    if queues_data:
        queue_names = queues_data.keys()

        queues_list = ""
        for queue in queue_names:
            queues_list += f"- <i>{queue}</i>\n"

        keyboard = types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            types.InlineKeyboardButton(
                text="Show Queue",
                callback_data="show",
            ),
            types.InlineKeyboardButton(
                text="Modify Queue",
                callback_data="modify",
            ),
            types.InlineKeyboardButton(
                text="Create New Queue",
                callback_data="create",
            ),
        ]
        keyboard.add(*buttons)

        await message.reply(
            f"<b>Here are all the queues you have set up:</b>\n{queues_list}\n"
            "If you'd like me to show a certain queue, please press "
            "<b>Show Queue</b> button below.\nTo modify a queue, please "
            "select the <b>Modify Queue</b> option below.\n"
            "To set up a new queue, press <b>Create New Queue</b>.",
            reply_markup=keyboard,
        )
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text="Create New Queue", callback_data="create")
        )

        await message.reply(
            "Looks like you have no queues set up right now.\n"
            "Don't worry though, you can easily set them up by pressing the "
            "<b>Create New Queue</b> button below.",
            reply_markup=keyboard,
        )


@dp.callback_query_handler(text=["show", "modify"])
async def ask_which_q(call: types.CallbackQuery):
    """
    Asks the user which queue they'd like to see/modify.
    """
    user_id = call.from_user.id
    team_id = await get_team_id(user_id)
    operation = call.data

    if operation == "modify" and str(user_id) != team_id:
        setup_person = await get_setup_person(team_id)

        await call.message.answer_sticker(NOPE_STICKER)

        await call.message.answer(
            "Sorry, you do not have permission to modify queues.\nAs part of a "
            "security measure, only the person who did the initial setup has "
            "permission to modify/create queues.\nIn your list of roommates, "
            f"that person is {setup_person}."
        )
    else:
        queues_data = await queues.find_one(
            {"id": team_id},
            {"queues": 1, "_id": 0},
        )

        queue_names = queues_data["queues"].keys()

        buttons = []
        queues_list = ""
        for queue in queue_names:
            queues_list += f"- <i>{queue.capitalize()}</i>\n"
            buttons.append(
                types.InlineKeyboardButton(
                    text=queue.capitalize(), callback_data=f"{operation}_{queue}"
                )
            )

        keyboard = types.InlineKeyboardMarkup(row_width=2)

        keyboard.add(*buttons)

        await call.message.edit_text(
            f"<b>Please select the queue you'd like me to {operation}.</b>"
            f"\n{queues_list}\n",
            reply_markup=keyboard,
        )

    await call.answer()


@dp.callback_query_handler(text_startswith="show_")
async def show_a_queue(call: types.CallbackQuery):
    """
    Shows the queue a user has selected to him/her.
    """
    team_id = await get_team_id(call.from_user.id)
    queue_type = call.data.split("_")[-1]

    queue_array = await get_queue_array(team_id, queue_type)

    queue_list = await get_queue_list(queue_array)

    await call.message.answer(f"Here is your <b>{queue_type}</b> queue:\n{queue_list}")


@dp.callback_query_handler(text_startswith="modify_")
async def modify_a_queue(call: types.CallbackQuery):
    """
    Provides some options to modify the queue (delete, reorder, reassign turn)
    """
    pass

