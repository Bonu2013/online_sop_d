from aiogram import Router,F
from aiogram.types import Message
from aiogram.filters import CommandStart
from keyboards.reply import register,start_reply,start_reply_admin
from filters.adminfilter import RoleFilter


router=Router()

@router.message(CommandStart(),RoleFilter('admin'))
async def start_handler(msg:Message,):
        await msg.answer("Assalomu Alaykum admin botga xush kelibsz!",reply_markup=start_reply_admin())

@router.message(CommandStart())
async def start_handler(msg:Message,db):
    if await db.is_user_exists(msg.from_user.id):
        await msg.answer("Assalomu Alaykum botga xush kelibsz!,\nSiz avval ro'yxatdan o'tgansiz:",reply_markup=start_reply())
    else:
        await msg.answer("Assalomu Alaykum botga xush kelibsz!,\nIltimos ro'yxatdan o'ting:",reply_markup=register())