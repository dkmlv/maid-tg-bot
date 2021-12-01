"""
Resuming a queue.
This option is also available only to the admin (aka setup person)
"""

import logging

from aiogram import types
from apscheduler.jobstores.base import JobLookupError

from loader import dp, sched
from utils.get_db_data import get_team_chat, get_team_id
from utils.sticker_file_ids import CONFUSED_STICKER, HI_STICKER


@dp.callback_query_handler(text_startswith="resume_")
async def explicit_resume(call: types.CallbackQuery):
    """Resume a specific team's queue."""
    logging.info("Resuming a queue (explicitly)")

    queue_name = call.data.split("_")[-1]
    team_id = await get_team_id(call.from_user.id)
    group_chat = await get_team_chat(call.from_user.id)

    sched.resume_job(job_id=f"{queue_name}_{team_id}", jobstore="mongo")

    try:
        sched.remove_job(f"resume_{queue_name}_{team_id}", "mongo")
    except JobLookupError:
        logging.info("User tried to resume a queue that wasn't paused.")
        await call.message.answer_sticker(CONFUSED_STICKER)
        await call.message.answer(
            "This queue wasn't paused, you don't have to resume it."
        )
        await call.answer()
        return

    await call.message.edit_text(
        "Done, queue is resumed. You will continue recieving notifications now."
    )

    if group_chat:
        await dp.bot.send_sticker(group_chat, HI_STICKER)
        await dp.bot.send_message(
            group_chat,
            f"Hey, {call.from_user.first_name} has just resumed the {queue_name} "
            "queue. You will now continue recieving notifications for this "
            "queue. Good luck!",
        )

    await call.answer()
