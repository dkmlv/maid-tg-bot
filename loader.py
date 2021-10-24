import logging

import motor.motor_asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.mongo import MongoStorage

from data import config

uri = "mongodb+srv://{}:{}@{}/{}?retryWrites=true&w=majority".format(
    config.DB_USER, config.DB_PSSWD, config.HOST, config.DB_NAME
)
client = motor.motor_asyncio.AsyncIOMotorClient(uri)
db = client.maid

# mongodb collections
users = db.users
teams = db.teams

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)

fsm_uri = "mongodb+srv://{}:{}@{}/aiogram_fsm?retryWrites=true&w=majority".format(
    config.DB_USER, config.DB_PSSWD, config.HOST
)
storage = MongoStorage(uri=fsm_uri)
dp = Dispatcher(bot, storage=storage)

logging.basicConfig(
    level=logging.INFO,
    format=u"%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)

