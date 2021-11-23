import asyncio
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils import exceptions

from loader import dp, sched
from states.all_states import QueueSetup
from utils.get_db_data import get_current_turn, get_team_id, get_queue_array


async def send_question(team_id, queue_name):
    """
    Gets the current turn person in a queue and sends the question to them
    (the 'can you do this chore today?' question).
    """
    queue_array = await get_queue_array(team_id, queue_name)
    user_id, user_name, _ = await get_current_turn(queue_array)

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(text="Yes", callback_data="schedule_next"),
        types.InlineKeyboardButton(text="No", callback_data="FUCK"),
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
        # TODO: inform the admin that user has blocked the bot
    except exceptions.RetryAfter as e:
        logging.error(
            f"Target [ID:{user_id}]: Flood limit is exceeded. Sleep {e.timeout} seconds."
        )
        await asyncio.sleep(e.timeout)
        return await send_question(team_id, queue_name)  # Recursive call
    except exceptions.UserDeactivated:
        logging.error(f"Target [ID:{user_id}]: user is deactivated")
        # TODO: inform admin that user has deleted their account
    except exceptions.TelegramAPIError:
        logging.exception(f"Target [ID:{user_id}]: failed")
    else:
        logging.info(f"Target [ID:{user_id}]: success, question sent.")


@dp.message_handler(regexp=r"[0-2]\d:[0-5]\d", state=QueueSetup.waiting_for_time)
async def schedule_question(message: types.Message, state: FSMContext):
    """
    Schedules the question to be sent to the current turn user
    (the 'can you do this chore today?' question).
    """
    team_id = await get_team_id(message.from_user.id)

    hour = int(message.text[:2])
    minute = int(message.text[-2:])

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

    await state.finish()
