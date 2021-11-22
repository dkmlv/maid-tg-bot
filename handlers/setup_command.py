import logging

from aiogram import types
from aiogram.utils.deep_linking import get_start_link

from handlers.send_invite_link import send_invite_link
from loader import dp, queues, teams, users
from utils.sticker_file_ids import CHARISMATIC_STICKER


@dp.message_handler(commands="setup", state="*")
async def check_user(message: types.Message):
    """
    Checks if the user exists in the database.
    If he/she does, gets a confirmation from the user to go on with the command.
    Otherwise, calls the `setup_team` function.
    """
    user_id = message.from_user.id
    user_name = message.from_user.full_name

    data = await users.find_one({"user_id": user_id})

    if data:
        keyboard = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton(
                text="Yes", callback_data=f"erase_{user_id}_{user_name}"
            ),
            types.InlineKeyboardButton(text="No", callback_data="cancel_setup"),
        ]
        keyboard.add(*buttons)

        await message.answer(
            "Looks like you are already a part of a roommates team. Are you "
            "sure you want to continue with the <b>/setup</b> command?\n"
            "(continuing will result in you getting erased from your "
            "existing roommates)",
            reply_markup=keyboard,
        )
    else:
        user_name = message.from_user.full_name
        await setup_team(user_id, user_name)
        await send_invite_link(message)


async def setup_team(user_id, user_name):
    """
    Adds the user to the users collection and creates a team for the user.
    Generates and sends back an invite link to share with roommates.
    The link is generated using the user's telegram id and will be used to let
    the bot know that this new user is roommates with the user who sent the
    link.
    """
    team_id = user_id

    user_data = {
        "name": user_name,
        "user_id": user_id,
        "team_id": team_id,
    }

    await users.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

    team_data = {"id": team_id, "members": {str(user_id): user_name}}
    await teams.update_one({"id": team_id}, {"$set": team_data}, upsert=True)

    queues_data = {"id": team_id, "queues": {}}
    await queues.update_one({"id": team_id}, {"$set": queues_data}, upsert=True)


@dp.callback_query_handler(text="cancel_setup")
async def cancel_setup(call: types.CallbackQuery):
    """
    Informs the user that the bot will not continue with the /setup command.
    """
    await call.message.delete_reply_markup()

    await call.message.answer_sticker(CHARISMATIC_STICKER)
    await call.message.answer(
        "Operation cancelled. You can keep on knocking out those chores with "
        "your roommates."
    )
