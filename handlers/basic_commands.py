import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.deep_linking import decode_payload, get_start_link

from loader import dp, teams, users


@dp.message_handler(commands="start")
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

        team_data = {f"members.{user_name}": user_id}
        await teams.update_one({"id": team_id}, {"$set": team_data}, upsert=True)

        await message.answer(
            "Hello there!\nMy name is Tohru and I will try my best to make your "
            "life and your roommates' lives a bit easier.\nSince you have "
            "signed up with a link shared by your roommate, you don't have "
            "to do anything (or maybe thank them because they are willing to "
            "do the whole setup and everyone appreciates a sincere 'thank you')."
            " Your roommate will do all the setup. I'm looking forward to "
            "working with you."
        )
    else:
        await message.reply(
            "Hello there!\nMy name is Tohru and I will try my best to make your "
            "and your roommates' lives a bit easier\nTo get started with the "
            "setup, use the <i>/setup</i> command."
        )


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

