"""
Handling the /setup command here. Shocking.
"""

import logging

from aiogram import types

from .group_stuff import ask_to_add_to_group
from .invite_link import send_invite_link
from ..other_core_modules.get_confirmation import get_confirmation
from loader import dp, queues, teams, users
from utils.sticker_file_ids import CHARISMATIC_STICKER
from utils.get_db_data import get_team_id, get_team_members


@dp.message_handler(commands="setup", state="*")
async def check_user(message: types.Message):
    """
    Checks if the user exists in the database.
    If he/she does, gets a confirmation from the user to go on with the command.
    Otherwise, calls the `setup_team` function.
    """
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    # if user doesnt exist in db, team_id will be None
    team_id = await get_team_id(user_id)

    if team_id:
        await get_confirmation(user_id, team_id)
    else:
        await setup_team(user_id, user_name)
        await send_invite_link(message)
        await ask_to_add_to_group(user_id)


async def setup_team(user_id, user_name):
    """
    Adds the user to the users collection and creates a team for the user.
    """
    team_id = user_id

    user_data = {
        "name": user_name,
        "user_id": user_id,
        "team_id": team_id,
    }

    await users.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

    team_data = {
        "id": team_id,
        "members": {str(user_id): user_name},
    }
    await teams.update_one(
        {"id": team_id},
        {"$set": team_data, "$unset": {"grougroup_chat_id": ""}},
        upsert=True,
    )

    queues_data = {"id": team_id, "queues": {}}
    await queues.update_one({"id": team_id}, {"$set": queues_data}, upsert=True)


@dp.callback_query_handler(text="cancel_erasing")
async def cancel_erasing(call: types.CallbackQuery):
    """
    Informs the user that the bot will not continue with erasing the user.
    """
    await call.message.delete_reply_markup()

    await call.message.answer_sticker(CHARISMATIC_STICKER)
    await call.message.answer(
        "Operation cancelled. You can keep on knocking out those chores with "
        "your roommates."
    )
