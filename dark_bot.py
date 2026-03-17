import asyncio
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= KEEP ALIVE =================
app_web = Flask(__name__)
@app_web.route('/')
def home(): return "Bot is Online"
def run(): app_web.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
BOT_TOKEN = "8740780011:AAHbnPoUV_4C6JGULWVQgOAvbvW96gkqEYo"
API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"
USERNAME = "rafiqmolla7"
PROJECT_ID = "0257"
SS_CODE = "211" # South Sudan

ALLOWED_USERS = {
    6528471341: "Sojib", 8081334307: "Sojib Das",
    8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"
}

# ব্রাউজার হেডার (যাতে সার্ভার মনে করে এটি প্যানেল থেকেই রিকোয়েস্ট করছে)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json, text/plain, */*"
}

keyboard = [["📱 Get Number"], ["🆔 My ID", "💰 Balance"]]
menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= GET NUMBER (PANEL STYLE RETRY) =================
async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🚀 Searching South Sudan Number... Please wait.")
    
    found_number = None
    # প্যানেলের মতো ৫ বার হাই-স্পিড ট্রাই
    for i in range(1, 6):
        await msg.edit_text(f"🚀 Searching SS Number (Attempt {i}/5)...")
        
        # New Version API URL with serial=1 (অনেক সময় New Version এ ১ দিলে দ্রুত কাজ করে)
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy={SS_CODE}&serial=1"
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            res = response.json()
            
            if res.get("code") == 200 and res.get("data"):
                found_number = res["data"]
                break
            elif res.get("code") == 103: # Account balance error
                await msg.edit_text("❌ Insufficient Balance in Panel!")
                return
        except Exception as e:
            print(f"Error: {e}")
        
        await asyncio.sleep(1) # ১ সেকেন্ড গ্যাপ

    if found_number:
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{found_number}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_msg")
        ]])
        await msg.edit_text(f"✅ **Number Received!**\n\n🌍 Country: `South Sudan`\n📱 Number: `{found_number}`\n\n⏳ Waiting for OTP...", parse_mode="Markdown", reply_markup=btn)
        asyncio.create_task(fetch_otp(update, context, found_number, msg))
    else:
        await msg.edit_text("❌ প্যানেলে নম্বর থাকলেও বট এখন পাচ্ছে না। সম্ভবত এপিআই রিকোয়েস্ট লিমিট হয়েছে। কিছুক্ষণ পর ট্রাই করুন।")

# ================= FETCH OTP =================
async def fetch_otp(update, context, number, msg):
    # নম্বর নিতে যে serial ব্যবহার করা হয়েছে ওটিপিতেও তাই দিতে হবে
    url = f"https://api.durianrcs.com/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={number}&pid={PROJECT_ID}&serial=1"

    for i in range(30):
        await asyncio.sleep(10)
        try:
            res = requests.get(url, headers=HEADERS, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                await msg.edit_text(f"✅ **OTP RECEIVED!**\n\n📱 Number: `{number}`\n🔑 {res['data']}", parse_mode="Markdown")
                return
        except: pass

    await msg.edit_text(f"⌛ OTP Timeout for `{number}`. Use Blacklist to refund.")

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS: return
    await update.message.reply_text("✅ Bot Ready (High Speed Mode)", reply_markup=menu)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if data[0] == "black":
        requests.get(f"https://api.durianrcs.com/out/ext_api/addBlack?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&pn={data[1]}", headers=HEADERS)
        await query.edit_message_text(f"🚫 `{data[1]}` blacklisted.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS: return
    t = update.message.text
    if t == "📱 Get Number": await get_number(update, context)
    elif t == "💰 Balance":
        res = requests.get(f"https://api.durianrcs.com/out/ext_api/getUserInfo?name={USERNAME}&ApiKey={API_KEY}", headers=HEADERS).json()
        await update.message.reply_text(f"💰 Balance: `{res['data']['money']}` USD", parse_mode="Markdown")

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    application.add_handler(CallbackQueryHandler(button_click))
    print("🚀 BOT STARTED")
    application.run_polling()
