"""
This is just a function that will catch all emojis and check if they
are food emojis or weapon emojis (this is kind of an easter egg).
"""

import logging

from aiogram import types
from aiogram.utils.emoji import emojize
from emoji.core import get_emoji_regexp

from loader import dp
from utils.sticker_file_ids import (
    AMUSED_STICKER,
    IS_FOR_ME_STICKER,
    QUESTION_STICKER,
)

EMOJI_REGEX = get_emoji_regexp(language="en")

# i scraped these from this site: https://www.alt-codes.net/food-emoji
FOOD_EMOJIS = [
    "U+1F347",
    "U+1F348",
    "U+1F349",
    "U+1F34A",
    "U+1F34B",
    "U+1F34C",
    "U+1F34D",
    "U+1F96D",
    "U+1F34E",
    "U+1F34F",
    "U+1F350",
    "U+1F351",
    "U+1F352",
    "U+1F353",
    "U+1F95D",
    "U+1F345",
    "U+1F965",
    "U+1F951",
    "U+1F346",
    "U+1F954",
    "U+1F955",
    "U+1F33D",
    "U+1F336",
    "U+1F952",
    "U+1F96C",
    "U+1F966",
    "U+1F344",
    "U+1F95C",
    "U+1F330",
    "U+1F35E",
    "U+1F950",
    "U+1F956",
    "U+1F968",
    "U+1F96F",
    "U+1F95E",
    "U+1F9C0",
    "U+1F356",
    "U+1F357",
    "U+1F969",
    "U+1F953",
    "U+1F354",
    "U+1F35F",
    "U+1F355",
    "U+1F32D",
    "U+1F96A",
    "U+1F32E",
    "U+1F32F",
    "U+1F959",
    "U+1F95A",
    "U+1F373",
    "U+1F958",
    "U+1F372",
    "U+1F963",
    "U+1F957",
    "U+1F37F",
    "U+1F9C2",
    "U+1F96B",
    "U+1F371",
    "U+1F358",
    "U+1F359",
    "U+1F35A",
    "U+1F35B",
    "U+1F35C",
    "U+1F35D",
    "U+1F360",
    "U+1F362",
    "U+1F363",
    "U+1F364",
    "U+1F365",
    "U+1F96E",
    "U+1F361",
    "U+1F95F",
    "U+1F960",
    "U+1F961",
    "U+1F980",
    "U+1F99E",
    "U+1F990",
    "U+1F991",
    "U+1F366",
    "U+1F367",
    "U+1F368",
    "U+1F369",
    "U+1F36A",
    "U+1F382",
    "U+1F370",
    "U+1F9C1",
    "U+1F967",
    "U+1F36B",
    "U+1F36C",
    "U+1F36D",
    "U+1F36E",
    "U+1F36F",
    "U+1F37C",
    "U+1F95B",
    "U+2615",
    "U+1F375",
    "U+1F376",
    "U+1F37E",
    "U+1F377",
    "U+1F378",
    "U+1F379",
    "U+1F37A",
    "U+1F37B",
    "U+1F942",
    "U+1F943",
    "U+1F964",
]

# these i just copy pasted directly
WEAPON_EMOJIS = ["U+1F52A", "U+1F5E1", "U+1F528", "U+1FA93", "U+1F52B"]


@dp.message_handler(regexp=EMOJI_REGEX)
async def react_to_emoji(message: types.Message):
    """React to any emoji sent by the user."""
    # converting the emoji into unicode hex format
    emoji = f"U+{ord(message.text):X}"

    if emoji in FOOD_EMOJIS:
        await message.answer_sticker(IS_FOR_ME_STICKER)
        await message.answer(
            f"is for me? {emojize(':point_right::point_left:')}",
        )
    elif emoji in WEAPON_EMOJIS:
        user_name = message.from_user.first_name

        await message.answer_sticker(AMUSED_STICKER)
        await message.answer(
            f"It will take a lot more than that to kill me, {user_name}-san."
        )
    else:
        await message.answer_sticker(QUESTION_STICKER)
        await message.answer("Why are you sending me random emojis?")
