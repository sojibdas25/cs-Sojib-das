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
    return "Bot is Online"

def run():
    app_web.run(host='0.0.0.0', port=10000)

def keep_alive():
    Thread(target=run).start()

# ================= CONFIGURATION =================
BOT_TOKEN = "8740780011:AAHbnPoUV_4C6JGULWVQgOAvbvW96gkqEYo"
API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"
USERNAME = "rafiqmolla7"
PROJECT_ID = "0257"
SUPPORT_LINK = "https://t.me/Sojib9690"

# ডিফল্ট দেশ সাউথ সুদান (কোড: 211)
CURRENT_COUNTRY_CODE = "211" 

ALLOWED_USERS = {
    6528471341: "Sojib",
    8081334307: "Sojib Das",
    8181512467: "Admin",
    8164389661: "pc",
    6630618306: "Chandon"
}

# ================= KEYBOARD MENU =================
keyboard = [
    ["📱 Get Number"],
    ["🌍 Country"],
    ["🆔 My ID", "💰 Balance"]
]
menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= START COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        button = InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=SUPPORT_LINK)]])
        await update.message.reply_text(
            f"❌ **Access Denied**\nYour ID: `{user_id}`\nAdmin approval required.",
            parse_mode="Markdown",
            reply_markup=button
        )
        return
    await update.message.reply_text(f"✅ Welcome {ALLOWED_USERS[user_id]}! Bot is ready.", reply_markup=menu)

# ================= COUNTRY SELECTION =================
async def show_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇸🇸 South Sudan", callback_data="set|211|South Sudan"),
            InlineKeyboardButton("🇱🇨 Saint Lucia", callback_data="set|758|Saint Lucia")
        ]
    ])
    await update.message.reply_text("🌍 Select Country:", reply_markup=buttons)

# ================= GET NUMBER =================
async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⚡ Fetching number, please wait...")

    # ডকুমেন্ট অনুযায়ী: cuy প্যারামিটার এবং serial=2 যোগ করা হয়েছে
    url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy={CURRENT_COUNTRY_CODE}&serial=2"

    try:
        res = requests.get(url, timeout=10).json()
        if res.get("code") == 200 and res.get("data"):
            number = res["data"]
            
            # নম্বর পাওয়ার পর ২ সেকেন্ড বিরতি (সিস্টেম স্ট্যাবিলিটির জন্য)
            await asyncio.sleep(2) 

            buttons = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{number}"),
                    InlineKeyboardButton("❌ Cancel", callback_data="cancel_msg")
                ]
            ])

            await msg.edit_text(
                f"✅ **Number Received!**\n\nCountry Code: `{CURRENT_COUNTRY_CODE}`\nNumber: `{number}`\n\n⏳ Waiting for OTP...",
                parse_mode="Markdown",
                reply_markup=buttons
            )

            # ব্যাকগ্রাউন্ডে ওটিপি চেক শুরু
            asyncio.create_task(fetch_otp(update, context, number, msg))
        else:
            await msg.edit_text(f"❌ Error: {res.get('msg', 'No number available')}")
    except Exception as e:
        await msg.edit_text("❌ Connection Error to API")

# ================= FETCH OTP (The Core Logic) =================
async def fetch_otp(update, context, number, msg):
    # সঠিক এন্ডপয়েন্ট getMsg এবং serial=2 বাধ্যতামূলক
    url = f"https://api.durianrcs.com/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={number}&pid={PROJECT_ID}&serial=2"

    # ২৫ বার ট্রাই করবে, প্রতি ১৫ সেকেন্ড অন্তর (ডকুমেন্টেশন অনুযায়ী)
    for i in range(25): 
        await asyncio.sleep(15) 
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                otp_code = res["data"]
                await msg.edit_text(
                    f"✅ **OTP RECEIVED!**\n\n📱 Number: `{number}`\n🔑 OTP: `{otp_code}`",
                    parse_mode="Markdown"
                )
                return
        except:
            pass

    await msg.edit_text(f"⌛ OTP Timeout for `{number}`.\nIf you didn't get code, please Blacklist.")

# ================= BUTTON CALLBACKS =================
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global CURRENT_COUNTRY_CODE
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")

    if data[0] == "set":
        CURRENT_COUNTRY_CODE = data[1]
        country_name = data[2]
        await query.edit_message_text(f"✅ Country set to: **{country_name}**", parse_mode="Markdown")

    elif data[0] == "black":
        number = data[1]
        black_url = f"https://api.durianrcs.com/out/ext_api/addBlack?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&pn={number}"
        requests.get(black_url)
        await query.edit_message_text(f"🚫 Number `{number}` blacklisted and refunded.")

    elif data[0] == "cancel_msg":
        await query.edit_message_text("❌ Request Cancelled.")

# ================= OTHER COMMANDS =================
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"https://api.durianrcs.com/out/ext_api/getUserInfo?name={USERNAME}&ApiKey={API_KEY}"
    try:
        res = requests.get(url).json()
        bal = res['data']['money'] if res.get("code") == 200 else "Error"
        await update.message.reply_text(f"💰 Your Balance: `{bal}` USD", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Failed to fetch balance.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS: return
    
    text = update.message.text
    if text == "📱 Get Number": await get_number(update, context)
    elif text == "🌍 Country": await show_country(update, context)
    elif text == "🆔 My ID": await update.message.reply_text(f"🆔 Your ID: `{user_id}`", parse_mode="Markdown")
    elif text == "💰 Balance": await balance(update, context)

# ================= MAIN RUNNER =================
if __name__ == '__main__':
    print("🚀 BOT IS STARTING...")
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    application.add_handler(CallbackQueryHandler(button_click))
    
    application.run_polling()
