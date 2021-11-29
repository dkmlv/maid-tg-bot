import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.mongo import MongoStorage
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler as Scheduler
import motor.motor_asyncio
from pymongo import MongoClient

from data import config

uri = "mongodb+srv://{}:{}@{}/maid?retryWrites=true&w=majority".format(
    config.DB_USER, config.DB_PSSWD, config.HOST
)
client = motor.motor_asyncio.AsyncIOMotorClient(uri)
db = client.maid

# mongodb collections
users = db.users
teams = db.teams
queues = db.queues

bot = Bot(token=config.BOT_TOKEN, parse_mode=types.ParseMode.HTML)

fsm_uri = "mongodb+srv://{}:{}@{}/aiogram_fsm?retryWrites=true&w=majority".format(
    config.DB_USER, config.DB_PSSWD, config.HOST
)
storage = MongoStorage(uri=fsm_uri)
dp = Dispatcher(bot, storage=storage)

scheduler_uri = "mongodb+srv://{}:{}@{}/apscheduler?retryWrites=true&w=majority".format(
    config.DB_USER, config.DB_PSSWD, config.HOST
)
# motor, unfortunately, does not work
scheduler_client = MongoClient(scheduler_uri)

sched = Scheduler(
    timezone="Asia/Tashkent",
    jobstores={"mongo": MongoDBJobStore(client=scheduler_client)},
    daemon=True,
)
sched.start()

logging.basicConfig(
    level=logging.INFO,
    format=u"%(filename)s [LINE:%(lineno)d] #%(levelname)-8s [%(asctime)s]  %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)
