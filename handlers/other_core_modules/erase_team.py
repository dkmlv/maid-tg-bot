"""
Erases the whole team from the db.
This will be used when admin (aka setup person) blocks the bot.
"""

import logging

from loader import queues, sched, teams, users
from utils.get_db_data import get_team_members


async def erase_team(user_id: int):
    """Erase team from the database.

    Parameters
    ----------
    user_id : int
        In this case user_id and team_id will be the same and they
        represent the id of the admin who blocked the bot
    """

    logging.info("Erasing team.")

    # removing scheduled jobs
    jobs = sched.get_jobs(jobstore="mongo")
    for job in jobs:
        if job.id.endswith(str(user_id)):
            sched.remove_job(job_id=job.id, jobstore="mongo")

    # deleting user from users collection
    team_members = await get_team_members(user_id)
    for member_id in team_members:
        await users.delete_one({"user_id": int(member_id)})

    # deleting queues and teams document
    await queues.delete_one({"id": user_id})
    await teams.delete_one({"id": user_id})
