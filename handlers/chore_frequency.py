import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, queues
from states.all_states import QueueSetup
from utils.get_db_data import get_queue_array, get_team_id, get_queue_list


WEEK_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


@dp.callback_query_handler(text="marking_done", state=QueueSetup.creating_queue)
async def ask_chore_frequency(call: types.CallbackQuery):
    """
    Asks the user how often the chore is done.
    """
    await call.message.delete_reply_markup()

    keyboard = types.InlineKeyboardMarkup()

    buttons = [
        types.InlineKeyboardButton(text="Every Day", callback_data="every_day"),
        types.InlineKeyboardButton(text="Once a Week", callback_data="once"),
    ]
    keyboard.add(*buttons)

    await call.message.answer("How often is this chore done?", reply_markup=keyboard)
    await call.answer()


@dp.callback_query_handler(text="every_day", state=QueueSetup.creating_queue)
async def set_often_freq(call: types.CallbackQuery):
    """
    Adds a job to the APScheduler that will be run every day.
    """
    await call.answer()


@dp.callback_query_handler(text="once", state=QueueSetup.creating_queue)
async def ask_which_day(call: types.CallbackQuery):
    """
    Asks the user what day of the week the chore is done.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)

    buttons = []

    for day in WEEK_DAYS:
        buttons.append(
            types.InlineKeyboardButton(text=day, callback_data=day.lower()),
        )
    # buttons = [
        # types.InlineKeyboardButton(text="Monday", callback_data="monday"),
        # types.InlineKeyboardButton(text="Tuesday", callback_data="tuesday"),
        # types.InlineKeyboardButton(text="Wednesday", callback_data="wednesday"),
        # types.InlineKeyboardButton(text="Thursday", callback_data="thursday"),
        # types.InlineKeyboardButton(text="Friday", callback_data="friday"),
        # types.InlineKeyboardButton(text="Saturday", callback_data="saturday"),
        # types.InlineKeyboardButton(text="Sunday", callback_data="sunday"),
    # ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        "What day is the chore done?",
        reply_markup=keyboard,
    )
    await call.answer()

