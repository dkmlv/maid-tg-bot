"""
Only responsibility - generate the invite link and send it back.
"""

import logging

from aiogram import types
from aiogram.utils.deep_linking import get_start_link

from loader import dp
from utils.get_db_data import get_team_id


@dp.message_handler(commands="invite_link")
@dp.throttled(rate=2)
async def send_invite_link(message: types.Message):
    """Generate an invite link to the user's current team and send it."""
    logging.info("providing invite link.")

    user_id = message.from_user.id
    team_id = await get_team_id(user_id)

    if not team_id:
        # user is not a part of any team
        await message.reply(
            "You are not a part of any team yet. To set up a new team for "
            "yourself, use the <b>/setup</b> command. If you'd like to join "
            "someone else's team, simply go through their invite link now."
        )
    else:
        link = await get_start_link(payload=str(team_id), encode=True)
        await message.reply(
            f"Here's your <b>invite link</b>:\n{link}\n\n"
            "You should share it with your roommates.\n"
            "This link will just let me know that people who click on it are "
            "your roommates and you will be able to see them on the list using "
            "the <b>/list</b> command.\n\n"
            "Once you see that all of your roommates are on the list, you can "
            "proceed with the setup of <b>/queues</b>.",
        )
