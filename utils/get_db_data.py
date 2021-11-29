"""
This is just that part that deals with very basic search queries to mongodb.
The reason behind including these functions is that they were used multiple
times in the code.
"""

import logging
from typing import Tuple, Union

from loader import queues, teams, users


async def get_team_id(user_id: int) -> Union[int, None]:
    """Return the team id of a user based on their user id."""
    data = await users.find_one(
        {"user_id": user_id},
        {"team_id": 1, "_id": 0},
    )

    if data:
        team_id = data.get("team_id")
    else:
        team_id = None

    return team_id


async def get_team_members(user_id: int) -> list:
    """Return the team members a user has based on their user id."""
    team_id = await get_team_id(user_id)
    team_data = await teams.find_one(
        {"id": team_id},
        {"members": 1, "_id": 0},
    )
    members = team_data["members"]

    return members


async def get_team_chat(user_id: int) -> Union[int, None]:
    """Return the team's Telegram group chat id."""
    team_id = await get_team_id(user_id)
    team_data = await teams.find_one(
        {"id": team_id},
        {"group_chat_id": 1, "_id": 0},
    )

    try:
        group_chat_id = team_data["group_chat_id"]
    except KeyError:
        group_chat_id = None

    return group_chat_id


async def get_queue_array(team_id: int, queue_name: str) -> list:
    """Return queue array for a team's specific queue."""
    queues_data = await queues.find_one(
        {"id": team_id},
        {"queues": 1, "_id": 0},
    )
    queue_array = queues_data["queues"][queue_name]

    return queue_array


async def get_queue_list(queue_array: list) -> str:
    """Return the queue list using the queue array."""
    queue_list = ""
    for index, member in enumerate(queue_array, start=1):
        name = member["name"]
        current_turn = member["current_turn"]

        if current_turn:
            queue_list += f"<b><i>{index}. {name}</i></b>\n"
        else:
            queue_list += f"{index}. {name}\n"

    return queue_list


async def get_setup_person(team_id: int) -> str:
    """Return the name of the setup person (aka admin) in a team"""
    setup_person = await users.find_one(
        {"user_id": team_id},
        {"name": 1, "_id": 0},
    )

    return setup_person["name"]


async def get_current_turn(queue_array: list) -> Tuple[int, str, int]:
    """Get the person whose turn it is to do the chore in a queue.

    Returns
    -------
    Tuple[int, str, int]
        A tuple of form: (user_id, user_name, index_position)
    """
    for index, member in enumerate(queue_array):
        if member["current_turn"]:
            data: Tuple[int, str, int] = (member["user_id"], member["name"], index)
            return data

    logging.error("Current turn person not found.")
    return (0, "", 0)
