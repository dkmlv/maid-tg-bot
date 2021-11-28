"""
Getting confirmation from the user to go on with erasing them.

This is needed either when:
    1) User uses /setup commmand while already being a part of a team.
    2) User wants so sign up with an invite link while already in a team.
"""

import logging

from aiogram import types

from loader import dp
from utils.get_db_data import get_team_members


async def get_confirmation(user_id: int, team_id: int):
    """
    Gets confirmation that the user wants to erase themselves from their present
    roommates' team.
    """
    num_of_members = len(await get_team_members(user_id))

    if user_id == team_id and num_of_members != 1:
        # deleting the admin is a bit of a different operation
        # since almost everything relies on admin's user id
        callback_data = "ask_who_to_make_admin"
    else:
        callback_data = f"erase_{user_id}"

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(text="Yes", callback_data=callback_data),
        types.InlineKeyboardButton(text="No", callback_data="cancel_erasing"),
    ]
    keyboard.add(*buttons)

    await dp.bot.send_message(
        user_id,
        "Looks like you are already a part of a roommates team. Are you "
        "sure you want to continue?\n(continuing will result in you "
        "getting erased from your present roommates' team)",
        reply_markup=keyboard,
    )
