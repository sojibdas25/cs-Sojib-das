import logging, requests, asyncio, sys, json, os, time
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ১. রেন্ডার কানেক্টিভিটি ---
app_web = Flask('')
@app_web.route('/')
def home(): return "CS DARK PRO: ACTIVE"

def run():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- ২. কনফিগারেশন ---
BOT_TOKEN = '8740780011:AAFZxUCXzcUJQzZPUFNJYYbfdKnZAUNI9Fs'
API_KEY = 'TXVzbXNNYk9BZHdJc3l1WllnYm15UT09'
DURIAN_USER = 'rafiqmolla7'
PROJECT_ID = '0257' 
GROUP_ID = -1003525081102 

ALLOWED_USERS = {
    6528471341: "Sojib", 8081334307: "Sojib Das",
    8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"
}

COUNTRIES = {
    "🇺🇦 Ukraine": "Ukraine", "🇸🇸 S. Sudan": "South Sudan", "🇱🇨 S. Lucia": "Saint Lucia",
    "🇺🇸 USA": "United States", "🇬🇧 UK": "United Kingdom", "🇨🇦 Canada": "Canada",
    "🇮🇳 India": "India", "🇧🇩 BD": "Bangladesh", "🇷🇺 Russia": "Russia",
    "🇲🇾 Malaysia": "Malaysia", "🇮🇩 Indonesia": "Indonesia",
    "🇻🇳 Vietnam": "Vietnam", "🇹🇭 Thailand": "Thailand", "🇸🇦 S. Arabia": "Saudi Arabia",
    "🇸🇱 S. Leone": "Sierra Leone", "🇩🇿 Algeria": "Algeria", "🇹🇿 Tanzania": "Tanzania"
}

# --- ৩. ওটিপি অটো-ফেচ ও গ্রুপ ফরোয়ার্ড (Fix Applied) ---
async def fetch_otp_task(context, chat_id, full_number, msg_id, user_id, country_name):
    # প্যানেল শুধু ডিজিট চায়, তাই সব চিহ্ন মুছে ফেলছি
    num_only = ''.join(filter(str.isdigit, str(full_number)))
    # প্যানেল অনুযায়ী API URL সংশোধন
    url = f"https://api.durianrcs.com/out/ext_api/getVcode?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2"
    
    for attempt in range(40): # ৬-৭ মিনিট চেক করবে
        await asyncio.sleep(10)
        try:
            res = requests.get(url, timeout=10).json()
            # প্যানেল রেসপন্স চেক
            if res.get('code') == 200 and res.get('data'):
                otp = res.get('data')
                
                # সাকসেস মেসেজ
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Get Another", callback_data=f"get_{country_name}")]])
                await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
                    text=f"✅ **OTP Received!**\n\n📱 **Number:** `{full_number}`\n🔑 **OTP Code:** `{otp}`", 
                    reply_markup=kb, parse_mode='Markdown')
                
                # গ্রুপে ফরোয়ার্ড (নিশ্চিত করা হয়েছে)
                await context.bot.send_message(chat_id=GROUP_ID, 
                    text=f"🔥 **Forwarded OTP:**\n🔑 Code: `{otp}`\n📱 Num: `{full_number}`\n👤 User: {ALLOWED_USERS.get(user_id, 'Admin')}", 
                    parse_mode='Markdown')
                return
        except Exception as e:
            logging.error(f"OTP Fetch Error: {e}")
    
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏳ Timeout! No OTP for `{full_number}`. Please block and retry.")

# --- ৪. মেইন লজিক ও বাটনস ---
def main_menu():
    return ReplyKeyboardMarkup([[KeyboardButton("📱 Get Number")], [KeyboardButton("💰 Balance"), KeyboardButton("ℹ️ My ID")]], resize_keyboard=True)

def country_menu():
    buttons = []
    keys = list(COUNTRIES.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(keys[i], callback_data=f"get_{COUNTRIES[keys[i]]}")]
        if i+1 < len(keys): row.append(InlineKeyboardButton(keys[i+1], callback_data=f"get_{COUNTRIES[keys[i+1]]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in ALLOWED_USERS:
        await update.message.reply_text(f"Welcome {ALLOWED_USERS[uid]}!", reply_markup=main_menu())

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("get_"):
        country = query.data.split("_")[1]
        sent_msg = await query.edit_message_text(f"🛰 Requesting **{country}** Only...")
        
        # প্যানেলকে বাধ্য করার জন্য force_country ও operator=any প্যারামিটার
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&country={country}&operator=any&force_country=1"
        
        try:
            res = requests.get(url, timeout=15).json()
            if res.get('code') == 200:
                number = res.get('data')
                # ব্লক এবং রিকোয়েস্ট বাটন ফিক্স
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 Block/Cancel", callback_data=f"block_{number}_{country}")],
                    [InlineKeyboardButton("🔄 New Number", callback_data=f"get_{country}")]
                ])
                await query.edit_message_text(f"🌍 **Country:** {country}\n📱 **Number:** `{number}`\n⏳ Waiting for OTP...", reply_markup=kb, parse_mode='Markdown')
                # ওটিপি ফেচিং শুরু
                asyncio.create_task(fetch_otp_task(context, query.message.chat_id, number, sent_msg.message_id, query.from_user.id, country))
            else:
                await query.edit_message_text(f"❌ {country} Stock Out.", reply_markup=country_menu())
        except: await query.edit_message_text("❌ Server Busy! Try again.")

    elif query.data.startswith("block_"):
        data = query.data.split("_")
        num = ''.join(filter(str.isdigit, data[1]))
        requests.get(f"https://api.durianrcs.com/out/ext_api/cancelMobile?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num}&serial=2")
        await query.edit_message_text(f"🚫 Blocked: {data[1]}", reply_markup=country_menu())

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, uid = update.message.text, update.effective_user.id
    if uid not in ALLOWED_USERS: return
    if text == "📱 Get Number": await update.message.reply_text("🌍 Select Country:", reply_markup=country_menu())
    elif text == "💰 Balance":
        res = requests.get(f"https://api.durianrcs.com/out/ext_api/getBalance?name={DURIAN_USER}&ApiKey={API_KEY}").json()
        await update.message.reply_text(f"💰 Balance: `{res.get('data', '0')}`", parse_mode='Markdown')

async def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_msg))
    app.add_handler(CallbackQueryHandler(callback_query))
    keep_alive()
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(drop_pending_updates=True)
        await asyncio.Event().wait()

if __name__ == '__main__':
    try: asyncio.run(main())
    except: pass
