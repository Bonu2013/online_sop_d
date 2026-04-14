from aiogram.fsm.state import StatesGroup,State

class UpdateProductState(StatesGroup):
    product_id=State()
    name=State()
    price=State()
    description=State()