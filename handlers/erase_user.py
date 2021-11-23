import logging

from aiogram import types

from handlers.marking import mark_next_person
from handlers.setup_command import setup_team
from loader import dp, queues, teams
from utils.get_db_data import get_team_id, get_team_members, get_current_turn


@dp.callback_query_handler(text="ask_which_user")
async def ask_who_to_delete(call: types.CallbackQuery):
    """
    Asks the user whose turn it is on the list to do the chore.
    """
    members = await get_team_members(call.from_user.id)

    buttons = []
    for member_id, member_name in members.items():
        # admin (setup person) wont be able to delete themselves this way
        # (they can still delete themselves using /setup repeatedly)
        if int(member_id) == call.from_user.id:
            continue

        buttons.append(
            types.InlineKeyboardButton(
                text=member_name,
                callback_data=f"erase_{member_id}_{member_name}",
            )
        )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)

    await call.message.edit_text(
        "<b>Select the roommate you want to remove.</b>",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="erase_")
async def erase_user(call: types.CallbackQuery):
    """
    Erase user from old team and old queues.
    """
    data = call.data.split("_")
    user_id = int(data[1])
    # in case someone had underscores in their telegram full name
    user_name = "_".join(data[2:])

    # erasing user from old team
    team_id = await get_team_id(user_id)
    await teams.update_one(
        {"id": team_id},
        {"$unset": {f"members.{user_id}": ""}},
    )

    # erasing user from old queues
    queue_data = await queues.find_one({"id": team_id}, {"queues": 1, "_id": 0})
    queue_data = queue_data["queues"]

    for queue_name in queue_data:
        queue_array = queue_data[queue_name]

        # ct - current turn
        ct_id, _, ct_pos = await get_current_turn(queue_array)

        # user being erased has their current_turn True
        if user_id == ct_id:
            queue_array, next_id = await mark_next_person(queue_array)

            del queue_array[ct_pos]

            # message user that its their turn now
            await dp.bot.send_message(
                next_id,
                "Since one of your roommates left your team, it is now your "
                f"turn in the {queue_name} queue.",
            )
        else:
            for index, member in enumerate(queue_array):
                if member["user_id"] == user_id:
                    del queue_array[index]

        new_data = {f"queues.{queue_name}": queue_array}
        await queues.update_one({"id": team_id}, {"$set": new_data}, upsert=True)

    logging.info("User erased")
    await call.message.delete_reply_markup()

    await dp.bot.send_message(
        user_id, "You have been deleted from your roommates team."
    )

    await setup_team(user_id, user_name)

    await call.answer()
