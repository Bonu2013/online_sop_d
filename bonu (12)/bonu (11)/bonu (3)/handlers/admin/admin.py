from aiogram import F,Router
from aiogram.types import Message,CallbackQuery

from keyboards.reply import admin_panel
from keyboards.inline import users_inline,user_action
from filters.adminfilter import RoleFilter
from states.AdsState import AdsState
from aiogram.fsm.context import FSMContext

router=Router()

@router.message(F.text=="Admin panel",RoleFilter('admin'))
async def admin(msg:Message):
    await msg.answer(text=f"Admin panelga xush kelibsiz: ",reply_markup=admin_panel())

@router.message(F.text=="Users",RoleFilter('admin'))
async def user(msg:Message,db):
    users= await db.get_users()
    await msg.answer("Foydalanuvchilar ro'yxati: ",reply_markup=users_inline(users))

@router.callback_query(F.data.startswith("user_"),RoleFilter('admin'))
async def user(call:CallbackQuery):
    user_id= int(call.data.split("_")[1]) #["user","16"]
    await call.message.answer("User rolini tanlang: ",reply_markup=user_action(user_id))
    await call.answer()

@router.callback_query(F.data.startswith("changeto_"),RoleFilter('admin'))
async def user(call:CallbackQuery,db): 
    _,role,user_id=call.data.split("_")
    user_id=int(user_id)
    await db.update_role(user_id,role)
    await call.message.answer("Role o'zgartirildi!")
    await call.answer()


async def broadcasting(bot, users, message):
    success = 0
    failed = 0
    for user_id in users:
        try:

            # Rasm + matn
            if message.photo:
                await bot.send_photo(
                    chat_id=int(user_id["telegram_id"]),
                    photo=message.photo[-1].file_id,
                    caption=message.caption
                )

            # Video + matn
            elif message.video:
                await bot.send_video(
                    chat_id=user_id,
                    video=message.video.file_id,
                    caption=message.caption
                )
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=message.text
                )

            success += 1

        except Exception:
            failed += 1

    return success, failed

@router.message(F.text == "Reklama", RoleFilter("admin"))
async def reklama(msg: Message, state: FSMContext):
    
    await msg.answer("📢 Reklama yuborish uchun rasm, video yoki matn yuboring:")
    
    await state.set_state(AdsState.waiting_for_ads)

@router.message(AdsState.waiting_for_ads)
async def reklama(msg:Message,state:FSMContext,db):
    users= await db.get_users_telegram_id()
    message=msg
    success, failed = await broadcasting(
        msg.bot,
        users,
        message
    )

    await msg.answer(
        f"📊 Reklama natijasi:\n"
        f"✅ Yuborildi: {success}\n"
        f"❌ Yuborilmadi: {failed}"
    )
    await state.clear()