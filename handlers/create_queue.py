import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, users, queues
from states.all_states import QueueSetup
from utils.sticker_file_ids import NOPE_STICKER
from utils.get_db_data import (
    get_queue_array,
    get_setup_person,
    get_team_id,
    get_team_members,
    get_queue_list,
)


async def create_queue(team_id, queue_type):
    """
    Creates a new queue array in mongodb and returns it.
    team_id -> used to obtain the queues object for the particular group of
    roommates.
    queue_type -> basically the name of the queue
    """
    members = await get_team_members(team_id)

    queue_array = []
    for user_id, name in members.items():
        entry = {
            "user_id": user_id,
            "name": name,
            "current_turn": False,
        }
        queue_array.append(entry)

    data = {f"queues.{queue_type}": queue_array}
    await queues.update_one({"id": team_id}, {"$set": data}, upsert=True)

    return queue_array


@dp.callback_query_handler(text="create")
async def ask_queue_type(call: types.CallbackQuery):
    """
    Asks the user to pick a queue type (which is essentially a queue name).
    """
    user_id = call.from_user.id
    team_id = await get_team_id(user_id)

    if str(user_id) != team_id:
        setup_person = await get_setup_person(team_id)

        await call.message.answer_sticker(NOPE_STICKER)

        await call.message.answer(
            "Sorry, you do not have permission to create queues.\nAs part of a "
            "security measure, only the person who did the initial setup has "
            "permission to modify/create queues.\nIn your list of roommates, "
            f"that person is {setup_person}."
        )
    else:
        keyboard = types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            types.InlineKeyboardButton(text="Cooking", callback_data="create_cooking"),
            types.InlineKeyboardButton(
                text="Cleaning", callback_data="create_cleaning"
            ),
            types.InlineKeyboardButton(
                text="Shopping", callback_data="create_shopping"
            ),
            types.InlineKeyboardButton(text="Bread", callback_data="create_bread"),
            types.InlineKeyboardButton(text="Garbage", callback_data="create_garbage"),
            types.InlineKeyboardButton(text="Custom", callback_data="custom"),
        ]

        keyboard.add(*buttons)

        await call.message.edit_text(
            "Awesome, you can choose to make a queue for one of the following or "
            "create a custom queue by picking one of the options below.",
            reply_markup=keyboard,
        )

    await call.answer()


@dp.callback_query_handler(text="custom")
async def create_custom_q(call: types.CallbackQuery):
    """
    Allows the user to create a custom queue.
    Asks the user to provide a name for the custom queue.
    """
    await call.message.delete_reply_markup()

    await call.message.edit_text("What should the queue be called?")

    await QueueSetup.waiting_for_queue_name.set()

    await call.answer()


@dp.message_handler(state=QueueSetup.waiting_for_queue_name)
async def name_custom_q(message: types.Message, state: FSMContext):
    """
    Names the custom queue and proceeds with the rest of the queue creation.
    """
    if not message.text.isalpha():
        await message.answer(
            "Queue name can only contain characters of the alphabet (no spaces "
            "or other special symbols)"
        )
    else:
        team_id = await get_team_id(message.from_user.id)
        queue_type = message.text

        queue_array = await create_queue(team_id, queue_type)
        queue_list = await get_queue_list(queue_array)

        keyboard = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton(
                text="Reorder", callback_data=f"reorder_{queue_type}"
            ),
            types.InlineKeyboardButton(
                text="Done", callback_data="f{queue_type}_ready"
            ),
        ]
        keyboard.add(*buttons)

        await message.answer(
            f"<b>Here is your {queue_type} queue:</b>\n{queue_list}\nIf you would like "
            f"the {queue_type} queue to have a different order, choose the <i><b>Reorder"
            "</b></i> option below.\nOnce you are happy with the queue order, select "
            "<i><b>Done</b></i>.",
            reply_markup=keyboard,
        )

        await state.finish()


@dp.callback_query_handler(text_startswith="create_")
async def create_specific_q(call: types.CallbackQuery):
    """
    Creates a new queue. Provides the list of roommates ro reorder.
    """
    user_id = call.from_user.id
    team_id = await get_team_id(user_id)
    queue_type = call.data.split("_")[-1]

    queue_array = await create_queue(team_id, queue_type)
    queue_list = await get_queue_list(queue_array)

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            text="Reorder", callback_data=f"reorder_{queue_type}"
        ),
        types.InlineKeyboardButton(text="Done", callback_data=f"{queue_type}_ready"),
    ]
    keyboard.add(*buttons)

    await call.message.edit_text(
        f"<b>Here is your {queue_type} queue:</b>\n{queue_list}\nIf you would like "
        f"the {queue_type} queue to have a different order, choose the <i><b>Reorder"
        "</b></i> option below.\nOnce you are happy with the queue order, select "
        "<i><b>Done</b></i>.",
        reply_markup=keyboard,
    )

    await call.answer()

