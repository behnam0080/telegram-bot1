import os
import threading
import traceback
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from keep_alive import run  # فایل keep_alive.py باید در پروژه باشد

# 📢 کانالی که عضویت در آن اجباری است
CHANNEL_USERNAME = "@accept_gp"                
CHANNEL_LINK = "https://t.me/accept_gp"        

# 🎬 دیتابیس فیلم‌ها (هر فیلم: عنوان + توضیح + لینک عکس)
films_by_genre = {
    "اکشن": [
        {"title": "چ", "desc": "به کارگردانی ابراهیم حاتمی‌کیا درباره شهید چمران.", "image": "https://upload.wikimedia.org/wikipedia/fa/8/82/Che_film.jpg"},
        {"title": "متری شیش و نیم", "desc": "درامی پلیسی با موضوع مواد مخدر.", "image": "https://upload.wikimedia.org/wikipedia/fa/f/f3/Metri_ShiishoNim.jpg"},
        {"title": "قاتل اهلی", "desc": "فیلمی از مسعود کیمیایی با محوریت مسائل اجتماعی.", "image": "https://upload.wikimedia.org/wikipedia/fa/3/31/Ghatel_Ahli.jpg"},
    ],
    "درام": [
        {"title": "جدایی نادر از سیمین", "desc": "برنده اسکار بهترین فیلم خارجی زبان.", "image": "https://upload.wikimedia.org/wikipedia/fa/c/c1/A_Separation_Poster.jpg"},
        {"title": "ابد و یک روز", "desc": "روایتی تلخ از فقر و مشکلات خانوادگی.", "image": "https://upload.wikimedia.org/wikipedia/fa/4/47/AbadO_Yek_Rooz.jpg"},
        {"title": "درباره الی", "desc": "فیلمی معمایی و پرمخاطب از اصغر فرهادی.", "image": "https://upload.wikimedia.org/wikipedia/fa/b/b9/Darbareye_Elly_poster.jpg"},
    ],
    "کمدی": [
        {"title": "مارمولک", "desc": "کمدی اجتماعی محبوب کمال تبریزی.", "image": "https://upload.wikimedia.org/wikipedia/fa/7/76/Marmoolak_movie.jpg"},
        {"title": "اخراجی‌ها", "desc": "کمدی جنگی پرمخاطب دهه ۸۰.", "image": "https://upload.wikimedia.org/wikipedia/fa/d/dc/Ekhrajiha_poster.jpg"},
        {"title": "هزارپا", "desc": "یکی از پرفروش‌ترین کمدی‌های تاریخ سینمای ایران.", "image": "https://upload.wikimedia.org/wikipedia/fa/a/a7/Hezarpa_poster.jpg"},
    ],
}

# حافظه ساده برای کاربران
user_started = set()

# 📌 بررسی عضویت
async def is_subscribed(user_id, bot):
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

# 📌 منوی ژانرها
def genre_menu():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(genre, callback_data=genre)] for genre in films_by_genre]
    )

# 📌 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not await is_subscribed(user_id, context.bot):
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✔ بررسی عضویت", callback_data="check_subscription")]
        ]
        await update.message.reply_text(
            "👋 خوش اومدی!\n\nبرای استفاده از ربات باید اول عضو کانال زیر بشی ⬇️",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    if user_id not in user_started:
        user_started.add(user_id)
        await update.message.reply_text(
            "👋 خوش اومدی! این اولین باره که وارد ربات شدی.\n"
            "اینجا می‌تونی ژانر فیلم مورد علاقه‌ات رو انتخاب کنی 🎬"
        )
    else:
        await update.message.reply_text("😊 دوباره خوش اومدی!")

    await update.message.reply_text("ژانر مورد علاقه‌ات رو انتخاب کن:", reply_markup=genre_menu())

# 📌 بررسی دوباره عضویت
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if not await is_subscribed(user_id, context.bot):
        keyboard = [
            [InlineKeyboardButton("📢 عضویت در کانال", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✔ بررسی مجدد", callback_data="check_subscription")]
        ]
        await query.edit_message_text(
            "⛔️ هنوز عضو کانال نشدی! لطفاً اول عضو کانال شو و دوباره امتحان کن.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await query.edit_message_text("✅ عضویتت تایید شد! حالا می‌تونی از امکانات ربات استفاده کنی.")
        await query.message.reply_text("ژانر مورد علاقه‌ات رو انتخاب کن:", reply_markup=genre_menu())

# 📌 انتخاب ژانر (ارسال عکس + توضیح)
async def genre_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    genre = query.data
    await query.edit_message_text(text=f"✅ ژانر انتخابی: {genre}")

    for film in films_by_genre[genre]:
        await context.bot.send_photo(
            chat_id=query.message.chat_id,
            photo=film["image"],
            caption=f"{film['title']}\n\n{film['desc']}"
        )

    keyboard = [[InlineKeyboardButton("🔙 بازگشت به انتخاب ژانر", callback_data="back_to_genres")]]
    await context.bot.send_message(
        chat_id=query.message.chat_id,
        text="⬇️ اگر می‌خوای به منوی ژانرها برگردی:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# 📌 بازگشت به ژانرها
async def back_to_genres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🎭 دوباره ژانر مورد علاقه‌ات رو انتخاب کن:", reply_markup=genre_menu())

# 📌 /genres
async def genres(update: Update, context: ContextTypes.DEFAULT_TYPE):
    genres_list = "\n".join([f"- {g}" for g in films_by_genre.keys()])
    await update.message.reply_text(f"🎭 لیست ژانرها:\n{genres_list}")

# 📌 اجرای برنامه
if __name__ == "__main__":
    TOKEN = os.getenv("BOT_TOKEN")
    if not TOKEN:
        print("❌ ERROR: BOT_TOKEN environment variable is not set. Set it in Render (Environment).")
        raise SystemExit(1)

    threading.Thread(target=run, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("genres", genres))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="^check_subscription$"))
    app.add_handler(CallbackQueryHandler(genre_selected, pattern="^(اکشن|درام|کمدی)$"))
    app.add_handler(CallbackQueryHandler(back_to_genres, pattern="^back_to_genres$"))

    try:
        print("✅ ربات در حال اجراست...")
        app.run_polling()
    except Exception:
        print("❌ ERROR: exception while running bot:")
        traceback.print_exc()
