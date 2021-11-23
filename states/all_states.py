from aiogram.dispatcher.filters.state import State, StatesGroup

class QueueSetup(StatesGroup):
    waiting_for_queue_name = State()
    waiting_for_time = State()
    setting_up = State()
