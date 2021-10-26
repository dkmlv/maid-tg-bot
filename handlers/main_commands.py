import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.deep_linking import decode_payload, get_start_link

from loader import dp, teams, users, queues
from states.all_states import QueueSetup
from utils.get_db_data import get_queue_array, get_team_id, get_team_members


@dp.message_handler(commands="setup")
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


@dp.message_handler(commands="list")
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


@dp.message_handler(commands="queues")
async def show_queues(message: types.Message):
    """
    Shows all the chore queues the user has.
    """
    user_id = message.from_user.id
    team_id = await get_team_id(user_id)

    queues_data = await queues.find_one(
        {"id": team_id},
        {"queues": 1, "_id": 0},
    )

    if queues_data:
        await message.reply("This wasn't supposed to run.")
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(
                text="Create New Queue", callback_data="create_queue"
            )
        )

        await message.reply(
            "Looks like you have no queues set up right now.\n"
            "Don't worry though, you can easily set them up by pressing the "
            "<b>Create New Queue</b> button below.",
            reply_markup=keyboard,
        )


@dp.callback_query_handler(text="create_queue")
async def create_queue(call: types.CallbackQuery):
    """
    Allows the user to create a queue.
    Offers some suggestions for queues and the ability to create a custom
    queue.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton(text="Cooking", callback_data="create_cooking_q"),
        types.InlineKeyboardButton(text="Cleaning", callback_data="create_cleaning_q"),
        types.InlineKeyboardButton(text="Shopping", callback_data="create_shopping_q"),
        types.InlineKeyboardButton(text="Bread", callback_data="create_bread_q"),
        types.InlineKeyboardButton(text="Garbage", callback_data="creat_garbage_q"),
        types.InlineKeyboardButton(text="Custom", callback_data="custom_q"),
    ]

    keyboard.add(*buttons)

    await call.message.edit_text(
        "Awesome, you can choose to make a queue for one of the following or "
        "create a custom queue by picking one of the options below.",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="create_")
async def create_specific_q(call: types.CallbackQuery):
    """
    Creates a new queue. Provides the list of roommates ro reorder.
    """
    user_id = call.from_user.id
    team_id = await get_team_id(user_id)

    members = await get_team_members(team_id)

    queue_data = []
    for user_id, name in members.items():
        entry = {
            "user_id": user_id,
            "name": name,
            "current_turn": False,
        }
        queue_data.append(entry)

    queue_type = call.data.split("_")[1]
    q_data = {f"queues.{queue_type}": queue_data}
    await queues.update_one({"id": team_id}, {"$set": q_data}, upsert=True)

    queue_list = ""
    for index, name in enumerate(members.values(), start=1):
        queue_list += f"{index}. {name}\n"

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            text="Reorder", callback_data=f"reorder_{queue_type}"
        ),
        types.InlineKeyboardButton(text="Done", callback_data="f{queue_type}_ready"),
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


@dp.callback_query_handler(text_startswith="reorder_")
async def ask_to_pick(call: types.CallbackQuery, state: FSMContext):
    """
    First part of reordering the queue.
    Asks the user to pick an item to move on the list.
    """
    await QueueSetup.reordering.set()

    team_id = await get_team_id(call.from_user.id)

    queue_type = call.data.split("_")[-1]
    await state.update_data(q_type=queue_type)

    queue_array = await get_queue_array(team_id, queue_type)
    await state.update_data(queue=queue_array)

    keyboard = types.InlineKeyboardMarkup()

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                text=name,
                callback_data=f"from_{index-1}",
            )
        )

    await call.message.edit_text(
        f"<b>Pick the name that you want to move on the list.</b>\n{queue_list}",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="from_", state=QueueSetup.reordering)
async def ask_to_position(call: types.CallbackQuery, state: FSMContext):
    """
    Second part of reordering the queue.
    Asks the user where they want to move the previously selected item.
    """
    from_position = int(call.data.split("_")[-1])
    await state.update_data(from_position=from_position)

    queue_data = await state.get_data()
    queue_array = queue_data["queue"]

    keyboard = types.InlineKeyboardMarkup()

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                text=str(index),
                callback_data=f"to_{index-1}",
            )
        )

    await call.message.edit_text(
        "<b>Pick the place that you want to move it to on the "
        f"list.</b>\n{queue_list}",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="to_", state=QueueSetup.reordering)
async def reorder_queue(call: types.CallbackQuery, state: FSMContext):
    """
    Third & final part of reordering the queue.
    Actually reorders the queue (big surprise)
    """
    queue_data = await state.get_data()

    from_position = queue_data["from_position"]
    to_position = int(call.data.split("_")[-1])

    queue_array = queue_data["queue"]
    queue_type = queue_data["q_type"]

    item_to_move = queue_array.pop(from_position)
    queue_array.insert(to_position, item_to_move)

    team_id = await get_team_id(call.from_user.id)

    q_data = {f"queues.{queue_type}": queue_array}
    await queues.update_one({"id": team_id}, {"$set": q_data}, upsert=True)

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(
            text="Reorder", callback_data=f"reorder_{queue_type}"
        ),
        types.InlineKeyboardButton(text="Done", callback_data="f{queue_type}_ready"),
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

    await state.finish()


@dp.callback_query_handler(text="custom_q")
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
    await state.finish()
    pass
