"""
This module is sort of the last step in the queue setup process.
Deals with asking the user how often a chore is done and when the
question should be sent.
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp
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
    """Ask the user how often the chore is done."""
    await QueueSetup.setting_freq.set()

    keyboard = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton(text="Every Day", callback_data="*"),
        types.InlineKeyboardButton(text="Every Other Day", callback_data="other"),
        types.InlineKeyboardButton(text="Once a Week", callback_data="once"),
        types.InlineKeyboardButton(text="Custom", callback_data="custom_freq"),
    ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        "How often is this chore done?",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(text="once", state=QueueSetup.setting_freq)
async def ask_which_day(call: types.CallbackQuery):
    """Ask the user what day of the week the chore is done."""
    keyboard = types.InlineKeyboardMarkup(row_width=3)

    buttons = []
    for index, day in enumerate(WEEK_DAYS):
        buttons.append(
            types.InlineKeyboardButton(
                text=day.title(),
                callback_data=str(index),
            ),
        )

    keyboard.add(*buttons)

    await call.message.edit_text(
        "What day is the chore done?",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(text="other", state=QueueSetup.setting_freq)
async def ask_day_combos(call: types.CallbackQuery):
    """Ask user to pick a combination of days for every other day."""
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton(
            text="Mon, Wed, Fri",
            callback_data="0,2,4",
        ),
        types.InlineKeyboardButton(
            text="Tue, Thu, Sat",
            callback_data="1,3,5",
        ),
    ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        "Please choose the option that fits you.",
        reply_markup=keyboard,
    )
    await call.answer()


@dp.callback_query_handler(text="custom_freq", state=QueueSetup.setting_freq)
async def ask_to_type_days(call: types.CallbackQuery):
    """Ask user to type out the names of weekdays."""
    await QueueSetup.waiting_for_custom_freq.set()
    await call.message.edit_text(
        "Please type out the names of weekdays when this chore is done.\n\n"
        "<b>For example:</b> Tuesday, Friday, Sunday"
    )
    await call.answer()


@dp.message_handler(state=QueueSetup.waiting_for_custom_freq)
async def check_days_and_confirm(message: types.Message):
    """Check that user typed days correctly and confirm the days."""
    weekdays = message.text.split(", ")

    callback_data = ""
    for weekday in weekdays:
        try:
            index = WEEK_DAYS.index(weekday.lower())
        except ValueError:
            await message.reply(
                "Are you sure you typed in the right format?\n\n"
                "<b>For example:</b> Tuesday, Friday, Sunday"
            )
            return
        else:
            if weekday == weekdays[-1]:
                callback_data += str(index)
            else:
                callback_data += f"{index},"

    await QueueSetup.setting_freq.set()

    print(callback_data)

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(text="Yes", callback_data=callback_data),
        types.InlineKeyboardButton(text="No", callback_data="custom_freq"),
    ]
    keyboard.add(*buttons)

    await message.answer(
        f"Just to confirm, the chore is done on: {message.text}, right?",
        reply_markup=keyboard,
    )


@dp.callback_query_handler(state=QueueSetup.setting_freq)
async def ask_time(call: types.CallbackQuery, state: FSMContext):
    """Ask the user what time should the question be sent.

    The question is just whether the person whose turn it is to do the
    chore can do the chore that day.
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
