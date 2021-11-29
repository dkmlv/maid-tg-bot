"""
The actual last part of the queue setup process.
Scheduling 'the question' to the person whose turn it is in a queue.
It's really just the bot asking whether they can do the chore that day.
Also serves as a reminder that it's their turn in a queue.
"""

import asyncio
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils import exceptions
from loader import dp, sched
from states.all_states import QueueSetup
from utils.get_db_data import get_current_turn, get_queue_array, get_team_id
from utils.sticker_file_ids import CHARISMATIC_STICKER


async def send_question(team_id, queue_name):
    """Send the question to the current turn person.

    The question is really just 'can you do this chore today?'.

    Parameters
    ----------
    team_id : int
        The id of the team. This will be used to get the person whose
        turn it is in the queue.
    queue_name : str
        This represents the name of the queue.
    """

    queue_array = await get_queue_array(team_id, queue_name)
    user_id, user_name, _ = await get_current_turn(queue_array)

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(text="Yes", callback_data=f"transfer_{queue_name}"),
        types.InlineKeyboardButton(text="No", callback_data=f"ask_why_{queue_name}"),
    ]
    keyboard.add(*buttons)

    text = (
        f"Hey {user_name}, today is your turn in the <b>{queue_name}</b> queue. "
        "Will you have time to do this chore today?"
    )

    try:
        await dp.bot.send_message(user_id, text, reply_markup=keyboard)
    except exceptions.BotBlocked:
        logging.error(f"Target [ID:{user_id}]: blocked by user")
        # inform the admin that user has blocked the bot
        await dp.bot.send_message(
            team_id,
            f"In your team, <b>{user_name}</b> has blocked me. You might "
            "wanna talk to them about it or remove them from your team using "
            "the <b>/list</b> command.",
        )
    except exceptions.RetryAfter as e:
        logging.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds."
        )
        await asyncio.sleep(e.timeout)
        return await send_question(team_id, queue_name)  # Recursive call
    except exceptions.UserDeactivated:
        logging.error(f"Target [ID:{user_id}]: user is deactivated")
        # inform admin that user has deleted their account
        await dp.bot.send_message(
            team_id,
            f"In your team, <b>{user_name}</b> has deleted their account. You "
            "might wanna talk to them about it or remove them from your team "
            "using the <b>/list</b> command.",
        )
    except exceptions.TelegramAPIError:
        logging.exception(f"Target [ID:{user_id}]: failed")
    else:
        logging.info(f"Target [ID:{user_id}]: success, question sent.")


@dp.message_handler(regexp=r"[0-2]?\d:[0-5]\d", state=QueueSetup.waiting_for_time)
async def schedule_question(message: types.Message, state: FSMContext):
    """Schedule the question to send to the current turn user."""
    team_id = await get_team_id(message.from_user.id)

    time = message.text.split(":")
    hour = int(time[0])
    minute = int(time[1])

    state_data = await state.get_data()
    queue_name = state_data["queue_name"]
    chore_frequency = state_data["chore_frequency"]

    sched.add_job(
        send_question,
        args=[team_id, queue_name],
        trigger="cron",
        jobstore="mongo",
        id=f"{queue_name}_{team_id}",
        day_of_week=chore_frequency,
        hour=hour,
        minute=minute,
        replace_existing=True,
    )

    await message.answer_sticker(CHARISMATIC_STICKER)
    await message.answer("Great, I'll try my best to keep track of this queue.")

    await state.finish()
