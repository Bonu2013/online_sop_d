from aiogram import F,Router
from aiogram.types import Message
from keyboards.inline import product_inline
router=Router()

@router.message(F.text=="Mahsulotlar")
async def product(msg:Message,db):
    products=await db.get_products()
    await msg.answer(f"Mahsulotlar ro'yxati: ",reply_markup=product_inline(products))