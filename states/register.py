from aiogram.fsm.state import StatesGroup,State

class RegisterState(StatesGroup):
    name=State()
    surname=State()
    age=State()
    phone_number=State()