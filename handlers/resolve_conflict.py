import logging
import datetime as dt

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, queues, sched
from states.all_states import TrackingQueue
from utils.get_db_data import get_team_chat, get_team_id
from utils.sticker_file_ids import SAD_STICKER, WHATEVER_STICKER


HOURS = 5


async def get_later_time():
    """
    Returns the time that is HOURS from now as a datetime string in isoformat.
    """
    now = dt.datetime.now()
    hours = dt.timedelta(hours=HOURS)

    return (now + hours).isoformat()


async def skip_chore_today(group_chat_id, user_name, queue_name):
    """
    Lets the group know that the chore is considered incomplete and has been
    skipped for the day.
    """
    await dp.bot.send_sticker(group_chat_id, WHATEVER_STICKER)
    await dp.bot.send_message(
        group_chat_id,
        "Well, since no one has replied 'I can do it', i will assume that "
        f"the chore in {queue_name} queue is incomplete and skip it for today."
        f" It is still {user_name}'s turn to do the chore.",
    )


@dp.callback_query_handler(text_startswith="ask_why_")
async def ask_for_reason(call: types.CallbackQuery, state: FSMContext):
    """
    Handler will be called when user doesnt have time to complete the chore.
    Asks the user why they dont have time to do the chore.
    The answer will be sent to the user's group chat along with a question of
    who can do the chore instead.
    """
    await call.message.delete()
    await TrackingQueue.waiting_for_reason.set()

    queue_name = call.data.split("_")[-1]
    await state.update_data(queue_name=queue_name)

    await call.message.answer_sticker(SAD_STICKER)
    await call.message.answer(
        "Can you please type out the reason why you can't complete the chore "
        "today?\nI will send it to your group chat and we'll try to work it "
        "out there."
    )


@dp.message_handler(state=TrackingQueue.waiting_for_reason)
async def inform_and_resolve(message: types.Message, state: FSMContext):
    """
    User has provided a reason and that reason is sent to the group.
    Bot asks who can do the chore instead.
    The first person to reply 'Yes' is swapped in the queue with current_turn.
    If no one replies 'Yes' in HOURS, bot considers the chore as incomplete
    and doesnt reassign current turn.
    """
    reason = message.text
    user_name = message.from_user.full_name
    group_chat_id = await get_team_chat(message.from_user.id)
    team_id = await get_team_id(message.from_user.id)

    if not group_chat_id:
        print("FUCK")
        return

    state_data = await state.get_data()
    queue_name = state_data["queue_name"]

    later_time = await get_later_time()

    sched.add_job(
        skip_chore_today,
        args=[group_chat_id, user_name, queue_name],
        trigger="date",
        run_date=later_time,
        jobstore="mongo",
        id=f"resolving_{queue_name}_{team_id}",
        replace_existing=True,
    )

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton(text="I can do it.", callback_data="swap_users")
    )

    await message.answer(
        "Thank you. Let's try and work this out in your group chat.",
    )

    await dp.bot.send_message(
        group_chat_id,
        f"Hey, turns out <b>{user_name}</b> can't do the chore in <b>{queue_name}</b> "
        f"queue today and they provided the following reason:\n\n{reason}\n\n"
        "Who can do it today instead? If you can't, just ignore this message.",
        reply_markup=keyboard,
    )

    await state.finish()
