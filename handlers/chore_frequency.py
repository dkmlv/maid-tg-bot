import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, queues
from states.all_states import QueueSetup


WEEK_DAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


async def ask_chore_frequency(call: types.CallbackQuery):
    """
    Asks the user how often the chore is done.
    """
    keyboard = types.InlineKeyboardMarkup()

    buttons = [
        types.InlineKeyboardButton(text="Every Day", callback_data="every_day"),
        types.InlineKeyboardButton(text="Once a Week", callback_data="once"),
    ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        "How often is this chore done?",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(text="every_day", state=QueueSetup.setting_up)
async def set_often_freq(call: types.CallbackQuery, state: FSMContext):
    """
    Adds a job to the APScheduler that will be run every day.
    """
    await call.message.delete_reply_markup()
    await call.answer()
    await state.finish()


@dp.callback_query_handler(text="once", state=QueueSetup.setting_up)
async def ask_which_day(call: types.CallbackQuery):
    """
    Asks the user what day of the week the chore is done.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)

    buttons = []

    for day in WEEK_DAYS:
        buttons.append(
            types.InlineKeyboardButton(text=day.title(), callback_data=day),
        )

    keyboard.add(*buttons)

    await call.message.edit_text(
        "What day is the chore done?",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(text=WEEK_DAYS, state=QueueSetup.setting_up)
async def set_once_freq(call: types.CallbackQuery, state: FSMContext):
    """
    Adds a job to the APScheduler that will be run once every week.
    """
    await call.message.delete_reply_markup()
    await call.answer()
    await state.finish()
