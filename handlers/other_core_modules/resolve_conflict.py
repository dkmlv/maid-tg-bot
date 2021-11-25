"""
Resolving a conflict that arises when someone doesn't have time to do
their chore on a given day. Informs the group why that person can't do
it and asks if anyone can do the chore instead. If no one replies, bot
skips chore for that day and proceeds as usual next time.
"""

import datetime as dt
import logging

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, queues, sched
from states.all_states import TrackingQueue
from utils.get_db_data import (
    get_current_turn,
    get_queue_array,
    get_team_chat,
    get_team_id,
)
from utils.sticker_file_ids import (
    CONFUSED_STICKER,
    NOPE_STICKER,
    SAD_STICKER,
    WHATEVER_STICKER,
    YAY_STICKER,
)

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
        await message.answer(
            "Looks like you don't have a group chat.\nPlease create a group (if "
            "you don't already have one) and add me there, so that we can "
            "solve this problem. Once I'm added to the group, send me the "
            "reason again."
        )
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
        types.InlineKeyboardButton(
            text="I can do it.", callback_data=f"swap_{queue_name}_{team_id}"
        )
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


@dp.callback_query_handler(text_startswith="swap_")
async def swap_users(call: types.CallbackQuery):
    """
    Swaps two users in the queue.
    """
    # data passed in will be in the form of "swap_qname_-123456789"
    data = call.data.split("_")
    queue_name = data[1]
    team_id = int(data[-1])
    user_name = call.from_user.first_name

    q_array = await get_queue_array(team_id, queue_name)

    # ct - current_turn
    _, ct_name, ct_pos = await get_current_turn(q_array)

    user_pos = None
    for index, member in enumerate(q_array):
        if member["user_id"] == call.from_user.id:
            user_pos = index

    if type(user_pos) != int:
        # person who replied is not in the roommates group in the db
        await call.message.answer_sticker(NOPE_STICKER)
        await call.message.answer(
            "You are not a part of the roommates group, you should get in touch"
            " with others and get the <b>invite link</b>."
        )
        return
    elif ct_pos == user_pos:
        # the person who said they cant do the chore clicked 'Yes, I can do it'
        await call.message.answer_sticker(CONFUSED_STICKER)
        await call.message.answer(
            f"I'm sorry, but you can't swap with yourself, {user_name}-san."
        )
        return

    # reassigning current_turn
    q_array[ct_pos]["current_turn"], q_array[user_pos]["current_turn"] = False, True
    # swapping positions in the queue
    q_array[ct_pos], q_array[user_pos] = q_array[user_pos], q_array[ct_pos]

    new_data = {f"queues.{queue_name}": q_array}
    await queues.update_one({"id": team_id}, {"$set": new_data}, upsert=True)

    logging.info("Swapped two users successfully")

    sched.remove_job(job_id=f"resolving_{queue_name}_{team_id}", jobstore="mongo")

    await call.message.delete_reply_markup()
    await call.message.answer_sticker(YAY_STICKER)
    await call.message.answer(
        f"Yaaay, thank you, {user_name}! You have swapped places with {ct_name}."
        f" {ct_name} will now do the chore when it's your turn.\nYou can check "
        f"out the new order in the {queue_name} queue, by typing <b>/queues</b> "
        "and then clicking on <b>Show Queue</b>."
    )

    await call.answer()
