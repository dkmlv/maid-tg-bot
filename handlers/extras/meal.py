"""
These are just functions that will be called when a user indicates that
they have time to cook in the 'Cooking' queue.
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp
from states.all_states import TrackingQueue
from utils.get_db_data import get_team_chat
from utils.sticker_file_ids import HUNGRY_STICKER, PROUD_STICKER


async def ask_meal_name(user_id: int):
    """Ask user what meal they're going to cook.

    Parameters
    ----------
    user_id : int
        The id of the user whose turn it is to cook
    """
    await TrackingQueue.waiting_for_meal_name.set()

    await dp.bot.send_message(
        user_id,
        "What meal are you going to cook today?\n(this name will be sent over "
        "to your group chat)",
    )


@dp.message_handler(state=TrackingQueue.waiting_for_meal_name)
async def inform_of_meal(message: types.Message, state: FSMContext):
    """Send the name of the meal to the group chat.

    If no group chat is found, let user know that and move on since
    this is really extra stuff and not a part of the core functionality.
    """

    group_chat = await get_team_chat(message.from_user.id)

    if group_chat:
        await dp.bot.send_sticker(group_chat, PROUD_STICKER)
        await dp.bot.send_message(
            group_chat,
            "Make sure that you work up your appetite because "
            f"{message.from_user.first_name} is cooking <b>{message.text}</b>"
            " today.",
        )

        await message.answer_sticker(HUNGRY_STICKER)
        await message.answer(
            "Great, good luck with cooking! Don't forget to share some of the "
            "food with me too."
        )
    else:
        await message.reply(
            "Looks like your team does not have a group chat.\nSince this meal "
            "stuff is really just an extra feature, you don't have create one "
            "and add me now. Good luck with cooking!"
        )

    await state.finish()
