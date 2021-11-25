"""
Only responsibility - generate the invite link and send it back.
"""

import logging

from aiogram import types
from aiogram.utils.deep_linking import get_start_link

from loader import dp
from utils.get_db_data import get_team_id


@dp.message_handler(commands="invite_link")
async def send_invite_link(message: types.Message):
    """
    Generates an invite link to the user's current team and sends it back.
    """
    user_id = message.from_user.id
    team_id = await get_team_id(user_id)

    link = await get_start_link(payload=str(team_id), encode=True)
    await dp.bot.send_message(
        user_id,
        f"Here's your <b>invite link</b>:\n{link}\n\n"
        "You should share it with your roommates.\n"
        "This link will just let me know that people who click on it are "
        "your roommates and you will be able to see them on the list using "
        "the <b>/list</b> command.\n\n"
        "Once you see that all of your roommates are on the list, you can "
        "proceed with the setup of queues.",
    )
