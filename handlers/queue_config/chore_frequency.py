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
        types.InlineKeyboardButton(text="Every Day", callback_data="*"),
        types.InlineKeyboardButton(text="Once a Week", callback_data="once"),
    ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        "How often is this chore done?",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(text="once", state=QueueSetup.setting_up)
async def ask_which_day(call: types.CallbackQuery):
    """
    Asks the user what day of the week the chore is done.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=3)

    buttons = []

    for index, day in enumerate(WEEK_DAYS):
        buttons.append(
            types.InlineKeyboardButton(text=day.title(), callback_data=str(index)),
        )

    keyboard.add(*buttons)

    await call.message.edit_text(
        "What day is the chore done?",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(
    text=[0, 1, 2, 3, 4, 5, 6, "*"],
    state=QueueSetup.setting_up,
)
async def ask_time(call: types.CallbackQuery, state: FSMContext):
    """
    Asks the user what time should the question be sent.
    The question is just whether the person whose turn it is to do the chore
    can do the chore that day.
    """
    await call.message.delete_reply_markup()

    chore_frequency = call.data
    await state.update_data(chore_frequency=chore_frequency)

    await QueueSetup.waiting_for_time.set()

    await call.message.edit_text(
        "Okay, what time should I ask a roommate whether they have time "
        "to do the chore when it is their turn?\n\n<b>NOTE:</b> I can only "
        "understand time in the 24-hour format, so please send me the time "
        "like: <code>16:00</code>, <b>NOT</b> <code>4:00 PM</code>."
    )
    await call.answer()
