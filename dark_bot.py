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

SUPPORT_LINK = "https://t.me/Sojib9690"

COUNTRY = "SS"  # ✅ ONLY South Sudan

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
["🆔 My ID","💰 Balance"]
]

menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= START =================

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in ALLOWED_USERS:
        button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Contact Admin", url=SUPPORT_LINK)]]
        )

        await update.message.reply_text(
"❌ Access Denied",
reply_markup=button)
        return

    name = ALLOWED_USERS[user]

    await update.message.reply_text(
f"✅ Welcome {name}\nSouth Sudan OTP Bot Ready 🇸🇸",
reply_markup=menu)

# ================= GET NUMBER =================

async def get_number(update:Update, context:ContextTypes.DEFAULT_TYPE):

    msg = await update.message.reply_text("⚡ Getting South Sudan number...")

    url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&c={COUNTRY}"

    try:
        res = requests.get(url, timeout=10).json()

        if res["code"] != 200 or not res["data"]:
            await msg.edit_text("❌ No number available")
            return

        number = str(res["data"])
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

        # 🔥 OTP AUTO START
        asyncio.create_task(fetch_otp(msg, number, clean_number))

    except:
        await msg.edit_text("❌ API Error")

# ================= OTP FETCH =================

async def fetch_otp(msg, show_number, clean_number):

    url = f"https://api.durianrcs.com/out/ext_api/getMessage?name={USERNAME}&ApiKey={API_KEY}&pn={clean_number}&pid={PROJECT_ID}"

    for i in range(60):  # 🔥 Long wait = OTP miss হবে না

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

# ================= MY ID =================

async def my_id(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🆔 {update.effective_user.id}")

# ================= BALANCE =================

async def balance(update:Update, context:ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Checking...")

# ================= HANDLER =================

async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    if user not in ALLOWED_USERS:
        return

    text = update.message.text

    if text == "📱 Get Number":
        await get_number(update, context)

    elif text == "🆔 My ID":
        await my_id(update, context)

    elif text == "💰 Balance":
        await balance(update, context)

# ================= MAIN =================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle))
app.add_handler(CallbackQueryHandler(button_click))

print("STRONG SS BOT RUNNING 🇸🇸")

keep_alive()
app.run_polling()
