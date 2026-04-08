from aiogram.fsm.state import StatesGroup,State

class AddProductState(StatesGroup):
    name=State()
    price=State()
    description=State()