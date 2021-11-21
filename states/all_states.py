from aiogram.dispatcher.filters.state import State, StatesGroup

class QueueSetup(StatesGroup):
    waiting_for_queue_name = State()
    setting_up = State()
