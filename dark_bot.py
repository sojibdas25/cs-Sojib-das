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

API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"
USERNAME = "rafiqmolla7"
PROJECT_ID = "0257"

SUPPORT_LINK = "https://t.me/Sojib9690"

COUNTRY = "SS"

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
        [[InlineKeyboardButton("Contact Admin", url=SUPPORT_LINK)]]
        )

        await update.message.reply_text(
"❌ Access Denied\nAdmin approval required",
reply_markup=button)
        return

    await update.message.reply_text("✅ Bot Ready", reply_markup=menu)

# ================= COUNTRY =================

async def show_country(update:Update, context:ContextTypes.DEFAULT_TYPE):

    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇸🇸 South Sudan", callback_data="set|SS"),
            InlineKeyboardButton("🇱🇨 Saint Lucia", callback_data="set|LC")
        ]
    ])

    await update.message.reply_text("🌍 Select Country:", reply_markup=buttons)

# ================= FAST GET NUMBER =================

async def get_number(update:Update, context:ContextTypes.DEFAULT_TYPE):

    msg = await update.message.reply_text("⚡ Fetching ultra fast number...")

    for i in range(3):  # 🔥 Auto retry 3 times

        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&c={COUNTRY}"

        try:
            res = requests.get(url, timeout=8).json()

            if res["code"] == 200 and res["data"]:
                number = res["data"]

                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel|{number}"),
                        InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{number}")
                    ]
                ])

                await msg.edit_text(
                    f"📱 Number ({COUNTRY}):\n`{number}`",
                    parse_mode="Markdown",
                    reply_markup=buttons
                )

                # 🔥 START OTP (background)
                asyncio.create_task(fetch_otp(update, context, number, msg))

                return

        except:
            pass

        await asyncio.sleep(1)

    await msg.edit_text("❌ No number available (Try again)")

# ================= ULTRA FAST OTP =================

async def fetch_otp(update, context, number, msg):

    url = f"https://api.durianrcs.com/out/ext_api/getMessage?name={USERNAME}&ApiKey={API_KEY}&pn={number}&pid={PROJECT_ID}"

    for i in range(25):  # 🔥 Fast polling

        try:
            res = requests.get(url, timeout=6).json()

            if res["code"] == 200 and res["data"]:
                otp = res["data"]

                await msg.edit_text(
                    f"📱 Number: `{number}`\n\n🔐 OTP:\n`{otp}`",
                    parse_mode="Markdown"
                )
                return

        except:
            pass

        await asyncio.sleep(2)  # 🔥 faster check

    await msg.edit_text(f"📱 `{number}`\n⌛ OTP Timeout")

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
        await query.edit_message_text("❌ Cancelled")

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

print("ULTRA FAST BOT RUNNING 🚀")

keep_alive()
app.run_polling()
