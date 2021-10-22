import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from loader import dp


@dp.message_handler(commands="start")
async def ask_location(message: types.Message):
    """
    Greets the user.
    """
    await message.reply(
        "Hello there!\n\nMy name is Tohru and I will try my best to make your "
        "life a bit easier."
    )


@dp.message_handler(commands="help", state="*")
async def give_help(message: types.Message):
    """
    Provides some instructions on how to use the bot to the user + brief info.
    """
    await message.reply(
        "<b>Instructions:</b>\n"
        "This is a test message that will be changed later."
    )


@dp.message_handler(state=None)
async def another_help_message(message: types.Message):
    """
    Will ask the user to type help to get more info.
    This function will be called when the user types a random message.
    """
    await message.reply("See <code>/help</code> for more information.")

