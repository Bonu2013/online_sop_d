from aiogram import F,Router
from aiogram.types import Message,CallbackQuery
from filters.adminfilter import RoleFilter
from aiogram.fsm.context import FSMContext
from states.add_product import AddProductState
from states.update_product import UpdateProductState
from keyboards.inline import product_action

router=Router()

@router.message(F.text=="Mahsulotlar qoshish",RoleFilter('admin'))
async def add_product(msg:Message,state:FSMContext):
    await msg.answer("Mahsulotni qo'shish uchun iltimos mahsulot nomini kiriting: ")
    await state.set_state(AddProductState.name)

@router.message(AddProductState.name)
async def add_product(msg:Message,state:FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("mahsulot narxini kiriting: ")
    await state.set_state(AddProductState.price)
    
@router.message(AddProductState.price)
async def add_product(msg:Message,state:FSMContext):
    await state.update_data(price=int(msg.text))
    await msg.answer("mahsulot description kiriting: ")
    await state.set_state(AddProductState.description)

@router.message(AddProductState.description)
async def add_product(msg:Message,state:FSMContext,db):
    await state.update_data(description=msg.text)

    data=await state.get_data()

    await db.add_product(data["name"],data["price"],data["description"])
    await msg.answer("Mahsulot muvaffaqiyatli qo'shildi")
    await state.clear()

@router.callback_query(F.data.startswith("product_"),RoleFilter('admin'))
async def control(call:CallbackQuery):
    product_id=int(call.data.split("_")[1])
    await call.message.answer("Mahsulotni tahrirlash/o'chirish: ",reply_markup=product_action(product_id))
    await call.answer()

@router.callback_query(F.data.startswith("delete_product_"))
async def delete(call:CallbackQuery,db):
    product_id=int(call.data.split("_")[2])
    await db.delete_product(product_id)
    await call.message.answer("Mahsulot muvaffaqiyatli o'chirildi!")
    await call.answer()

@router.callback_query(F.data.startswith("edit_product_"))
async def update(call:CallbackQuery,state:FSMContext):
    product_id=int(call.data.split("_")[2])
    await state.set_state(UpdateProductState.product_id)
    await state.update_data(product_id=product_id)
    await call.message.answer("Mahsulotni nomini kiriting: ")
    await state.set_state(UpdateProductState.name)

@router.message(UpdateProductState.name)
async def update_product(msg:Message,state:FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("mahsulot narxini kiriting: ")
    await state.set_state(UpdateProductState.price)

@router.message(UpdateProductState.price)
async def update_product(msg:Message,state:FSMContext):
    await state.update_data(price=int(msg.text))
    await msg.answer("mahsulot tasnifini kiriting: ")
    await state.set_state(UpdateProductState.description)

@router.message(UpdateProductState.description)
async def update_product(msg:Message,state:FSMContext,db):
    await state.update_data(description=msg.text)
    data= await state.get_data()
    await db.update_product(data["product_id"],data["name"],data["price"],data["description"])
    await msg.answer("Mahsulot muvaffaqiyatli yangilandi!")
    await state.clear()