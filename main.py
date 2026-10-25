import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)

# بيانات البوت المستلمة
TOKEN = "8622474758:AAFcIwB0EOHK1luEnYig6yxE4ZxmbU0XOxo"
ADMIN_ID = 1056007305  # آيدي الأدمن

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

# قاعدة بيانات مؤقتة في الذاكرة (يمكن ربطها بقاعدة بيانات لاحقاً)
PRODUCTS = [
    {
        "id": 1,
        "name": "ملفات الاستخبارات العسكرية",
        "price_sar": 50,
        "desc": "ملفات سرية ومهمة للتحليل العسكري",
        "link": "https://t.me/+example_group_link",
        "image": "https://images.unsplash.com/photo-1541872703-74c5e44368f9",
    }
]
REVIEWS = [
    {
        "user": "أبو فهد",
        "text": "متجر ممتاز وملفات دقيقة جداً!",
        "rating": "⭐⭐⭐⭐⭐",
    }
]
USERS = [ADMIN_ID]  # لتخزين محادثات العملاء لإرسال الرسائل الجماعية


class AddProduct(StatesGroup):
    name = State()
    price = State()
    desc = State()
    link = State()
    image = State()


class BroadcastState(StatesGroup):
    message = State()


# أمر البدء ولائحة الترحيب وتطبيق الويب المصغر
@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id not in USERS:
        USERS.append(message.from_user.id)

    # زر فتح المتجر المصغّر كـ Mini App
    web_app_url = (
        "https://your-render-app-name.onrender.com"  # استبدله برابط موقعك على ريندر
    )
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🛍️ فتح متجر العاقل",
                    web_app=WebAppInfo(url=web_app_url),
                )
            ]
        ]
    )
    await message.answer(
        "مرحباً بك في *متجر العاقل* للملفات العسكرية 🎖️\nاضغط بالأسفل لفتح المتجر:",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


# لوحة تحكم الأدمن
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("عذراً، هذا الأمر خاص بالأدمن فقط.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ إضافة منتج", callback_data="add_product"
                ),
                InlineKeyboardButton(
                    text="⚙️ تعديل/حذف منتج", callback_data="manage_products"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📢 رسالة جماعية", callback_data="broadcast"
                ),
                InlineKeyboardButton(
                    text="⭐ إدارة التقييمات", callback_data="manage_reviews"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📊 إحصائية الطلبات", callback_data="stats"
                )
            ],
        ]
    )
    await message.answer("لوحة تحكم الأدمن لمتجر العاقل:", reply_markup=keyboard)


# بدء إضافة منتج جديد
@router.callback_query(F.data == "add_product")
async def start_add_product(callback: callback_query, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.message.answer("أدخل اسم المنتج الجديد:")
    await state.set_state(AddProduct.name)
    await callback.answer()


@router.message(AddProduct.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "أدخل سعر المنتج بالريال السعودي (سيتم تحويله تلقائياً لنجوم تيليجرام):"
    )
    await state.set_state(AddProduct.price)


@router.message(AddProduct.price)
async def process_price(message: Message, state: FSMContext):
    try:
        price_sar = float(message.text)
        # المعادلة التقريبية: كل 1 ريال = تقريباً 2.5 نجمة أو حسب السعر المعتمد (مثلاً 1 ريال = 2 نجمة)
        stars = int(price_sar * 2)
        await state.update_data(price_sar=price_sar, stars=stars)
        await message.answer(
            f"السعر بالريال: {price_sar} ر.س\nما يعادله بنجوم تيليجرام: 🌟 {stars} نجمة\n\nالآن أدخل وصف المنتج:"
        )
        await state.set_state(AddProduct.desc)
    except ValueError:
        await message.answer("الرجاء إدخال رقم صحيح للسعر.")


@router.message(AddProduct.desc)
async def process_desc(message: Message, state: FSMContext):
    await state.update_data(desc=message.text)
    await message.answer("أدخل رابط قروب الملفات الذي سيحصل عليه الزبون عند الشراء:")
    await state.set_state(AddProduct.link)


@router.message(AddProduct.link)
async def process_link(message: Message, state: FSMContext):
    await state.update_data(link=message.text)
    await message.answer("أرسل صورة المنتج الآن (كملف صورة مرفقة):")
    await state.set_state(AddProduct.image)


@router.message(AddProduct.image, F.photo)
async def process_image(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.get_data()

    new_product = {
        "id": len(PRODUCTS) + 1,
        "name": data["name"],
        "price_sar": data["price_sar"],
        "stars": data["stars"],
        "desc": data["desc"],
        "link": data["link"],
        "image": photo_id,
    }
    PRODUCTS.append(new_product)
    await state.clear()

    await message.answer(
        f"✅ تمت إضافة المنتج بنجاح!\n⭐ السعر بالنجوم: {data['stars']} نجمة"
    )

    # إرسال رسالة جماعية للزبائن بالمنتج الجديد تلقائياً
    for user_id in USERS:
        try:
            await bot.send_message(
                user_id,
                f"🚨 *منتج عسكري جديد في متجر العاقل!\n\n📌 *{data['name']}**\n💰 السعر: {data['price_sar']} ر.س (🌟 {data['stars']} نجمة)\n📝 {data['desc']}",
                parse_mode="Markdown",
            )
        except Exception:
            pass


# إحصائيات الطلبات والأدمن
@router.callback_query(F.data == "stats")
async def show_stats(callback: callback_query):
    await callback.message.answer(
        f"📊 *إحصائيات متجر العاقل:*\n\n- عدد المنتجات الحالية: {len(PRODUCTS)}\n- إجمالي العملاء المسجلين: {len(USERS)}\n- إجمالي الطلبات: 0 طلب",
        parse_mode="Markdown",
    )
    await callback.answer()


async def main():
    dp.include_router(router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if _name_ == "_main_":
    asyncio.run(main())