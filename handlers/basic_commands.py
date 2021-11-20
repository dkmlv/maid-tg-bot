import logging

from aiogram import types
from aiogram.utils.deep_linking import decode_payload

from loader import dp, teams, users
from utils.get_db_data import get_setup_person, get_team_members
from utils.sticker_file_ids import (
    HI_STICKER,
    HERE_STICKER,
    QUESTION_STICKER,
)


@dp.message_handler(commands="start", state="*")
async def greet(message: types.Message):
    """
    Greets the user.
    """
    args = message.get_args()

    await message.answer_sticker(HI_STICKER)

    if args:
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
    members = await get_team_members(message.from_user.id)

    mates_list = ""
    for index, name in enumerate(members.values(), start=1):
        mates_list += f"{index}. {name}\n"

    await message.reply("<b>Here is your list of roommates:</b>\n" + mates_list)

    await message.answer_sticker(HERE_STICKER)


@dp.message_handler(commands="help", state="*")
async def give_help(message: types.Message):
    """
    Provides some instructions on how to use the bot to the user + brief info.
    """
    await message.reply(
        "<b>Instructions:</b>\n" "This is a test message that will be changed later."
    )


@dp.message_handler(state=None)
async def another_help_message(message: types.Message):
    """
    Will ask the user to type help to get more info.
    This function will be called when the user types a random message.
    """
    await message.answer_sticker(QUESTION_STICKER)
    await message.reply("See <b>/help</b> for more information.")

