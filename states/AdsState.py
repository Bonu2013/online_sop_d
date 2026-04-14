from aiogram.fsm.state import StatesGroup,State

class AdsState(StatesGroup):
    waiting_for_ads=State()