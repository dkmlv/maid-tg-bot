"""
Deleting the queue from the db and removing scheduled job.
This option is only available to admin (aka setup person)
"""

import logging

from aiogram import types

from loader import dp, queues, sched
from utils.get_db_data import get_team_id


@dp.callback_query_handler(text_startswith="delete_")
async def delete_a_queue(call: types.CallbackQuery):
    """Delete a queue from list of queues and remove scheduled job."""
    team_id = await get_team_id(call.from_user.id)
    queue_name = call.data.split("_")[-1]

    # cancel the scheduled message (the 'can u do this chore today' msg)
    sched.remove_job(job_id=f"{queue_name}_{team_id}")

    await queues.update_one(
        {"id": team_id},
        {"$unset": {f"queues.{queue_name}": ""}},
    )

    logging.info("Queue deleted.")

    await call.message.delete_reply_markup()
    await call.message.edit_text(f"<b>{queue_name}</b> queue deleted.")
    await call.answer()
