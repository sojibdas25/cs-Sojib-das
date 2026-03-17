import asyncio
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= SERVER KEEP ALIVE =================
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
BASE_URL = "https://mm.durianrcs.com" # আপনার প্যানেলের সঠিক ডোমেইন

ALLOWED_USERS = {
    6528471341: "Sojib", 8081334307: "Sojib Das",
    8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"
}

keyboard = [["📱 Get Number"], ["🆔 My ID", "💰 Balance"]]
menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= GET NUMBER (AUTO 5 RETRIES) =================
async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🚀 সাউথ সুদানের নম্বর খোঁজা হচ্ছে...")
    
    found_number = None
    for i in range(1, 6): # ১ ক্লিকে ৫ বার ট্রাই করবে
        if i > 1:
            await msg.edit_text(f"🚀 নম্বর পাওয়া যায়নি, আবার চেষ্টা করছি... ({i}/5)")
        
        # সাউথ সুদানের জন্য একদম সঠিক API কল
        url = f"{BASE_URL}/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy=211&serial=2"
        
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                found_number = res["data"]
                break
        except:
            pass
        await asyncio.sleep(1)

    if found_number:
        btn = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{found_number}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_msg")
        ]])
        await msg.edit_text(f"✅ **সাউথ সুদান নম্বর পাওয়া গেছে!**\n\n📱 নম্বর: `{found_number}`\n\n⏳ ওটিপির জন্য অপেক্ষা করুন...", parse_mode="Markdown", reply_markup=btn)
        asyncio.create_task(fetch_otp(update, context, found_number, msg))
    else:
        await msg.edit_text("❌ এই মুহূর্তে প্যানেলে কোনো নম্বর নেই। কিছুক্ষণ পর আবার চেষ্টা করুন।")

# ================= FETCH OTP =================
async def fetch_otp(update, context, number, msg):
    url = f"{BASE_URL}/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={number}&pid={PROJECT_ID}&serial=2"

    for i in range(30): # ৫ মিনিট ধরে ওটিপি চেক করবে
        await asyncio.sleep(10)
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                otp_res = res["data"]
                await msg.edit_text(f"✅ **ওটিপি চলে এসেছে!**\n\n📱 নম্বর: `{number}`\n🔑 {otp_res}", parse_mode="Markdown")
                return
        except:
            pass

    await msg.edit_text(f"⌛ ওটিপি আসেনি। নম্বরটি ব্ল্যাকলিস্ট করুন।")

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS: return
    await update.message.reply_text("✅ সাউথ সুদান নম্বর বট প্রস্তুত।", reply_markup=menu)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")
    if data[0] == "black":
        requests.get(f"{BASE_URL}/out/ext_api/addBlack?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&pn={data[1]}")
        await query.edit_message_text(f"🚫 `{data[1]}` ব্ল্যাকলিস্ট করা হয়েছে।")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS: return
    t = update.message.text
    if t == "📱 Get Number": await get_number(update, context)
    elif t == "💰 Balance":
        res = requests.get(f"{BASE_URL}/out/ext_api/getUserInfo?name={USERNAME}&ApiKey={API_KEY}").json()
        await update.message.reply_text(f"💰 ব্যালেন্স: `{res['data']['money']}` USD", parse_mode="Markdown")

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    application.add_handler(CallbackQueryHandler(button_click))
    print("🚀 BOT STARTED SUCCESSFULLY")
    application.run_polling()
