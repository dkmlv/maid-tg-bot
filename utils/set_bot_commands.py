from aiogram import types


async def set_default_commands(dp):
    """
    Sets commands for the bot.
    (This could have also been done directly through BotFather)
    """
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", "about info"),
            types.BotCommand("help", "how to use the bot"),
            types.BotCommand("setup", "start the setup process"),
            types.BotCommand("invite_link", "link to the current team"),
            types.BotCommand("list", "see the list of roommates"),
            types.BotCommand("queues", "show & modify queues"),
        ]
    )
