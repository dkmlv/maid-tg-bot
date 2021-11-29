"""
This code will trigger when user indicates that they can do the chore.
Bot just transfers 'current_turn' to the next person in the queue.
"""

import logging
from typing import Tuple

from aiogram import types
from loader import dp, queues
from utils.get_db_data import get_queue_array, get_team_id
from utils.sticker_file_ids import CHARISMATIC_STICKER


async def mark_next_person(queue_array: list) -> Tuple[list, int]:
    """Mark next person in the queue (transfers current_turn to them).

    Parameters
    ----------
    queue_array : list
        This array represents the queue

    Returns
    -------
    Tuple[list, int]
        The modified queue_array & the id of the person marked
    """

    for index, member in enumerate(queue_array):
        if member["current_turn"]:
            queue_array[index]["current_turn"] = False

            # shouldnt fail when next person is at the beginning of the
            # queue
            next_person_pos = (index + 1) % len(queue_array)
            queue_array[next_person_pos]["current_turn"] = True

            return (queue_array, queue_array[next_person_pos]["user_id"])

    logging.error("Failed to find next person in the queue")
    return ([], 0)


@dp.callback_query_handler(text_startswith="transfer_")
async def transfer_turn(call: types.CallbackQuery):
    """Transfer current_turn to the next person in the queue.

    Just calls the mark_next_person() func and updates the db with the
    new queue.
    """

    await call.message.delete()

    team_id = await get_team_id(call.from_user.id)
    queue_name = call.data.split("_")[1]
    queue_array = await get_queue_array(team_id, queue_name)

    await mark_next_person(queue_array)

    new_data = {f"queues.{queue_name}": queue_array}
    await queues.update_one({"id": team_id}, {"$set": new_data}, upsert=True)

    await call.message.answer_sticker(CHARISMATIC_STICKER)
    await call.message.answer("Great, good luck!")
