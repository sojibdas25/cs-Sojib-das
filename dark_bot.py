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
SUPPORT_LINK = "https://t.me/Sojib9690"

# South Sudan কান্ট্রি কোড ২১১ এবং প্রজেক্ট সেটআপ
SS_CODE = "211"

ALLOWED_USERS = {
    6528471341: "Sojib",
    8081334307: "Sojib Das",
    8181512467: "Admin",
    8164389661: "pc",
    6630618306: "Chandon"
}

keyboard = [["📱 Get Number"], ["🆔 My ID", "💰 Balance"]]
menu = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ================= GET NUMBER (AUTO RETRY 5 TIMES) =================
async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("🚀 Searching South Sudan Number (Attempt 1/5)...")
    
    number = None
    # অটোমেটিক ৫ বার ট্রাই করার লজিক
    for attempt in range(1, 6):
        if attempt > 1:
            await status_msg.edit_text(f"🚀 Searching South Sudan Number (Attempt {attempt}/5)...")
        
        # এপিআই ইউআরএল - সাউথ সুদান ফিক্সড
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy={SS_CODE}&serial=2"
        
        try:
            res = requests.get(url, timeout=8).json()
            if res.get("code") == 200 and res.get("data"):
                number = res["data"]
                break # নম্বর পাওয়া গেলে লুপ থেকে বের হয়ে যাবে
        except:
            pass
        
        await asyncio.sleep(1) # প্রতি ট্রাই এর মাঝে সামান্য বিরতি

    if number:
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{number}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_msg")
        ]])

        await status_msg.edit_text(
            f"✅ **Number Found!**\n\n🌍 Country: `South Sudan`\n📱 Number: `{number}`\n\n⏳ Waiting for OTP... (Auto checking)",
            parse_mode="Markdown",
            reply_markup=buttons
        )
        
        # ওটিপি চেক শুরু
        asyncio.create_task(fetch_otp(update, context, number, status_msg))
    else:
        await status_msg.edit_text("❌ No number available after 5 attempts. Please try again later.")

# ================= FETCH OTP (FAST POLLING) =================
async def fetch_otp(update, context, number, status_msg):
    url = f"https://api.durianrcs.com/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={number}&pid={PROJECT_ID}&serial=2"

    # ৩০ বার চেক করবে, প্রতি ১০ সেকেন্ড অন্তর (মোট ৫ মিনিট)
    for i in range(30):
        await asyncio.sleep(10) 
        try:
            res = requests.get(url, timeout=8).json()
            if res.get("code") == 200 and res.get("data"):
                otp_info = res["data"]
                await status_msg.edit_text(
                    f"✅ **OTP RECEIVED!**\n\n📱 Number: `{number}`\n🔑 {otp_info}",
                    parse_mode="Markdown"
                )
                return
        except:
            pass

    await status_msg.edit_text(f"⌛ OTP Timeout for `{number}`.\nUse Blacklist button to get refund.")

# ================= OTHER HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=SUPPORT_LINK)]])
        await update.message.reply_text("❌ Access Denied", reply_markup=btn)
        return
    await update.message.reply_text(f"✅ Welcome {ALLOWED_USERS[user_id]}!", reply_markup=menu)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")

    if data[0] == "black":
        num = data[1]
        requests.get(f"https://api.durianrcs.com/out/ext_api/addBlack?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&pn={num}")
        await query.edit_message_text(f"🚫 `{num}` blacklisted. Balance will be refunded.")
    elif data[0] == "cancel_msg":
        await query.edit_message_text("❌ Request Cancelled.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        res = requests.get(f"https://api.durianrcs.com/out/ext_api/getUserInfo?name={USERNAME}&ApiKey={API_KEY}").json()
        bal = res['data']['money'] if res.get("code") == 200 else "Error"
        await update.message.reply_text(f"💰 Balance: `{bal}` USD", parse_mode="Markdown")
    except:
        await update.message.reply_text("❌ Error checking balance.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS: return
    text = update.message.text
    if text == "📱 Get Number": await get_number(update, context)
    elif text == "🆔 My ID": await update.message.reply_text(f"🆔 ID: `{user_id}`", parse_mode="Markdown")
    elif text == "💰 Balance": await balance(update, context)

if __name__ == '__main__':
    print("🚀 BOT RUNNING...")
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    application.add_handler(CallbackQueryHandler(button_click))
    application.run_polling()
