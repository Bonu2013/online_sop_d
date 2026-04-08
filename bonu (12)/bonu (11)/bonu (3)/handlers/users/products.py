from aiogram import Router,F
from aiogram.types import Message,CallbackQuery
from filters.adminfilter import RoleFilter
from keyboards.inline import savat_inline,payment_keyboard
router=Router()

@router.callback_query(F.data.startswith("product_"),RoleFilter('user'))
async def product(call:CallbackQuery,db):
    product_id= int(call.data.split("_")[1])
    user_id= await db.get_user_id(call.from_user.id)
    await db.add_product_to_cart(user_id,product_id)
    await call.answer("Mahsulot savatga qo'shildi")

@router.message(F.text=="Savatcha")
async def savatcha(msg:Message,db):
    user_id= await db.get_user_id(msg.from_user.id)
    products=await db.get_cart_products(user_id)
    await msg.answer("Mahsulotlar ro'yxati: ",reply_markup=savat_inline(products))

@router.callback_query(F.data.startswith("remove_product_"))
async def remove_from_cart(call:CallbackQuery,db):
    user_id= await db.get_user_id(call.from_user.id)
    product_id= int(call.data.split("_")[2])
    await db.remove_one_product(user_id,product_id)
    products=await db.get_cart_products(user_id)
    await call.message.answer("Mahsulotlar ro'yxati: ",reply_markup=savat_inline(products))
    await call.answer()

@router.callback_query(F.data=='order')
async def zakaz(call:CallbackQuery,db):
    user_id= await db.get_user_id(call.from_user.id)
    products,total=await db.get_cart_with_total(user_id)
    if not products:
        await call.message.answer("Savatchangiz bo'sh")
        return

    text = "🛒 Buyurtmangiz:\n\n"

    for product in products:
        text += f"• {product['name']} - {product['price']} so'm\n"

    text += f"\n💰 Umumiy narx: {total} so'm"

    await call.message.answer(
        text,
        reply_markup=payment_keyboard()
    )

@router.callback_query(F.data == "pay_card")
async def pay_card(call: CallbackQuery,db):
    user_id= await db.get_user_id(call.from_user.id)
    await db.confirm_order(user_id)

    await call.message.answer(
        "💳 To'lov uchun karta:\n"
        "8600 1234 5678 9012\n\n"
        "To'lov qilgandan keyin chek yuboring."
    )


@router.callback_query(F.data == "pay_cash")
async def pay_cash(call: CallbackQuery,db):
    user_id= await db.get_user_id(call.from_user.id)

    await db.confirm_order(user_id)

    await call.message.answer(
        "✅ Buyurtmangiz qabul qilindi!\n"
        "Courier yetkazib berganda naqd to'laysiz."
    )

@router.message(F.text=="Mening buyurtmalarim")
async def nun(msg:Message,db):
    user_id= await db.get_user_id(msg.from_user.id)
    orders = await db.get_user_order_history(user_id)

    for order_id, data in orders.items():
        text = f"📦 Order #{order_id}\n"

        for p in data["products"]:
            text += f"- {p['name']} ({p['price']} so'm)\n"

        text += f"\n💰 Total: {data['total']} so'm"

        await msg.answer(text=text)
    