"""
Handler for the /queues command and some of the options in the Inline
Keyboard: show, delete, modify.
"""

import logging

from aiogram import types

from loader import dp, queues
from utils.get_db_data import (
    get_team_id,
    get_setup_person,
)
from utils.sticker_file_ids import NOPE_STICKER


async def get_admin_keyboard():
    """
    Returns an inline keyboard for the admin issuing /queues command.
    Admin keyboard is different from user keyboard since it has more
    options (modify, delete, create)
    """
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
            text="Delete Queue",
            callback_data="delete",
        ),
        types.InlineKeyboardButton(
            text="Create New Queue",
            callback_data="create",
        ),
    ]
    keyboard.add(*buttons)

    return keyboard


async def get_user_keyboard():
    """
    Returns an inline keyboard for any user (not admin) issuing /queues command.
    """
    keyboard = types.InlineKeyboardMarkup()

    keyboard.add(
        types.InlineKeyboardButton(
            text="Show Queue",
            callback_data="show",
        )
    )

    return keyboard


@dp.message_handler(commands="queues", state="*")
@dp.callback_query_handler(text="back")
@dp.throttled(rate=2)
async def show_queues(entity):
    """
    Shows all the chore queues the user has along with some options on what can
    be done with them. Accepts 'entity', which can either be a CallbackQuery or a Message.
    It is a CallbackQuery when user clicks the Back button in the queues
    dialogue and is a Message when the 'queues' command is issued.
    """
    team_id = await get_team_id(entity.from_user.id)

    if not team_id:
        # user is not a part of any team
        await entity.reply(
            "You are not a part of any team yet. To set up a new team for "
            "yourself, use the <b>/setup</b> command. If you'd like to join "
            "someone else's team, simply go through their invite link now."
        )
        return

    queues_data = await queues.find_one(
        {"id": team_id},
        {"queues": 1, "_id": 0},
    )
    queues_data = queues_data["queues"]

    if queues_data and entity.from_user.id == team_id:
        queue_names = queues_data.keys()

        queues_list = ""
        for queue in queue_names:
            queues_list += f"- <i>{queue}</i>\n"

        keyboard = await get_admin_keyboard()

        text = (
            f"<b>Here are all the queues you have set up:</b>\n{queues_list}\n"
            "If you'd like me to show a certain queue, please press "
            "<b>Show Queue</b> button below.\nTo modify a queue, please "
            "select the <b>Modify Queue</b> option below.\n"
            "To delete a queue, press <b>Delete Queue</b>.\n"
            "To set up a new queue, press <b>Create New Queue</b>."
        )
    elif queues_data:
        # every user other than the admin is using /queues command
        # at least one queue is set up
        queue_names = queues_data.keys()

        queues_list = ""
        for queue in queue_names:
            queues_list += f"- <i>{queue}</i>\n"

        keyboard = await get_user_keyboard()

        text = (
            f"<b>Here are all the queues you have set up:</b>\n{queues_list}\n"
            "If you'd like me to show a certain queue, please press "
            "<b>Show Queue</b> button below."
        )
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text="Create New Queue", callback_data="create")
        )

        text = (
            "Looks like you have no queues set up right now.\n"
            "Don't worry though, you can easily set them up by pressing the "
            "<b>Create New Queue</b> button below."
        )

    if type(entity) == types.CallbackQuery:
        await entity.message.edit_text(text, reply_markup=keyboard)
        await entity.answer()
    else:
        await entity.reply(text, reply_markup=keyboard)


@dp.callback_query_handler(text=["show", "modify", "delete"])
async def ask_which_q(call: types.CallbackQuery):
    """
    Asks the user which queue they'd like to see/modify.
    """
    user_id = call.from_user.id
    team_id = await get_team_id(user_id)
    operation = call.data

    if (operation == "modify" or operation == "delete") and user_id != team_id:
        setup_person = await get_setup_person(team_id)

        await call.message.answer_sticker(NOPE_STICKER)

        await call.message.answer(
            f"Sorry, you do not have permission to {operation} queues.\nAs "
            "part of a security measure, only the person who did the initial "
            "setup has permission to modify/create/delete queues.\nIn your "
            f"list of roommates, that person is {setup_person}."
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
        keyboard.add(types.InlineKeyboardButton(text="Back", callback_data="back"))

        await call.message.edit_text(
            f"<b>Please select the queue you'd like me to {operation}.</b>"
            f"\n{queues_list}\n",
            reply_markup=keyboard,
        )

    await call.answer()
