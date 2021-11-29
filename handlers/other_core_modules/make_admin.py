"""
Transferring admin privileges to someone else in the team.
Since the whole bot heavily relies on admin's id, when they leave,
they should pick someone else to take the admin privileges first.
"""

import logging

from aiogram import types

from loader import dp, queues, sched, teams, users
from utils.get_db_data import get_team_members


@dp.callback_query_handler(text="ask_who_to_make_admin")
async def ask_who_to_make_admin(call: types.CallbackQuery):
    """Ask the admin to pick someone to transfer admin priviliges to."""
    members = await get_team_members(call.from_user.id)

    buttons = []
    for member_id, member_name in members.items():
        # it wouldn't make sense for the admin to pick themselves
        if int(member_id) == call.from_user.id:
            continue

        buttons.append(
            types.InlineKeyboardButton(
                text=member_name,
                callback_data=f"mkadmin_{member_id}_{len(members)}",
            )
        )

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)

    await call.message.edit_text(
        "<b>Select the roommate you want to transfer admin priviliges to.</b>",
        reply_markup=keyboard,
    )

    await call.answer()


@dp.callback_query_handler(text_startswith="mkadmin_")
async def make_admin(call: types.CallbackQuery):
    """Transfer admin priviliges to the user.

    Their user id becomes the new team id for everyone in the team.
    """

    await call.message.delete()

    data = call.data.split("_")
    new_admin_id = int(data[1])
    num_of_team_members = int(data[-1])

    old_admin_name = call.from_user.full_name
    old_admin_id = call.from_user.id

    # changing users' team_id to new team_id (changes old admin's team_id too)
    for _ in range(num_of_team_members):
        await users.update_one(
            {"team_id": old_admin_id},
            {"$set": {"team_id": new_admin_id}},
        )

    # changing team id in the 'teams' collection
    # (this may be obvious, but im dumb and may forget later)
    await teams.update_one(
        {"id": old_admin_id},
        {"$set": {"id": new_admin_id}},
    )

    # changing team id in the 'queues' collection
    # (this may be obvious, but im dumb and may forget later)
    await queues.update_one(
        {"id": old_admin_id},
        {"$set": {"id": new_admin_id}},
    )

    # ideally u'd modify the jobs to reflect the new team_id, but i
    # couldn't do that, so i went for removing jobs and informing
    jobs = sched.get_jobs(jobstore="mongo")
    for job in jobs:
        if job.id.endswith(str(old_admin_id)):
            sched.remove_job(job_id=job.id, jobstore="mongo")

    logging.info("Admin priviliges transferred")

    await dp.bot.send_message(
        new_admin_id,
        f"{old_admin_name} has transferred admin priviliges to you.\nYou MUST "
        "modify all queues as the message scheduling won't work otherwise.\n"
        "To modify a queue, simply send <b>/queues</b> command and select "
        "<b>Modify Queue</b> option.",
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="Yes", callback_data=f"erase_{old_admin_id}")
    )

    await call.message.answer(
        "Admin priviliges transferred. Continue with removing you from the team?",
        reply_markup=keyboard,
    )
