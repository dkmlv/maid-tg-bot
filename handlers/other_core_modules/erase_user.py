"""
Deleting any user from their present roommates' team.
"""

import logging

from aiogram import types
from loader import dp, queues, sched, teams, users
from utils.get_db_data import get_current_turn, get_team_id, get_team_members
from utils.sticker_file_ids import NOPE_STICKER

from .transfer_turn import mark_next_person


@dp.callback_query_handler(text="ask_which_user")
async def ask_who_to_delete(call: types.CallbackQuery):
    """Ask to select a roommate to remove from the team."""
    user_id = call.from_user.id
    team_id = await get_team_id(user_id)

    if user_id != team_id:
        await call.message.answer_sticker(NOPE_STICKER)
        await call.message.answer(
            "Sorry, you do not have permission to remove a user from a team."
        )
    else:
        members = await get_team_members(user_id)

        buttons = []
        for member_id, member_name in members.items():
            # admin (setup person) wont be able to delete themselves this way
            # (they can still delete themselves using /setup)
            if int(member_id) == call.from_user.id:
                continue

            buttons.append(
                types.InlineKeyboardButton(
                    text=member_name,
                    callback_data=f"erase_{member_id}",
                )
            )

        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(*buttons)

        await call.message.edit_text(
            "<b>Select the roommate you want to remove.</b>",
            reply_markup=keyboard,
        )

    await call.answer()


async def erase_from_queues(user_id: int, team_id: int):
    """Erase a user from their present queues.

    This is kept as a separate function since this is a bit complicated
    since the user getting erased may have their current_turn True.
    In this case, the current_turn should be transferred to the next
    person in the queue and only then should the user be erased.

    Parameters
    ----------
    user_id : int
        Telegram user id of the user getting erased
    team_id : int
        The team from which the user is getting erased
    """

    queue_data = await queues.find_one(
        {"id": team_id},
        {"queues": 1, "_id": 0},
    )
    queue_data = queue_data["queues"]

    for queue_name, queue_array in queue_data.items():
        # ct - current turn
        ct_id, _, ct_pos = await get_current_turn(queue_array)

        # user being erased has their current_turn True
        if user_id == ct_id:
            queue_array, next_id = await mark_next_person(queue_array)

            del queue_array[ct_pos]

            # message user that its their turn now
            await dp.bot.send_message(
                next_id,
                "Since one of your roommates left your team, it is now "
                f"your turn in the {queue_name} queue.",
            )
        else:
            for index, member in enumerate(queue_array):
                if member["user_id"] == user_id:
                    del queue_array[index]
                    break

        new_data = {f"queues.{queue_name}": queue_array}
        await queues.update_one(
            {"id": team_id},
            {"$set": new_data},
            upsert=True,
        )


@dp.callback_query_handler(text_startswith="erase_")
async def erase_anyone(call: types.CallbackQuery):
    """Erase anyone (user/admin) from present team and present queues."""
    data = call.data.split("_")
    user_id = int(data[1])

    team_id = await get_team_id(user_id)
    assert team_id is not None

    # deleting user from the users collection
    await users.delete_one({"user_id": user_id})

    if user_id == team_id:
        # handling case when admin is the only user left in the team
        jobs = sched.get_jobs(jobstore="mongo")
        for job in jobs:
            if job.id.endswith(str(user_id)):
                sched.remove_job(job_id=job.id, jobstore="mongo")

        await queues.delete_one({"id": user_id})
        await teams.delete_one({"id": user_id})
    else:
        # normal user wants to delete themselves
        # erasing user from old teams
        await teams.update_one(
            {"id": team_id},
            {"$unset": {f"members.{user_id}": ""}},
        )

        # erasing user from present queues
        await erase_from_queues(user_id, team_id)

    logging.info("User erased")
    await call.message.delete_reply_markup()

    await dp.bot.send_message(
        user_id,
        "You have been deleted from your roommates team. To set up a new team "
        "for yourself, use the <b>/setup</b> command. If you'd like to join "
        "someone else's team, simply go through their invite link now.",
    )

    await call.answer()
