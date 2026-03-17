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
    ContextTypes,
    filters
)

# ================= KEEP ALIVE =================

web = Flask(__name__)

@web.route("/")
def home():
    return "Bot Running"

def run():
    web.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================= CONFIG =================

BOT_TOKEN = "8740780011:AAHbnPoUV_4C6JGULWVQgOAvbvW96gkqEYo"

API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"

USERNAME = "rafiqmolla7"

PID = "0257"

BASE_URL = "https://api.durianrcs.com"

ADMIN_ID = 8081334307

SUPPORT_LINK = "https://t.me/Sojib9690"

ALLOWED_USERS = {
6528471341:"Sojib",
8081334307:"Sojib Das",
8181512467:"Admin",
8164389661:"pc",
6630618306:"Chandon"
}

# ================= MENU =================

keyboard = [
["📊 Status","👥 Users"],
["⚙️ Settings","📞 Support"]
]

menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= START =================

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in ALLOWED_USERS:

        button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Support Admin",url=SUPPORT_LINK)]]
        )

        await update.message.reply_text(
"""Access Denied

Contact admin to get access.""",
reply_markup=button)

        return

    name = ALLOWED_USERS[user]

    await update.message.reply_text(
f"Welcome {name}\nBot is ready.",
reply_markup=menu)

# ================= SUPPORT =================

async def support(update:Update,context:ContextTypes.DEFAULT_TYPE):

    button = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Open Support",url=SUPPORT_LINK)]]
    )

    await update.message.reply_text(
"Click the button below",
reply_markup=button)

# ================= USER LIST =================

async def users(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text="Allowed Users\n\n"

    for uid,name in ALLOWED_USERS.items():

        text+=f"{name} - {uid}\n"

    await update.message.reply_text(text)

# ================= ADD USER =================

async def adduser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    uid=int(context.args[0])
    name=" ".join(context.args[1:])

    ALLOWED_USERS[uid]=name

    await update.message.reply_text(
f"User Added: {name}"
)

# ================= REMOVE USER =================

async def removeuser(update:Update,context:ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    uid=int(context.args[0])

    if uid in ALLOWED_USERS:

        del ALLOWED_USERS[uid]

        await update.message.reply_text(
"User Removed"
)

# ================= MESSAGE HANDLER =================

async def handle(update:Update,context:ContextTypes.DEFAULT_TYPE):

    user=update.effective_user.id

    if user not in ALLOWED_USERS:
        return

    text=update.message.text

    if text=="📊 Status":

        await update.message.reply_text("Bot Running")

    elif text=="👥 Users":

        await users(update,context)

    elif text=="⚙️ Settings":

        await update.message.reply_text("Settings panel")

    elif text=="📞 Support":

        await support(update,context)

# ================= MAIN =================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("adduser",adduser))
app.add_handler(CommandHandler("removeuser",removeuser))

app.add_handler(MessageHandler(filters.TEXT,handle))

print("BOT RUNNING")

keep_alive()

app.run_polling()
