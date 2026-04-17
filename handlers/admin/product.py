from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from filters.adminfilter import RoleFilter
from aiogram.fsm.context import FSMContext
from states.add_product import AddProductState
from states.update_product import UpdateProductState
from keyboards.inline import product_action

router = Router()

# ADD PRODUCT
@router.message(F.text == "Mahsulotlar qoshish", RoleFilter('admin'))
async def add_product_start(msg: Message, state: FSMContext):
    await msg.answer("Mahsulot nomini kiriting:")
    await state.set_state(AddProductState.name)

@router.message(AddProductState.name)
async def add_product_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Narxini kiriting:")
    await state.set_state(AddProductState.price)

@router.message(AddProductState.price)
async def add_product_price(msg: Message, state: FSMContext):
    if msg.text.isdigit():
        await state.update_data(price=int(msg.text))
        await msg.answer("Tavsif kiriting:")
        await state.set_state(AddProductState.description)
    else:
        await msg.answer("Faqat raqam kiriting!")

@router.message(AddProductState.description)
async def add_product_finish(msg: Message, state: FSMContext, db):
    await state.update_data(description=msg.text)
    data = await state.get_data()

    await db.add_product(data["name"], data["price"], data["description"])
    await msg.answer("Mahsulot qo'shildi ")
    await state.clear()


# DELETE
@router.callback_query(F.data.startswith("delete_product_"))
async def delete_product(call: CallbackQuery, db):
    product_id = int(call.data.split("_")[2])
    await db.delete_product(product_id)
    await call.message.answer("O'chirildi ")
    await call.answer()


# UPDATE
@router.callback_query(F.data.startswith("edit_product_"))
async def update_start(call: CallbackQuery, state: FSMContext):
    product_id = int(call.data.split("_")[2])
    await state.update_data(product_id=product_id)
    await call.message.answer("Yangi nom:")
    await state.set_state(UpdateProductState.name)

@router.message(UpdateProductState.name)
async def update_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Yangi narx:")
    await state.set_state(UpdateProductState.price)

@router.message(UpdateProductState.price)
async def update_price(msg: Message, state: FSMContext):
    await state.update_data(price=int(msg.text))
    await msg.answer("Yangi tavsif:")
    await state.set_state(UpdateProductState.description)

@router.message(UpdateProductState.description)
async def update_finish(msg: Message, state: FSMContext, db):
    await state.update_data(description=msg.text)
    data = await state.get_data()

    await db.update_product(
        data["product_id"],
        data["name"],
        data["price"],
        data["description"]
    )

    await msg.answer("Yangilandi ")
    await state.clear()