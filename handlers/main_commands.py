import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils.deep_linking import decode_payload, get_start_link

from loader import dp, teams, users


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

    team_data = {"id": team_id, "members": {user_name: user_id}}
    await teams.update_one({"id": team_id}, {"$set": team_data}, upsert=True)

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
    for index, name in enumerate(members.keys(), start=1):
        mates_list += f"{index}. {name}\n"

    await message.reply("<b>Here is your list of roommates:</b>\n" + mates_list)


@dp.message_handler(commands="queues")
async def show_queues(message: types.Message):
    """
    Shows all the chore queues the user has.
    """
    user_id = message.from_user.id
    data = await users.find_one(
        {"user_id": user_id},
        {"team_id": 1, "_id": 0},
    )
    team_id = data["team_id"]

    queues_data = await teams.find_one(
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
    Offers some queues that come with the bot and the ability to create a
    custom queue.
    """
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    buttons = [
        types.InlineKeyboardButton(text="Cooking", callback_data="create_cooking_q"),
        types.InlineKeyboardButton(text="Cleaning", callback_data="create_cleaning_q"),
        types.InlineKeyboardButton(text="Shopping", callback_data="create_shopping_q"),
        types.InlineKeyboardButton(text="Bread", callback_data="create_bread_q"),
        types.InlineKeyboardButton(text="Garbage", callback_data="creat_garbage_q"),
        types.InlineKeyboardButton(text="Custom", callback_data="create_custom_q"),
    ]

    keyboard.add(*buttons)

    await call.message.answer(
        "Awesome, you can choose to make a queue for one of the following or "
        "create a custom queue by picking one of the options below.",
        reply_markup=keyboard,
    )

