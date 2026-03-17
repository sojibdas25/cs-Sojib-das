import asyncio
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= SERVER SETTINGS =================
app_web = Flask(__name__)
@app_web.route('/')
def home(): return "Multi-Country Bot Active"
def run(): app_web.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
BOT_TOKEN = "8740780011:AAHbnPoUV_4C6JGULWVQgOAvbvW96gkqEYo"
USERNAME = "rafiqmolla7"
API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09" # প্যানেল থেকে নিশ্চিত হয়ে নিন
PROJECT_ID = "0257"
BASE_URL = "https://mm.durianrcs.com"

ALLOWED_USERS = {6528471341: "Sojib", 8081334307: "Sojib Das", 8181512467: "Admin"}

# কান্ট্রি কোড লিস্ট
COUNTRIES = {
    "🇸🇸 South Sudan": "211",
    "🇨🇬 Congo": "242",
    "🇺🇸 USA": "1"
}

keyboard = [["📱 Get Number"], ["🆔 My ID", "💰 Balance"]]
menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= COUNTRY SELECTOR =================
async def show_countries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = []
    for name, code in COUNTRIES.items():
        buttons.append([InlineKeyboardButton(name, callback_data=f"sel|{code}|{name}")])
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("🌍 কোন দেশের নম্বর নিতে চান?", reply_markup=reply_markup)

# ================= GET NUMBER LOGIC =================
async def fetch_number(update, context, country_code, country_name, query_msg):
    found_num = None
    # প্যানেলের সাথে ম্যাচ করতে ৫ বার হাই-স্পিড ট্রাই
    for i in range(1, 6):
        await query_msg.edit_text(f"🚀 {country_name} নম্বর খোঁজা হচ্ছে... চেষ্টা: {i}/5")
        
        # ট্রাই ১: সিরিয়াল ২ দিয়ে
        url = f"{BASE_URL}/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy={country_code}&serial=2"
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                found_num = res["data"]
                serial_used = "2"
                break
        except: pass
        
        await asyncio.sleep(1)

    if found_num:
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{found_num}|{serial_used}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel")
        ]])
        await query_msg.edit_text(f"✅ **নম্বর পাওয়া গেছে!**\n\n🌍 দেশ: `{country_name}`\n📱 নম্বর: `{found_num}`\n\n⏳ ওটিপি চেক করা হচ্ছে...", parse_mode="Markdown", reply_markup=btn)
        asyncio.create_task(wait_for_otp(update, context, found_num, serial_used, query_msg))
    else:
        await query_msg.edit_text(f"❌ দুঃখিত, {country_name}-এ এই মুহূর্তে কোনো নম্বর খালি নেই।")

# ================= OTP LOGIC =================
async def wait_for_otp(update, context, number, serial, msg):
    otp_url = f"{BASE_URL}/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={number}&pid={PROJECT_ID}&serial={serial}"
    
    for _ in range(25):
        await asyncio.sleep(12)
        try:
            res = requests.get(otp_url, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                await msg.edit_text(f"✅ **ওটিপি পাওয়া গেছে!**\n\n📱 নম্বর: `{number}`\n🔑 ওটিপি: `{res['data']}`", parse_mode="Markdown")
                return
        except: pass

    await msg.edit_text(f"⌛ `{number}` নম্বরে ওটিপি আসেনি। রিফান্ড পেতে ব্ল্যাকলিস্ট করুন।")

# ================= CALLBACK HANDLER =================
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")

    if data[0] == "sel":
        await fetch_number(update, context, data[1], data[2], query.message)
    elif data[0] == "black":
        num, ser = data[1], data[2]
        requests.get(f"{BASE_URL}/out/ext_api/addBlack?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&pn={num}&serial={ser}")
        await query.edit_message_text(f"🚫 `{num}` ব্ল্যাকলিস্ট করা হয়েছে।")

# ================= START & TEXT HANDLER =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS: return
    await update.message.reply_text("🤖 Multi-Country OTP Bot Ready!", reply_markup=menu)

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS: return
    txt = update.message.text
    if txt == "📱 Get Number": await show_countries(update, context)
    elif txt == "💰 Balance":
        res = requests.get(f"{BASE_URL}/out/ext_api/getUserInfo?name={USERNAME}&ApiKey={API_KEY}").json()
        await update.message.reply_text(f"💰 ব্যালেন্স: `{res['data']['money']}` USD")

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.add_handler(CallbackQueryHandler(handle_callback))
    print("🚀 BOT IS LIVE")
    app.run_polling()
