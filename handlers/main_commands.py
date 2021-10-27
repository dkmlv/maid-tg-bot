import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.deep_linking import get_start_link

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
    Shows all the chore queues the user has along with some options on what can
    be done with them.
    """
    user_id = message.from_user.id
    team_id = await get_team_id(user_id)

    queues_data = await queues.find_one(
        {"id": team_id},
        {"queues": 1, "_id": 0},
    )
    queues_data = queues_data["queues"]

    if queues_data:
        queue_names = queues_data.keys()

        queues_list = ""
        for queue in queue_names:
            queues_list += f"- <i>{queue.capitalize()}</i>\n"

        keyboard = types.InlineKeyboardMarkup(row_width=2)

        buttons = [
            types.InlineKeyboardButton(
                text="Show Queue",
                callback_data="show",
            ),
            types.InlineKeyboardButton(
                text="Modify Queue",
                callback_data="modify",
            ),
            types.InlineKeyboardButton(
                text="Create New Queue",
                callback_data="create",
            ),
        ]
        keyboard.add(*buttons)

        await message.reply(
            f"<b>Here are all the queues you have set up:</b>\n{queues_list}\n"
            "If you'd like me to show a certain queue, please press "
            "<b>Show Queue</b> button below.\nTo modify a queue, please "
            "select the <b>Modify Queue</b> option below.\n"
            "To set up a new queue, press <b>Create New Queue</b>.",
            reply_markup=keyboard,
        )
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton(text="Create New Queue", callback_data="create")
        )

        await message.reply(
            "Looks like you have no queues set up right now.\n"
            "Don't worry though, you can easily set them up by pressing the "
            "<b>Create New Queue</b> button below.",
            reply_markup=keyboard,
        )


@dp.callback_query_handler(text=["show", "modify"])
async def ask_which_q(call: types.CallbackQuery):
    """
    Asks the user which queue they'd like to see/modify.
    """
    user_id = call.from_user.id
    team_id = await get_team_id(user_id)
    operation = call.data

    if operation == "modify" and str(user_id) != team_id:
        setup_person = await users.find_one(
            {"user_id": int(team_id)},
            {"name": 1, "_id": 0},
        )
        setup_person = setup_person["name"]

        await call.message.answer(
            "Sorry, you do not have permission to modify queues.\nAs part of a "
            "security measure, only the person who did the initial setup has "
            "permission to modify/create queues.\nIn your list of roommates, "
            f"that person is {setup_person}."
        )
    else:
        queues_data = await queues.find_one(
            {"id": team_id},
            {"queues": 1, "_id": 0},
        )

        queue_names = queues_data["queues"].keys()

        buttons = []
        queues_list = ""
        for queue in queue_names:
            queues_list += f"- <i>{queue.capitalize()}</i>\n"
            buttons.append(
                types.InlineKeyboardButton(
                    text=queue.capitalize(), callback_data=f"{operation}_{queue}"
                )
            )

        keyboard = types.InlineKeyboardMarkup(row_width=2)

        keyboard.add(*buttons)

        await call.message.edit_text(
            f"<b>Please select the queue you'd like me to {operation}.</b>"
            f"\n{queues_list}\n",
            reply_markup=keyboard,
        )

    await call.answer()


@dp.callback_query_handler(text_startswith="show_")
async def show_a_queue(call: types.CallbackQuery):
    """
    Shows the queue a user has selected to him/her.
    """
    team_id = await get_team_id(call.from_user.id)
    queue_type = call.data.split("_")[-1]

    queue_array = await get_queue_array(team_id, queue_type)

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

    await call.message.answer(f"Here is your <b>{queue_type}</b> queue:\n{queue_list}")


@dp.callback_query_handler(text_startswith="modify_")
async def modify_a_queue(call: types.CallbackQuery):
    """
    Provides some options to modify the queue (delete, reorder, reassign turn)
    """
    team_id = await get_team_id(call.from_user.id)
    queue_type = call.data.split("_")[-1]

    queue_array = await get_queue_array(team_id, queue_type)

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

    await call.message.answer(f"Here is your <b>{queue_type}</b> queue:\n{queue_list}")


@dp.callback_query_handler(text="create")
async def ask_queue_type(call: types.CallbackQuery):
    """
    Asks the user to pick a queue type (which is essentially a queue name).
    """
    user_id = call.from_user.id
    team_id = await get_team_id(user_id)

    if str(user_id) != team_id:
        setup_person = await users.find_one(
            {"user_id": int(team_id)},
            {"name": 1, "_id": 0},
        )
        setup_person = setup_person["name"]

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


async def get_queue_list(queue_array):
    """
    Returns the queue list using the queue array.
    (this function will mainly be called by another function)
    """
    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

    return queue_list


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

    queue_list = await get_queue_list(queue_array)

    for index, member in enumerate(queue_array, start=1):
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

    await state.finish()


@dp.callback_query_handler(text_endswith="_ready", state="*")
async def ask_whose_turn(call: types.CallbackQuery, state: FSMContext):
    """
    Asks the user whose turn it is on the list to do the chore.
    """
    await QueueSetup.marking.set()

    team_id = await get_team_id(call.from_user.id)

    queue_type = call.data.split("_")[0]
    await state.update_data(queue_type=queue_type)

    queue_array = await get_queue_array(team_id, queue_type)
    await state.update_data(queue_array=queue_array)

    keyboard = types.InlineKeyboardMarkup()

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        queue_list += f"{index}. {name}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                text=name,
                callback_data=f"turn_{index-1}",
            )
        )

    await call.message.edit_text(
        f"<b>Select the person whose turn it is to do the chore.</b>\n{queue_list}",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="turn_", state=QueueSetup.marking)
async def mark_roommate(call: types.CallbackQuery, state: FSMContext):
    """
    Changes the 'current_turn' status of the selected user to True.
    Asks if there are any other roommates to select
    (e.g. for chores that are done in pairs)
    """
    state_data = await state.get_data()

    queue_type = state_data["queue_type"]
    queue_array = state_data["queue_array"]

    position = int(call.data.split("_")[1])

    queue_array[position]["current_turn"] = True

    team_id = await get_team_id(call.from_user.id)

    q_data = {f"queues.{queue_type}": queue_array}
    await queues.update_one({"id": team_id}, {"$set": q_data}, upsert=True)

    keyboard = types.InlineKeyboardMarkup()

    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        current_turn = member["current_turn"]

        if current_turn:
            queue_list += f"<b><i>{index}. {name}</i></b>\n"
        else:
            queue_list += f"{index}. {name}\n"

        keyboard.add(
            types.InlineKeyboardButton(
                text=name,
                callback_data="turn_{index-1}",
            )
        )

    keyboard.add(
        types.InlineKeyboardButton(text="Done", callback_data="assigning_done")
    )

    await call.message.edit_text(
        "Awesome, if this chore is usually done by more than one person at a "
        "time, please select another person whose turn it is to do this chore."
        f"\n{queue_list}\nOnce you are done, press <i><b>Done</b></i>.",
        reply_markup=keyboard,
    )

    await call.answer()

