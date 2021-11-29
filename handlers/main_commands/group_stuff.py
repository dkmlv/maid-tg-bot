"""
Deals with Telegram group related stuff:
    1. Ask to add bot to group
    2. Detect when bot is added/removed to/from group
"""

import logging

from aiogram import types
from aiogram.utils.deep_linking import get_startgroup_link

from loader import dp, teams
from utils.get_db_data import get_team_id


async def ask_to_add_to_group(user_id):
    """Ask the user to add the bot to the roommates group chat.

    Later on, the bot will resolve conflicts in the group chat by
    asking if any user can substitute the one who can't do the chore.

    Parameters
    ----------
    user_id : int
        Telegram user id to which the bot should send the message
    """

    link = await get_startgroup_link(payload="_", encode=True)

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text="Add to Group", url=link))

    await dp.bot.send_message(
        user_id,
        "Also I'd like to kindly ask you to add me to your roommates' group "
        "here on Telegram. If you don't already have one, please create it "
        "and add me there. Otherwise, whenever there is a problem with the "
        "queue, I won't be able to help you.",
        reply_markup=keyboard,
    )


@dp.my_chat_member_handler(chat_type=("group", "supergroup"))
async def group_chat(my_chat_member: types.ChatMemberUpdated):
    """Detect when added/removed to/from Telegram group chat.

    When bot is added to group chat, insert the chat id to db.
    When bot is removed from group chat, ask the person why they did it.
    """

    bot_added = my_chat_member.new_chat_member.is_chat_member()

    user_id = my_chat_member.from_user.id
    user_name = my_chat_member.from_user.first_name
    team_id = await get_team_id(user_id)

    if bot_added:
        logging.info("Bot added to group")

        group_id = my_chat_member.chat.id
        group_data = {"group_chat_id": group_id}
        await teams.update_one({"id": team_id}, {"$set": group_data}, upsert=True)
    else:
        logging.info("Bot removed from group")

        await teams.update_one(
            {"id": team_id},
            {"$unset": {"group_chat_id": ""}},
            upsert=True,
        )
        await dp.bot.send_message(
            user_id,
            f"Why did you do this to me, {user_name}?\nWhy did you remove me "
            "from the group?",
        )
