import asyncio
import requests
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ================= KEEP ALIVE (To keep the bot running 24/7) =================
app_web = Flask(__name__)
@app_web.route('/')
def home(): return "New Version Bot is Online"
def run(): app_web.run(host='0.0.0.0', port=10000)
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION (নিউ ভার্সন সেটিংস) =================
BOT_TOKEN = "8740780011:AAHbnPoUV_4C6JGULWVQgOAvbvW96gkqEYo"
API_KEY = "TXVzbXNNYk9BZHdJc3l1WllnYm15UT09"
USERNAME = "rafiqmolla7"
PROJECT_ID = "0257"
SUPPORT_LINK = "https://t.me/Sojib9690"

# নিউ ভার্সন সাউথ সুদান কোড
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

# ================= GET NUMBER (NEW VERSION - AUTO 5 RETRIES) =================
async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text("⚡ [New Version] Searching SS Number (Attempt 1/5)...")
    
    number = None
    for attempt in range(1, 6):
        if attempt > 1:
            await status_msg.edit_text(f"⚡ [New Version] Searching SS Number (Attempt {attempt}/5)...")
        
        # নিউ ভার্সন এপিআই: অবশ্যই serial=2 এবং cuy=211 থাকতে হবে
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&cuy={SS_CODE}&serial=2"
        
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                number = res["data"]
                break 
        except:
            pass
        await asyncio.sleep(1) # দ্রুত ট্রাই করার জন্য ১ সেকেন্ড বিরতি

    if number:
        # নম্বর পাওয়ার পর ওল্ড ভার্সনের তুলনায় নিউ ভার্সনে দ্রুত রেসপন্স পাওয়া যায়
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton("🚫 Blacklist", callback_data=f"black|{number}"),
            InlineKeyboardButton("❌ Cancel", callback_data="cancel_msg")
        ]])

        await status_msg.edit_text(
            f"✅ **Number Found! (New Version)**\n\n🌍 Country: `South Sudan`\n📱 Number: `{number}`\n\n⏳ Waiting for OTP... (Auto Polling)",
            parse_mode="Markdown",
            reply_markup=buttons
        )
        
        # নিউ ভার্সন ওটিপি ফেচ শুরু
        asyncio.create_task(fetch_otp(update, context, number, status_msg))
    else:
        await status_msg.edit_text("❌ No SS number available in New Version. Try again later.")

# ================= FETCH OTP (NEW VERSION - FAST POLLING) =================
async def fetch_otp(update, context, number, status_msg):
    # নিউ ভার্সনে serial=2 ব্যবহার না করলে ওটিপি আসবে না
    url = f"https://api.durianrcs.com/out/ext_api/getMsg?name={USERNAME}&ApiKey={API_KEY}&pn={number}&pid={PROJECT_ID}&serial=2"

    # ৩০ বার ট্রাই করবে, প্রতি ১০ সেকেন্ড অন্তর (ডকুমেন্ট অনুযায়ী ফাস্ট পোলিং)
    for i in range(30):
        await asyncio.sleep(10) 
        try:
            res = requests.get(url, timeout=10).json()
            if res.get("code") == 200 and res.get("data"):
                otp_data = res["data"] # "Code: 123456" এই ফরম্যাটে আসবে
                await status_msg.edit_text(
                    f"✅ **OTP RECEIVED!**\n\n📱 Number: `{number}`\n🔑 {otp_data}",
                    parse_mode="Markdown"
                )
                return
        except:
            pass

    await status_msg.edit_text(f"⌛ OTP Timeout for `{number}`.\nIf you didn't get code, use Blacklist button.")

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS:
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=SUPPORT_LINK)]])
        await update.message.reply_text("❌ Access Denied", reply_markup=btn)
        return
    await update.message.reply_text(f"✅ New Version Bot Ready!", reply_markup=menu)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split("|")

    if data[0] == "black":
        num = data[1]
        # ব্ল্যাকলিস্ট এপিআই (রিফান্ড নিশ্চিত করার জন্য)
        requests.get(f"https://api.durianrcs.com/out/ext_api/addBlack?name={USERNAME}&ApiKey={API_KEY}&pid={PROJECT_ID}&pn={num}")
        await query.edit_message_text(f"🚫 `{num}` Blacklisted and refunded.")
    elif data[0] == "cancel_msg":
        await query.edit_message_text("❌ Request Cancelled.")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    res = requests.get(f"https://api.durianrcs.com/out/ext_api/getUserInfo?name={USERNAME}&ApiKey={API_KEY}").json()
    bal = res['data']['money'] if res.get("code") == 200 else "Error"
    await update.message.reply_text(f"💰 Balance: `{bal}` USD", parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ALLOWED_USERS: return
    text = update.message.text
    if text == "📱 Get Number": await get_number(update, context)
    elif text == "🆔 My ID": await update.message.reply_text(f"🆔 ID: `{user_id}`", parse_mode="Markdown")
    elif text == "💰 Balance": await balance(update, context)

if __name__ == '__main__':
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    application.add_handler(CallbackQueryHandler(button_click))
    print("🚀 NEW VERSION BOT STARTED...")
    application.run_polling()
