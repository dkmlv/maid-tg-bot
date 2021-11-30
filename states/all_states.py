from aiogram.dispatcher.filters.state import State, StatesGroup


class QueueSetup(StatesGroup):
    setting_freq = State()
    setting_up = State()
    waiting_for_custom_freq = State()
    waiting_for_queue_name = State()
    waiting_for_time = State()


class TrackingQueue(StatesGroup):
    waiting_for_reason = State()
    waiting_for_meal_name = State()
    waiting_for_number = State()
