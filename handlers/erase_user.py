import logging

from aiogram import types

from handlers.marking import mark_next_person
from handlers.setup_command import setup_team
from loader import dp, queues, teams
from utils.get_db_data import get_team_id, get_current_turn


@dp.callback_query_handler(text="erase_user")
async def erase_user(call: types.CallbackQuery):
    """
    Erase user from old team and old queues.
    """
    user_id = call.from_user.id
    user_name = call.from_user.full_name

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

        current_turn_id, current_turn_pos = await get_current_turn(queue_array)

        if user_id == current_turn_id:
            queue_array, next_id = await mark_next_person(queue_array)

            # message user that its their turn now
            await dp.bot.send_message(
                next_id,
                "Since one of your roommates left your team, it is now your "
                f"turn in the {queue_name} queue.",
            )

            del queue_array[current_turn_pos]
        else:
            for index, member in enumerate(queue_array):
                if member["user_id"] == user_id:
                    del queue_array[index]

        new_data = {f"queues.{queue_name}": queue_array}
        await queues.update_one({"id": team_id}, {"$set": new_data}, upsert=True)

    logging.info("user erased")
    await call.message.delete_reply_markup()

    await setup_team(user_id, user_name)

    await call.answer()

