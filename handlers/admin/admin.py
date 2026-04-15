from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from keyboards.reply import admin_panel
from keyboards.inline import users_inline, user_action
from filters.adminfilter import RoleFilter
from states.AdsState import AdsState
from aiogram.fsm.context import FSMContext

router = Router()

# Admin panelga kirish
@router.message(F.text == "Admin panel", RoleFilter('admin'))
async def admin(msg: Message):
    await msg.answer(text="Admin panelga xush kelibsiz:", reply_markup=admin_panel())

# Foydalanuvchilar ro'yxatini ko'rish
@router.message(F.text == "Users", RoleFilter('admin'))
async def user(msg: Message, db):
    users = await db.get_users()
    await msg.answer("Foydalanuvchilar ro'yxati:", reply_markup=users_inline(users))

# Foydalanuvchi bosilganda rolni tanlash
@router.callback_query(F.data.startswith("user_"), RoleFilter('admin'))
async def user_callback(call: CallbackQuery):
    user_id = int(call.data.split("_")[1])
    await call.message.answer("User rolini tanlang:", reply_markup=user_action(user_id))
    await call.answer()

# Rolni o'zgartirish
@router.callback_query(F.data.startswith("changeto_"), RoleFilter('admin'))
async def change_role(call: CallbackQuery, db): 
    _, role, user_id = call.data.split("_")
    user_id = int(user_id)
    await db.update_role(user_id, role)
    await call.message.answer(f"Foydalanuvchi roli '{role}'ga o'zgartirildi!")
    await call.answer()

# Reklama yuborish funksiyasi (Broadcasting)
async def broadcasting(bot, users, message: Message):
    success = 0
    failed = 0
    
    for user_data in users:
        try:
            # db.get_users_telegram_id() dan 'telegram_id' kaliti kelishi kerak
            target_id = int(user_data["telegram_id"])

            # Rasm + matn bo'lsa
            if message.photo:
                await bot.send_photo(
                    chat_id=target_id,
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )
            # Video + matn bo'lsa
            elif message.video:
                await bot.send_video(
                    chat_id=target_id,
                    video=message.video.file_id,
                    caption=message.caption
                )
            # Faqat matn bo'lsa
            else:
                await bot.send_message(
                    chat_id=target_id,
                    text=message.text
                )
            success += 1
        except Exception as e:
            print(f"Xatolik {user_data.get('telegram_id')}: {e}")
            failed += 1
            
    return success, failed

# Reklama buyrug'ini qabul qilish
@router.message(F.text == "Reklama", RoleFilter("admin"))
async def start_reklama(msg: Message, state: FSMContext):
    await msg.answer("Reklama yuborish uchun rasm, video yoki matn yuboring:")
    await state.set_state(AdsState.waiting_for_ads)

# Reklamani tarqatish
@router.message(AdsState.waiting_for_ads)
async def process_reklama(msg: Message, state: FSMContext, db):
    # Bazadan barcha userlarning telegram_id larini olamiz
    users = await db.get_users_telegram_id() 
    
    # Xabarni yuboramiz
    success, failed = await broadcasting(msg.bot, users, msg)

    await msg.answer(
        f"Reklama natijasi:\n"
        f"✅ Yuborildi: {success}\n"
        f"❌ Yuborilmadi: {failed}"
    )
    await state.clear()