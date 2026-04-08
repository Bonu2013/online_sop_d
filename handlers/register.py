from aiogram import Router,F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from keyboards.reply import start_reply

from states.register import RegisterState

router=Router()

@router.message(F.text=="Register")
async def register(msg:Message,state:FSMContext,db):
    if await db.is_user_exists(msg.from_user.id):
        await msg.answer("Siz avval ro'yxatdan o'tgansiz iltimos asosiy menyudan foydalaning",reply_markup=start_reply())
    else:
        await msg.answer("Registratsiyadan o'tish uchun ismingizni yozing: ")
        await state.set_state(RegisterState.name)

@router.message(RegisterState.name)
async def register(msg:Message,state:FSMContext):
    await state.update_data(name=msg.text)
    await msg.answer("Familyangizni kiriting: ")
    await state.set_state(RegisterState.surname)

@router.message(RegisterState.surname)
async def register(msg:Message,state:FSMContext):
    await state.update_data(surname=msg.text)
    await msg.answer("Yoshingizni kiriting: ")
    await state.set_state(RegisterState.age)

@router.message(RegisterState.age)
async def register(msg:Message,state:FSMContext):
    await state.update_data(age=int(msg.text))
    await msg.answer("Telefon raqamingizni kiriting: ")
    await state.set_state(RegisterState.phone_number)

@router.message(RegisterState.phone_number)
async def register(msg:Message,state:FSMContext,db):
    await state.update_data(phone_number=msg.text)
    
    data=await state.get_data()
    await msg.answer(text=f" Malumotlaringiz: \nIsmingiz: {data["name"]}\nFamilyangiz: {data["surname"]}\nYoshingiz: {data["age"]}\nTelefon raqamingiz: {data["phone_number"]}")
    await db.add_user(int(msg.from_user.id),data["name"],data["surname"],data["age"],data["phone_number"])
    await msg.answer("Malumotlarigiz muvaffaqiyatli saqlandi",reply_markup=start_reply())
    await state.clear()