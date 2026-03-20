import asyncio
import aiohttp

from telegram import *
from telegram.ext import *

# ================= GLOBAL =================

session = None
semaphore = asyncio.Semaphore(20)  # 20 user same speed

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
GROUP_ID = -1003525081102

async def get_json(url):
    async with session.get(url, timeout=10) as res:
        return await res.json()
        
# ================= DATABASE =================

USER_STATS = {}

# ================= USERS =================

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
["🆔 My ID","📊 Status"]
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

# ================= STATUS =================

async def status(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id
    data = USER_STATS.get(user, {})

    if not data:
        await update.message.reply_text("📊 No OTP yet")
        return

    text = "📊 OTP Stats:\n\n"
    total = 0

    for country,count in data.items():
        text += f"{country} → {count}\n"
        total += count

    text += f"\n🔥 Total: {total}"

    await update.message.reply_text(text)

# ================= ADMIN OTP =================

async def allotp(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    text = "📊 All Users OTP:\n\n"

    for user,data in USER_STATS.items():
        total = sum(data.values())
        text += f"{user} → {total}\n"

    await update.message.reply_text(text)

async def resetotp(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    USER_STATS.clear()
    await update.message.reply_text("♻️ Reset Done")

# ================= MASK =================

def mask(num):
    num = num.replace("+","")
    return num[:3] + "******" + num[4:]

# ================= COUNTRY =================

async def get_number(update:Update, context:ContextTypes.DEFAULT_TYPE):

    buttons = []

    for name in COUNTRIES:
        buttons.append([InlineKeyboardButton(name, callback_data=f"get|{name}")])

    await update.message.reply_text("🌍 Select Country:", reply_markup=InlineKeyboardMarkup(buttons))

# ================= BUTTON =================

async def button_click(update:Update, context:ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data.split("|")

    if data[0] == "get":

        name = data[1]
        country = COUNTRIES[name]

        msg = await query.edit_message_text(f"⚡ Getting {name}...")

        for i in range(3):

            try:
                url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy={country}"

                res = await get_json(url)

                if res.get("code") != 200 or not res.get("data"):
                    continue

                number = str(res["data"])
                clean = number.replace("+","")

                buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("❌ Cancel", callback_data=f"cancel|{clean}"),
                        InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{clean}")
                    ]
                ])

                await msg.edit_text(
                    f"🌍 {name}\n📱 `{number}`\n⏳ Waiting OTP...",
                    parse_mode="Markdown",
                    reply_markup=buttons
                )

                asyncio.create_task(fetch_otp(msg, number, clean, query.from_user, name))
                return

            except:
                pass

        await msg.edit_text("❌ No number please try again")

    elif data[0] == "cancel":
        await query.edit_message_text("❌ Cancelled")

    elif data[0] == "black":
        await query.edit_message_text("🚫 Blacklisted")

# ================= OTP =================

async def fetch_otp(msg, number, clean, user, country):

    start = asyncio.get_event_loop().time()
    
    url = f"https://api.durianrcs.com/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={clean}&pid={PROJECT_ID}"

while True:

        try:
            res = await get_json(url)

            if res.get("data") and res["data"] != "":
                otp = res["data"]

                uid = user.id
                uname = user.first_name

                # ===== SAVE =====
                if uid not in USER_STATS:
                    USER_STATS[uid] = {}

                if country not in USER_STATS[uid]:
                    USER_STATS[uid][country] = 0

                USER_STATS[uid][country] += 1

                # ===== USER MESSAGE =====
                user_buttons = InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 OTP Group", url="https://t.me/CsDrakOtpZone")]
                ])

                await msg.edit_text(
f"""━━━━━━━━━━━━━━
📱 NUMBER: `{number}`

🔐 OTP RECEIVED:
`{otp}`
━━━━━━━━━━━━━━""",
                    parse_mode="Markdown",
                    reply_markup=user_buttons
                )

                # ===== GROUP MESSAGE =====
                masked = mask(number)

                text = f"""🚀 NEW OTP

👤 User: {uname}
🆔 ID: {uid}

📱 Number: {masked}
🔐 OTP: `{otp}`

━━━━━━━━━━━━━━
🔐 Secure OTP Service
━━━━━━━━━━━━━━"""

                group_buttons = InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("📢 Otp Group", url="https://t.me/CsDrakOtpZone"),
                        InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/Sojib9690")
                    ],
                    [
                        InlineKeyboardButton("🤖 Number Bot", url="https://t.me/CSDarkSMSBot")
                    ]
                ])

                await msg._bot.send_message(
                    chat_id=GROUP_ID,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=group_buttons
                )

                return

        except:
            pass

        await asyncio.sleep(1.5)

    await msg.edit_text(f"📱 {number}\n⌛ OTP not received (timeout)")
# ================= ADMIN =================

async def approve(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    user_id = int(context.args[0])
    name = " ".join(context.args[1:])
    ALLOWED_USERS[user_id] = name
    await update.message.reply_text("✅ Approved")

async def remove_user(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    user_id = int(context.args[0])
    if user_id in ALLOWED_USERS:
        del ALLOWED_USERS[user_id]
        await update.message.reply_text("❌ Removed")

async def list_users(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "👥 Users:\n\n"
    for uid,name in ALLOWED_USERS.items():
        text += f"{name} → `{uid}`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def broadcast(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Use: /broadcast your message")
        return

    msg = " ".join(context.args)

    sent = 0

    for uid in ALLOWED_USERS:
        try:
            await context.bot.send_message(uid, f"📢 ADMIN MESSAGE:\n\n{msg}")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ Sent to {sent} users")
    
# ================= COUNTRY ADMIN =================

async def add_country(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    try:
        name = context.args[0]
        code = context.args[1]
        COUNTRIES[name] = code
        await update.message.reply_text(f"✅ Country Added: {name}")
    except:
        await update.message.reply_text("Use: /addcountry 🇧🇩 Bangladesh BD")


async def remove_country(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    
    try:
        name = context.args[0]
        if name in COUNTRIES:
            del COUNTRIES[name]
            await update.message.reply_text(f"❌ Removed: {name}")
    except:
        pass


async def list_country(update:Update, context:ContextTypes.DEFAULT_TYPE):
    text = "🌍 Countries:\n\n"
    for k,v in COUNTRIES.items():
        text += f"{k} → {v}\n"
    await update.message.reply_text(text)


# ================= STATS ADMIN =================

async def allstats(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return

    text = "📊 ALL USER STATS:\n\n"

    for uid,data in USER_STATS.items():
        total = sum(data.values())
        text += f"{uid} → {total}\n"

    await update.message.reply_text(text)


async def resetstats(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return

    try:
        uid = int(context.args[0])
        if uid in USER_STATS:
            USER_STATS[uid] = {}
            await update.message.reply_text("♻️ User Reset Done")
    except:
        await update.message.reply_text("Use: /resetstats user_id")


async def resetall(update:Update, context:ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return

    USER_STATS.clear()
    await update.message.reply_text("♻️ All Stats Reset")
    
# ================= HANDLE =================

async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):

    user = update.effective_user.id

    if user not in ALLOWED_USERS:
        return

    text = update.message.text

    if text == "📱 Get Number":
        await get_number(update, context)

    elif text == "🆔 My ID":
        await update.message.reply_text(f"{user}")

    elif text == "📊 Status":
        await status(update, context)

# ================= MAIN =================

async def on_startup(app):
    global session
    session = aiohttp.ClientSession()
    
app = ApplicationBuilder().token(BOT_TOKEN).post_init(on_startup).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("remove", remove_user))
app.add_handler(CommandHandler("users", list_users))

app.add_handler(CommandHandler("broadcast", broadcast))

app.add_handler(CommandHandler("allotp", allotp))
app.add_handler(CommandHandler("resetotp", resetotp))

app.add_handler(CommandHandler("addcountry", add_country))
app.add_handler(CommandHandler("removecountry", remove_country))
app.add_handler(CommandHandler("countries", list_country))

app.add_handler(CommandHandler("allstats", allstats))
app.add_handler(CommandHandler("resetstats", resetstats))
app.add_handler(CommandHandler("resetall", resetall))

app.add_handler(MessageHandler(filters.TEXT, handle))
app.add_handler(CallbackQueryHandler(button_click))

print("🔥 SUPER BOT RUNNING 🔥")

keep_alive()
app.run_polling()
