import logging, requests, asyncio, os
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# --- ১. রেন্ডার কানেক্টিভিটি ---
app_web = Flask('')
@app_web.route('/')
def home(): return "SYSTEM STATUS: ISO CODES ACTIVE"

def run():
    port = int(os.environ.get('PORT', 8080))
    app_web.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- ২. মেইন কনফিগারেশন ---
BOT_TOKEN = '8740780011:AAFZxUCXzcUJQzZPUFNJYYbfdKnZAUNI9Fs'
API_KEY = 'TXVzbXNNYk9BZHdJc3l1WllnYm15UT09'
DURIAN_USER = 'rafiqmolla7'
PROJECT_ID = '0257' 
GROUP_ID = -1003525081102 

ALLOWED_USERS = {
    6528471341: "Sojib", 8081334307: "Sojib Das",
    8181512467: "Admin", 8164389661: "pc", 6630618306: "Chandon"
}

# ২৮টি দেশের কান্ট্রি কোড (iso) লিস্ট
COUNTRIES = {
    "🇺🇸 USA": "us", "🇦🇴 Angola": "ao", "🇳🇬 Nigeria": "ng",
    "🇲🇿 Mozambique": "mz", "🇲🇽 Mexico": "mx", "🇰🇪 Kenya": "ke",
    "🇹🇭 Thailand": "th", "🇨🇲 Cameroon": "cm", "🇪🇬 Egypt": "eg",
    "🇸🇳 Senegal": "sn", "🇱🇾 Libya": "ly", "🇮🇳 India": "in",
    "🇷🇺 Russia": "ru", "🇨🇬 Congo (cg)": "cg", "🇦🇫 Afghanistan": "af",
    "🇲🇷 Mauritania": "mr", "🇹🇬 Togo": "tg", "🇹🇳 Tunisia": "tn",
    "🇦🇷 Argentina": "ar", "🇩🇿 Algeria": "dz", "🇲🇼 Malawi": "mw",
    "🇿🇲 Zambia": "zm", "🇻🇪 Venezuela": "ve", "🇺🇬 Uganda": "ug",
    "🇬🇭 Ghana": "gh", "🇪🇹 Ethiopia": "et", "🇩🇴 Dominican": "do",
    "🇨🇩 Congo (cd)": "cd"
}

# --- ৩. ওটিপি ও কনফার্মেশন লজিক ---
async def fetch_otp_task(context, chat_id, full_number, msg_id, user_id, iso_code):
    num_only = ''.join(filter(str.isdigit, str(full_number)))
    
    # নম্বরটি "Pick Up" করার জন্য রিকোয়েস্ট (যাতে প্যানেলে Not Taken না আসে)
    requests.get(f"https://api.durianrcs.com/out/ext_api/setRelease?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2", timeout=5)
    
    vcode_url = f"https://api.durianrcs.com/out/ext_api/getVcode?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num_only}&serial=2"
    
    for _ in range(60): 
        await asyncio.sleep(10)
        try:
            res = requests.get(vcode_url, timeout=10).json()
            if res.get('code') == 200 and res.get('data'):
                otp = res.get('data')
                
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Get New Number", callback_data=f"get_{iso_code}")]])
                await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, 
                    text=f"✅ **OTP Received!**\n\n📱 **Num:** `{full_number}`\n🔑 **Code:** `{otp}`", 
                    reply_markup=kb, parse_mode='Markdown')
                
                await context.bot.send_message(chat_id=GROUP_ID, 
                    text=f"🔥 **New OTP Alert!**\n🔑 Code: `{otp}`\n📱 Num: `{full_number}`\n👤 User: {ALLOWED_USERS.get(user_id, 'Admin')}", 
                    parse_mode='Markdown')
                return
        except: pass
    await context.bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏳ Timeout! `{full_number}` এ ওটিপি আসেনি।")

# --- ৪. কমান্ড ও বাটনস ---
def main_menu():
    return ReplyKeyboardMarkup([[KeyboardButton("📱 Get Number")], [KeyboardButton("💰 Balance"), KeyboardButton("ℹ️ My ID")]], resize_keyboard=True)

def country_menu():
    buttons = []
    keys = list(COUNTRIES.keys())
    for i in range(0, len(keys), 2):
        row = [InlineKeyboardButton(keys[i], callback_data=f"get_{COUNTRIES[keys[i]]}")]
        if i+1 < len(keys):
            row.append(InlineKeyboardButton(keys[i+1], callback_data=f"get_{COUNTRIES[keys[i+1]]}"))
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ALLOWED_USERS:
        await update.message.reply_text("🌑 **CS DARK BOT**\nCountry ISO codes enabled.", reply_markup=main_menu())

async def callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith("get_"):
        iso = query.data.split("_")[1]
        sent_msg = await query.edit_message_text(f"🛰 Requesting **{iso.upper()}** Number...")
        
        # এখানে 'iso' প্যারামিটার ব্যবহার করা হয়েছে নির্দিষ্ট কান্ট্রি কোডের জন্য
        url = f"https://api.durianrcs.com/out/ext_api/getMobile?name={DURIAN_USER}&ApiKey={API_KEY}&pid={PROJECT_ID}&num=1&serial=2&iso={iso}&force_country=1"
        
        try:
            res = requests.get(url, timeout=15).json()
            if res.get('code') == 200:
                number = res.get('data')
                kb = InlineKeyboardMarkup([[InlineKeyboardButton("🚫 Block/Cancel", callback_data=f"block_{number}_{iso}")]])
                await query.edit_message_text(f"🌍 **Country Code:** {iso.upper()}\n📱 **Number:** `{number}`\n⏳ Waiting for OTP...", reply_markup=kb, parse_mode='Markdown')
                asyncio.create_task(fetch_otp_task(context, query.message.chat_id, number, sent_msg.message_id, query.from_user.id, iso))
            else:
                await query.edit_message_text(f"❌ {iso.upper()} এ স্টক নেই।", reply_markup=country_menu())
        except: await query.edit_message_text("❌ এপিআই সংযোগে সমস্যা হচ্ছে।")

    elif query.data.startswith("block_"):
        data = query.data.split("_")
        num = ''.join(filter(str.isdigit, data[1]))
        requests.get(f"https://api.durianrcs.com/out/ext_api/cancelMobile?name={DURIAN_USER}&ApiKey={API_KEY}&mobile={num}&serial=2")
        await query.edit_message_text(f"🚫 `{data[1]}` বাতিল করা হয়েছে।", reply_markup=country_menu())

async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, uid = update.message.text, update.effective_user.id
    if uid not in ALLOWED_USERS: return
    if text == "📱 Get Number": await update.message.reply_text("🌍 Select Country:", reply_markup=country_menu())
    elif text == "💰 Balance":
        res = requests.get(f"https://api.durianrcs.com/out/ext_api/getBalance?name={DURIAN_USER}&ApiKey={API_KEY}").json()
        await update.message.reply_text(f"💰 Balance: `{res.get('data', '0')}` Credits", parse_mode='Markdown')

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
