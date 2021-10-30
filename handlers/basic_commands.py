import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.deep_linking import decode_payload, get_start_link

from loader import dp, queues, teams, users
from utils.get_db_data import get_setup_person
from utils.sticker_file_ids import (
    HI_STICKER,
    HERE_STICKER,
    CONFUSED_STICKER,
    QUESTION_STICKER,
)


@dp.message_handler(commands="start", state="*")
async def greet(message: types.Message):
    """
    Greets the user.
    """
    args = message.get_args()

    if args:
        payload = decode_payload(args)

        user_name = message.from_user.full_name
        user_id = message.from_user.id
        team_id = payload

        user_data = {
            "name": user_name,
            "user_id": user_id,
            "team_id": team_id,
        }

        await users.update_one({"user_id": user_id}, {"$set": user_data}, upsert=True)

        team_data = {f"members.{str(user_id)}": user_name}
        await teams.update_one({"id": team_id}, {"$set": team_data}, upsert=True)

        setup_person = await get_setup_person(team_id)

        await message.answer_sticker(HI_STICKER)

        await message.answer(
            "Hello there!\nMy name is <b>Tohru</b> and I will try my best to "
            "make your and your roommates' lives a bit easier.\nSince you have "
            "signed up with a link shared by your roommate, you don't have "
            "to do anything. Your roommate will do all the setup.\n ."
            " I'm looking forward to working with you."
        )

        await message.answer(
            f"P.S. Maybe thank {setup_person}, because they are willing to do "
            "the whole setup and everyone appreciates a sincere 'thank you'"
        )
    else:
        await message.answer_sticker(HI_STICKER)

        await message.answer(
            "Hello there!\nMy name is Tohru and I will try my best to make your "
            "and your roommates' lives a bit easier\nTo get started with the "
            "setup, use the <i>/setup</i> command."
        )


@dp.message_handler(commands="setup", state="*")
async def initial_setup(message: types.Message):
    """
    Adds the user to the users collection and creates a team for the user.
    Generates and sends back an invite link to share with roommates.
    The link is generated using the user's telegram id and will be used to let
    the bot know that this new user is roommates with the user who sent the
    link.
    """
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    team_id = str(user_id)

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

    link = await get_start_link(payload=team_id, encode=True)
    await message.reply(
        f"Here's your <b>invite link</b>:\n{link}\n\n"
        "You should share it with your roommates (<b>IMPORTANT:</b> do not "
        "click on the link yourself).\n"
        "This link will just let me know that people who click on it are "
        "your roommates and you will be able to see them on the list using "
        "the <i>/list</i> command.\n"
        "Once you see that all of your roommates are on the list, you can "
        "proceed with the setup of queues & reminders."
    )


@dp.message_handler(commands="list", state="*")
async def provide_list(message: types.Message):
    """
    Provides the list of roommates that the user has.
    """
    user_id = message.from_user.id
    data = await users.find_one(
        {"user_id": user_id},
        {"team_id": 1, "_id": 0},
    )
    team_id = data["team_id"]

    team_data = await teams.find_one(
        {"id": team_id},
        {"members": 1, "_id": 0},
    )
    members = team_data["members"]

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
    await message.reply("See <code>/help</code> for more information.")
