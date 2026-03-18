import asyncio
import aiohttp
from flask import Flask
from threading import Thread

from telegram import *
from telegram.ext import *

# ================= KEEP ALIVE =================

app_web = Flask(__name__)

@app_web.route('/')
def home():
    return "Bot Running"

@app_web.route('/ping')
def ping():
    return "pong"

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
    6630618306: "Chandon",
    8477306760: " Ridoy Sarkar",
    8050716664: "Bolay Kumar",
    8107209599: "PS. SUPOT KUMAR",
    1830287857: "AK Anonto",
    5257295219: "Kanok Kumar"
}

COUNTRIES = {
    "🇸🇸 South Sudan": "SS",
    "🇸🇿 Eswatini": "SZ"
}

SEEN_USERS = set()
# ================= MENU =================

menu = ReplyKeyboardMarkup([
["📱 Get Number"],
["🆔 My ID"]
], resize_keyboard=True)

# ================= START =================

async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    name = update.effective_user.first_name

    if user not in SEEN_USERS:
        SEEN_USERS.add(user)
        await context.bot.send_message(ADMIN_ID,f"🚨 New User\n{user} | {name}")

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

    await update.message.reply_text(f"✅ Welcome {ALLOWED_USERS[user]}", reply_markup=menu)

# ================= COUNTRY SELECT =================

async def get_number(update:Update, context:ContextTypes.DEFAULT_TYPE):

    buttons = []

    for name in COUNTRIES:
        buttons.append([InlineKeyboardButton(name, callback_data=f"get|{name}")])

    await update.message.reply_text("🌍 Select Country:", reply_markup=InlineKeyboardMarkup(buttons))

# ================= FAST GET =================

async def button_click(update:Update, context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")

    if data[0] == "get":

        name = data[1]
        country = COUNTRIES[name]

        msg = await query.edit_message_text(f"⚡ Getting {name}...")

        async with aiohttp.ClientSession() as session:

            for _ in range(3):

                try:
                    url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy={country}"

                    async with session.get(url, timeout=6) as resp:
                        res = await resp.json()

                    if res.get("code") != 200 or not res.get("data"):
                        continue

                    number = str(res["data"])
                    clean = number.replace("+","")

                    buttons = InlineKeyboardMarkup([
                        [
                            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel"),
                            InlineKeyboardButton("🚫 Blacklist", callback_data=f"black")
                        ]
                    ])

                    await msg.edit_text(
                        f"🌍 {name}\n📱 `{number}`\n⏳ Waiting OTP...",
                        parse_mode="Markdown",
                        reply_markup=buttons
                    )

                    asyncio.create_task(fetch_otp(msg, number, clean))
                    return

                except:
                    pass

        await msg.edit_text("❌ No number, try again")

    elif data[0] == "cancel":
        await query.edit_message_text("❌ Cancelled")

    elif data[0] == "black":
        await query.edit_message_text("🚫 Blacklisted")

# ================= OTP =================

async def fetch_otp(msg, number, clean):

    url = f"https://api.durianrcs.com/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={clean}&pid={PROJECT_ID}"

    async with aiohttp.ClientSession() as session:

        for _ in range(120):  # 🔥 optimized loop

            try:
                async with session.get(url, timeout=5) as resp:
                    res = await resp.json()

                if res.get("data"):
                    otp = res["data"]

                    await msg.edit_text(
                        f"📱 {number}\n\n🔐 OTP:\n`{otp}`",
                        parse_mode="Markdown"
                    )
                    return

            except:
                pass

            await asyncio.sleep(3)

    await msg.edit_text(
        f"📱 {number}\n⌛ OTP not received"
    )

# ================= ADMIN =================

async def add_country(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        name = context.args[0]
        full = " ".join(context.args[1:])
        COUNTRIES[name] = full
        await update.message.reply_text(f"✅ Added {name}")
    except:
        await update.message.reply_text("Use: /addcountry name full_name")

async def remove_country(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        name = context.args[0]
        del COUNTRIES[name]
        await update.message.reply_text(f"❌ Removed {name}")
    except:
        pass

async def list_country(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "🌍 Countries:\n\n"
    for k,v in COUNTRIES.items():
        text += f"{k} → {v}\n"
    await update.message.reply_text(text)

# ================= HANDLER =================

async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in ALLOWED_USERS:
        return

    text = update.message.text

    if text == "📱 Get Number":
        await get_number(update, context)

    elif text == "🆔 My ID":
        await update.message.reply_text(f"{user}")

# ================= MAIN =================

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("addcountry", add_country))
app.add_handler(CommandHandler("removecountry", remove_country))
app.add_handler(CommandHandler("countries", list_country))

app.add_handler(MessageHandler(filters.TEXT, handle))
app.add_handler(CallbackQueryHandler(button_click))

print("🔥 SUPER BOT RUNNING 🔥")

keep_alive()
app.run_polling(concurrent_updates=True)
