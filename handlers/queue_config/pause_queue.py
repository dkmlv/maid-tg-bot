"""
Pausing a queue.
This option is also available only to the admin (aka setup person)
"""

import datetime as dt
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, sched
from states.all_states import TrackingQueue
from utils.get_db_data import get_team_id, get_team_chat
from utils.sticker_file_ids import CHARISMATIC_STICKER


@dp.callback_query_handler(text_startswith="pause_")
async def ask_days_num(call: types.CallbackQuery, state: FSMContext):
    """Ask for how many days should the queue be paused."""
    await TrackingQueue.waiting_for_number.set()

    queue_name = call.data.split("_")[-1]
    await state.update_data(queue_name=queue_name)

    await call.message.edit_text(
        "For how many days should the queue be paused?",
    )
    await call.answer()


async def resume_the_job(job_id: str):
    """Find the job instance with `job_id` and resume the job."""
    job = sched.get_job(job_id=job_id, jobstore="mongo")

    if job:
        job.resume()
    else:
        logging.error("UNEXPECTED: Job to resume not found.")


@dp.message_handler(regexp=r"^[0-9]+$", state=TrackingQueue.waiting_for_number)
async def pause_queue(message: types.Message, state: FSMContext):
    """Pause the queue for a given number of days."""
    logging.info("Pausing queue.")

    state_data = await state.get_data()
    queue_name = state_data["queue_name"]
    team_id = await get_team_id(message.from_user.id)
    job_id = f"{queue_name}_{team_id}"

    group_chat = await get_team_chat(message.from_user.id)
    sched.pause_job(job_id=job_id, jobstore="mongo")

    today = dt.datetime.today()
    days = dt.timedelta(days=int(message.text))
    resume_date = (today + days).isoformat()

    try:
        sched.add_job(
            resume_the_job,
            trigger="date",
            args=[job_id],
            run_date=resume_date,
            jobstore="mongo",
            id=f"resume_{queue_name}_{team_id}",
            replace_existing=True,
        )
    except Exception:
        await message.reply("I'm sorry, something went wrong.")
        logging.exception("Adding the resume_job resulted in an error.")
    else:
        await message.answer_sticker(CHARISMATIC_STICKER)
        await message.answer(
            "Done, your team won't receive any messages regarding this queue for "
            f"{message.text} days now. You can relax."
        )

        # inform the group of the pause
        if group_chat:
            await dp.bot.send_sticker(group_chat, CHARISMATIC_STICKER)
            await dp.bot.send_message(
                group_chat,
                f"{message.from_user.first_name} has paused the {queue_name} "
                f"queue for {message.text} days. You won't recieve any "
                "notifications during this time. Enjoy your vacation.",
            )
    finally:
        await state.finish()
