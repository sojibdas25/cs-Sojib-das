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

ADMIN_ID = 8081334307

ALLOWED_USERS = {
    6528471341: "Sojib",
    8081334307: "Sojib Das",
    8181512467: "Admin",
    8164389661: "pc",
    6630618306: "Chandon"
}

SEEN_USERS = set()

# ================= MENU =================

keyboard = [
["📱 Get Number"],
["🆔 My ID","💰 Balance"]
]

menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= START =================

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    name = update.effective_user.first_name

    # notify admin
    if user not in SEEN_USERS:
        SEEN_USERS.add(user)
        await context.bot.send_message(
            ADMIN_ID,
            f"🚨 New User:\nID: {user}\nName: {name}"
        )

    if user not in ALLOWED_USERS:

        button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Contact Admin", url="https://t.me/Sojib9690")]]
        )

        await update.message.reply_text(
f"""❌ Access Denied

Your ID: {user}
Admin approval required""",
reply_markup=button
        )
        return

    await update.message.reply_text(
f"""✅ Welcome {ALLOWED_USERS[user]}

🔥 CS Dark SMS System Ready""",
reply_markup=menu
    )

# ================= FAST GET NUMBER =================

async def get_number(update:Update, context:ContextTypes.DEFAULT_TYPE):

    msg = await update.message.reply_text("⚡ Getting South Sudan number...")

    for i in range(15):  # more retry = faster success

        try:
            url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&c=SS"
            res = requests.get(url, timeout=8).json()

            if res["code"] != 200 or not res["data"]:
                continue

            number = str(res["data"])

            if not number.startswith("+211"):
                continue

            clean = number.replace("+","")

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("❌ Cancel", callback_data=f"cancel|{clean}"),
                    InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{clean}")
                ]
            ])

            await msg.edit_text(
                f"📱 South Sudan Number:\n`{number}`",
                parse_mode="Markdown",
                reply_markup=buttons
            )

            asyncio.create_task(fetch_otp(msg, number, clean))
            return

        except:
            pass

    await msg.edit_text("❌ No valid number found")

# ================= OTP FIX (SUPER FAST) =================

async def fetch_otp(msg, number, clean):

    url = f"https://api.durianrcs.com/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={clean}&pid={PROJECT_ID}"

    for i in range(80):  # long + fast check

        try:
            res = requests.get(url, timeout=5).json()

            if res.get("data") and res["data"] != "":

                otp = res["data"]

                await msg.edit_text(
                    f"📱 {number}\n\n🔐 OTP:\n`{otp}`",
                    parse_mode="Markdown"
                )
                return

        except:
            pass

        await asyncio.sleep(2)  # FAST CHECK

    await msg.edit_text(f"📱 {number}\n⌛ OTP not received")

# ================= BUTTON =================

async def button_click(update:Update, context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")

    if data[0] == "cancel":
        await query.edit_message_text("❌ Number Cancelled")

    elif data[0] == "black":
        await query.edit_message_text("🚫 Blacklisted")

# ================= ADMIN =================

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not admin")
        return

    try:
        user_id = int(context.args[0])
        name = " ".join(context.args[1:]) or f"User{user_id}"

        ALLOWED_USERS[user_id] = name

        await update.message.reply_text(f"✅ Approved: {name} ({user_id})")

        await context.bot.send_message(
            user_id,
            f"🎉 Approved as {name}\nSend /start"
        )

    except:
        await update.message.reply_text("Use: /approve user_id name")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    try:
        user_id = int(context.args[0])

        if user_id in ALLOWED_USERS:
            name = ALLOWED_USERS[user_id]
            del ALLOWED_USERS[user_id]

            await update.message.reply_text(f"❌ Removed: {name}")

    except:
        pass

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 Users:\n\n"

    for uid, name in ALLOWED_USERS.items():
        text += f"{name} → `{uid}`\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# ================= HANDLER =================

async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in ALLOWED_USERS:
        return

    text = update.message.text

    if text == "📱 Get Number":
        await get_number(update, context)

    elif text == "🆔 My ID":
        await update.message.reply_text(f"🆔 {user}")

    elif text == "💰 Balance":
        await update.message.reply_text("💰 Checking...")

# ================= MAIN =================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("remove", remove_user))
app.add_handler(CommandHandler("users", list_users))

app.add_handler(MessageHandler(filters.TEXT, handle))
app.add_handler(CallbackQueryHandler(button_click))

print("🔥 CS DARK SMS BOT RUNNING 🔥")

keep_alive()
app.run_polling()
