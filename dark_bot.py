import asyncio
import requests
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

API_KEY = "bHVuKzA5QW5DZjl5eEVadnBxUnlzdz09"
USERNAME = "rafiqmolla7"
PROJECT_ID = "0257"

COUNTRY = "SS"

# ================= MENU =================

keyboard = [
["📱 Get Number"],
["🆔 My ID","💰 Balance"]
]

menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= START =================

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
"✅ South Sudan OTP Bot Ready 🇸🇸",
reply_markup=menu)

# ================= GET NUMBER =================

async def get_number(update:Update, context:ContextTypes.DEFAULT_TYPE):

    msg = await update.message.reply_text("⚡ Getting South Sudan number...")

    for i in range(10):

        try:
            url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&c=SS"
            res = requests.get(url, timeout=10).json()

            if res["code"] != 200 or not res["data"]:
                continue

            number = str(res["data"])

            # ✅ only +211
            if not number.startswith("+211"):
                continue

            clean_number = number.replace("+","")

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel|{clean_number}"),
                    InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{clean_number}")
                ]
            ])

            await msg.edit_text(
                f"📱 South Sudan Number:\n`{number}`",
                parse_mode="Markdown",
                reply_markup=buttons
            )

            asyncio.create_task(fetch_otp(msg, number, clean_number))
            return

        except:
            pass

    await msg.edit_text("❌ No valid South Sudan number found")

# ================= OTP =================

async def fetch_otp(msg, show_number, clean_number):

    url = f"https://api.durianrcs.com/out/ext_api/getMessage?name={USERNAME}&ApiKey={API_KEY}&pn={clean_number}&pid={PROJECT_ID}"

    for i in range(60):

        try:
            res = requests.get(url, timeout=6).json()

            if res.get("data"):
                otp = res["data"]

                await msg.edit_text(
                    f"📱 {show_number}\n\n🔐 OTP:\n`{otp}`",
                    parse_mode="Markdown"
                )
                return

        except:
            pass

        await asyncio.sleep(3)

    await msg.edit_text(f"📱 {show_number}\n⌛ OTP not received")

# ================= BUTTON =================

async def button_click(update:Update, context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")

    if data[0] == "cancel":
        await query.edit_message_text("❌ Number Cancelled")

    elif data[0] == "black":
        await query.edit_message_text("🚫 Blacklisted")

# ================= HANDLER =================

async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):

    text = update.message.text

    if text == "📱 Get Number":
        await get_number(update, context)

    elif text == "🆔 My ID":
        await update.message.reply_text(f"🆔 {update.effective_user.id}")

    elif text == "💰 Balance":
        await update.message.reply_text("💰 Checking...")

# ================= MAIN =================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))
app.add_handler(CallbackQueryHandler(button_click))

print("BOT RUNNING 🇸🇸")

keep_alive()
app.run_polling()
