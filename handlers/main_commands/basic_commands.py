"""
Handlers for some basic commands including: /start, /list, /help.
Plus handlers for when user types in 'thank you' or a random message.
"""

import logging

from aiogram import types
from aiogram.utils.deep_linking import decode_payload

from loader import dp, teams, users
from utils.get_db_data import get_setup_person, get_team_members, get_team_id
from utils.sticker_file_ids import (
    HI_STICKER,
    HERE_STICKER,
    HUMBLE_STICKER,
    QUESTION_STICKER,
)


@dp.message_handler(commands="start", state="*")
async def greet(message: types.Message):
    """
    Greets the user.
    """
    args = message.get_args()

    await message.answer_sticker(HI_STICKER)

    if args and message.chat.type == "private":
        payload = decode_payload(args)

        user_name = message.from_user.full_name
        user_id = message.from_user.id
        team_id = int(payload)

        user_data = {
            "name": user_name,
            "user_id": user_id,
            "team_id": team_id,
        }

        await users.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

        team_data = {f"members.{str(user_id)}": user_name}
        await teams.update_one({"id": team_id}, {"$set": team_data}, upsert=True)

        setup_person = await get_setup_person(team_id)
        # notify the setup person that someone signed up with invite link
        await dp.bot.send_message(
            team_id, f"{user_name} just signed up with your invite link."
        )

        await message.answer(
            "Hello there!\n\nMy name is <b>Tohru</b> and I will try my best to "
            "make your and your roommates' lives a bit easier.\nSince you have "
            "signed up with a link shared by your roommate, you don't have "
            "to do anything. Your roommate will do all the setup.\n\n"
            "I'm looking forward to working with you."
        )

        await message.answer(
            f"P.S. Maybe thank {setup_person}, because they are willing to do "
            "the whole setup and everyone appreciates a sincere 'thank you'."
        )
    elif message.chat.type in ("group", "supergroup"):
        await message.answer(
            "Hi everyone!\n\nMy name is Tohru and I will try me best to make "
            "your lives a bit easier.\nWhenever there is a problem with a queue"
            ", I will let you know here so that we can figure out a solution "
            "together.\n\nI'm very excited about working with you all.",
        )
    else:
        await message.answer(
            "Hello there!\nMy name is Tohru and I will try my best to make your "
            "and your roommates' lives a bit easier.\nTo get started with the "
            "setup, use the <b>/setup</b> command."
        )


@dp.message_handler(commands="list", state="*")
async def provide_list(message: types.Message):
    """
    Provides the list of roommates that the user has.
    """
    user_id = message.from_user.id
    team_id = await get_team_id(user_id)
    members = await get_team_members(user_id)

    if user_id == team_id:
        # user issuing the command is admin (the setup person)
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                text="Remove User",
                callback_data="ask_which_user",
            )
        )
    else:
        keyboard = None

    mates_list = ""
    for index, name in enumerate(members.values(), start=1):
        mates_list += f"{index}. {name}\n"

    await message.reply(
        "<b>Here is your list of roommates:</b>\n" + mates_list,
        reply_markup=keyboard,
    )

    await message.answer_sticker(HERE_STICKER)


@dp.message_handler(commands="help", state="*")
async def give_help(message: types.Message):
    """
    Provides some instructions on how to use the bot to the user + brief info.
    """
    await message.reply(
        "<b>Instructions:</b>\n" "This is a test message that will be changed later."
    )


@dp.message_handler(regexp="(thank you|ty)", state=None)
async def react_to_thanks(message: types.Message):
    """
    This function will be called when the user types a random message.
    """
    user_name = message.from_user.first_name

    await message.answer_sticker(HUMBLE_STICKER)
    await message.reply(f"No need, I'm just doing my job, {user_name}-san.")


@dp.message_handler(state=None)
async def another_help_message(message: types.Message):
    """
    This function will be called when the user types a random message.
    """
    await message.answer_sticker(QUESTION_STICKER)
    await message.reply("See <b>/help</b> for more information.")
