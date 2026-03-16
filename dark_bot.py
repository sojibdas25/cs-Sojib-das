import logging, requests, asyncio, sys, json, os, time
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ১. রেন্ডার স্ট্যাবিলিটি (২৪ ঘণ্টা অনলাইন) ---
app_web = Flask('')
@app_web.route('/')
def home(): return "SYSTEM 100% STABLE"

def run():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- ২. আপনার কনফিগারেশন ---
BOT_TOKEN = '8740780011:AAFZxUCXzcUJQzZPUFNJYYbfdKnZAUNI9Fs'
API_KEY = 'TXVzbXNNYk9BZHdJc3l1WllnYm15UT09'
DURIAN_USER = 'rafiqmolla7'
PROJECT_ID = '0257' 
GROUP_ID = -1003525081102 

ALLOWED_USERS = {
    6528471341: "Sojib", 8081334307: "Sojib Das",
    8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"
}

# প্যানেলের ডকুমেন্টেশন অনুযায়ী ফিক্সড কান্ট্রি নেম
COUNTRIES = {
    "🇺🇦 Ukraine": "Ukraine", "🇸🇸 S. Sudan": "South Sudan", "🇱🇨 S. Lucia": "Saint Lucia",
    "🇺🇸 USA": "United States", "🇬🇧 UK": "United Kingdom", "🇨🇦 Canada": "Canada",
    "🇮🇳 India": "India", "🇧🇩 BD": "Bangladesh", "🇷🇺 Russia": "Russia",
    "🇲🇾 Malaysia": "Malaysia", "🇮🇩 Indonesia": "Indonesia",
    "🇻🇳 Vietnam": "Vietnam", "🇹🇭 Thailand": "Thailand", "🇸🇦 S. Arabia": "Saudi Arabia",
    "🇸🇱 S. Leone": "Sierra Leone", "🇩🇿 Algeria": "Algeria", "🇹🇿 Tanzania": "Tanzania"
}

# --- ৩. ওটিপি অটো-ফেচ ও গ্রুপ সিঙ্ক ---
async def fetch_otp_task(context, chat_id, number, msg_id, user_id, country_name):
    # প্যানেল ওটিপি চেক করার সময় + চিহ্ন ছাড়া নম্বর চায়
    clean_num = ''.join(filter(str.isdigit, str(number)))
    url = f"https://api.durianrcs.com/out/ext_api/getVcode?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={clean_num}&serial=2"
    
    for _ in range(60): # ১০ মিনিট চেক করবে
        await asyncio.sleep(10)
        try:
            res = requests.get(url, timeout=10).json()
            if res.get('code') == 200 and res.get('data'):
                otp = res.get('data')
                
                # সাকসেস মেসেজ ও বাটন
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Get New Number", callback_data=f"get_{country_name}")]])
                await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"✅ **OTP Received!**\n📱 Num: `{number}`\n🔑 Code: `{otp}`", reply_markup=kb, parse_mode='Markdown')
                
                # সরাসরি আপনার গ্রুপে ওটিপি ফরোয়ার্ড
                group_msg = f"🔥 **Forwarded OTP:** `{otp}`\n📱 Num: `{number}`\n👤 User: {ALLOWED_USERS.get(user_id, 'Admin')}"
                await context.bot.send_message(chat_id=GROUP_ID, text=group_msg, parse_mode='Markdown')
                return
        except: pass
    
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏳ Timeout! `{number}` এ ওটিপি আসেনি।")

# --- ৪. হ্যান্ডলারস ---
def main_menu():
    return ReplyKeyboardMarkup([[KeyboardButton("📱 Get Number")], [KeyboardButton("💰 Balance"), KeyboardButton("ℹ️ My ID")], [KeyboardButton("📢 OTP Group")]], resize_keyboard=True)

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
        country_name = query.data.split("_")[1]
        sent_msg = await query.edit_message_text(f"🛰 Requesting **{country_name}** Only...")
        
        # প্যানেলকে নির্দিষ্ট দেশ দিতে বাধ্য করার জন্য স্ট্রিক্ট প্যারামিটার
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&country={country_name}&operator=any&force_country=1&is_not_standard=1"
        
        try:
            res = requests.get(url, timeout=10).json()
            if res.get('code') == 200:
                number = res.get('data')
                # ব্লক এবং রিকোয়েস্ট বাটন ফিক্স
                kb = InlineKeyboardMarkup([
                    [InlineKeyboardButton("🚫 Block/Cancel", callback_data=f"block_{number}_{country_name}")],
                    [InlineKeyboardButton("🔄 Request Again", callback_data=f"get_{country_name}")]
                ])
                await query.edit_message_text(f"🌍 **Country:** {country_name}\n📱 **Number:** `{number}`\n⏳ Waiting for OTP...", reply_markup=kb, parse_mode='Markdown')
                asyncio.create_task(fetch_otp_task(context, query.message.chat_id, number, sent_msg.message_id, query.from_user.id, country_name))
            else:
                await query.edit_message_text(f"❌ {country_name} Stock Out.", reply_markup=country_menu())
        except: await query.edit_message_text("❌ সার্ভার এরর!")

    elif query.data.startswith("block_"):
        data = query.data.split("_")
        num, country = data[1], data[2]
        clean_num = ''.join(filter(str.isdigit, num))
        requests.get(f"https://api.durianrcs.com/out/ext_api/cancelMobile?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={clean_num}&serial=2")
        await query.edit_message_text(f"🚫 Number `{num}` Blocked.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Try Again", callback_data=f"get_{country}")]]))

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, uid = update.message.text, update.effective_user.id
    if uid not in ALLOWED_USERS: return
    if text == "📱 Get Number": await update.message.reply_text("🌍 Select Country:", reply_markup=country_menu())
    elif text == "💰 Balance":
        res = requests.get(f"https://api.durianrcs.com/out/ext_api/getBalance?name={DURIAN_USER}&ApiKey={API_KEY}").json()
        await update.message.reply_text(f"💰 Balance: `{res.get('data', '0')}` Credits", parse_mode='Markdown')
    elif text == "ℹ️ My ID": await update.message.reply_text(f"🆔 ID: `{uid}`", parse_mode='Markdown')

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
