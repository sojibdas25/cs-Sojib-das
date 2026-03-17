import asyncio
from flask import Flask
from threading import Thread

from telegram import (
    Update,
    ReplyKeyboardMarkup,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# ================= KEEP ALIVE =================

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot Running"

def run():
    app_web.run(host='0.0.0.0', port=10000)

def keep_alive():
    Thread(target=run).start()

# ================= CONFIG =================

BOT_TOKEN = "8740780011:AAHbnPoUV_4C6JGULWVQgOAvbvW96gkqEYo"

API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"

USERNAME = "rafiqmolla7"

PID = "0257"

BASE_URL = "https://api.durianrcs.com"
ADMIN_ID = 8081334307
SUPPORT_LINK = "https://t.me/Sojib9690"

COUNTRY = "SS"

# ✅ Allowed Users
ALLOWED_USERS = {
6528471341:"Sojib",
8081334307:"Sojib Das",
8181512467:"Admin",
8164389661:"pc",
6630618306:"Chandon"
}

# ================= MENU =================

keyboard = [
["📱 Get Number"],
["🌍 Country"],
["🆔 My ID","💰 Balance"]
]

menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= START =================

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in ALLOWED_USERS:

        button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Support Admin", url=SUPPORT_LINK)]]
        )

        await update.message.reply_text(
"""বিশ্বাসঘাতককে আবার বিশ্বাস করা
আর অন্ধকার শহরে আয়না বিক্রি করা একই কথা..

ধন্যবাদ
🥱☠""",
reply_markup=button)

        return

    name = ALLOWED_USERS[user]

    await update.message.reply_text(
f"Welcome {name}\nBot Ready",
reply_markup=menu)

# ================= COUNTRY =================

async def show_country(update:Update, context:ContextTypes.DEFAULT_TYPE):

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇸🇸 South Sudan", callback_data="set|SS"),
            InlineKeyboardButton("🇱🇨 Saint Lucia", callback_data="set|LC")
        ]
    ])

    await update.message.reply_text("🌍 Select Country:", reply_markup=buttons)

# ================= GET NUMBER =================

async def get_number(update:Update, context:ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text("⏳ Getting number...")

    await asyncio.sleep(2)
    number = "1234567890"  # 👉 এখানে API বসাবে

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel|{number}"),
            InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{number}")
        ]
    ])

    await update.message.reply_text(
        f"📱 Number:\n`{number}`",
        parse_mode="Markdown",
        reply_markup=buttons
    )

# ================= BUTTON =================

async def button_click(update:Update, context:ContextTypes.DEFAULT_TYPE):

    global COUNTRY

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")

    if data[0] == "set":
        COUNTRY = data[1]
        await query.edit_message_text(f"🌍 Country set: {COUNTRY}")

    elif data[0] == "cancel":
        await query.edit_message_text("❌ Number Cancelled")

    elif data[0] == "black":
        await query.edit_message_text("🚫 Blacklisted")

# ================= MY ID =================

async def my_id(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 ID: {update.effective_user.id}")

# ================= BALANCE =================

async def balance(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Checking balance...")

# ================= HANDLER =================

async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in ALLOWED_USERS:
        return

    text = update.message.text

    if text == "📱 Get Number":
        await get_number(update, context)

    elif text == "🌍 Country":
        await show_country(update, context)

    elif text == "🆔 My ID":
        await my_id(update, context)

    elif text == "💰 Balance":
        await balance(update, context)

# ================= MAIN =================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))
app.add_handler(CallbackQueryHandler(button_click))

print("BOT RUNNING")

keep_alive()
app.run_polling()
