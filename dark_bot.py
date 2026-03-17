import asyncio
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= KEEP ALIVE =================
app_web = Flask(__name__)
@app_web.route('/')
def home(): return "Multi-Country Bot Live"
def run(): app_web.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
BOT_TOKEN = "8740780011:AAHbnPoUV_4C6JGULWVQgOAvbvW96gkqEYo"
USERNAME = "rafiqmolla7"
API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"
PROJECT_ID = "0257"
BASE_URL = "https://mm.durianrcs.com"

ALLOWED_USERS = {6528471341: "Sojib", 8081334307: "Sojib Das", 8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"}

# আপনার দেওয়া ২৬টি দেশের তালিকা ও কোড
COUNTRIES = {
    "🇺🇸 USA": "1", "🇦🇴 Angola": "244", "🇳🇬 Nigeria": "234", "🇲🇿 Mozambique": "258",
    "🇲🇽 Mexico": "52", "🇰🇪 Kenya": "254", "🇹🇭 Thailand": "66", "🇨🇲 Cameroon": "237",
    "🇪🇬 Egypt": "20", "🇸🇳 Senegal": "221", "🇱🇾 Libya": "218", "🇮🇳 India": "91",
    "🇷🇺 Russia": "7", "🇨🇬 Congo": "242", "🇦🇫 Afghanistan": "93", "🇲🇷 Mauritania": "222",
    "🇹🇬 Togo": "228", "🇹🇳 Tunisia": "216", "🇦🇷 Argentina": "54", "🇩🇿 Algeria": "213",
    "🇲🇼 Malawi": "265", "🇿🇲 Zambia": "260", "🇻🇪 Venezuela": "58", "🇺🇬 Uganda": "256",
    "🇬🇭 Ghana": "233", "🇪🇹 Ethiopia": "251"
}

keyboard = [["📱 Get Number"], ["🆔 My ID", "💰 Balance"]]
menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= COUNTRY MENU (Paginated) =================
async def show_country_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = []
    temp_row = []
    for name, code in COUNTRIES.items():
        temp_row.append(InlineKeyboardButton(name, callback_data=f"get|{code}|{name}"))
        if len(temp_row) == 2: # প্রতি লাইনে ২টা করে বাটন
            buttons.append(temp_row)
            temp_row = []
    if temp_row: buttons.append(temp_row)
    
    reply_markup = InlineKeyboardMarkup(buttons)
    await update.message.reply_text("🌍 দেশ সিলেক্ট করুন:", reply_markup=reply_markup)

# ================= QUICK GET NUMBER =================
async def get_number_quick(update, context, cuy, c_name, query_msg):
    await query_msg.edit_text(f"⚡ {c_name} নম্বর খোঁজা হচ্ছে (Quick Check)...")
    
    # এক ক্লিকে সরাসরি একবারই চেক (serial=2 নিউ ভার্সন অনুযায়ী)
    url = f"{BASE_URL}/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy={cuy}&serial=2"
    
    try:
        res = requests.get(url, timeout=12).json()
        if res.get("code") == 200 and res.get("data"):
            number = res["data"]
            btn = InlineKeyboardMarkup([[
                InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{number}"),
                InlineKeyboardButton("❌ Cancel", callback_data="cancel")
            ]])
            await query_msg.edit_text(f"✅ **নম্বর পাওয়া গেছে!**\n\n🌍 দেশ: `{c_name}`\n📱 নম্বর: `{number}`\n\n⏳ ওটিপি আসার সাথে সাথে এখানে দেখাবে...", parse_mode="Markdown", reply_markup=btn)
            
            # ওটিপি ফেচিং শুরু
            asyncio.create_task(fetch_otp(update, context, number, query_msg))
        else:
            await query_msg.edit_text(f"❌ {c_name}-এ এই মুহূর্তে নম্বর নেই। (প্যানেল কোড: {res.get('code')})")
    except:
        await query_msg.edit_text("❌ এপিআই কানেকশন এরর!")

# ================= FAST OTP FETCH =================
async def fetch_otp(update, context, number, msg):
    url = f"{BASE_URL}/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={number}&pid={PROJECT_ID}&serial=2"

    for i in range(30): # ৫ মিনিট চেক করবে
        await asyncio.sleep(10) # ১০ সেকেন্ড পর পর চেক
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                otp_info = res["data"]
                await msg.edit_text(f"✅ **ওটিপি পাওয়া গেছে!**\n\n📱 নম্বর: `{number}`\n🔑 {otp_info}", parse_mode="Markdown")
                return
        except: pass

    await msg.edit_text(f"⌛ `{number}` ওটিপি আসেনি। রিফান্ড পেতে Blacklist করুন।")

# ================= CALLBACKS =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")

    if data[0] == "get":
        await get_number_quick(update, context, data[1], data[2], query.message)
    elif data[0] == "black":
        requests.get(f"{BASE_URL}/out/ext_api/addBlack?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&pn={data[1]}&serial=2")
        await query.edit_message_text(f"🚫 `{data[1]}` ব্ল্যাকলিস্ট করা হয়েছে।")
    elif data[0] == "cancel":
        await query.edit_message_text("❌ বাতিল করা হয়েছে।")

# ================= HANDLERS =================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ALLOWED_USERS: return
    txt = update.message.text
    if txt == "📱 Get Number": await show_country_menu(update, context)
    elif txt == "💰 Balance":
        res = requests.get(f"{BASE_URL}/out/ext_api/getUserInfo?name={USERNAME}&ApiKey={API_KEY}").json()
        await update.message.reply_text(f"💰 ব্যালেন্স: `{res['data']['money']}` USD")
    elif txt == "🆔 My ID":
        await update.message.reply_text(f"🆔 আপনার আইডি: `{update.effective_user.id}`")

if __name__ == '__main__':
    keep_alive()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", lambda u, c: u.message.reply_text("✅ বট প্রস্তুত!", reply_markup=menu)))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    app.add_handler(CallbackQueryHandler(callback_handler))
    print("🚀 HIGH-SPEED BOT STARTED")
    app.run_polling()
