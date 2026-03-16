import requests
import asyncio
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIG =================

BOT_TOKEN = "8740780011:AAFTVCQL58jQiANZTwgienk9-Vi_sTDYPHk"

API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"
USERNAME = "rafiqmolla7"
PID = "0257"

BASE_URL = "https://api.durianrcs.com/out/ext_api"

ADMIN_ID = 8081334307

GROUP_ID = -1003525081102

# Allowed users (Name + ID)
ALLOWED_USERS = {
6528471341:"Sojib",
8081334307:"Sojib Das",
8181512467:"Admin",
8164389661:"pc",
6630618306:"Chandon"
}

sessions = {}

# ================= KEYBOARD =================

keyboard = [
["📱 Get Number"],
["📩 Check OTP","❌ Cancel"],
["💰 Balance"]
]

markup = ReplyKeyboardMarkup(keyboard,resize_keyboard=True)

# ================= START =================

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if user_id not in ALLOWED_USERS:

        button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Support Admin",url="https://t.me/8081334307")]]
        )

        await update.message.reply_text(
"""বিশ্বাসঘাতককে আবার বিশ্বাস করা
আর অন্ধকার শহরে আয়না বিক্রি করা একই কথা..

ধন্যবাদ
🥱☠""",
reply_markup=button)

        return

    name = ALLOWED_USERS[user_id]

    await update.message.reply_text(
f"Welcome {name}\nOTP BOT READY",
reply_markup=markup)

# ================= BALANCE =================

async def balance(update:Update):

    url=f"{BASE_URL}/getUserInfo?name={USERNAME}&ApiKey={API_KEY}"

    r=requests.get(url).json()

    if r["code"]==200:

        bal=r["data"]["money"]

        await update.message.reply_text(f"Balance: {bal}")

# ================= GET NUMBER =================

async def get_number(update:Update):

    user=update.effective_user.id

    url=f"{BASE_URL}/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PID}&cuy=SS"

    r=requests.get(url).json()

    if r["code"]==200:

        number=r["data"]

        sessions[user]=number

        await update.message.reply_text(
        f"Number: {number}\nWaiting OTP..."
        )

        asyncio.create_task(auto_check(update,number))

    else:

        await update.message.reply_text("No number available")

# ================= AUTO OTP =================

async def auto_check(update,number):

    for i in range(30):

        await asyncio.sleep(5)

        url=f"{BASE_URL}/getMessage?name={USERNAME}&ApiKey={API_KEY}&phone={number}"

        r=requests.get(url).json()

        if r["code"]==200:

            otp=r["data"]

            text=f"Number: {number}\nOTP: {otp}"

            await update.message.reply_text(text)

            await context.bot.send_message(
            chat_id=GROUP_ID,
            text=text)

            return

# ================= CHECK OTP =================

async def check_otp(update:Update):

    user=update.effective_user.id

    if user not in sessions:

        await update.message.reply_text("No active number")

        return

    number=sessions[user]

    url=f"{BASE_URL}/getMessage?name={USERNAME}&ApiKey={API_KEY}&phone={number}"

    r=requests.get(url).json()

    if r["code"]==200:

        otp=r["data"]

        await update.message.reply_text(f"OTP: {otp}")

# ================= CANCEL =================

async def cancel(update:Update):

    user=update.effective_user.id

    if user not in sessions:

        await update.message.reply_text("No active number")

        return

    number=sessions[user]

    url=f"{BASE_URL}/cancelMobile?name={USERNAME}&ApiKey={API_KEY}&phone={number}"

    requests.get(url)

    del sessions[user]

    await update.message.reply_text("Number cancelled")

# ================= ADMIN ADD USER =================

async def adduser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    user_id=int(context.args[0])
    name=context.args[1]

    ALLOWED_USERS[user_id]=name

    await update.message.reply_text(f"User Added: {name}")

# ================= ADMIN REMOVE USER =================

async def removeuser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    user_id=int(context.args[0])

    if user_id in ALLOWED_USERS:

        del ALLOWED_USERS[user_id]

        await update.message.reply_text("User removed")

# ================= HANDLER =================

async def handle(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user.id

    if user not in ALLOWED_USERS:
        return

    text=update.message.text

    if text=="📱 Get Number":

        await get_number(update)

    elif text=="📩 Check OTP":

        await check_otp(update)

    elif text=="❌ Cancel":

        await cancel(update)

    elif text=="💰 Balance":

        await balance(update)

# ================= MAIN =================

app=ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))

app.add_handler(CommandHandler("adduser",adduser))
app.add_handler(CommandHandler("removeuser",removeuser))

app.add_handler(MessageHandler(filters.TEXT,handle))

print("BOT RUNNING")

app.run_polling()
