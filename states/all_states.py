from aiogram.dispatcher.filters.state import State, StatesGroup

class QueueSetup(StatesGroup):
    waiting_for_queue_name = State()
    reordering = State()
    # marking here means choosing the roommate whose turn it is to do the chore
    marking = State() 
